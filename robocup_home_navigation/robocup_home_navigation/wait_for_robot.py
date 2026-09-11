"""等机器人控制链和导航传感器就绪后再启动 Nav2。"""

import time

import rclpy
from controller_manager_msgs.srv import ListControllers
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from tf2_msgs.msg import TFMessage


class RobotReadinessWaiter(Node):
    def __init__(self):
        super().__init__('navigation_robot_readiness')
        self.scan_received = False
        self.odom_received = False
        self.odom_tf_received = False
        self.controller_client = self.create_client(
            ListControllers, '/controller_manager/list_controllers')
        self.create_subscription(
            LaserScan, '/scan', self._on_scan, qos_profile_sensor_data)
        self.create_subscription(
            Odometry, '/swerve_drive_controller/odom', self._on_odom,
            qos_profile_sensor_data)
        self.create_subscription(
            TFMessage, '/tf', self._on_tf, qos_profile_sensor_data)

    def _on_scan(self, _message):
        self.scan_received = True

    def _on_odom(self, _message):
        self.odom_received = True

    def _on_tf(self, message):
        for transform in message.transforms:
            parent = transform.header.frame_id.lstrip('/')
            child = transform.child_frame_id.lstrip('/')
            if parent == 'odom' and child == 'base_link':
                self.odom_tf_received = True

    def controllers_ready(self):
        if not self.controller_client.wait_for_service(timeout_sec=0.2):
            return False
        future = self.controller_client.call_async(ListControllers.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=1.0)
        if not future.done() or future.result() is None:
            return False
        states = {item.name: item.state for item in future.result().controller}
        return states.get('swerve_drive_controller') == 'active'

    def wait(self):
        self.get_logger().info('等待底盘控制器、激光雷达、里程计和 TF 就绪……')
        last_report = 0.0
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.2)
            controller_ready = self.controllers_ready()
            if (controller_ready and self.scan_received and self.odom_received
                    and self.odom_tf_received):
                self.get_logger().info('机器人已就绪，现在启动定位和 Nav2')
                return
            now = time.monotonic()
            if now - last_report >= 5.0:
                self.get_logger().info(
                    f'等待中：底盘={controller_ready}，激光={self.scan_received}，'
                    f'里程计={self.odom_received}，'
                    f'odom->base_link={self.odom_tf_received}')
                last_report = now


def main(args=None):
    rclpy.init(args=args)
    node = RobotReadinessWaiter()
    try:
        node.wait()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
