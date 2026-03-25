#!/bin/python

import json
import sys

from markdownTable import markdownTable


def main():
    l = json.load(sys.stdin)
    table = (
        markdownTable(l)
        .setParams(
            row_sep="markdown",
            quote=False,
            padding_weight="center",
            # multiline=True,
        )
        .getMarkdown()
    )
    print(table)


if __name__ == "__main__":
    main()
