import argparse
import math

from dobot_me6_examples.ee_control_common import add_common_args, positive_float, run_trajectory


def parse_args():
    parser = argparse.ArgumentParser(description="Track a circular end-effector position trajectory.")
    add_common_args(parser)
    parser.add_argument("--radius", type=positive_float, default=0.055)
    parser.add_argument("--plane", choices=("xy", "xz", "yz"), default="xy")
    parser.add_argument("--cycles", type=positive_float, default=1.0)
    return parser.parse_args()


def make_target(args):
    def factory(center):
        def target_at(t):
            phase = 2.0 * math.pi * args.cycles * t / args.duration
            p = center[:]
            c = args.radius * math.cos(phase)
            s = args.radius * math.sin(phase)
            if args.plane == "xy":
                p[0] += c
                p[1] += s
            elif args.plane == "xz":
                p[0] += c
                p[2] += s
            else:
                p[1] += c
                p[2] += s
            return p
        return target_at
    return factory


def main():
    args = parse_args()
    run_trajectory("ee_circle", args, make_target(args))
