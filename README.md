# 3D Files for Movensys Manipulator

This repository provides USD files for running `movensys-manipulator` in NVIDIA Isaac Sim.

## 1. Quick Start Guide

### 1-1. Environment Setup
```
export ROS_DOMAIN_ID=70
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/$ROS_DISTRO/lib

source /opt/ros/$ROS_DISTRO/setup.bash
```
```
source ~/.bashrc
```

### 1-2. Install Isaacsim

### 1-3. Clone Repository
```
mkdir -p  ~/workspaces
cd ~/workspaces
git clone https://github.com/movensys/movensys-simulation.git
```

### 1-4. Running Isaac Sim

1. Run Isaac Sim.
```
~/isaacsim/isaac-sim.selector.sh
```
2. Activate `isaacsim.ros2.bridge`
3. Click `Start`
4. Open USD file: `~/workspaces/movensys-simulation/<usd_name>.usd` as your test scenario.
5. Click `Play` on the left side.


## 2. Related Repositories

- [movensys-manipulator](https://github.com/movensys/movensys-manipulator) - Manipulator example for WMX ROS2 package
