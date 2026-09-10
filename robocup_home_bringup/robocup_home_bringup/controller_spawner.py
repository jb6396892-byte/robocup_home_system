import argparse
import sys

import rclpy
from controller_manager import configure_controller, list_controllers, load_controller, switch_controllers
from rclpy.node import Node


def _states(node: Node, manager: str, timeout: float) -> dict[str, str]:
    response = list_controllers(
        node, manager, service_timeout=timeout, call_timeout=timeout)
    return {controller.name: controller.state for controller in response.controller}


def main(args=None):
    parser = argparse.ArgumentParser(description='稳定加载并启动整机控制器')
    parser.add_argument('controllers', nargs='+')
    parser.add_argument('--controller-manager', default='/controller_manager')
    parser.add_argument('--timeout', type=float, default=60.0)
    parsed, ros_args = parser.parse_known_args(args)

    rclpy.init(args=ros_args)
    node = Node('robocup_controller_spawner')
    ok = False
    try:
        manager = parsed.controller_manager
        timeout = parsed.timeout
        states = _states(node, manager, timeout)

        for name in parsed.controllers:
            if name in states:
                node.get_logger().info(f'控制器已加载，跳过：{name} ({states[name]})')
                continue
            node.get_logger().info(f'正在加载控制器：{name}')
            response = load_controller(
                node, manager, name, service_timeout=timeout, call_timeout=timeout)
            if not response.ok:
                node.get_logger().error(f'控制器加载失败：{name}')
                raise RuntimeError(name)
            states = _states(node, manager, timeout)

        for name in parsed.controllers:
            state = states.get(name)
            if state == 'unconfigured':
                node.get_logger().info(f'正在配置控制器：{name}')
                response = configure_controller(
                    node, manager, name, service_timeout=timeout, call_timeout=timeout)
                if not response.ok:
                    node.get_logger().error(f'控制器配置失败：{name}')
                    raise RuntimeError(name)
                states = _states(node, manager, timeout)

        activate = [name for name in parsed.controllers if states.get(name) != 'active']
        if activate:
            node.get_logger().info('正在统一启动控制器：' + ', '.join(activate))
            response = switch_controllers(
                node, manager, [], activate, True, True, timeout, call_timeout=timeout)
            if not response.ok:
                node.get_logger().error('控制器统一启动失败')
                raise RuntimeError(','.join(activate))

        states = _states(node, manager, timeout)
        ok = all(states.get(name) == 'active' for name in parsed.controllers)
        if ok:
            node.get_logger().info('全部控制器已启动')
        else:
            detail = ', '.join(f'{name}={states.get(name, "缺失")}' for name in parsed.controllers)
            node.get_logger().error('控制器状态不正确：' + detail)
    except Exception as error:  # controller_manager 的服务异常类型因版本不同而变化
        node.get_logger().error(f'控制器启动失败：{error}')
    finally:
        node.destroy_node()
        rclpy.shutdown()

    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
