FROM osrf/ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    curl \
    git \
    iputils-ping \
    netcat-openbsd \
    nlohmann-json3-dev \
    python3-colcon-common-extensions \
    python3-pip \
    python3-rosdep \
    python3-pytest \
    ros-humble-ament-copyright \
    ros-humble-ament-flake8 \
    ros-humble-ament-lint-auto \
    ros-humble-ament-lint-common \
    ros-humble-ament-pep257 \
    ros-humble-control-msgs \
    ros-humble-controller-manager \
    ros-humble-gazebo-plugins \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-gazebo-ros2-control \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-broadcaster \
    ros-humble-joint-state-publisher-gui \
    ros-humble-joint-trajectory-controller \
    ros-humble-moveit \
    ros-humble-moveit-servo \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-ros2launch \
    ros-humble-rosidl-default-generators \
    ros-humble-rviz2 \
    ros-humble-xacro \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init 2>/dev/null || true && rosdep update

ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN if ! id -u ${USERNAME} >/dev/null 2>&1; then \
      groupadd --gid ${USER_GID} ${USERNAME} && \
      useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}; \
    fi

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER ${USERNAME}
WORKDIR /home/${USERNAME}/ws

RUN rosdep update

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
