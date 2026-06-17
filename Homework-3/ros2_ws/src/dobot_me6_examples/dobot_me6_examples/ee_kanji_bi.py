import argparse

from dobot_me6_examples.ee_stroke_common import add_stroke_args, run_stroke_script


STROKES = [
    [(0.16, 0.13), (0.42, 0.13)],
    [(0.58, 0.13), (0.84, 0.13)],
    [(0.23, 0.08), (0.23, 0.23)],
    [(0.77, 0.08), (0.77, 0.23)],
    [(0.15, 0.28), (0.84, 0.28)],
    [(0.18, 0.39), (0.36, 0.32), (0.30, 0.55)],
    [(0.18, 0.52), (0.34, 0.46)],
    [(0.46, 0.33), (0.80, 0.33)],
    [(0.52, 0.40), (0.76, 0.40)],
    [(0.50, 0.49), (0.82, 0.49)],
    [(0.54, 0.34), (0.54, 0.57)],
    [(0.73, 0.34), (0.73, 0.57)],
    [(0.46, 0.62), (0.82, 0.62)],
    [(0.50, 0.68), (0.78, 0.86)],
    [(0.78, 0.68), (0.50, 0.86)],
    [(0.18, 0.72), (0.34, 0.62), (0.30, 0.90)],
    [(0.15, 0.86), (0.36, 0.80)],
]


def parse_args():
    parser = argparse.ArgumentParser(description="Track a stylized stroke path for the kanji 薇.")
    add_stroke_args(parser)
    return parser.parse_args()


def main():
    run_stroke_script("ee_kanji_bi", parse_args(), STROKES)

