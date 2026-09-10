import time

import rclpy
from control_msgs.action import FollowJointTrajectory
from geometry_msgs.msg import Twist
from rclpy.action import ActionClient
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectoryPoint


JOINTS = [f'fr3_joint{i}' for i in range(1, 8)]
STOW = [0.0, -0.7854, 0.0, -2.3562, 0.0, 1.5708, 0.7854]


class SmokeTest(Node):
    def __init__(self):
        super().__init__('stage1_smoke_test')
        self.cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.arm = ActionClient(self, FollowJointTrajectory, '/fr3_arm_controller/follow_joint_trajectory')

    def drive(self, x: float, yaw: float, seconds: float) -> None:
        command = Twist()
        command.linear.x = x
        command.angular.z = yaw
        end = time.monotonic() + seconds
        while rclpy.ok() and time.monotonic() < end:
            self.cmd_vel.publish(command)
            rclpy.spin_once(self, timeout_sec=0.05)
        self.cmd_vel.publish(Twist())
        rclpy.spin_once(self, timeout_sec=0.2)

    def move_arm(self, positions, seconds: int = 3) -> bool:
        if not self.arm.wait_for_server(timeout_sec=8.0):
            self.get_logger().error('FR3 轨迹 Action 不可用')
            return False
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINTS
        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = seconds
        goal.trajectory.points = [point]
        send_future = self.arm.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=5.0)
        if not send_future.done() or not send_future.result().accepted:
            self.get_logger().error('FR3 轨迹被控制器拒绝')
            return False
        result_future = send_future.result().get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=seconds + 8.0)
        if not result_future.done():
            self.get_logger().error('等待 FR3 轨迹结果超时')
            return False
        result = result_future.result().result
        if result.error_code != 0:
            self.get_logger().error(
                f'FR3 轨迹失败：code={result.error_code}, {result.error_string}')
            return False
        return True


def main(args=None):
    rclpy.init(args=args)
    node = SmokeTest()
    ok = False
    try:
        node.get_logger().info('底盘依次前进、旋转并停止')
        node.drive(0.12, 0.0, 1.5)
        node.drive(0.0, 0.25, 1.5)
        node.drive(0.0, 0.0, 0.5)
        node.get_logger().info('FR3 离开收拢姿态后再返回')
        test_pose = STOW.copy()
        test_pose[0] = 0.20
        ok = node.move_arm(test_pose) and node.move_arm(STOW)
        if ok:
            node.get_logger().info('阶段 1 运动冒烟测试通过')
    finally:
        node.cmd_vel.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    raise SystemExit(0 if ok else 1)
