import argparse
import select
import sys
import termios
import time
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
    parser.add_argument("--trajectory-topic", default="/me6_arm_controller/joint_trajectory")
    parser.add_argument("--start", choices=("current", "ready", "home"), default="current")
    parser.add_argument("--step", type=float, default=0.006)
    parser.add_argument("--command-duration", type=float, default=0.08)
    parser.add_argument("--rate", type=float, default=20.0)
    parser.add_argument("--gain", type=float, default=2.5)
    parser.add_argument("--damping", type=float, default=0.04)
    parser.add_argument("--max-joint-step", type=float, default=0.045)
    return parser.parse_args()


def read_keys(timeout=0.05):
    readable, _, _ = select.select([sys.stdin], [], [], timeout)
    if not readable:
        return []
    keys = [sys.stdin.read(1)]
    while select.select([sys.stdin], [], [], 0.0)[0]:
        keys.append(sys.stdin.read(1))
    return keys


def movement_from_keys(keys):
    movement = [0.0, 0.0, 0.0]
    for key in keys:
        if key not in KEY_BINDINGS:
            continue
        axis, sign = KEY_BINDINGS[key]
        movement[axis] = sign
    return movement


def main():
    args = parse_args()
    rclpy.init()
    node = TrajectoryClient(args.action_name, args.trajectory_topic)
    kin = DobotME6Kinematics()
    q = get_start_q(node, args.start)
    target, _, _ = kin.forward(q)
    period = 1.0 / args.rate

    print(HELP)
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            cycle_start = time.monotonic()
            keys = read_keys(timeout=period)
            rclpy.spin_once(node, timeout_sec=0.0)
            if "q" in keys:
                break
            movement = movement_from_keys(keys)
            if movement == [0.0, 0.0, 0.0]:
                continue
            for axis, sign in enumerate(movement):
                target[axis] += sign * args.step
            q, _ = kin.step_ik(
                q,
                target,
                gain=args.gain,
                damping=args.damping,
                max_joint_step=args.max_joint_step,
            )
            rc = node.publish_positions([q], args.command_duration)
            if rc != 0:
                break
            elapsed = time.monotonic() - cycle_start
            if elapsed < period:
                time.sleep(period - elapsed)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        node.destroy_node()
        rclpy.shutdown()
