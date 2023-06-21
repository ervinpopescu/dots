#!/bin/python

import argparse
import json
import os

parser = argparse.ArgumentParser(
    prog="sort_json.py",
    description="Sorts json file given as input",
    epilog="",
)
parser.add_argument("filename")
args = parser.parse_args()

with open(os.path.abspath(args.filename), "r") as read_file:
    data = json.load(read_file)

with open(os.path.abspath(args.filename), "w") as write_file:
    json.dump(data, write_file, indent=2, sort_keys=True)
