import threading
import time
from pathlib import Path

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from robocup_home_interfaces.msg import MissionStatus
from robocup_home_interfaces.srv import SetTargets

from .go_to_location import LocationNavigator


class Stage2TaskServer(Node):
    """阶段 2 的最小任务入口：收到三项任务后自动去客厅入口。"""

    def __init__(self):
        super().__init__('stage2_task_server')
        self.declare_parameter('location', 'living_room_entry')
        self.declare_parameter('navigation_timeout', 180.0)
        default_locations = str(
            Path(get_package_share_directory('robocup_home_navigation')) / 'config' / 'locations.yaml')
        self.declare_parameter('locations_file', default_locations)
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.status_publisher = self.create_publisher(
            MissionStatus, '/mission/status', qos)
        self.service = self.create_service(
            SetTargets, '/competition/set_targets', self._on_targets)
        self._lock = threading.Lock()
        self._running = False
        self._started_at = time.monotonic()
        self._publish_status('WAIT_TARGETS', MissionStatus.RUNNING, '等待三个目标名称')
        self.get_logger().info('阶段 2 任务入口已就绪：/competition/set_targets')

    def _publish_status(self, state, result, detail):
        message = MissionStatus()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'map'
        message.state = state
        message.result = result
        message.detail = detail
        message.elapsed_seconds = float(time.monotonic() - self._started_at)
        self.status_publisher.publish(message)

    def _on_targets(self, request, response):
        names = [name.strip() for name in request.target_names]
        if any(not name for name in names) or len(set(names)) != 3:
            response.accepted = False
            response.message = '必须提供三个非空且互不重复的名称'
            return response
        with self._lock:
            if self._running:
                response.accepted = False
                response.message = '当前任务仍在执行'
                return response
            self._running = True
        response.accepted = True
        response.message = '目标已接收，开始导航至客厅'
        response.target_ids = names
        threading.Thread(target=self._navigate_worker, daemon=True).start()
        return response

    def _navigate_worker(self):
        location_name = self.get_parameter('location').value
        locations_file = Path(self.get_parameter('locations_file').value)
        timeout = float(self.get_parameter('navigation_timeout').value)
        try:
            with locations_file.open(encoding='utf-8') as stream:
                location = yaml.safe_load(stream)['locations'][location_name]
            self._publish_status(
                'NAVIGATING_TO_LIVING_ROOM', MissionStatus.RUNNING,
                f'正在前往 {location_name}')
            navigator = LocationNavigator(timeout)
            try:
                success = navigator.navigate(location_name, location)
                if not success:
                    navigator.recover()
                    success = navigator.navigate(location_name, location)
            finally:
                navigator.close()
            if success:
                self._publish_status(
                    'ARRIVED_LIVING_ROOM', MissionStatus.SUCCEEDED, '已经到达客厅入口')
            else:
                self._publish_status(
                    'NAVIGATION_FAILED', MissionStatus.FAILED, '恢复并重试一次后仍失败')
        except Exception as error:  # 任务线程不能让服务节点退出
            self.get_logger().error(f'阶段 2 任务异常：{error}')
            self._publish_status('NAVIGATION_FAILED', MissionStatus.FAILED, str(error))
        finally:
            with self._lock:
                self._running = False


def main(args=None):
    rclpy.init(args=args)
    node = Stage2TaskServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
