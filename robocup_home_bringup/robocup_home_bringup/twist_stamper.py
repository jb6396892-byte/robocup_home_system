import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node


class TwistStamper(Node):
    def __init__(self):
        super().__init__('twist_stamper')
        self.declare_parameter('input_topic', '/cmd_vel')
        self.declare_parameter('output_topic', '/swerve_drive_controller/cmd_vel')
        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self._publisher = self.create_publisher(TwistStamped, output_topic, 10)
        self._subscription = self.create_subscription(Twist, input_topic, self._on_twist, 10)
        self.get_logger().info(f'Adapting Twist {input_topic} -> TwistStamped {output_topic}')

    def _on_twist(self, message: Twist) -> None:
        stamped = TwistStamped()
        stamped.header.stamp = self.get_clock().now().to_msg()
        stamped.header.frame_id = 'base_link'
        stamped.twist = message
        self._publisher.publish(stamped)


def main(args=None):
    rclpy.init(args=args)
    node = TwistStamper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
