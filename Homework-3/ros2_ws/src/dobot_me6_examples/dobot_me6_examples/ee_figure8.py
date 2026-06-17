import argparse
import math

from dobot_me6_examples.ee_control_common import add_common_args, positive_float, run_trajectory


def parse_args():
    parser = argparse.ArgumentParser(description="Track a figure-eight end-effector position trajectory.")
    add_common_args(parser)
    parser.add_argument("--width", type=positive_float, default=0.080)
    parser.add_argument("--height", type=positive_float, default=0.040)
    parser.add_argument("--plane", choices=("xy", "xz", "yz"), default="xz")
    parser.add_argument("--cycles", type=positive_float, default=1.0)
    return parser.parse_args()


def make_target(args):
    def factory(center):
        def target_at(t):
            phase = 2.0 * math.pi * args.cycles * t / args.duration
            a = 0.5 * args.width * math.sin(phase)
            b = args.height * math.sin(phase) * math.cos(phase)
            p = center[:]
            if args.plane == "xy":
                p[0] += a
                p[1] += b
            elif args.plane == "xz":
                p[0] += a
                p[2] += b
            else:
                p[1] += a
                p[2] += b
            return p
        return target_at
    return factory


def main():
    args = parse_args()
    run_trajectory("ee_figure8", args, make_target(args))
