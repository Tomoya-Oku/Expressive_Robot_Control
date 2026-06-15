import math
import os
import time

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node
from sensor_msgs.msg import JointState

from .dobot_dashboard_client import DobotDashboardClient


JOINT_NAMES = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
JOINT_LIMITS = {
    "joint1": (-math.pi, math.pi),
    "joint2": (-2.3562, 2.3562),
    "joint3": (-2.7925, 2.7925),
    "joint4": (-math.pi, math.pi),
    "joint5": (-2.3562, 2.3562),
    "joint6": (-2.0 * math.pi, 2.0 * math.pi),
}


class Me6TrajectoryBridge(Node):
    def __init__(self):
        super().__init__("dobot_me6_trajectory_bridge")
        self.declare_parameter("robot_ip", os.getenv("DOBOT_ME6_IP", "192.168.5.1"))
        self.declare_parameter(
            "motion_port", int(os.getenv("DOBOT_ME6_MOTION_PORT", "30003"))
        )
        self.declare_parameter("dry_run", True)
        self.declare_parameter("speed_ratio", 10.0)
        self.declare_parameter(
            "command_template",
            "JointMovJ({j1:.3f},{j2:.3f},{j3:.3f},{j4:.3f},{j5:.3f},{j6:.3f})",
        )

        self._joint_state_pub = self.create_publisher(JointState, "joint_states", 10)
        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            "me6_arm_controller/follow_joint_trajectory",
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
        )
        self._positions = [0.0] * len(JOINT_NAMES)
        self._timer = self.create_timer(0.05, self.publish_joint_state)
        self.get_logger().info(
            "Started ME6 trajectory bridge. dry_run=%s"
            % self.get_parameter("dry_run").value
        )

    def publish_joint_state(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = self._positions
        self._joint_state_pub.publish(msg)

    def goal_callback(self, goal_request):
        ok, reason = self.validate_trajectory(goal_request.trajectory)
        if not ok:
            self.get_logger().error(reason)
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().warn("Cancel requested. StopRobot is sent when dry_run is false.")
        if not self.get_parameter("dry_run").value:
            host = self.get_parameter("robot_ip").value
            port = self.get_parameter("motion_port").value
            with DobotDashboardClient(host, port, dry_run=False) as client:
                self.get_logger().warn(client.send("StopRobot()"))
        return CancelResponse.ACCEPT

    def validate_trajectory(self, trajectory):
        if list(trajectory.joint_names) != JOINT_NAMES:
            return False, f"Joint order must be exactly {JOINT_NAMES}"
        if not trajectory.points:
            return False, "Trajectory has no points"
        for point_index, point in enumerate(trajectory.points):
            if len(point.positions) != len(JOINT_NAMES):
                return False, f"Point {point_index} does not contain 6 positions"
            for name, position in zip(JOINT_NAMES, point.positions):
                lower, upper = JOINT_LIMITS[name]
                if position < lower or position > upper:
                    return False, f"{name}={position:.3f} rad is outside [{lower:.3f}, {upper:.3f}]"
        return True, ""

    def execute_callback(self, goal_handle):
        host = self.get_parameter("robot_ip").value
        port = self.get_parameter("motion_port").value
        dry_run = self.get_parameter("dry_run").value
        speed_ratio = float(self.get_parameter("speed_ratio").value)
        template = self.get_parameter("command_template").value
        result = FollowJointTrajectory.Result()

        trajectory = goal_handle.request.trajectory
        feedback = FollowJointTrajectory.Feedback()
        feedback.joint_names = JOINT_NAMES

        try:
            with DobotDashboardClient(host, port, dry_run=dry_run) as client:
                self.get_logger().info(client.send(f"SpeedFactor({speed_ratio:.1f})"))
                previous_time = 0.0
                for point in trajectory.points:
                    if goal_handle.is_cancel_requested:
                        goal_handle.canceled()
                        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
                        return result
                    target_time = point.time_from_start.sec + point.time_from_start.nanosec * 1e-9
                    time.sleep(max(0.0, target_time - previous_time))
                    previous_time = target_time
                    degrees = [math.degrees(value) for value in point.positions]
                    command = template.format(
                        j1=degrees[0],
                        j2=degrees[1],
                        j3=degrees[2],
                        j4=degrees[3],
                        j5=degrees[4],
                        j6=degrees[5],
                    )
                    response = client.send(command)
                    self.get_logger().info(response)
                    self._positions = list(point.positions)
                    feedback.desired.positions = list(point.positions)
                    feedback.actual.positions = self._positions
                    goal_handle.publish_feedback(feedback)
        except Exception as exc:
            self.get_logger().error(f"Trajectory execution failed: {exc}")
            goal_handle.abort()
            result.error_code = FollowJointTrajectory.Result.INVALID_GOAL
            result.error_string = str(exc)
            return result

        goal_handle.succeed()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        return result


def main():
    rclpy.init()
    node = Me6TrajectoryBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
