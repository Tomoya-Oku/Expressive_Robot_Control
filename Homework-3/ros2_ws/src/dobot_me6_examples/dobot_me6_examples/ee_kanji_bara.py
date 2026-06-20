import argparse

from dobot_me6_examples.ee_kanji_bi import STROKES as BI_STROKES
from dobot_me6_examples.ee_kanji_shou import STROKES as SHOU_STROKES
from dobot_me6_examples.ee_stroke_common import add_stroke_args, compose_horizontal, run_stroke_script


STROKES = compose_horizontal([SHOU_STROKES, BI_STROKES], gap=0.06)


def parse_args():
    parser = argparse.ArgumentParser(description="Track a stylized stroke path for the compound word bara.")
    add_stroke_args(parser, default_width=0.160, default_height=0.110)
    return parser.parse_args()


def main():
    run_stroke_script("ee_kanji_bara", parse_args(), STROKES)
