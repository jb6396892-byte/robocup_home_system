import hashlib
import os
import pathlib
import re
import tempfile
from xml.dom import minidom

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction, RegisterEventHandler, SetEnvironmentVariable
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _augment_world(world_path: pathlib.Path) -> pathlib.Path:
    content = world_path.read_text(encoding='utf-8')
    plugins = []
    if 'sensors-system' not in content:
        plugins.append('''
    <plugin filename="ignition-gazebo-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>''')
    if 'imu-system' not in content:
        plugins.append('''
    <plugin filename="ignition-gazebo-imu-system" name="gz::sim::systems::Imu"/>''')
    if not plugins:
        return world_path
    match = re.search(r'<world\b[^>]*>', content)
    if match is None:
        raise RuntimeError(f'世界文件中没有 <world> 元素：{world_path}')
    augmented = content[:match.end()] + ''.join(plugins) + content[match.end():]
    digest = hashlib.sha256(augmented.encode()).hexdigest()[:12]
    output = pathlib.Path(tempfile.gettempdir()) / f'robocup_world_{digest}.sdf'
    output.write_text(augmented, encoding='utf-8')
    return output


def _robot_description(description_share: str, controller_config: str) -> str:
    xacro_file = os.path.join(description_share, 'urdf', 'competition_robot.urdf.xacro')
    robot_xml = xacro.process_file(xacro_file, mappings={'controller_config': controller_config}).toxml()
    # Gazebo requires both finger joints as independent ros2_control resources.
    # The upstream URDF uses a mimic tag for finger 2, so remove only that tag.
    dom = minidom.parseString(robot_xml)
    for joint in dom.getElementsByTagName('joint'):
        if joint.getAttribute('name') == 'fr3_finger_joint2':
            for mimic in list(joint.getElementsByTagName('mimic')):
                joint.removeChild(mimic)
    return dom.toxml()


def _launch_setup(context):
    world = pathlib.Path(LaunchConfiguration('world_path').perform(context)).expanduser()
    if not world.is_absolute():
        raise RuntimeError(f'world_path 必须是绝对路径：{world}')
    if not world.is_file():
        raise RuntimeError(f'world_path 不存在：{world}')
    world = _augment_world(world)

    description_share = get_package_share_directory('robocup_home_description')
    controller_config = os.path.join(description_share, 'config', 'ros2_controllers.yaml')
    robot_description = _robot_description(description_share, controller_config)
    gz_share = get_package_share_directory('ros_gz_sim')
    wpr_share = get_package_share_directory('wpr_simulation_ros2')
    franka_share = get_package_share_directory('franka_description')
    gui = LaunchConfiguration('gui').perform(context).lower() in ('true', '1', 'yes')
    gz_args = f'-r -v 2 {world}' if gui else f'-r -s -v 2 {world}'
    resource_path = os.pathsep.join(filter(None, [
        os.path.join(wpr_share, 'models'),
        str(pathlib.Path(franka_share).parent),
        str(pathlib.Path(description_share).parent),
        os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
        os.environ.get('IGN_GAZEBO_RESOURCE_PATH', ''),
    ]))

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gz_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': gz_args, 'on_exit_shutdown': 'true'}.items())
    state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}], output='screen')
    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge', output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU',
        ],
        parameters=[{'use_sim_time': True}])
    create = Node(
        package='ros_gz_sim', executable='create', output='screen',
        arguments=['-name', 'robocup_home_robot', '-topic', 'robot_description',
                   '-x', LaunchConfiguration('spawn_x'), '-y', LaunchConfiguration('spawn_y'),
                   '-z', LaunchConfiguration('spawn_z')])
    spawner = Node(
        package='robocup_home_bringup', executable='controller_spawner', output='screen',
        arguments=['joint_state_broadcaster', 'swerve_ik_controller', 'swerve_drive_controller',
                   'fr3_arm_controller', 'fr3_gripper', 'fr3_gripper_mirror',
                   '--controller-manager', '/controller_manager', '--timeout', '60'])
    start_controllers = RegisterEventHandler(OnProcessExit(target_action=create, on_exit=[spawner]))
    return [
        LogInfo(msg=['阶段 1：world=', str(world), ', target_source=', LaunchConfiguration('target_source')]),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', resource_path),
        SetEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', resource_path),
        gazebo,
        state_publisher,
        bridge,
        Node(package='tf2_ros', executable='static_transform_publisher',
             arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
             parameters=[{'use_sim_time': True}], output='screen'),
        Node(package='robocup_home_bringup', executable='twist_stamper',
             parameters=[{'use_sim_time': True}], output='screen'),
        create,
        start_controllers,
    ]


def generate_launch_description():
    default_world = os.path.join(
        get_package_share_directory('wpr_simulation_ros2'), 'worlds', 'example.world')
    return LaunchDescription([
        DeclareLaunchArgument('world_path', default_value=default_world,
                              description='任意 SDF/world 文件的绝对路径'),
        DeclareLaunchArgument('target_source', default_value='service',
                              choices=['service', 'voice']),
        DeclareLaunchArgument('mode', default_value='test', choices=['test', 'competition']),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('spawn_x', default_value='0.0'),
        DeclareLaunchArgument('spawn_y', default_value='0.0'),
        DeclareLaunchArgument('spawn_z', default_value='0.0'),
        OpaqueFunction(function=_launch_setup),
    ])
