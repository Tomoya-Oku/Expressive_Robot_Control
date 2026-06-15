from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description_pkg = FindPackageShare("dobot_me6_description")
    bringup_pkg = FindPackageShare("dobot_me6_bringup")
    gazebo_pkg = FindPackageShare("gazebo_ros")

    urdf = PathJoinSubstitution([description_pkg, "urdf", "dobot_me6.urdf.xacro"])
    world = PathJoinSubstitution([bringup_pkg, "worlds", "empty.world"])

    robot_description = {
        "robot_description": Command(["xacro ", urdf, " control_mode:=gazebo"])
    }

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([gazebo_pkg, "launch", "gazebo.launch.py"])
        ),
        launch_arguments={"world": world}.items(),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[robot_description],
        output="screen",
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "dobot_me6"],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    arm_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["me6_arm_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    return LaunchDescription(
        [
            gazebo,
            robot_state_publisher,
            spawn_entity,
            RegisterEventHandler(
                OnProcessExit(target_action=spawn_entity, on_exit=[joint_state_broadcaster])
            ),
            RegisterEventHandler(
                OnProcessExit(target_action=joint_state_broadcaster, on_exit=[arm_controller])
            ),
        ]
    )
