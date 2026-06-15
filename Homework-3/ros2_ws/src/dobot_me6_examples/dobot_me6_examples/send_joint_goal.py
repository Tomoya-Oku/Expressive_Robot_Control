import argparse
import math
import sys

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectoryPoint


JOINT_NAMES = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
TARGETS = {
    "home": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "ready": [0.0, -30.0, 45.0, 0.0, 35.0, 0.0],
    "inspect": [35.0, -25.0, 60.0, 20.0, 30.0, -25.0],
}


class JointGoalClient(Node):
    def __init__(self, action_name: str):
        super().__init__("dobot_me6_send_joint_goal")
        self.client = ActionClient(self, FollowJointTrajectory, action_name)

    def send(self, degrees, duration):
        if not self.client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("FollowJointTrajectory action server is not available.")
            return 1

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINT_NAMES
        point = JointTrajectoryPoint()
        point.positions = [math.radians(value) for value in degrees]
        point.time_from_start.sec = int(duration)
        point.time_from_start.nanosec = int((duration - int(duration)) * 1e9)
        goal.trajectory.points = [point]

        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected.")
            return 1

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result().result
        self.get_logger().info(f"Result error_code={result.error_code}")
        return 0 if result.error_code == FollowJointTrajectory.Result.SUCCESSFUL else 1


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=sorted(TARGETS), default="ready")
    parser.add_argument(
        "--joints-deg",
        nargs=6,
        type=float,
        metavar=("J1", "J2", "J3", "J4", "J5", "J6"),
        help="Override target with six joint angles in degrees.",
    )
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument(
        "--action-name",
        default="/me6_arm_controller/follow_joint_trajectory",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    degrees = args.joints_deg if args.joints_deg is not None else TARGETS[args.target]

    rclpy.init()
    node = JointGoalClient(args.action_name)
    rc = node.send(degrees, args.duration)
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(rc)
