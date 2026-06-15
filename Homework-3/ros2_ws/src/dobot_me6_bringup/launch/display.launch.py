from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description_pkg = FindPackageShare("dobot_me6_description")
    urdf = PathJoinSubstitution([description_pkg, "urdf", "dobot_me6.urdf.xacro"])
    rviz_config = PathJoinSubstitution([description_pkg, "rviz", "dobot_me6.rviz"])

    robot_description = {
        "robot_description": Command(["xacro ", urdf, " control_mode:=fake"])
    }

    return LaunchDescription(
        [
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[robot_description],
                output="screen",
            ),
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                output="screen",
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                arguments=["-d", rviz_config],
                output="screen",
            ),
        ]
    )
