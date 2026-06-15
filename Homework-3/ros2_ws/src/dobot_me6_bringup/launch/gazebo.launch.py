from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    start_rviz = LaunchConfiguration("start_rviz")
    description_pkg = FindPackageShare("cra_description")
    bringup_pkg = FindPackageShare("dobot_me6_bringup")
    gazebo_pkg = FindPackageShare("gazebo_ros")
    rviz_pkg = FindPackageShare("dobot_rviz")

    urdf = PathJoinSubstitution([description_pkg, "urdf", "me6_robot.xacro"])
    world = PathJoinSubstitution([bringup_pkg, "worlds", "empty.world"])
    rviz_config = PathJoinSubstitution([rviz_pkg, "rviz", "urdf.rviz"])

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

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        condition=IfCondition(start_rviz),
        output="screen",
    )

    ee_marker = Node(
        package="dobot_me6_examples",
        executable="ee_marker",
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("start_rviz", default_value="false"),
            gazebo,
            robot_state_publisher,
            spawn_entity,
            RegisterEventHandler(
                OnProcessExit(target_action=spawn_entity, on_exit=[joint_state_broadcaster])
            ),
            RegisterEventHandler(
                OnProcessExit(target_action=joint_state_broadcaster, on_exit=[arm_controller])
            ),
            ee_marker,
            rviz,
        ]
    )
