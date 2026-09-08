# Version baseline

Captured 2026-09-08 on Ubuntu 22.04.5 LTS.

- Kernel: 6.8.0-40-generic
- ROS: Humble
- Gazebo Fortress: 6.18.0
- `franka_ros2`: `9faaaaf6ad4e4cc177cb93716547cc8ab20c5bd2`
- `franka_description`: `02afaae282d4a8e10d7d2f781b23b3515c303ce5`
- WPR and local FR3 demo: imported source snapshots (no Git metadata)
- NVIDIA driver: `nvidia-driver-595-open` 595.91.07; RTX 4060 Laptop GPU verified
- Swap: `/swapfile`, 16 GiB, active
- Perception Python environment: intentionally deferred until Stage 3 to avoid a
  multi-gigabyte CUDA/PyTorch download before any vision node needs it
