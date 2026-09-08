import argparse
import pathlib
import shutil
import subprocess
import sys
import time

import rclpy
import yaml
from controller_manager_msgs.srv import ListControllers
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CameraInfo, Image, Imu, JointState, LaserScan
from tf2_msgs.msg import TFMessage


REQUIRED_MESSAGES = {
    '/clock': Clock,
    '/scan': LaserScan,
    '/camera/image': Image,
    '/camera/depth_image': Image,
    '/camera/camera_info': CameraInfo,
    '/imu/data': Imu,
    '/swerve_drive_controller/odom': Odometry,
    '/joint_states': JointState,
}


def _print(ok: bool, label: str, detail: str = '') -> None:
    state = 'PASS' if ok else 'FAIL'
    suffix = f' - {detail}' if detail else ''
    print(f'[{state}] {label}{suffix}')


def static_checks() -> bool:
    ok = True
    expected = {
        'WPR example world': pathlib.Path('/home/smg/wpr_ros2_ws/src/wpr_simulation_ros2/worlds/example.world'),
        'Franka overlay': pathlib.Path('/home/smg/franka_ros2_ws/install/setup.bash'),
        'class whitelist': pathlib.Path('/home/smg/robocup_home_ws/src/robocup_home_system/config/object_classes.yaml'),
        'ROS-aware Python venv': pathlib.Path('/home/smg/robocup_home_ws/.venv/bin/python'),
    }
    for name, path in expected.items():
        exists = path.is_file()
        _print(exists, name, str(path))
        ok &= exists
    class_file = expected['class whitelist']
    model_root = pathlib.Path('/home/smg/wpr_ros2_ws/src/wpr_simulation_ros2/models')
    if class_file.is_file() and model_root.is_dir():
        class_ids = {item['id'] for item in yaml.safe_load(class_file.read_text())['classes']}
        missing_models = sorted(name for name in class_ids if not (model_root / name / 'model.config').is_file())
    else:
        missing_models = ['model root or class file unavailable']
    models_ok = not missing_models and len(class_ids) == 18
    _print(models_ok, '18 competition models', 'missing: ' + ', '.join(missing_models) if missing_models else str(model_root))
    ok &= models_ok
    has_gpu_tool = shutil.which('nvidia-smi') is not None
    if has_gpu_tool:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,driver_version', '--format=csv,noheader'],
            capture_output=True, text=True, timeout=5, check=False)
        has_gpu_tool = result.returncode == 0
        detail = result.stdout.strip() or result.stderr.strip()
    else:
        detail = 'driver unavailable; install/reboot still required'
    _print(has_gpu_tool, 'NVIDIA runtime', detail)
    if not has_gpu_tool:
        ok = False
    swap_entries = pathlib.Path('/proc/swaps').read_text().splitlines()[1:]
    has_swap = bool(swap_entries)
    _print(has_swap, 'swap', swap_entries[0].split()[0] if has_swap else 'none active; 16 GB recommended')
    ok &= has_swap
    return ok


class RuntimeChecker(Node):
    def __init__(self):
        super().__init__('robocup_health_check')
        self.client = self.create_client(ListControllers, '/controller_manager/list_controllers')
        self.received = set()
        self.tf_edges = set()
        self._health_subscriptions = [
            self.create_subscription(message_type, topic, lambda _msg, name=topic: self.received.add(name), qos_profile_sensor_data)
            for topic, message_type in REQUIRED_MESSAGES.items()
        ]
        self._health_subscriptions.append(
            self.create_subscription(TFMessage, '/tf', self._on_tf, qos_profile_sensor_data))
        static_qos = QoSProfile(depth=100)
        static_qos.reliability = ReliabilityPolicy.RELIABLE
        static_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self._health_subscriptions.append(
            self.create_subscription(TFMessage, '/tf_static', self._on_tf, static_qos))

    def _on_tf(self, message: TFMessage) -> None:
        for transform in message.transforms:
            self.tf_edges.add((transform.header.frame_id, transform.child_frame_id))

    def _connected(self, start: str, goal: str) -> bool:
        graph = {}
        for parent, child in self.tf_edges:
            graph.setdefault(parent, set()).add(child)
            graph.setdefault(child, set()).add(parent)
        pending = [start]
        visited = set()
        while pending:
            frame = pending.pop()
            if frame == goal:
                return True
            if frame in visited:
                continue
            visited.add(frame)
            pending.extend(graph.get(frame, ()) - visited)
        return False

    def check(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        missing = set(REQUIRED_MESSAGES)
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
            missing.difference_update(self.received)
            if not missing:
                break
        topics_ok = not missing
        _print(topics_ok, 'required ROS messages', 'no data: ' + ', '.join(sorted(missing)) if missing else 'all received')

        transforms = (
            ('map', 'odom'), ('odom', 'base_link'), ('base_link', 'lidar_link'),
            ('base_link', 'rgbd_camera_link'), ('base_link', 'fr3_link0'),
            ('base_link', 'fr3_hand_tcp'),
        )
        pending_tf = set(transforms)
        tf_deadline = time.monotonic() + min(timeout, 5.0)
        while rclpy.ok() and pending_tf and time.monotonic() < tf_deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            pending_tf = {
                pair for pair in pending_tf
                if not self._connected(pair[0], pair[1])
            }
        tf_missing = [f'{target}<-{source}' for target, source in sorted(pending_tf)]
        tf_ok = not tf_missing
        _print(tf_ok, 'TF tree', 'missing: ' + ', '.join(tf_missing) if tf_missing else 'connected')

        controllers_ok = False
        detail = 'controller_manager service unavailable'
        if self.client.wait_for_service(timeout_sec=2.0):
            future = self.client.call_async(ListControllers.Request())
            rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)
            if future.done() and future.result() is not None:
                states = {c.name: c.state for c in future.result().controller}
                needed = {
                    'joint_state_broadcaster', 'swerve_ik_controller', 'swerve_drive_controller',
                    'fr3_arm_controller', 'fr3_gripper', 'fr3_gripper_mirror',
                }
                controllers_ok = all(states.get(name) == 'active' for name in needed)
                detail = ', '.join(f'{name}={states.get(name, "missing")}' for name in sorted(needed))
        _print(controllers_ok, 'controllers', detail)
        return topics_ok and tf_ok and controllers_ok


def main(args=None):
    parser = argparse.ArgumentParser(description='Stage 0/1 health check')
    parser.add_argument('--static-only', action='store_true')
    parser.add_argument('--timeout', type=float, default=15.0)
    parsed, ros_args = parser.parse_known_args(args)
    ok = static_checks()
    if not parsed.static_only:
        rclpy.init(args=ros_args)
        node = RuntimeChecker()
        try:
            ok = node.check(parsed.timeout) and ok
        finally:
            node.destroy_node()
            rclpy.shutdown()
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1:])
