"""Launch file for camera transform tuning with RViz visualization"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory('movensys_camera')

    xacro_file = os.path.join(get_package_share_directory('movensys_manipulator_description'),
        'urdf', 'movensys_manipulator.xacro')

    rviz_config = os.path.join(pkg_share, 'rviz', 'camera_transform_tuning.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock (/clock)'
    )

    child_frame = LaunchConfiguration('child_frame')
    declare_child_frame = DeclareLaunchArgument(
        'child_frame',
        default_value=PythonExpression([
            "'camera_top_color_optical_frame' if '", use_sim_time, "'.lower() == 'true' else 'camera_top_link'"
        ]),
        description='Child frame for camera transform'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', xacro_file]),
            'use_sim_time': use_sim_time
        }]
    )

    camera_transform_tuning_node = Node(
        package='movensys_camera',
        executable='camera_transform_tuning.py',
        name='camera_transform_tuner',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'child_frame': child_frame
        }]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_child_frame,
        robot_state_publisher,
        camera_transform_tuning_node,
        rviz_node,
    ])
