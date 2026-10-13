# Movensys Simulation

USD scene files for running the
[`movensys-manipulator`](https://github.com/movensys/movensys-manipulator),
[`movensys-navigation`](https://github.com/movensys/movensys-navigation), and
[`movensys-intelligence`](https://github.com/movensys/movensys-intelligence)
examples in [NVIDIA Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/).

## Overview

This repository ships ready-to-open Isaac Sim scenes for the Dobot CR3A/CR5A
manipulators and the `diffbot` differential-drive base, all driven by the
[WMX R2](https://github.com/movensys/wmx-r2) motion stack. Each scene wires the
robot, gripper or wheels, sensors, and the `isaacsim.ros2.bridge` action graphs
(joint states, `/cmd_vel_safe`, camera, LiDAR, TF) needed by the matching example, so
you can launch a demo without authoring the scene from scratch.

## Repository Layout

```
.
├── dobot_cr3a/   # USD scenes for the Dobot CR3A manipulator
│   ├── movensys_manipulator/   # shared CR3A robot asset (referenced by every scene)
│   └── board_game_stuffs/      # RoboPoly board, dice, and tray assets + generators
├── dobot_cr5a/   # USD scenes for the Dobot CR5A manipulator
│   └── movensys_manipulator/   # shared CR5A robot asset
└── diffbot/      # USD scenes for the differential-drive mobile base
    └── movensys_navigation/    # shared diffbot robot asset
```

Each robot directory contains a `movensys_<domain>/` asset folder built with the
Isaac Sim asset structure — `configuration/*_base.usd`, `*_physics.usd`,
`*_robot.usd`, and `*_sensor.usd` layers composed into a single entry-point
`movensys_<domain>.usd`. The numbered scenes reference that asset, so a fix to
the robot, its physics, or its sensors propagates to every scene at once.

### Scene naming convention

Manipulator scenes are named `<n><mode>_<example>.usd`, where `<mode>` selects
how the robot is driven:

| Suffix | Mode         | Purpose                                                    |
|--------|--------------|------------------------------------------------------------|
| `a`    | `simulation` | Pure Isaac Sim — no physical hardware needed               |
| `b`    | `hil`        | Hardware-in-the-loop: sim visuals with the WMX runtime     |
| `c`    | `real`       | Visualization against the real robot                       |

Diffbot scenes are not numbered; they use the `navigation_<mode>.usd` form.

## Scenes

### `dobot_cr3a/` — Dobot CR3A

| Scene                            | Simulation                                  | HIL                                  | Real                                  |
|----------------------------------|---------------------------------------------|--------------------------------------|---------------------------------------|
| Trajectory planning              | `3a_trajectory_simulation.usd`               | `3b_trajectory_hil.usd`               | `3c_trajectory_real.usd`               |
| AprilTag pick-and-place          | `4a_apriltag_pick_and_place_simulation.usd`  | `4b_apriltag_pick_and_place_hil.usd`  | `4c_apriltag_pick_and_place_real.usd`  |
| Nvblox obstacle avoidance        | `5a_obstacle_avoidance_simulation.usd`       | `5b_obstacle_avoidance_hil.usd`       | `5c_obstacle_avoidance_real.usd`       |
| AprilTag + Nvblox                | `6a_apriltag_obstacle_avoidance_simulation.usd` | `6b_apriltag_obstacle_avoidance_hil.usd` | `6c_apriltag_obstacle_avoidance_real.usd` |
| RoboPoly (VLM board game)        | `7a_robopoly_simulation.usd`                 | `7b_robopoly_hil.usd`                 | `7c_robopoly_real.usd`                 |
| YOLO pick-and-place              | `8a_yolo_pick_and_place_simulation.usd`      | `8b_yolo_pick_and_place_hil.usd`      | `8c_yolo_pick_and_place_real.usd`      |

### `dobot_cr5a/` — Dobot CR5A

| Scene               | Simulation                  | HIL                  | Real                  |
|---------------------|-----------------------------|----------------------|-----------------------|
| Trajectory planning | `trajectory_simulation.usd` | `trajectory_hil.usd` | `trajectory_real.usd` |

### `diffbot/` — mobile base

| Scene                                     | Simulation                  | HIL                  |
|-------------------------------------------|-----------------------------|----------------------|
| Manual driving, SLAM mapping, Nav2        | `navigation_simulation.usd` | `navigation_hil.usd` |

The same two diffbot scenes back all three navigation examples (manual driving,
SLAM mapping, autonomous navigation); the scene provides the base, wheels,
LiDAR, and depth camera, and the Nav2 stack decides what to do with them. There
is no `real` scene — the real base is visualized in RViz, not Isaac Sim.

### RoboPoly board assets

`dobot_cr3a/board_game_stuffs/` holds the props used by the RoboPoly scenes —
the printed board (`board.png`, `monopoly_board.drawio`), the dice
(`dice.usda`, `create_dice.py`), and the parts tray (`tray.usda`, `tray.STL`) —
plus helper scripts for generating randomized board variations and shuffling
token placement for perception training data. See
[`board_game_stuffs/README.md`](dobot_cr3a/board_game_stuffs/README.md).

## Requirements

- Ubuntu 22.04 or 24.04
- [NVIDIA Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/installation/index.html) 5.0.0+
- ROS 2 (Jazzy recommended) with the `isaacsim.ros2.bridge` extension enabled
- One of the driving workspaces:
  [`movensys-manipulator`](https://github.com/movensys/movensys-manipulator) for
  the arm scenes,
  [`movensys-navigation`](https://github.com/movensys/movensys-navigation) for
  the diffbot scenes

## Quick Start

### 1. Configure the ROS 2 environment

Add the following to your `~/.bashrc` (or source it per shell). `ROS_DOMAIN_ID`
and `RMW_IMPLEMENTATION` must match the values used by the workspace that drives
the scene, or Isaac Sim and the ROS 2 nodes will not see each other:

```
export ROS_DOMAIN_ID=73
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/ros/$ROS_DISTRO/lib

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
   [`movensys-manipulator`](https://github.com/movensys/movensys-manipulator) or
   [`movensys-navigation`](https://github.com/movensys/movensys-navigation)
   to drive the robot.

Each example walkthrough in those repositories names the scene it expects at the
top of the page, under `~/workspaces/movensys-simulation/<MANIPULATOR_MODEL>/`
or `<NAVIGATION_MODEL>/`.

## Related Repositories

- [movensys-manipulator](https://github.com/movensys/movensys-manipulator) — Manipulator examples (MoveIt 2 / cuMotion, AprilTag, Nvblox, YOLO)
- [movensys-navigation](https://github.com/movensys/movensys-navigation) — Nav2-based mobile base examples
- [movensys-intelligence](https://github.com/movensys/movensys-intelligence) — VLM-driven task planning (RoboPoly)
- [wmx-r2](https://github.com/movensys/wmx-r2) — WMX R2 EtherCAT motion control stack

## License

Released under the MIT License. See [`LICENSE.txt`](LICENSE.txt) for details.
