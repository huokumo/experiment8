# 实验八：仿真环境下的激光SLAM建图与定位调试

## 实验任务场景

你所在的公司正在为仓储与厂区巡检机器人开发自主移动功能。机器人进入陌生区域后，需要一边观察周围的墙面、立柱、箱体和通道，一边判断自身移动了多远、转过了多少角度，并将连续获取的环境信息拼接成地图。后续的路线规划与巡检任务，需要使用这些地图和位姿信息。

在前期工作中，项目组已完成激光点云采集与预处理，能够观察原始点云，比较过滤、裁剪、降采样和去噪的效果。现在需要继续解决一个问题：机器人运动时，每一帧点云都来自不同的位置，怎样把这些点云放到同一个坐标系中，逐步形成清晰的环境地图？

项目负责人将激光建图与位姿调试任务交给你。你需要部署以实验七为基础、增加低平台的仿真场景，将保留逐点时间的原始点云和IMU数据接入FAST-LIO，完成静止初始化，分段控制机器人前进与转向，并在RViz中同时观察机器人位置、当前点云、运动轨迹和三维地图。随后比较降采样参数对地图结构的影响，判断墙面是否重叠、立柱轮廓是否清楚、停车后的位姿是否稳定。

任务完成后，向项目组提交地图文件、运行参数、位姿记录、关键截图和实验报告，说明地图是怎样逐步形成的、运动过程中定位是否连续，以及参数调整带来了哪些变化。

处理流程如下：

```text
安装Gazebo与部署工程
          ↓
原始三维点云 + IMU
          ↓
消息格式适配，保留点坐标与逐点时间
          ↓
FAST-LIO：IMU初始化 → 点云去畸变 → 降采样 → 点云与地图匹配
          ↓
机器人位姿、运动轨迹、三维点云地图
          ↓
RViz观察 → 参数比较 → 保存地图与实验记录
```

## 岗位能力要求

作为机器人感知与调试工程师，你需要把传感器输入、算法运行和地图效果联系起来，完成以下工作：

1. **部署与接入**：完成仿真工程部署，认识原始点云、IMU和消息适配的作用；
2. **建图与观察**：完成静止初始化与分段运动，结合Gazebo和RViz判断地图、轨迹和机器人位置是否对应；
3. **定位与调参**：读取估计位姿，比较前进、转向和停车时的变化，调整降采样参数并解释显示效果；
4. **记录与交付**：保存地图、参数、截图和数据，使同一轮实验的过程与结果能够对应查看。

## 实验目标

完成本实验后，应能够：

1. 从初始环境安装Gazebo Fortress与实验依赖，完成工程构建；
2. 说明实验七预处理练习与实验八FAST-LIO输入之间的关系；
3. 完成FAST-LIO静止初始化，在RViz中观察地图与当前点云；
4. 通过分段前进、转向和停车，观察位姿与轨迹变化；
5. 比较不同降采样参数下的地图结构；
6. 保存PCD地图、运行参数和实验报告。

## 预备知识

1、Linux基础：熟悉软件安装、目录切换、文件解压和编辑操作。

2、ROS 2基础：了解工作区、功能包、话题、消息和launch，能够加载环境并启动程序。

3、点云基础：了解三维点坐标、无效点、体素降采样和逐点时间，能够使用RViz观察点云。

4、运动与坐标基础：了解位置、姿态、线速度、角速度及坐标变换，知道IMU提供角速度与加速度信息。

## 实验环境

初始虚拟机与实验六、实验七开始前相同：已配置Ubuntu 22.04、ROS 2 Humble、CMake、colcon和VS Code。Gazebo Fortress及实验工程按本手册独立安装，不要求保留前面实验的工作区。

| 操作系统 | ROS版本 | 仿真器 | 算法与显示工具 |
| --- | --- | --- | --- |
| Ubuntu 22.04 x86_64 | ROS 2 Humble | Gazebo Fortress 6 | FAST-LIO、PCL、Python 3、VS Code、RViz 2 |

