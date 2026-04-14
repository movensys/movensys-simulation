""" Static transform publisher acquired via MoveIt 2 hand-eye calibration """
""" EYE-TO-HAND: world -> camera """
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description() -> LaunchDescription:
    simulation_arg = DeclareLaunchArgument(
        "simulation", default_value="false",
        description="Set to true for simulation, false for real robot"
    )

    start_camera_top_transform_simulation = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        output="log",
        condition=IfCondition(LaunchConfiguration("simulation")),
        parameters=[{"use_sim_time": True}],
        arguments=[
            "--frame-id", "world_manipulator",
            "--child-frame-id", "camera_top_color_optical_frame",
            "--x", "0.2",
            "--y", "0.0",
            "--z", "0.7",
            "--roll", "0",
            "--pitch", "1.57",
            "--yaw", "0",
        ],
    )

    start_camera_top_transform_real = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        output="log",
        condition=UnlessCondition(LaunchConfiguration("simulation")),
        parameters=[{"use_sim_time": False}],
        arguments=[
            "--frame-id", "world_manipulator",
            "--child-frame-id", "camera_top_link",
            "--x", "0.2",
            "--y", "0.0",
            "--z", "0.7",
            "--roll", "0",
            "--pitch", "1.57",
            "--yaw", "0",
        ],
    )

    return LaunchDescription([
        simulation_arg,
        start_camera_top_transform_simulation,
        start_camera_top_transform_real,
    ])