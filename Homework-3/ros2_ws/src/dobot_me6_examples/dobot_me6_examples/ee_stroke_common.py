import argparse
import math
from typing import Sequence, Tuple

from dobot_me6_examples.ee_control_common import add_common_args, positive_float, run_trajectory


Stroke = Sequence[Tuple[float, float]]


def add_stroke_args(parser: argparse.ArgumentParser, default_width=0.090, default_height=0.110):
    add_common_args(parser)
    parser.add_argument("--width", type=positive_float, default=default_width)
    parser.add_argument("--height", type=positive_float, default=default_height)
    parser.add_argument("--plane", choices=("xy", "xz", "yz"), default="xz")
    parser.add_argument("--cycles", type=positive_float, default=1.0)


def make_stroke_target(args, strokes: Sequence[Stroke]):
    points_2d = sample_strokes(strokes, 0.01)

    def factory(center):
        points_3d = [map_point(center, p, args.width, args.height, args.plane) for p in points_2d]

        def target_at(t):
            phase = (args.cycles * t / args.duration) % 1.0
            return sample_polyline(points_3d, phase)

        return target_at

    return factory


def run_stroke_script(name: str, args, strokes: Sequence[Stroke]):
    run_trajectory(name, args, make_stroke_target(args, strokes))


def sample_strokes(strokes: Sequence[Stroke], spacing: float):
    sampled = []
    for stroke in strokes:
        if not stroke:
            continue
        if sampled:
            sampled.extend(interpolate_segment(sampled[-1], stroke[0], spacing))
        else:
            sampled.append(stroke[0])
        for start, end in zip(stroke, stroke[1:]):
            sampled.extend(interpolate_segment(start, end, spacing))
    return sampled


def interpolate_segment(start, end, spacing):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dist = math.hypot(dx, dy)
    steps = max(1, int(dist / max(spacing, 1e-6)))
    return [(start[0] + dx * i / steps, start[1] + dy * i / steps) for i in range(1, steps + 1)]


def map_point(center, point, width, height, plane):
    u = (point[0] - 0.5) * width
    v = (0.5 - point[1]) * height
    mapped = list(center)
    first_axis, second_axis = {"xy": (0, 1), "xz": (0, 2), "yz": (1, 2)}[plane]
    mapped[first_axis] += u
    mapped[second_axis] += v
    return mapped


def sample_polyline(points: Sequence[Sequence[float]], phase: float):
    if not points:
        return [0.0, 0.0, 0.0]
    if len(points) == 1:
        return list(points[0])
    scaled = phase * (len(points) - 1)
    index = min(int(scaled), len(points) - 2)
    ratio = scaled - index
    return [
        points[index][axis] + (points[index + 1][axis] - points[index][axis]) * ratio
        for axis in range(3)
    ]
