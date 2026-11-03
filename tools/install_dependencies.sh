#!/usr/bin/env bash
# Initial image: Ubuntu 22.04 + ROS 2 Humble, with the course apt sources configured.
set -eo pipefail
if [ "$(id -u)" -ne 0 ]; then
  echo 'Run with sudo: sudo bash tools/install_dependencies.sh'; exit 2
fi
apt-get update
# Install Fortress first, following the same starting environment as Experiment6/7.
apt-get install -y ros-humble-ros-gz
apt-get install -y git build-essential cmake python3-colcon-common-extensions \
  python3-numpy python3-scipy python3-yaml libeigen3-dev libpcl-dev \
  libignition-gazebo6-dev ros-humble-ament-cmake-python \
  ros-humble-rclcpp ros-humble-rclcpp-components ros-humble-pcl-ros ros-humble-pcl-conversions \
  ros-humble-rosidl-default-generators ros-humble-rosidl-default-runtime \
  ros-humble-std-srvs ros-humble-visualization-msgs \
  ros-humble-tf2-ros ros-humble-tf2-ros-py ros-humble-robot-state-publisher \
  ros-humble-launch-xml ros-humble-rviz2 ros-humble-ros2run \
  ros-humble-ros2param ros-humble-ros2node \
  ros-humble-rosbag2 ros-humble-rosbag2-storage-default-plugins
