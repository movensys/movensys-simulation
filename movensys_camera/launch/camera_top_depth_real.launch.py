# SPDX-FileCopyrightText: NVIDIA CORPORATION & AFFILIATES
# Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import os

from ament_index_python import get_package_share_directory
import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    realsense_config_file_path = os.path.join(
        get_package_share_directory('movensys_perception'),
        'config', 'realsense_top_depth.yaml'
    )

    camera_node = ComposableNode(
        package='realsense2_camera',
        plugin='realsense2_camera::RealSenseNodeFactory',
        name='realsense2_camera',
        namespace='',
        parameters=[realsense_config_file_path],
        remappings=[
            ('~/color/image_raw', '/image_top/rgb'),
            ('~/color/camera_info', '/image_top/camera_info')
        ]
    )

    # Realsense depth is in uint16 and millimeters. Convert to float32 and meters
    convert_metric_node = ComposableNode(
        package='isaac_ros_depth_image_proc',
        plugin='nvidia::isaac_ros::depth_image_proc::ConvertMetricNode',
        name='convert_metric',
        remappings=[
            ('image_raw', '/realsense2_camera/aligned_depth_to_color/image_raw'),
            ('image', '/image_top/depth')
        ]
    )

    realsense_container = ComposableNodeContainer(
        package='rclcpp_components',
        name='realsense_container',
        namespace='',
        executable='component_container_mt',
        composable_node_descriptions=[
            camera_node, 
            convert_metric_node
        ],
        output='screen'
    )

    return launch.LaunchDescription([realsense_container])
