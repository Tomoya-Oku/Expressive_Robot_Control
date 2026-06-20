import argparse

from dobot_me6_examples.ee_kanji_biang import STROKES as BIANG_STROKES
from dobot_me6_examples.ee_kanji_men import STROKES as MEN_STROKES
from dobot_me6_examples.ee_stroke_common import add_stroke_args, compose_horizontal, run_stroke_script


STROKES = compose_horizontal([BIANG_STROKES, BIANG_STROKES, MEN_STROKES], gap=0.04)


def parse_args():
    parser = argparse.ArgumentParser(description="Track a stylized stroke path for the compound word biang biang men.")
    add_stroke_args(parser, default_width=0.180, default_height=0.120)
    return parser.parse_args()


def main():
    run_stroke_script("ee_kanji_biang_biang_men", parse_args(), STROKES)
