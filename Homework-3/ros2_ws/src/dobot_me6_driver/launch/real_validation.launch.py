from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description_pkg = FindPackageShare("cra_description")
    urdf = PathJoinSubstitution([description_pkg, "urdf", "me6_robot.xacro"])
    robot_description = {
        "robot_description": Command(["xacro ", urdf, " control_mode:=fake"])
    }

    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_ip", default_value="192.168.5.1"),
            DeclareLaunchArgument("motion_port", default_value="30003"),
            DeclareLaunchArgument("dry_run", default_value="true"),
            DeclareLaunchArgument("speed_ratio", default_value="10.0"),
            Node(
                package="dobot_me6_driver",
                executable="me6_trajectory_bridge",
                output="screen",
                parameters=[
                    {
                        "robot_ip": LaunchConfiguration("robot_ip"),
                        "motion_port": LaunchConfiguration("motion_port"),
                        "dry_run": LaunchConfiguration("dry_run"),
                        "speed_ratio": LaunchConfiguration("speed_ratio"),
                    }
                ],
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                output="screen",
                parameters=[robot_description],
            ),
        ]
    )
