#!/bin/python3

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
    data = json.loads(read_file.read())

with open(os.path.abspath(args.filename), "w") as write_file:
    write_file.write(json.dumps(data, indent=2, sort_keys=True))