本手册使用root用户，工作区为 `/root/exp8`，结果目录为 `/root/exp8/data/experiment8`，地图目录为 `/root/exp8/maps`。DDS配置沿用实验1，各终端保持一致。

| 文件或目录 | 用途 |
| --- | --- |
| `experiment8_teaching_20261103.zip` | 实验八完整教学包 |
| `src/experiment5` | 部署时下载的R1模型资源 |
| `src/experiment7` | 部署时下载的激光点云与IMU仿真工程 |
| `src/experiment8_slam/launch/experiment8.launch.py` | 同时启动仿真、消息适配、FAST-LIO和RViz |
| `src/experiment8_slam/config/fastlio_sim.yaml` | FAST-LIO教学场景参数 |
| `src/experiment8_slam/config/experiment8.rviz` | 地图、当前帧、机器人和轨迹显示配置 |
| `src/experiment8_slam/scripts/livox_adapter.py` | 将原始点云适配为Livox消息格式 |
| `src/experiment8_slam/scripts/save_map.py` | 保存当前点云地图 |
| `src/fast_lio` | FAST-LIO算法源码 |
| `src/livox_ros_driver2` | 官方Livox消息定义，仅用于构建消息 |

本实验使用Mid-360扫描模式的教学仿真，无需连接真实雷达或安装Livox SDK2。R1保持站姿进行平面移动。

> 验证状态：2026年11月3日已完成教学平台编译、运行、界面、三组参数和地图保存验证。教学包通过文件分发，未推送Git；本手册保留原有配图位置。详细实测结果见同目录的平台验证记录。

## 实验步骤

### 1、安装Gazebo Fortress

（1）在桌面空白处右键，选择【Open Terminal Here】打开终端，关闭其他正在运行的仿真场景。

（2）更新软件包列表。

```bash
apt update
```

（3）安装Gazebo Fortress及ROS 2接口。出现安装确认提示时，输入 `Y` 并回车。

```bash
apt install ros-humble-ros-gz
```

`ros_gz_sim` 用于启动仿真，`ros_gz_bridge` 用于传递仿真与ROS之间的数据。软件源沿用课程初始环境配置。

（4）加载ROS环境，查看Gazebo主版本。

```bash
source /opt/ros/humble/setup.bash
ign gazebo --versions
```

输出中应包含主版本 `6`。

> 图1（待补）：Gazebo安装完成与版本输出。

### 2、解压教学包并安装依赖

（1）将配套文件 `experiment8_teaching_20261103.zip` 放到虚拟机的 `/root` 目录。此处使用当前分发的教学包，不填写尚未发布的下载链接。

（2）安装解压工具，将教学包解压并命名为实验工作区。以下操作用于初始环境中尚未存在 `/root/exp8` 的情况。

```bash
apt install -y unzip
cd /root
mkdir -p /root/exp8
unzip experiment8_teaching_20261103.zip -d /root/exp8
cd /root/exp8
```

解压后，`/root/exp8` 下应直接包含 `src`、`tools` 和 `README.md`，不应再套一层同名目录。

（3）运行依赖安装脚本，安装点云处理、插件编译、坐标变换及显示工具；随后安装数据记录工具。

```bash
bash tools/install_dependencies.sh
apt install -y ros-humble-rosbag2 ros-humble-rosbag2-storage-default-plugins
```

已安装且满足要求的软件包会自动跳过。主要依赖用途如下：

| 依赖 | 用途 |
| --- | --- |
| PCL、Eigen | 点云处理与矩阵计算 |
| `libignition-gazebo6-dev` | 编译仿真插件 |
| `rosidl_default_generators` | 生成Livox消息等接口 |
| TF2、`robot_state_publisher` | 发布坐标变换和机器人模型关系 |
| RViz 2 | 显示点云、地图、机器人与轨迹 |
| rosbag2 | 保存同一轮实验的输入与输出数据 |

