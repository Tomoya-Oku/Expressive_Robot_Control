import argparse
import math

from dobot_me6_examples.ee_control_common import add_common_args, positive_float, run_trajectory


def parse_args():
    parser = argparse.ArgumentParser(description="Track a reciprocating straight-line end-effector trajectory.")
    add_common_args(parser)
    parser.add_argument("--length", type=positive_float, default=0.120)
    parser.add_argument("--plane", choices=("xy", "xz", "yz"), default="xz")
    parser.add_argument("--axis", choices=("x", "y", "z"), default=None)
    parser.add_argument("--cycles", type=positive_float, default=1.0)
    return parser.parse_args()


def make_target(args):
    if args.axis is None:
        axis_name = {"xy": "x", "xz": "x", "yz": "y"}[args.plane]
    else:
        axis_name = args.axis
    axis_index = {"x": 0, "y": 1, "z": 2}[axis_name]

    def factory(center):
        def target_at(t):
            phase = 2.0 * math.pi * args.cycles * t / args.duration
            p = center[:]
            p[axis_index] += 0.5 * args.length * math.sin(phase)
            return p
        return target_at
    return factory


def main():
    args = parse_args()
    run_trajectory("ee_line", args, make_target(args))
