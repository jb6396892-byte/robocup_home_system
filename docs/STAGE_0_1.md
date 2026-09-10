# 阶段 0 和阶段 1 交接说明

## 已经完成

- 建立独立的比赛总工程，不修改 WPR 和 Franka 上游源码。
- 固定环境加载顺序：ROS 2 → WPR → Franka → 比赛总工程。
- 组合 TMR 底盘、单 FR3、夹爪、激光雷达、RGB-D 和 IMU。
- Gazebo 中只使用一条无冲突的 `ros2_control` 控制链。
- `/cmd_vel` 可通过适配节点控制 TMR。
- 支持任意世界绝对路径，不依赖不存在的 `official.world`。
- NVIDIA 驱动和 16 GiB swap 已验证。
- 整机稳定运行、底盘运动、机械臂运动、夹爪运动和传感器数据均已通过测试。

PyTorch、Ultralytics 和模型权重等到阶段 3 再安装。目前没有视觉节点调用它们，提前安装只会占用数 GB 空间。

## 启动

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
ros2 launch robocup_home_bringup competition.launch.py gui:=true
```

默认启动 WPR 的 `example.world`。如需换世界：

```bash
ros2 launch robocup_home_bringup competition.launch.py \
  world_path:=/绝对路径/example.world \
  target_source:=service gui:=false
```

启动文件只会在 `/tmp` 中生成补充传感器插件后的临时世界，不会修改原始世界文件。

另开终端检查：

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
ros2 run robocup_home_bringup health_check --timeout 20
ros2 run robocup_home_bringup stage1_smoke_test
```

冒烟测试依次执行底盘前进、旋转、停止，机械臂关节 1 小幅运动并回到收拢姿态。运行前确认周围没有障碍。

## 阶段 2 接手时注意

阶段 1 暂时发布固定的 `map → odom`。接入 AMCL 后必须关闭这个固定发布器，只允许 AMCL 发布 `map → odom`，否则 TF 会冲突。

导航期间机械臂必须保持收拢。Nav2 footprint 要包含收拢后的机械臂，临时障碍必须由实时激光进入局部代价地图。
