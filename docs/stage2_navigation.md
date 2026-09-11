# 阶段 2：建图和自主导航

阶段 2 当前已跑通“固定起点自动定位 → 自主到达客厅入口”。下面的命令不需要在 RViz 点目标，也不需要手动设置初始位姿。

## 1. 赛前建图

启动 SLAM Toolbox 和整机：

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
source ~/robocup_home_ws/install/setup.bash
ros2 launch robocup_home_navigation mapping.launch.py gui:=true
```

另开终端，用键盘慢速走遍比赛区域：

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
source ~/robocup_home_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

建图结束后保存地图：

```bash
ros2 run nav2_map_server map_saver_cli -f ~/robocup_home_ws/src/robocup_home_system/robocup_home_navigation/maps/official
```

然后根据新地图修改 `config/locations.yaml` 中的五个地点。正式世界的起点不是 `(0, 0, 0)` 时，也要同步修改 `config/nav2_overrides.yaml` 的 `amcl.initial_pose`。

仓库内的 `maps/example.*` 是 WPR 示例世界的启动用地图，可以直接测试代码。它不是正式比赛地图；正式地图必须使用上面的 SLAM 流程生成。

## 2. 自主导航测试

启动整机、地图、AMCL 和 Nav2：

```bash
ros2 launch robocup_home_navigation navigation.launch.py gui:=true
```

启动后会先等待底盘控制器、激光雷达、里程计和 TF 全部有数据，再启动
AMCL 和 Nav2。终端出现“机器人已就绪”后再发送目标；不要按固定秒数猜测。

直接测试去客厅：

```bash
ros2 run robocup_home_navigation go_to_location living_room_entry
```

模拟任务到达后自动出发：

```bash
ros2 service call /competition/set_targets robocup_home_interfaces/srv/SetTargets \
  "{target_names: [apple, banana, coke]}"
```

查看状态：

```bash
ros2 topic echo /mission/status
```

三个名称必须非空且互不重复。阶段 2 只用它触发导航，阶段 4 再接正式类别白名单和视觉流程。

## 3. 配置说明

- AMCL 自动使用固定起点初始化，不需要 RViz 的 `2D Pose Estimate`。
- 不要在 Gazebo 中用鼠标直接拖动机器人；这不会产生正确的里程计。需要移动时
  使用键盘控制或导航目标。如果确实拖动过，重启本启动文件恢复固定起点。
- 全局代价地图包含静态层、实时激光障碍层和膨胀层。
- 局部代价地图实时订阅 `/scan`，临时障碍不会写进静态地图。
- footprint 为 `1.06 m × 0.72 m`，把底盘和收拢后的机械臂一起算入。
- 导航失败后先清空局部、全局代价地图，再后退、旋转，最后只重试一次。

## 4. 碰撞测试

碰撞监视器只允许在测试模式打开：

```bash
ros2 launch robocup_home_navigation navigation.launch.py \
  mode:=test test_contact_monitor:=true
```

发生底盘碰撞时会发布 `/test/collision_detected`。`mode:=competition` 不加载 Contact 系统、不桥接 Contact 话题，也不会启动监视器，避免仿真真值进入比赛决策。

阶段 2 最终验收还需要在场景中随机放两个小障碍，连续测试 20 次，记录至少 19 次成功且零碰撞。目前完成的是功能闭环，不代表已经完成这项统计验收。
