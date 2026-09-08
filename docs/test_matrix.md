# Stage 0/1 test matrix

Date: 2026-09-08

| Check | Result | Evidence |
|---|---|---|
| Overlay build | PASS | `colcon build --symlink-install`: 2 packages finished |
| Xacro / URDF tree | PASS | `check_urdf`; root is `base_link`, FR3 and all sensors connected |
| Arbitrary absolute world argument | PASS | WPR `example.world` supplied through `world_path` and copied only to `/tmp` for sensor-system augmentation |
| Unified controls | PASS | TMR + FR3 are loaded by one Gazebo ros2_control plugin; 6 controllers active together |
| Sensor data | PASS | Fresh `/clock`, lidar, RGB, depth, CameraInfo, IMU, odom and joint-state messages received |
| RGB-D field of view | PASS | Rear-high camera pose avoids the folded FR3; RGB is non-uniform (0–251) and all 307200 depth pixels are finite (0.172–5.057 m) |
| Runtime rates | PASS | Headless WPR load: scan 8.3 Hz, RGB 11.8 Hz, depth 11.5 Hz, IMU 86 Hz, odom 42 Hz, joint states 419 Hz |
| Sensor frame IDs | PASS | `lidar_link`, `rgbd_camera_optical_frame`, `imu_link` |
| TF graph | PASS | `map -> odom -> base_link -> sensors / fr3_link0 -> fr3_hand_tcp` connected |
| Base motion | PASS | `/cmd_vel` adapter test: forward, rotate, stop; odometry changed |
| FR3 motion | PASS | Joint 1 moved to 0.20 rad and returned to stow; both action goals succeeded |
| Gripper motion | PASS | Both physical finger controllers opened and closed; four action goals succeeded |
| 10-minute stability | PASS | Final headless run: 23:07:26–23:18:17, no crash, controller loss or sensor interruption |
| Clean shutdown | PASS | Controllers and both hardware components deactivate cleanly on Ctrl-C |
| NVIDIA driver | PASS | `nvidia-driver-595-open` 595.91.07; `nvidia-smi` detects the RTX 4060 Laptop GPU with 8188 MiB |
| 16 GB swap | PASS | `/swapfile` is active with 16 GiB |
| PyTorch / Ultralytics | DEFERRED | Deliberately postponed to Stage 3 to avoid unnecessary multi-GB downloads and premature version locking |
| Demo motion visibility | DEFERRED | Current Stage 1 arm motion is intentionally small; enlarge it later for presentation/video clarity |

The identity `map -> odom` transform is a Stage 1 placeholder. Stage 2 localization
must replace it with AMCL's transform.
