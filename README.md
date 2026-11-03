# 实验8：仿真环境下的激光SLAM建图与定位调试

本工程衔接实验7，沿用 R1 机器人、Mid-360 扫描方向仿真和室内场景，将原始三维点云与 IMU 接入 FAST-LIO，观察运动过程中的位姿、轨迹和三维地图，并保存点云地图。

**当前状态：已在教学平台完成编译、三组降采样参数、Gazebo/RViz、建图与位姿里程计、地图保存及数据录制验证，已发布至本仓库。** 实测结果见 [平台验证记录](docs/PLATFORM_VALIDATION.md)。

完整操作步骤、RViz观察要求和实验记录表见 [实验八指导手册](docs/STUDENT_GUIDE.md)。手册中的配图位置待实际运行后补充。

## 数据流程

```text
实验7仿真场景
  ├─ /livox/points（原始点云，含逐点时间）
  │       ↓ 消息格式适配，保留时间与坐标
  │   /livox/lidar（Livox CustomMsg）
  └─ /livox/imu（角速度、加速度）
          ↓
      FAST-LIO
  IMU初始化 → 点云去畸变 → 降采样 → 点云与地图匹配
          ↓
  /Odometry 位姿里程计  /path 轨迹  /Laser_map 三维点云地图
          ↓
      RViz观察与PCD地图保存
```

实验7的无效点过滤、范围裁剪、降采样和去噪用于认识点云处理。本实验读取保留逐点时间的原始数据，由 FAST-LIO 完成其所需的内部处理。

实验8在基础场景增加两处低平台，为高度估计提供可观测的水平面。

本实验中的“定位”指持续运行时的激光惯性位姿估计。保存 PCD 后的重定位、回环优化及导航作为后续扩展。

## 工程内容

| 目录或文件 | 用途 |
| --- | --- |
| `src/experiment8_slam` | 点云消息适配、TF衔接、启动和地图保存工具 |
| `src/fast_lio` | 固定版本的 FAST-LIO ROS 2 源码 |
| `src/livox_ros_driver2` | 官方 Livox 消息定义，仅编译消息 |
| `tools/install_dependencies.sh` | 安装Gazebo Fortress和构建依赖 |
| `tools/prepare_workspace.sh` | 下载固定版本的实验5资源与实验7仿真工程 |
| `tools/build.sh` | 编译工作区 |
| `SOURCE_LOCK.json` | 依赖来源及固定提交 |
| `patches/fast_lio_integration.patch` | 相对上游的集成修改记录 |

实验5与实验7资源分别放在 `src/experiment5` 和 `src/experiment7`，完整教学ZIP已包含这些资源，并通过哈希校验；直接使用Git源码时仍按固定提交下载。无需另行启动实验7的launch。

## 从初始环境部署

初始环境与实验6、实验7一致：Ubuntu 22.04、ROS 2 Humble、CMake、colcon及VS Code，沿用课程软件源。下列示例将工程放在 `/root/exp8`，使用root用户。

```bash
cd /root/exp8
bash tools/install_dependencies.sh
bash tools/prepare_workspace.sh
bash tools/build.sh
```

加载环境并启动场景、算法和RViz：

```bash
source /opt/ros/humble/setup.bash
source /root/exp8/install/setup.bash
export PYTHONNOUSERSITE=1
ros2 launch experiment8_slam experiment8.launch.py map_path:=/root/exp8/maps/map.pcd
```

启动后先保持机器人静止，等待IMU初始化及首批地图形成。RViz固定坐标系为 `camera_init`，勾选 `FAST-LIO map` 和 `FAST-LIO trajectory`，观察地图和运动轨迹；勾选 `Registered current scan` 可叠加观察当前帧。

新终端同样加载ROS和工作区环境，再分段控制机器人：

```bash
source /opt/ros/humble/setup.bash
source /root/exp8/install/setup.bash
export PYTHONNOUSERSITE=1
ros2 run experiment8_slam drive_for.py --vx 0.15 --seconds 2
ros2 run experiment8_slam drive_for.py --yaw-rate 0.3 --seconds 1
```

分别观察前进、转向和停车时，机器人模型、当前点云、累计地图及轨迹的变化。运动时长使用仿真时钟计时，每条指令结束会发送零速度。

保存当前地图：

```bash
ros2 run experiment8_slam save_map.py
ls -lh /root/exp8/maps/map.pcd
```

无图形界面时可用 `gui:=false rviz:=false` 启动；此模式已通过三组参数运行验证。

## 坐标与接口约定

- 仿真点云为5 Hz，IMU约200 Hz；逐点 `offset_time` 单位为纳秒，相对该帧起始时间。
- 仿真IMU和激光雷达重合，安装在 `base_link` 上方1.3 m。FAST-LIO外参设为零平移和单位旋转，不沿用实体Mid-360的默认外参数值。
- TF链为 `camera_init → body → base_link → lidar_frame → imu_frame`。FAST-LIO的 `body` 对应IMU位置，`camera_init`原点在算法初始化的IMU位置附近。
- 启动实验7时关闭 `world → base_link` 真值TF；`/r1/ground_truth` 仅供后续对比，FAST-LIO不订阅该话题。
- `line`、`tag` 和反射强度使用实验7的简化仿真值，不作为真实硬件特性验证依据。
- 本工程中的 `livox_ros_driver2` 只有消息定义，不需要安装 SDK2。连接实体雷达时需换用官方完整驱动，不能同时编译两个同名包。

第三方许可及修改说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
