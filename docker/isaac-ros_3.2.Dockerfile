ARG ARCH=amd64
FROM isaac_ros_dev-x86_64 AS base-amd64
FROM isaac_ros_dev-aarch64 AS base-arm64
FROM base-${ARCH}

USER root
WORKDIR /workspaces

RUN rm -f /etc/apt/sources.list.d/yarn.list || true

RUN apt-get update && \
    apt-get install -y \
      ros-humble-ament-package \
      ros-humble-ament-index-cpp \
      ros-humble-ament-cmake-core \
      ros-humble-ament-index-python \
      python3-colcon-common-extensions \
      python3-setuptools \
      ros-humble-pal-statistics \
      ros-humble-pal-statistics-msgs \
      ros-humble-rmw-cyclonedds-cpp \
      ros-humble-tf-transformations \
      ros-humble-isaac-ros-cumotion-examples \
      ros-humble-isaac-ros-apriltag \
      ros-humble-isaac-ros-nvblox \
      ros-humble-isaac-ros-examples \
      ros-humble-isaac-ros-realsense \
      ros-humble-isaac-ros-ess \
      ros-humble-isaac-ros-ess-models-install && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install --only-upgrade -y \
        ros-humble-rclcpp-action \
        ros-humble-moveit* \
    && rm -rf /var/lib/apt/lists/*

RUN sudo apt-get update

RUN rosdep update && \
    rosdep install isaac_ros_nvblox