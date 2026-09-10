import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from ros_gz_interfaces.msg import Contacts
from std_msgs.msg import Bool


class TestCollisionMonitor(Node):
    """只做测试统计，绝不能被比赛状态机当作决策输入。"""

    def __init__(self):
        super().__init__('test_collision_monitor')
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.publisher = self.create_publisher(Bool, '/test/collision_detected', qos)
        self.subscription = self.create_subscription(
            Contacts, '/test/base_contacts', self._on_contacts, 10)
        self.count = 0
        self.get_logger().warning('Gazebo Contact 碰撞监视器已启动：仅限 test 模式')

    def _on_contacts(self, message):
        if not message.contacts:
            return
        self.count += 1
        self.publisher.publish(Bool(data=True))
        if self.count == 1 or self.count % 30 == 0:
            contact = message.contacts[0]
            self.get_logger().error(
                f'检测到碰撞 #{self.count}：'
                f'{contact.collision1.name} <-> {contact.collision2.name}')


def main(args=None):
    rclpy.init(args=args)
    node = TestCollisionMonitor()
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
