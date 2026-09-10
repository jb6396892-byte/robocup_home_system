# SEU 2026 RoboCup@Home 总工程

本仓库保存比赛自己的代码。WPR、Franka 等上游项目放在独立工作空间，不能直接改上游源码。

当前已经完成阶段 0、阶段 1，并跑通阶段 2 的核心导航闭环：TMR 底盘、单 FR3、传感器、固定起点自动定位、Nav2 和客厅入口自主导航均能在 Gazebo 中工作。阶段 2 还需要完成 20 次随机障碍统计验收，再进入视觉计数和 `/map` 定位。

## 仓库结构

| 包或目录 | 谁负责 | 用途 |
|---|---|---|
| `robocup_home_description` | 平台组 | 整机 URDF、传感器和控制器配置 |
| `robocup_home_bringup` | 集成组 | 总启动、健康检查和冒烟测试 |
| `robocup_home_navigation` | 导航组 | 建图、定位、Nav2 和停靠点 |
| `robocup_home_perception` | 视觉组 | YOLO、深度定位和多帧去重 |
| `robocup_home_manipulation` | 机械臂组 | MoveIt、抓取与放置 |
| `robocup_home_mission` | 集成组 | 目标输入、状态机、计时和结果冻结 |
| `robocup_home_interfaces` | 全队共用 | 服务、消息和 Action 定义；修改前先在群里确认 |
| `config/object_classes.yaml` | 视觉组 | 18 类物体的唯一名称和别名 |
| `docs/` | 全队 | 当前进度、规则摘要和测试记录 |

## 第一次准备环境

系统环境统一使用 Ubuntu 22.04、ROS 2 Humble 和 Gazebo Fortress。

先把本仓库放到总工作空间：

```bash
mkdir -p ~/robocup_home_ws/src
cd ~/robocup_home_ws/src
git clone https://github.com/jb6396892-byte/robocup_home_system.git
```

WPR 使用组委会提供的 `wpr_simulation_ros2.zip`。解压后把包目录改名为 `wpr_simulation_ros2`，放入 `~/wpr_ros2_ws/src/`，再构建：

```bash
cd ~/wpr_ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build --symlink-install
```

Franka 使用仓库锁定的版本：

```bash
mkdir -p ~/franka_ros2_ws/src
cd ~/franka_ros2_ws
source /opt/ros/humble/setup.bash
vcs import src < ~/robocup_home_ws/src/robocup_home_system/dependencies.repos
vcs import src < src/franka_ros2/dependency.repos --recursive --skip-existing
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF
```

最后构建比赛总工程：

```bash
cd ~/robocup_home_ws
source src/robocup_home_system/scripts/setup_env.bash
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build --symlink-install
source install/setup.bash
```

如果队友的 WPR 或 Franka 工作空间不在默认位置，构建前指定路径：

```bash
export ROBOCUP_WPR_WS=/你的路径/wpr_ros2_ws
export ROBOCUP_FRANKA_WS=/你的路径/franka_ros2_ws
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
```

## 启动和检查

启动默认 WPR 示例世界：

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
ros2 launch robocup_home_bringup competition.launch.py gui:=true
```

启动组委会给出的其他世界时，传入绝对路径：

```bash
ros2 launch robocup_home_bringup competition.launch.py \
  world_path:=/绝对路径/比赛世界.world gui:=true
```

另开终端检查：

```bash
source ~/robocup_home_ws/src/robocup_home_system/scripts/setup_env.bash
ros2 run robocup_home_bringup health_check --timeout 20
ros2 run robocup_home_bringup stage1_smoke_test
```

冒烟测试会让底盘和机械臂运动，运行前确认机器人周围没有障碍。

自主导航的启动、建图和任务触发命令见 [docs/stage2_navigation.md](docs/stage2_navigation.md)。

## 一起开发

不要直接在 `main` 上写功能。每个人从最新 `main` 建自己的分支，例如：

```bash
git switch main
git pull --ff-only
git switch -c nav/amcl-config
```

完成后先构建和测试，再推送分支并创建 Pull Request。详细规则见 [CONTRIBUTING.md](CONTRIBUTING.md)，决赛目标和分工见 [docs/finals_plan.md](docs/finals_plan.md)。

不要向仓库提交 `build/`、`install/`、`log/`、数据集、录屏、rosbag 或模型权重。
