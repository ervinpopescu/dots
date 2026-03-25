#!/bin/python

import argparse
import json5
import os

parser = argparse.ArgumentParser(
    prog="sort_json.py",
    description="Sorts json file given as input",
    epilog="",
)
parser.add_argument("filename")
args = parser.parse_args()

with open(os.path.abspath(args.filename), "r") as file:
    data = json5.load(file)

with open(os.path.abspath(args.filename), "w") as file:
    json5.dump(
        data, file, indent=2, quote_keys=True, sort_keys=True, trailing_commas=False
    )
