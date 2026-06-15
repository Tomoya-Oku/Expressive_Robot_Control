# Homework-3: DOBOT ME6 ROS 2 Docker Environment

This directory provides a Docker-based ROS 2 Humble workspace for DOBOT ME6/E6 visualization, MoveIt, Gazebo simulation, and hardware validation checks without touching a host machine that already has ROS 1 installed. The primary robot model comes from the official `Dobot-Arm/DOBOT_6Axis_ROS2_V4` ROS 2 SDK vendored in `ros2_ws/src/DOBOT_6Axis_ROS2_V4`.

## Layout

- `docker/`: Dockerfile for ROS 2 Humble, Gazebo, MoveIt, and ros2_control
- `compose.yaml`: Docker Compose settings for GUI, host networking, and device access
- `ros2_ws/src/DOBOT_6Axis_ROS2_V4`: official DOBOT ROS 2 SDK with ME6/E6 URDF, STL meshes, MoveIt, Gazebo, and TCP integration
- `ros2_ws/src/dobot_me6_description`: approximate fallback URDF/Xacro for coursework
- `ros2_ws/src/dobot_me6_bringup`: fallback RViz, fake control, and Gazebo launch files
- `ros2_ws/src/dobot_me6_driver`: TCP connectivity check and guarded dry-run trajectory bridge
- `ros2_ws/src/dobot_me6_examples`: JointTrajectory goal examples
- `UPSTREAM_DOBOT_6AXIS_ROS2_V4.md`: upstream URL and imported commit

## Runtime Environment

This workspace assumes the following environment.

| Item | Recommended/Used Version |
| --- | --- |
| Host OS | Verified on Ubuntu 22.04 LTS |
| Docker Engine | Docker Engine 20.10.17 or newer |
| Docker Compose | Docker Compose plugin v2.6.0 or newer |
| Container OS | Ubuntu 22.04 family |
| ROS 2 | Humble Hawksbill |
| Docker base image | `osrf/ros:humble-desktop` |
| Gazebo | Gazebo Classic provided by ROS 2 Humble apt packages |
| GUI | X11 |
| CPU/memory | x86_64, 8 GB RAM or more recommended |
| Disk space | 10 GB or more recommended for the Docker image and workspace |
| Hardware network | Wired LAN recommended, reachable from the host to the DOBOT ME6 |

Docker installation assumes the official Docker apt repository method on Ubuntu 22.04. The local setup was based on the Qiita article "Ubuntu 22.04にdockerをインストールする".

Check the host versions with:

```bash
docker --version
docker compose version
uname -m
lsb_release -a
```

Check ROS 2 inside the container with:

```bash
make shell
ros2 --version
printenv ROS_DISTRO
```

`printenv ROS_DISTRO` should return `humble`.

## Environment Setup

Docker and the Docker Compose plugin are required on the host. ROS 2 runs only inside the Docker container, so an existing host ROS 1 installation is fine. Linux/X11 is assumed for RViz and Gazebo.

### 1. Install Docker

On Ubuntu 22.04 without Docker, install Docker Engine and the Compose plugin from Docker's official apt repository.

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

After installation, confirm that the Docker daemon is running.

```bash
sudo systemctl status docker
sudo docker run hello-world
docker compose version
```

If `sudo docker run hello-world` succeeds, Docker itself is installed. Configure user permissions in the next step if you want to run `make build` and `make ws` without `sudo`.

### 2. Check Docker permissions

First confirm that the current user can access the Docker daemon.

```bash
docker ps
```

If you see `permission denied while trying to connect to the docker API`, add the current user to the `docker` group.

```bash
sudo usermod -aG docker $USER
```

Note: membership in the `docker` group effectively grants root-level control through the Docker daemon. Check the administration policy on shared machines.

Run this command only once. Do not put it in `.bashrc`. To apply the group change, log out of Ubuntu and log back in, or apply it to the current terminal with:

