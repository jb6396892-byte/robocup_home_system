# 协作开发约定

## 最简单的开发流程

每次开始前先更新 `main`，再新建自己的分支：

```bash
git switch main
git pull --ff-only
git switch -c 方向/简短功能名
```

分支名前缀统一使用：`nav/`、`perception/`、`manipulation/`、`mission/`、`integration/` 或 `docs/`。

开发完成后：

```bash
cd ~/robocup_home_ws
source src/robocup_home_system/scripts/setup_env.bash
colcon build --symlink-install
colcon test --event-handlers console_direct+
colcon test-result --verbose
git status
git add 你修改的文件
git commit -m "feat: 简短说明"
git push -u origin 当前分支名
```

然后在 GitHub 创建 Pull Request。至少让另一名队友看一遍再合并，不直接向 `main` 推功能代码。

## 减少冲突

- 每个方向主要修改自己的 ROS 包。
- `robocup_home_interfaces`、总启动文件和整机 URDF 是公共文件，修改前先说明原因。
- 一个 Pull Request 只做一件事，不顺手重排无关文件。
- 不把本机绝对路径写进代码；使用 ROS 包路径、启动参数或环境变量。
- 不直接修改 `wpr_simulation_ros2`、`franka_ros2` 等上游仓库。

## 提交信息

- `feat:` 新功能
- `fix:` 修复问题
- `docs:` 只改文档
- `test:` 增加或修改测试
- `chore:` 构建、配置和普通维护

提交信息可以写中文，例如：

```text
feat: 增加 AMCL 自动初始位姿
fix: 修正相机坐标系方向
```

## 不能提交的内容

不要提交个人密钥、Token、账号密码、数据集、模型权重、录屏、rosbag、`build/`、`install/` 和 `log/`。大文件放团队共享盘，并在文档中记录文件名、版本和 SHA-256。

## 合并前最低检查

- 能在干净终端按 README 的顺序加载环境。
- `colcon build --symlink-install` 成功。
- 修改过的节点至少能启动，不刷错误日志。
- 改接口时，同一个 Pull Request 中同步修改调用方和文档。
- 改机器人模型或控制器时，必须重新运行健康检查和冒烟测试。