> 图2（待补）：解压后的工程目录与依赖安装结果。

### 3、准备资源并构建工程

（1）检查教学包中的固定版本模型与仿真资源。

```bash
cd /root/exp8
bash tools/prepare_workspace.sh
```

完整教学包已包含 `src/experiment5` 和 `src/experiment7`。脚本核对资源文件，无需再次下载，也无需另外运行实验五或实验七的启动文件。

（2）创建结果目录并编译。

```bash
mkdir -p /root/exp8/data/experiment8 /root/exp8/maps
bash tools/build.sh
```

脚本依次编译模型、仿真、消息和建图功能包，并限制并行编译数量。构建完成后再进行下一步。

（3）加载工作区环境。

```bash
source /root/exp8/install/setup.bash
export PYTHONNOUSERSITE=1
```

`PYTHONNOUSERSITE=1` 使当前终端使用系统安装的Python库，避免个人安装的不同版本相互影响。

> 图3（待补）：工程构建完成，显示功能包汇总结果。

### 4、认识实验七与实验八的衔接

（1）用VS Code打开工程。

```bash
code --no-sandbox --user-data-dir /root/exp8/data/vscode /root/exp8
```

（2）查看 `src/experiment8_slam/launch/experiment8.launch.py` 和 `scripts/livox_adapter.py`，结合下表认识数据流。

| 话题 | 内容 | 在本实验中的作用 |
| --- | --- | --- |
| `/livox/points` | 原始PointCloud2点云，含逐点时间 | 来自实验七仿真，是消息适配器的输入 |
| `/livox/lidar` | Livox CustomMsg点云 | FAST-LIO读取的点云输入 |
| `/livox/imu` | 角速度、加速度 | FAST-LIO读取的IMU输入 |
| `/r1/lidar/points_filtered` | 实验七处理后的XYZ点云 | 可用于回顾预处理效果，本实验不将它接入FAST-LIO |

消息适配器保留帧起始时间、点坐标与逐点时间，主要改变消息格式。仿真中 `offset_time` 的单位为纳秒，表示该点相对帧起始时刻的时间偏移。

（3）说明两次实验的任务区别。

| 实验 | 主要任务 | 需要保留的关键数据 |
| --- | --- | --- |
| 实验七 | 理解过滤、裁剪、降采样和去噪，比较处理效果 | 原始点云及IMU |
| 实验八 | 使用FAST-LIO估计运动并建立地图 | 带时间的原始点云与同步的IMU |

不能仅因为点云在RViz中显示清楚，就认为它可以直接接入任意建图算法。实验七导出的XYZ点云缺少本实验所需的逐点时间信息。

### 5、启动仿真与FAST-LIO

（1）将当前终端作为**终端1**，加载环境并启动实验。

```bash
source /opt/ros/humble/setup.bash
source /root/exp8/install/setup.bash
export PYTHONNOUSERSITE=1
ros2 launch experiment8_slam experiment8.launch.py map_path:=/root/exp8/maps/baseline.pcd
```

该命令同时启动Gazebo、点云与IMU接口、消息适配器、FAST-LIO及RViz。`map_path` 指定稍后保存地图的文件位置，启动本身不等于已保存地图。

（2）启动后先保持机器人静止，观察终端中的 `IMU Initial Done` 信息，并等待RViz出现首批地图点。

IMU初始化用于估计初始重力方向和相关状态。首次建图时先观察静止效果，再发送运动指令。

（3）在Gazebo中找到R1、蓝色墙壁、立柱、箱体和两处棕色低平台；在RViz中寻找相应的点云轮廓。

> 图4（待补）：Gazebo场景与静止初始化后的RViz地图并排显示，标出蓝墙、立柱等对应结构。

### 6、设置RViz，区分当前帧与地图