```bash
newgrp docker
docker ps
```

### 3. Enter Homework-3

Move to the `Homework-3` directory that contains this README. If your prompt is already in `~/Expressive_Robot_Control/Homework-3`, do not run `cd Homework-3` again.

```bash
cd ~/Expressive_Robot_Control/Homework-3
```

### 4. Allow GUI display

Allow local X11 connections so RViz and Gazebo can open windows from the Docker container.

```bash
xhost +local:docker
```

After the session, revoke the permission if desired.

```bash
xhost -local:docker
```

### 5. Build the Docker image

This creates the Docker image with ROS 2 Humble, Gazebo, MoveIt, ros2_control, and dependencies needed by the DOBOT official SDK.

```bash
make build
```

### 6. Build the ROS 2 workspace

This resolves dependencies with `rosdep` and builds the ME6-related packages with `colcon`.

```bash
make ws
```

To enter the built container and inspect the workspace manually:

```bash
make shell
source install/setup.bash
ros2 pkg list | grep -E 'dobot|me6|cra_description'
```

Note: the upstream `me6_moveit/package.xml` lists `warehouse_ros_mongo`, but ROS 2 Humble does not provide `ros-humble-warehouse-ros-mongo` through apt. `make ws` skips that rosdep key. It is not required for the normal RViz, Gazebo, or MoveIt demo flows.

## Visualize in RViz

This launches the official ME6 model in RViz.

```bash
make rviz
```

In another terminal:

```bash
cd Homework-3
make shell
source install/setup.bash
ros2 run dobot_me6_examples send_joint_goal --target ready
```

## Validate Trajectories with Fake Control

This starts the fallback local model with a `ros2_control` fake hardware backend, so no physical robot moves.

```bash
make fake
```

In another terminal:

```bash
make shell
source install/setup.bash
ros2 run dobot_me6_examples send_joint_goal --target home
```

## Gazebo Simulation

This spawns the official ME6 model in Gazebo.

```bash
make sim
```

MoveIt virtual demo:

```bash
make moveit
```

Prefer the official SDK model in `cra_description/urdf/me6_robot.xacro` and `me6_moveit`. `dobot_me6_description` remains as a small fallback model for ROS 2 control checks without upstream dependencies.

## Hardware Validation

Start with a communication-only check:

```bash
export DOBOT_ME6_IP=192.168.5.1
make real-check
```

The trajectory bridge defaults to dry-run mode.

```bash
make shell
source install/setup.bash
ros2 launch dobot_me6_driver real_validation.launch.py robot_ip:=$DOBOT_ME6_IP dry_run:=true
```

To use the official SDK TCP bringup:

```bash
make real
```

Only switch `dry_run` off after checking the emergency stop, workspace, speed limits, homing state, and manufacturer-side safety settings.

```bash
ros2 launch dobot_me6_driver real_validation.launch.py robot_ip:=$DOBOT_ME6_IP dry_run:=false speed_ratio:=10.0
```

From another terminal:

```bash
ros2 run dobot_me6_examples send_joint_goal --target ready --duration 5.0
```

Note: `dobot_me6_driver` uses a command skeleton based on common DOBOT CR/CRA Dashboard/Motion TCP APIs. If the ME6 firmware uses different command names, ports, units, or joint order, adapt `dobot_dashboard_client.py` to the official hardware manual before enabling motion.

## ROS 1 Isolation

The host ROS 1 installation is not used. ROS 2 environment variables, Python packages, and Gazebo packages stay inside the Docker image. The host only provides Docker, X11 display access, and network access to the robot.

## References

- Docker Docs: Install Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
- Docker Docs: Linux post-installation steps for Docker Engine: https://docs.docker.com/engine/install/linux-postinstall/
- Qiita: Ubuntu 22.04にdockerをインストールする: https://qiita.com/yoshiyasu1111/items/17d9d928ceebb1f1d26d
