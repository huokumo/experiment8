#!/usr/bin/env bash
set -eo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
if [ ! -d "$REPO/src/experiment5" ] || [ ! -d "$REPO/src/experiment7" ]; then
  echo 'First run: bash tools/prepare_workspace.sh'; exit 2
fi
export PYTHONNOUSERSITE=1
source /opt/ros/humble/setup.bash
cd "$REPO"
# FAST-LIO compilation uses considerable memory; limit parallel compilation.
export CMAKE_BUILD_PARALLEL_LEVEL=2
export MAKEFLAGS=-j2
colcon build --symlink-install --executor sequential \
  --packages-select experiment5_depth experiment7_lidar livox_ros_driver2 fast_lio experiment8_slam \
  --cmake-args -DCMAKE_BUILD_TYPE=Release
echo "Build finished. Load: source $REPO/install/setup.bash"
