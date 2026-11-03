# 第三方代码及修改说明

- `src/fast_lio`：Ericsii/FAST_LIO_ROS2，固定提交见 SOURCE_LOCK.json。保留上游 LICENSE（GPL v2）及源码版权。上游 package.xml 的 BSD 字段与根 LICENSE 不一致，本教学包保留原文并按 GPL v2 保存、分发该部分的完整源码。
- `src/fast_lio/include/ikd-Tree`：hku-mars/ikd-Tree 固定提交，保留源码许可与版权声明。
- `src/livox_ros_driver2/msg`：Livox-SDK 官方驱动的消息文件，MIT；只构建消息，不是官方硬件驱动，不包含 SDK2。
- 实验5模型与实验7仿真依赖通过固定提交下载；实验7所用 Livox 扫描方向表来自官方 MIT 仿真仓库。
- 本仓库新编写的教学集成脚本按根目录 BSD-3-Clause 许可发布；第三方代码遵循各自许可。

FAST-LIO 集成修改：IMU 使用 SensorDataQoS；修正里程计协方差在发布后才赋值的顺序；地图显示和保存从当前 ikd-Tree 提取，避免定时重复累计上一帧；地图保存失败返回 false；移除未使用的 Python 绘图链接，统一使用CMake指定的C++17标准。算法的 IMU 初始化、去畸变和状态估计流程保持上游实现。逐行修改记录见 `patches/fast_lio_integration.patch`，这些集成修改已在2026年11月3日完成教学平台编译及运行验证，结果见 docs/PLATFORM_VALIDATION.md。
