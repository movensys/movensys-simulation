ARG ARCH=amd64
FROM nvcr.io/nvidia/isaac/ros:isaac_ros_6a0af6f39da3232fdca6b60f4b174e8a-${ARCH}

USER root
WORKDIR /workspaces

RUN rm -f /etc/apt/sources.list.d/yarn.list || true

RUN apt-get update && \
    apt-get install -y \
      ros-jazzy-ament-package \
      ros-jazzy-ament-index-cpp \
      ros-jazzy-ament-cmake-core \
      ros-jazzy-ament-index-python \
      ros-jazzy-pal-statistics \
      ros-jazzy-pal-statistics-msgs \
      ros-jazzy-rmw-cyclonedds-cpp \
      ros-jazzy-tf-transformations \
      ros-jazzy-realsense2-camera \
      ros-jazzy-isaac-ros-apriltag \
      ros-jazzy-isaac-ros-realsense \
      ros-jazzy-isaac-ros-depth-image-proc \
      ros-jazzy-isaac-ros-image-proc \
      python3-colcon-common-extensions \
      python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y \
      ros-jazzy-isaac-ros-cumotion-examples \
      ros-jazzy-isaac-ros-nvblox \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
        ros-jazzy-rclcpp-action \
        ros-jazzy-moveit-ros \
        ros-jazzy-moveit-planners \
        ros-jazzy-moveit-plugins \
        ros-jazzy-moveit-setup-assistant \
        ros-jazzy-moveit-configs-utils \
    && rm -rf /var/lib/apt/lists/*