（1）确认RViz的【Global Options】→【Fixed Frame】为 `camera_init`。该坐标系是FAST-LIO的建图参考坐标系。

（2）在左侧【Displays】中找到以下显示项。

| 显示项 | 对应话题 | 观察内容 |
| --- | --- | --- |
| `R1 estimated pose` | 机器人模型与TF | FAST-LIO估计位姿下的机器人位置 |
| `FAST-LIO map` | `/Laser_map` | 多次观测更新形成的地图 |
| `Registered current scan` | `/cloud_registered` | 已转换到建图坐标系的当前帧点云 |
| `FAST-LIO trajectory` | `/path` | 估计位姿形成的运动轨迹 |

（3）先只显示 `FAST-LIO map`，调整视角，使蓝墙和立柱位于画面中央；再勾选 `Registered current scan`，观察绿色当前帧与地图的叠加关系。

鼠标左键拖动旋转视角，滚轮缩放，按住中键拖动平移视角。比较两幅画面时保持视角和点大小一致。

（4）取消勾选地图，只保留当前帧；然后反向切换，说明两者的区别。

- 当前帧反映一次扫描的观测，随扫描更新；
- 地图融合了不同时间、不同位置的观测，保留已建立的环境结构；
- 两者位于同一坐标系中，便于观察墙面是否对齐。

> 图5（待补）：相同视角下，当前帧、地图、两者叠加的三幅画面；保留显示项名称与Fixed Frame。

### 7、读取位姿并观察坐标关系

（1）新开终端，作为**终端2**，加载环境。

```bash
source /opt/ros/humble/setup.bash
source /root/exp8/install/setup.bash
export PYTHONNOUSERSITE=1
```

（2）读取一条估计位姿。

```bash
ros2 topic echo /Odometry --once
```

观察 `header.frame_id`、`child_frame_id`、`pose.pose.position` 和 `pose.pose.orientation`。本工程输出的父坐标系为 `camera_init`，子坐标系为 `body`。

`position` 表示位置，单位为米；`orientation` 使用四元数表示姿态，不应将其中的 `z` 数值直接当成转角。

（3）结合RViz中的TF显示理解坐标链。

```text
camera_init → body → base_link → lidar_frame → imu_frame
 建图参考      IMU      机器人机身    激光雷达       IMU接口
```

本仿真中激光雷达与IMU位于同一安装位置，在 `base_link` 上方1.3 m。`body → base_link` 用于将算法位姿对应到机器人模型；FAST-LIO中的雷达与IMU外参采用零平移、单位旋转。

本实验关闭仿真真值的 `world → base_link` 动态TF，由算法估计结果驱动机器人显示。因此RViz应使用 `camera_init`，不沿用实验七的 `world` 设置。

（4）将静止时的位置填入记录表。

| 状态 | X/m | Y/m | Z/m | 当前观察 |
| --- | --- | --- | --- | --- |
| 初始化后静止 |  |  |  |  |
| 前进后 |  |  |  |  |
| 转向后 |  |  |  |  |
| 再次前进后 |  |  |  |  |
| 停车后 |  |  |  |  |

> 图6（待补）：静止时的Odometry输出与RViz坐标关系。

### 8、分段前进，观察地图更新

本实验的运动时长按仿真时钟计时，指令结束自动停车。界面运行较慢时，等待的现实时间可能增加。

（1）终端1保持运行，在终端2发送一次短距离前进指令。

```bash
ros2 run experiment8_slam drive_for.py --vx 0.15 --seconds 2
```

`--vx` 为前进速度，单位为m/s；`--seconds` 为发送指令的时间。指令结束后程序发送零速度。

（2）同时观察两个窗口。

| Gazebo中看什么 | RViz中看什么 |
| --- | --- |
| R1是否向前移动并停车 | 机器人模型是否沿相应方向移动 |
| 机器人与蓝墙的距离是否减小 | 当前帧是否继续与地图中的墙面对齐 |
| 场景中的墙体保持不动 | 地图中的墙体是否基本稳定，有无明显重影 |

