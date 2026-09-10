import argparse
import math
import time
from pathlib import Path

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Point, PoseStamped
from nav2_msgs.action import BackUp, NavigateToPose, Spin
from nav2_msgs.srv import ClearEntireCostmap
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node


class LocationNavigator(Node):
    def __init__(self, timeout):
        super().__init__('go_to_location')
        self.timeout = timeout
        # 使用独立执行器，确保本节点可安全嵌入任务服务的后台线程。
        self._executor = SingleThreadedExecutor(context=self.context)
        self._executor.add_node(self)
        self.navigator = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.backup = ActionClient(self, BackUp, '/backup')
        self.spin = ActionClient(self, Spin, '/spin')
        self.local_clear = self.create_client(
            ClearEntireCostmap, '/local_costmap/clear_entirely_local_costmap')
        self.global_clear = self.create_client(
            ClearEntireCostmap, '/global_costmap/clear_entirely_global_costmap')
        self._last_feedback = 0.0

    def _wait(self, future, timeout):
        deadline = time.monotonic() + timeout
        while rclpy.ok() and not future.done() and time.monotonic() < deadline:
            self._executor.spin_once(timeout_sec=0.1)
        return future.done()

    def close(self):
        self._executor.remove_node(self)
        self._executor.shutdown()
        self.destroy_node()

    def _feedback(self, message):
        now = time.monotonic()
        if now - self._last_feedback > 3.0:
            remaining = message.feedback.distance_remaining
            self.get_logger().info(f'距目标约 {remaining:.2f} m')
            self._last_feedback = now

    def navigate(self, name, location):
        if not self.navigator.wait_for_server(timeout_sec=30.0):
            self.get_logger().error('Nav2 的 /navigate_to_pose 尚未就绪')
            return False
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = float(location['x'])
        goal.pose.pose.position.y = float(location['y'])
        yaw = float(location['yaw'])
        goal.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(yaw / 2.0)
        self.get_logger().info(
            f'前往 {name}：x={location["x"]:.2f}, y={location["y"]:.2f}, yaw={yaw:.2f}')
        send_future = self.navigator.send_goal_async(goal, feedback_callback=self._feedback)
        if not self._wait(send_future, 10.0) or not send_future.result().accepted:
            self.get_logger().error('导航目标未被接受')
            return False
        handle = send_future.result()
        result_future = handle.get_result_async()
        if not self._wait(result_future, self.timeout):
            self.get_logger().error(f'导航超过 {self.timeout:.0f} 秒，取消本次目标')
            cancel = handle.cancel_goal_async()
            self._wait(cancel, 5.0)
            return False
        return result_future.result().status == GoalStatus.STATUS_SUCCEEDED

    def _clear(self, client, label):
        if not client.wait_for_service(timeout_sec=5.0):
            self.get_logger().warning(f'{label}清除服务不可用')
            return
        future = client.call_async(ClearEntireCostmap.Request())
        if self._wait(future, 5.0):
            self.get_logger().info(f'已清除{label}')
        else:
            self.get_logger().warning(f'清除{label}超时')

    def _run_recovery_action(self, client, goal, label):
        if not client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warning(f'{label}恢复动作不可用')
            return
        send = client.send_goal_async(goal)
        if not self._wait(send, 5.0) or not send.result().accepted:
            self.get_logger().warning(f'{label}恢复动作未被接受')
            return
        result = send.result().get_result_async()
        if not self._wait(result, 15.0):
            self.get_logger().warning(f'{label}恢复动作超时')

    def recover(self):
        self.get_logger().warning('导航失败：清代价地图，然后后退并旋转')
        self._clear(self.local_clear, '局部代价地图')
        self._clear(self.global_clear, '全局代价地图')
        backup_goal = BackUp.Goal()
        backup_goal.target = Point(x=-0.20)
        backup_goal.speed = 0.08
        backup_goal.time_allowance.sec = 10
        self._run_recovery_action(self.backup, backup_goal, '后退')
        spin_goal = Spin.Goal()
        spin_goal.target_yaw = 0.70
        spin_goal.time_allowance.sec = 10
        self._run_recovery_action(self.spin, spin_goal, '旋转')


def _load_location(path, name):
    with path.open(encoding='utf-8') as stream:
        locations = yaml.safe_load(stream)['locations']
    if name not in locations:
        choices = '、'.join(locations)
        raise KeyError(f'没有地点 {name}；可选：{choices}')
    return locations[name]


def main(args=None):
    default_file = Path(get_package_share_directory('robocup_home_navigation')) / 'config' / 'locations.yaml'
    parser = argparse.ArgumentParser(description='导航到预设地点，失败后恢复并重试一次')
    parser.add_argument('location', nargs='?', default='living_room_entry')
    parser.add_argument('--locations-file', type=Path, default=default_file)
    parser.add_argument('--timeout', type=float, default=180.0)
    parsed, ros_args = parser.parse_known_args(args)
    try:
        location = _load_location(parsed.locations_file, parsed.location)
    except (OSError, KeyError, TypeError) as error:
        parser.error(str(error))

    rclpy.init(args=ros_args)
    node = LocationNavigator(parsed.timeout)
    success = False
    try:
        success = node.navigate(parsed.location, location)
        if not success:
            node.recover()
            node.get_logger().info('只重试一次导航')
            success = node.navigate(parsed.location, location)
        if success:
            node.get_logger().info(f'已经到达 {parsed.location}')
        else:
            node.get_logger().error(f'未能到达 {parsed.location}，不再继续重试')
    except KeyboardInterrupt:
        node.get_logger().warning('用户中止导航')
    finally:
        node.close()
        if rclpy.ok():
            rclpy.shutdown()
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
