# Stage 0 and Stage 1 handoff

## Scope

Implemented now: a clean overlay workspace, fixed source order, the 18-class ID and
alias table, arbitrary absolute world paths, one TMR plus one FR3, RGB-D/lidar/IMU,
one Gazebo ros2_control plugin, the base/arm controllers, Twist adapter, TF, health
check and a bounded smoke test.

PyTorch, Ultralytics and model weights are delayed until Stage 3. They have no caller
in Stage 0/1 and downloading them now consumes several GB. This is the deliberate
quota-saving exception. No CUDA Toolkit is needed yet.

## Start

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
ros2 launch robocup_home_bringup competition.launch.py \
  world_path:=/home/smg/wpr_ros2_ws/src/wpr_simulation_ros2/worlds/example.world \
  target_source:=service gui:=false
```

The launch copies the selected world to `/tmp` only when it needs to add Gazebo's
sensor and IMU systems. The organizer world is never modified.

In a second terminal:

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
ros2 run robocup_home_bringup health_check --timeout 20
ros2 run robocup_home_bringup stage1_smoke_test
```

The smoke test drives forward, rotates, stops, moves FR3 joint 1 by 0.2 rad and
returns to stow. Run it only with free space around the robot.

## Stage 0 system actions still requiring a reboot

Install the driver reported by `ubuntu-drivers devices`, create swap only if absent,
then reboot. These actions require administrator privileges and are intentionally not
hidden inside the workspace setup:

```bash
sudo bash ~/robocup_home_ws/src/robocup_home_system/scripts/finish_stage0_system.bash
sudo reboot
```

The script installs whatever `ubuntu-drivers devices` currently marks as
`recommended` (currently `nvidia-driver-595`) and creates swap only when none is active.

After reboot, `nvidia-smi` and `swapon --show` must pass. Do not install the full CUDA
Toolkit unless a future CUDA extension actually requires it.

## Temporary TF convention

Stage 1 publishes an identity `map -> odom` transform. Stage 2 must disable that
publisher when AMCL becomes the authoritative source of `map -> odom`.