（3）读取前进后的 `/Odometry`，填写记录表，比较前后位置变化。

```bash
ros2 topic echo /Odometry --once
```

速度乘以时间可估计指令对应的运动距离，但应以实际仿真反馈与估计结果为准。仿真运行速度、障碍保护等因素会影响实际移动距离。

（4）等待数次扫描更新后观察红色轨迹。当前配置按若干帧更新路径，轨迹可能晚于机器人模型变化，不能仅凭轨迹尚未延长就判断定位失效。

> 图7（待补）：相同视角的前进前后画面，保留机器人、地图、当前帧和轨迹。

### 9、转向与停车，观察定位连续性

（1）发送一次原地转向指令。

```bash
ros2 run experiment8_slam drive_for.py --yaw-rate 0.3 --seconds 1
```

`--yaw-rate` 为绕竖直轴的角速度，单位为rad/s。正值表示按本工程坐标约定向左转。

（2）转向后观察Gazebo中机器人朝向的变化，并在RViz中确认机器人模型朝向相应改变、墙面位置基本稳定。再读取一次 `/Odometry`，记录位置与姿态变化。

（3）沿新的朝向短距离前进。

```bash
ros2 run experiment8_slam drive_for.py --vx 0.15 --seconds 2
```

机器人沿自身前方移动；已经转向后，建图坐标系中的X、Y位置可能同时变化。结合轨迹拐点理解“机器人向前”与“地图坐标X增加”的区别。

（4）保持停车，间隔数秒读取两次位姿。

```bash
ros2 topic echo /Odometry --once
```

查看位置是否持续漂移、地图是否出现分层或重影。将实际现象填入表格，不预填合格结果。

| 运动阶段 | Gazebo运动 | RViz模型与轨迹 | 地图对齐情况 | 实际问题 |
| --- | --- | --- | --- | --- |
| 前进 |  |  |  |  |
| 原地转向 |  |  |  |  |
| 转向后前进 |  |  |  |  |
| 停车 |  |  |  |  |

> 图8（待补）：转向前后与停车后的画面，突出机器人朝向、轨迹拐点及墙面是否重影。

### 10、认识建图内部的预处理

（1）查看 `src/experiment8_slam/config/fastlio_sim.yaml` 中的参数，联系实验七所学知识。

| 参数 | 初始值 | 含义 |
| --- | --- | --- |
| `preprocess.blind` | `0.25` | 忽略雷达附近小于该距离的点，单位为m |
| `point_filter_num` | `1` | 预处理阶段的点抽取间隔 |
| `filter_size_surf` | `0.12` | 当前帧匹配前的体素降采样尺寸，单位为m |
| `filter_size_map` | `0.12` | 地图更新使用的降采样尺寸，单位为m |
| `common.time_offset_lidar_to_imu` | `0.0` | 雷达与IMU之间的时间偏移，单位为s |
| `mapping.extrinsic_T` | `[0.0, 0.0, 0.0]` | 雷达与IMU之间的平移外参 |

（2）说明逐点时间的用途。

一帧扫描中的点在不同时刻采集。机器人在这一帧期间可能已经移动或转动，直接把所有点都当成同一时刻采集，会使墙面等结构发生变形。FAST-LIO结合IMU与逐点时间进行运动补偿，使这些点能够在统一时刻下参与匹配。

（3）区分三个环节：消息适配用于转换数据格式；去畸变用于补偿扫描期间的运动；降采样用于减少参与计算的点数。三者解决的问题不同。

### 11、比较降采样参数

（1）先保存当前默认参数下的地图，保存方式见第12节，再在终端1按 `Ctrl+C` 停止本轮场景。

（2）打开参数文件。

