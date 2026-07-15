# Movensys Simulation

USD scene files for running the [`movensys-manipulator`](https://github.com/movensys/movensys-manipulator) examples in [NVIDIA Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/).

## Overview

This repository ships ready-to-open Isaac Sim scenes for the Dobot CR3A and CR5A
manipulators driven by the WMX R2 stack. Each scene wires the robot, gripper,
sensors, and `isaacsim.ros2.bridge` topics needed by the matching example in
`movensys-manipulator`, so you can launch a demo without authoring the scene
from scratch.

## Repository Layout

```
.
├── dobot_cr3a/   # USD scenes for the Dobot CR3A manipulator
└── dobot_cr5a/   # USD scenes for the Dobot CR5A manipulator
```

### Scene naming convention

Each scene is named `<n><mode>_<example>.usd`, where `<mode>` selects how the
robot is driven:

| Suffix | Mode             | Purpose                                       |
|--------|------------------|-----------------------------------------------|
| `a`    | `simulation`     | Pure Isaac Sim — no physical hardware needed  |
| `b`    | `hil`            | Hardware-in-the-loop — sim with WMX runtime   |
| `c`    | `real`           | Visualization against the real robot          |

The CR3A directory provides scenes for the trajectory, AprilTag pick-and-place,
obstacle avoidance, RoboPoly, and AprilTag obstacle-avoidance examples. The
CR5A directory currently provides the trajectory scene.

## Requirements

- Ubuntu 22.04 or 24.04
- [NVIDIA Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/installation/index.html) 5.0.0+
- ROS 2 (Jazzy recommended) with the `isaacsim.ros2.bridge` extension enabled
- The [`movensys-manipulator`](https://github.com/movensys/movensys-manipulator) workspace to drive the scenes

## Quick Start

### 1. Configure the ROS 2 environment

Add the following to your `~/.bashrc` (or source it per shell):

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

### 2. Clone the repository

```
mkdir -p ~/workspaces
cd ~/workspaces
git clone https://github.com/movensys/movensys-simulation.git
```

### 3. Launch Isaac Sim

```
~/isaacsim/isaac-sim.selector.sh
```

1. Enable the `isaacsim.ros2.bridge` extension and click **Start**.
2. Open a scene under `~/workspaces/movensys-simulation/`, for example:
   `dobot_cr3a/3a_trajectory_simulation.usd`.
3. Click **Play** in the left toolbar to start the simulation.
4. Run the matching example from
   [`movensys-manipulator`](https://github.com/movensys/movensys-manipulator)
   to drive the robot.

## Related Repositories

- [movensys-manipulator](https://github.com/movensys/movensys-manipulator) — Manipulator examples for the WMX R2 package
- [movensys-intelligence](https://github.com/movensys/movensys-intelligence) — VLM-driven task planning for the manipulator

## License

Released under the MIT License. See [`LICENSE.txt`](LICENSE.txt) for details.
