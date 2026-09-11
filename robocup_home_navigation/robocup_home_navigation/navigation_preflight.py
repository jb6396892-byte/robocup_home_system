"""阻止在已有整机仿真上再次启动同名机器人和 Nav2。"""

import time

import rclpy
from rclpy.node import Node


def main(args=None):
    rclpy.init(args=args)
    node = Node('navigation_preflight')
    try:
        # 给 DDS 一点时间发现已经存在的节点和服务。
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        services = {name for name, _types in node.get_service_names_and_types()}
        nodes = {name for name, _namespace in node.get_node_names_and_namespaces()}
        conflicts = []
        if '/controller_manager/list_controllers' in services:
            conflicts.append('controller_manager')
        for name in ('amcl', 'planner_server', 'controller_server'):
            if name in nodes:
                conflicts.append(name)
        if conflicts:
            node.get_logger().error(
                '检测到上一套仿真仍在运行：' + '、'.join(conflicts)
                + '。请先关闭旧的 ros2 launch/Gazebo，再重新启动导航。')
            raise SystemExit(2)
        node.get_logger().info('启动检查通过：当前没有重复的机器人或 Nav2 实例')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
