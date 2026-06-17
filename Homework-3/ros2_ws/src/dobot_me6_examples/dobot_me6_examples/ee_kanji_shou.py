import argparse

from dobot_me6_examples.ee_stroke_common import add_stroke_args, run_stroke_script


STROKES = [
    [(0.18, 0.14), (0.42, 0.14)],
    [(0.58, 0.14), (0.82, 0.14)],
    [(0.23, 0.09), (0.23, 0.24)],
    [(0.77, 0.09), (0.77, 0.24)],
    [(0.14, 0.28), (0.86, 0.28)],
    [(0.20, 0.34), (0.80, 0.34)],
    [(0.24, 0.34), (0.24, 0.51), (0.76, 0.51), (0.76, 0.34)],
    [(0.32, 0.40), (0.68, 0.40)],
    [(0.20, 0.57), (0.80, 0.57)],
    [(0.27, 0.63), (0.73, 0.63), (0.73, 0.82), (0.27, 0.82), (0.27, 0.63)],
    [(0.36, 0.70), (0.64, 0.70)],
    [(0.50, 0.58), (0.50, 0.82)],
    [(0.20, 0.88), (0.80, 0.88)],
]


def parse_args():
    parser = argparse.ArgumentParser(description="Track a stylized stroke path for the kanji 薔.")
    add_stroke_args(parser)
    return parser.parse_args()


def main():
    run_stroke_script("ee_kanji_shou", parse_args(), STROKES)

