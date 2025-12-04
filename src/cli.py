from __future__ import annotations

import argparse


LANG_CHOICES = ["kotlin", "openapi"]


def parse_cli_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("--output", default="output.csv", help="Output CSV path")
    parser.add_argument("--lang", choices=LANG_CHOICES, help="Language override")
    parser.add_argument("--config", default=".env", help="Path to configuration file")

    return parser.parse_args(argv)
