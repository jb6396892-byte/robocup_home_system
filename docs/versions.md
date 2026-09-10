# 已验证版本

记录时间：2026-09-08，系统为 Ubuntu 22.04.5 LTS。

- 内核：6.8.0-40-generic
- ROS：Humble
- Gazebo Fortress：6.18.0
- `franka_ros2`：`9faaaaf6ad4e4cc177cb93716547cc8ab20c5bd2`
- `franka_description`：`02afaae282d4a8e10d7d2f781b23b3515c303ce5`
- WPR 和本地 FR3 Demo：组委会源码快照，没有 Git 历史
- NVIDIA 驱动：`nvidia-driver-595-open` 595.91.07
- GPU：RTX 4060 Laptop，已通过 `nvidia-smi` 验证
- Swap：`/swapfile`，16 GiB，已启用
- 视觉 Python 环境：阶段 3 再建立并锁定版本

队友第一次搭建时尽量使用这些版本。确实需要升级时，先新建分支测试，不能直接改全队环境。
