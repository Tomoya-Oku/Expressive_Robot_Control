import argparse
import select
import sys
import termios
import tty

import rclpy

from dobot_me6_examples.ee_control_common import (
    DobotME6Kinematics,
    TrajectoryClient,
    get_start_q,
)


KEY_BINDINGS = {
    "w": (0, 1.0),
    "s": (0, -1.0),
    "a": (1, 1.0),
    "d": (1, -1.0),
    "r": (2, 1.0),
    "f": (2, -1.0),
}


HELP = """
Keyboard EE control
  w/s: +X / -X
  a/d: +Y / -Y
  r/f: +Z / -Z
  q: quit
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Keyboard teleoperation for ME6 end-effector position.")
    parser.add_argument("--action-name", default="/me6_arm_controller/follow_joint_trajectory")
    parser.add_argument("--start", choices=("current", "ready", "home"), default="current")
    parser.add_argument("--step", type=float, default=0.015)
    parser.add_argument("--command-duration", type=float, default=0.25)
    parser.add_argument("--gain", type=float, default=2.5)
    parser.add_argument("--damping", type=float, default=0.04)
    parser.add_argument("--max-joint-step", type=float, default=0.045)
    return parser.parse_args()


def read_key(timeout=0.1):
    readable, _, _ = select.select([sys.stdin], [], [], timeout)
    if not readable:
        return None
    return sys.stdin.read(1)


def main():
    args = parse_args()
    rclpy.init()
    node = TrajectoryClient(args.action_name)
    kin = DobotME6Kinematics()
    q = get_start_q(node, args.start)
    target, _, _ = kin.forward(q)

    print(HELP)
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            key = read_key()
            rclpy.spin_once(node, timeout_sec=0.0)
            if key is None:
                continue
            if key == "q":
                break
            if key not in KEY_BINDINGS:
                continue
            axis, sign = KEY_BINDINGS[key]
            target[axis] += sign * args.step
            q, err = kin.step_ik(
                q,
                target,
                gain=args.gain,
                damping=args.damping,
                max_joint_step=args.max_joint_step,
            )
            node.get_logger().info(
                f"target=({target[0]:.3f}, {target[1]:.3f}, {target[2]:.3f}), estimated_error={err:.4f} m"
            )
            rc = node.send_positions([q], args.command_duration)
            if rc != 0:
                break
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        node.destroy_node()
        rclpy.shutdown()
