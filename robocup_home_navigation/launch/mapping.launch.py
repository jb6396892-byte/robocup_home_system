import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    nav_share = get_package_share_directory('robocup_home_navigation')
    bringup_share = get_package_share_directory('robocup_home_bringup')
    wpr_share = get_package_share_directory('wpr_simulation_ros2')
    slam_share = get_package_share_directory('slam_toolbox')

    robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'competition.launch.py')),
        launch_arguments={
            'world_path': LaunchConfiguration('world_path'),
            'gui': LaunchConfiguration('gui'),
            'publish_static_map_odom': 'false',
        }.items())
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_share, 'launch', 'online_async_launch.py')),
        launch_arguments={
            'use_sim_time': 'true',
            'slam_params_file': os.path.join(nav_share, 'config', 'slam_toolbox.yaml'),
        }.items())

    return LaunchDescription([
        DeclareLaunchArgument(
            'world_path',
            default_value=os.path.join(wpr_share, 'worlds', 'example.world')),
        DeclareLaunchArgument('gui', default_value='true'),
        robot,
        TimerAction(period=8.0, actions=[slam]),
    ])
