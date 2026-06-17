import argparse

from dobot_me6_examples.ee_stroke_common import add_stroke_args, run_stroke_script


STROKES = [
    [(0.16, 0.12), (0.42, 0.12)],
    [(0.20, 0.18), (0.36, 0.18), (0.36, 0.42), (0.20, 0.42), (0.20, 0.18)],
    [(0.26, 0.24), (0.32, 0.36)],
    [(0.32, 0.24), (0.24, 0.36)],
    [(0.12, 0.50), (0.44, 0.50)],
    [(0.20, 0.58), (0.36, 0.58), (0.36, 0.78), (0.20, 0.78), (0.20, 0.58)],
    [(0.28, 0.58), (0.28, 0.78)],
    [(0.14, 0.86), (0.42, 0.86)],
    [(0.52, 0.14), (0.86, 0.14)],
    [(0.58, 0.24), (0.82, 0.24), (0.82, 0.46), (0.58, 0.46), (0.58, 0.24)],
    [(0.64, 0.34), (0.76, 0.34)],
    [(0.52, 0.54), (0.88, 0.54)],
    [(0.60, 0.62), (0.82, 0.80)],
    [(0.82, 0.62), (0.60, 0.80)],
    [(0.54, 0.88), (0.86, 0.88)],
]


def parse_args():
    parser = argparse.ArgumentParser(description="Track a stylized stroke path for the kanji 麺.")
    add_stroke_args(parser)
    return parser.parse_args()


def main():
    run_stroke_script("ee_kanji_men", parse_args(), STROKES)