```bash
code --no-sandbox --user-data-dir /root/exp8/data/vscode /root/exp8/src/experiment8_slam/config/fastlio_sim.yaml
```

本组比较只修改 `filter_size_surf`，分别使用 `0.08`、`0.12` 和 `0.24`，保持 `filter_size_map`、运动指令和其他参数一致。保存文件后重新启动整套场景，使参数从启动时读入。

（3）例如，将 `filter_size_surf` 改为 `0.08` 后，在终端1运行：

```bash
ros2 launch experiment8_slam experiment8.launch.py map_path:=/root/exp8/maps/leaf_008.pcd
```

重新静止初始化，再按第8、9节执行相同的前进、转向、前进动作。可在终端2查看当前实际参数：

```bash
ros2 param get /laser_mapping filter_size_surf
```

（4）其余两组分别使用 `leaf_012.pcd` 和 `leaf_024.pcd` 作为保存路径。每组均从新启动的场景开始，保持RViz视角和点大小一致，避免把上一组已经移动后的状态带入比较。

（5）观察墙面、细立柱、轨迹连续性和运行流畅程度，记录实际结果。

| 当前帧体素尺寸/m | 墙面与立柱轮廓 | 当前帧与地图对齐 | 位姿和轨迹连续性 | 运行观察 | 保存文件 |
| --- | --- | --- | --- | --- | --- |
| 0.08 |  |  |  |  | `leaf_008.pcd` |
| 0.12 |  |  |  |  | `leaf_012.pcd` |
| 0.24 |  |  |  |  | `leaf_024.pcd` |

此处只改变当前帧的降采样尺寸，最终地图点数还受地图降采样和实际观测范围影响，不能仅凭地图点数判断哪组参数更好。

> 图9（待补）：三组参数在相同视角下的地图与当前帧对比，标明体素尺寸；另保留实际参数输出。

### 12、保存三维点云地图

（1）机器人停车、终端1保持运行时，在终端2执行：

```bash
ros2 run experiment8_slam save_map.py
```

程序向FAST-LIO请求保存当前地图。默认组保存到启动时指定的 `/root/exp8/maps/baseline.pcd`；其他组保存到各自指定的文件。

（2）查看文件。

```bash
ls -lh /root/exp8/maps
```

同一轮中再次保存会更新该轮指定的文件。需要保留多轮结果时，应使用不同的文件名。

（3）读取默认组PCD文件的文本头部，找到 `FIELDS`、`POINTS` 和 `DATA`。下列命令只读取头部，不打印后面的二进制点数据。

```bash
python3 - <<'PY'
with open('/root/exp8/maps/baseline.pcd', 'rb') as file:
    for line in file:
        print(line.decode('ascii').rstrip())
        if line.startswith(b'DATA '):
            break
PY
```

`FIELDS` 说明点字段，`POINTS` 说明保存点数，`DATA` 说明存储方式。地图保存成功应有程序成功提示，并能找到对应的非空文件。

PCD保存的是点云地图。本实验不会因为保存了PCD，就自动具备重启后加载地图定位或回环校正功能。

> 图10（待补）：地图保存成功提示、文件列表及PCD头部信息。

### 13、保存参数与运行数据

（1）在本轮场景仍运行时，导出FAST-LIO实际使用的参数。

```bash
ros2 param dump /laser_mapping --output-dir /root/exp8/data/experiment8
```

比较多组参数时，应将导出的参数文件分别重命名，放入与对应地图同名的记录目录，避免后一次覆盖前一次。

（2）需要保存一轮输入、估计输出与对比数据时，在终端2执行：

```bash
BAG_DIR=/root/exp8/data/experiment8/run_$(date +%Y%m%d_%H%M%S)
ros2 bag record -o "$BAG_DIR" /livox/points /livox/lidar /livox/imu /Odometry /path /clock /tf /tf_static /r1/ground_truth
```

