import argparse
import math
import sys

import rclpy
from geometry_msgs.msg import PointStamped, PoseStamped

from dobot_me6_examples.ee_control_common import (
    DobotME6Kinematics,
    TrajectoryClient,
    get_start_q,
    positive_float,
)


class MocapMimicNode(TrajectoryClient):
    def __init__(self, args):
        super().__init__(args.action_name, args.trajectory_topic)
        self.args = args
        self.kinematics = DobotME6Kinematics()
        self.command_q = get_start_q(self, args.start)
        self.center, _, _ = self.kinematics.forward(self.command_q)
        self.mocap_origin = None
        self.latest_mocap = None
        msg_type = PoseStamped if args.message_type == "pose_stamped" else PointStamped
        self.create_subscription(msg_type, args.mocap_topic, self.mocap_callback, 10)
        self.create_timer(1.0 / args.rate, self.control_loop)

    def mocap_callback(self, msg):
        if isinstance(msg, PoseStamped):
            point = msg.pose.position
        else:
            point = msg.point
        sample = [point.x, point.y, point.z]
        if self.mocap_origin is None:
            self.mocap_origin = sample
            self.get_logger().info(f"Captured mocap origin from {self.args.mocap_topic}: {self.mocap_origin}")
        self.latest_mocap = sample

    def control_loop(self):
        if self.latest_mocap is None or self.mocap_origin is None:
            return
        target = self.make_target()
        base_q = self.latest_joints or self.command_q
        self.command_q, err = self.kinematics.step_ik(
            base_q,
            target,
            self.args.gain,
            self.args.damping,
            self.args.max_joint_step,
        )
        self.publish_positions([self.command_q], 1.0 / self.args.rate)
        if err > self.args.warn_error:
            self.get_logger().warn(f"mocap target tracking error estimate={err:.4f} m")

    def make_target(self):
        delta = [
            (self.latest_mocap[i] - self.mocap_origin[i]) * self.args.scale
            for i in range(3)
        ]
        delta = clamp_vector(delta, self.args.max_offset)
        return [self.center[i] + delta[i] for i in range(3)]


def clamp_vector(values, max_norm):
    norm = math.sqrt(sum(v * v for v in values))
    if norm <= max_norm:
        return values
    scale = max_norm / max(norm, 1e-9)
    return [v * scale for v in values]


def parse_args():
    parser = argparse.ArgumentParser(description="Mimic human mocap translation with ME6 end-effector motion.")
    parser.add_argument("--mocap-topic", default="/mocap/pose")
    parser.add_argument("--message-type", choices=("pose_stamped", "point_stamped"), default="pose_stamped")
    parser.add_argument("--trajectory-topic", default="/me6_arm_controller/joint_trajectory")
    parser.add_argument("--action-name", default="/me6_arm_controller/follow_joint_trajectory")
    parser.add_argument("--start", choices=("current", "ready", "home"), default="current")
    parser.add_argument("--rate", type=positive_float, default=20.0)
    parser.add_argument("--scale", type=positive_float, default=0.20)
    parser.add_argument("--max-offset", type=positive_float, default=0.080)
    parser.add_argument("--gain", type=float, default=2.0)
    parser.add_argument("--damping", type=float, default=0.04)
    parser.add_argument("--max-joint-step", type=float, default=0.025)
    parser.add_argument("--warn-error", type=positive_float, default=0.050)
    return parser.parse_args()


def main():
    rclpy.init()
    node = MocapMimicNode(parse_args())
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    sys.exit(0)

