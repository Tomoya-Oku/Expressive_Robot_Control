#!/usr/bin/env bash
set -e

source /opt/ros/humble/setup.bash

if [ -f /usr/share/gazebo/setup.bash ]; then
  source /usr/share/gazebo/setup.bash
fi

if [ -f /home/ros/ws/install/setup.bash ]; then
  source /home/ros/ws/install/setup.bash
fi

exec "$@"