记录启动后，可在另一个已加载环境的终端发送运动指令；完成一组短程运动和停车记录后，在记录终端按 `Ctrl+C` 停止。最后再停止场景。

`/r1/ground_truth` 是仿真给出的对比位姿，不是FAST-LIO的输入。仿真真值与算法输出的参考坐标系、机身参考点可能不同，对比时需要统一，不能直接逐项相减作为定位误差。

（3）整理本轮地图、参数、截图和位姿记录。

| 应保存的内容 | 要求 |
| --- | --- |
| PCD地图 | 使用能区分实验组的文件名 |
| 参数文件 | 与对应地图、截图来自同一轮运行 |
| 位姿记录 | 填写静止、前进、转向和停车后的实际读数 |
| RViz截图 | 保留Fixed Frame、显示项、相同视角及参数说明 |
| 运行数据 | 根据实验要求保存点云、IMU与算法输出数据包 |

> 图11（待补）：参数导出、数据记录完成信息与本轮结果目录。

### 14、整理实验报告

按下表完成报告，结论应结合自己的参数、位姿与截图。

| 报告内容 | 要求 |
| --- | --- |
| 任务与部署 | 简述任务，记录系统、ROS、Gazebo及构建结果 |
| 数据接入 | 画出原始点云、消息适配、IMU与FAST-LIO的连接关系 |
| 建图观察 | 用截图区分当前帧与地图，说明运动时墙面是否对齐 |
| 定位观察 | 提交分段运动前后读数，说明位置、朝向与轨迹变化 |
| 参数比较 | 对比三档体素尺寸，说明选择依据 |
| 文件交付 | 提交地图、参数、截图和要求的数据包 |
| 问题处理 | 记录实际问题、处理方法和仍未解决的现象 |

思考并回答：

1. 实验七的XYZ降采样结果为什么不能直接替代本实验的带时间点云输入？
2. 当前帧点云和三维地图在显示内容上有什么区别？
3. 机器人转向后继续前进，为什么地图坐标系中的X、Y可能同时变化？
4. 体素尺寸较小是否一定更好？请结合自己的观察说明。
5. 保存地图、持续运行时的位姿估计、重新加载地图定位，三者分别完成什么任务？

## 常见问题

| 现象 | 优先查看 |
| --- | --- |
| Gazebo中有机器人，RViz中没有地图 | 仿真是否运行、FAST-LIO是否初始化、Fixed Frame是否为 `camera_init` |
| 看得到地图，看不到当前帧 | 是否勾选 `Registered current scan`，话题是否为 `/cloud_registered` |
| 地图正常，轨迹暂时未变化 | 等待若干帧更新，再结合 `/Odometry` 与模型位置判断 |
| 修改参数后没有变化 | 是否保存文件并重启整套场景，实际参数是否与修改一致 |
| 地图保存失败 | `/map_save` 对应算法是否仍在运行、地图是否已经形成、目录是否可写 |
| 两轮地图或记录被覆盖 | 是否为每轮指定不同文件名并及时整理参数文件 |

## 实验核心结论

1. 建图需要把不同时刻的观测转换到共同参考坐标系中；
2. 原始点云的逐点时间与IMU共同支持扫描期间的运动补偿；
3. 当前帧用于观察本次扫描，地图用于呈现已经建立的环境结构；
4. 位姿、轨迹和地图应结合Gazebo中的实际运动一起观察；
5. 降采样参数需要结合计算负担、环境结构和定位连续性选择；
6. 保存PCD地图与实现重启后的地图定位是不同任务。

## 实验总结

本实验衔接实验七的点云处理知识，从独立部署开始，将原始点云与IMU接入FAST-LIO，开展静止初始化、分段建图、位姿观察和参数比较，最后保存地图与实验记录。

通过本实验，应能够说明“数据从哪里来、运动怎样估计、地图怎样形成”，并依据RViz画面和实际记录判断当前建图效果。
