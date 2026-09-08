# SEU 2026 RoboCup@Home system

ROS 2 Humble / Gazebo Fortress workspace for the TMR + single FR3 competition robot.
Upstream WPR and Franka repositories remain unmodified and are sourced as overlays.

## Build

```bash
cd ~/robocup_home_ws
source /opt/ros/humble/setup.bash
source ~/wpr_ros2_ws/install/setup.bash
source ~/franka_ros2_ws/install/setup.bash
colcon build --symlink-install
source install/setup.bash
```

The helper `source src/robocup_home_system/scripts/setup_env.bash` applies that order.

## Stage 1 launch

```bash
ros2 launch robocup_home_bringup competition.launch.py \
  world_path:=/home/smg/wpr_ros2_ws/src/wpr_simulation_ros2/worlds/example.world \
  target_source:=service gui:=true
```

Drive through `/cmd_vel` (`geometry_msgs/Twist`). The adapter republishes stamped
commands to the TMR controller. Use `ros2 run robocup_home_bringup health_check`
after startup. See `docs/STAGE_0_1.md` for checks and test commands.

Large datasets, bags and model weights are deliberately excluded from this repository.
