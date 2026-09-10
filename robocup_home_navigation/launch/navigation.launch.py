import hashlib
import os
import pathlib
import tempfile

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _merge(base, override):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def _start_nav2(context):
    nav_share = get_package_share_directory('robocup_home_navigation')
    nav2_share = get_package_share_directory('nav2_bringup')
    map_file = pathlib.Path(LaunchConfiguration('map').perform(context)).expanduser()
    override_file = pathlib.Path(nav_share) / 'config' / 'nav2_overrides.yaml'
    if not map_file.is_file():
        raise RuntimeError(f'地图文件不存在：{map_file}')

    with open(os.path.join(nav2_share, 'params', 'nav2_params.yaml'), encoding='utf-8') as stream:
        params = yaml.safe_load(stream)
    with override_file.open(encoding='utf-8') as stream:
        _merge(params, yaml.safe_load(stream))
    encoded = yaml.safe_dump(params, sort_keys=False).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:12]
    merged_file = pathlib.Path(tempfile.gettempdir()) / f'robocup_nav2_{digest}.yaml'
    merged_file.write_bytes(encoded)

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_share, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'map': str(map_file),
            'params_file': str(merged_file),
            'use_sim_time': 'true',
            'autostart': 'true',
            # Humble bringup_launch.py evaluates this value as a Python expression.
            'slam': 'False',
            'use_composition': 'False',
            'use_respawn': 'false',
        }.items())
    return [
        LogInfo(msg=['阶段 2：自动定位并启动 Nav2，map=', str(map_file)]),
        TimerAction(period=8.0, actions=[nav2]),
    ]


def generate_launch_description():
    nav_share = get_package_share_directory('robocup_home_navigation')
    bringup_share = get_package_share_directory('robocup_home_bringup')
    wpr_share = get_package_share_directory('wpr_simulation_ros2')
    robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'competition.launch.py')),
        launch_arguments={
            'world_path': LaunchConfiguration('world_path'),
            'target_source': LaunchConfiguration('target_source'),
            'mode': LaunchConfiguration('mode'),
            'gui': LaunchConfiguration('gui'),
            'spawn_x': LaunchConfiguration('spawn_x'),
            'spawn_y': LaunchConfiguration('spawn_y'),
            'spawn_z': LaunchConfiguration('spawn_z'),
            'publish_static_map_odom': 'false',
        }.items())
    return LaunchDescription([
        DeclareLaunchArgument(
            'world_path',
            default_value=os.path.join(wpr_share, 'worlds', 'example.world')),
        DeclareLaunchArgument(
            'map', default_value=os.path.join(nav_share, 'maps', 'example.yaml')),
        DeclareLaunchArgument('target_source', default_value='service'),
        DeclareLaunchArgument('mode', default_value='test', choices=['test', 'competition']),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('spawn_x', default_value='0.0'),
        DeclareLaunchArgument('spawn_y', default_value='0.0'),
        DeclareLaunchArgument('spawn_z', default_value='0.0'),
        robot,
        Node(
            package='robocup_home_navigation', executable='stage2_task_server',
            parameters=[{'use_sim_time': True}], output='screen'),
        OpaqueFunction(function=_start_nav2),
    ])
