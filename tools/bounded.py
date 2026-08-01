#!/usr/bin/env python3
"""Rewrite an app so it renders once and exits, instead of looping forever.

Apps end their main loop on halt(), so running one as-is over USB never
returns. tools/run_on_device.sh uses this to check that each app initialises
and renders without raising, then exits on its own.

    python3 tools/bounded.py examples/snake.py /tmp/snake.py
"""
import re
import sys

MARKER = "APP_OK"


def rewrite(source, tail="\nprint('{}')\n".format(MARKER)):
    """Return `source` with its main loop reduced to a single pass.

    The `while True:` is anchored to column 0 on purpose: badge.py scales its
    name with an inner `while True:`, and the games have their own, all of
    which must keep looping.
    """
    source, count = re.subn(r"^while True:", "for _once in range(1):",
                            source, count=1, flags=re.M)
    if count != 1:
        raise SystemExit("no top-level `while True:` main loop found")
    source = re.sub(r"\bdisplay\.halt\(\)", "pass", source)
    return source + tail


if __name__ == "__main__":
    src, dest = sys.argv[1], sys.argv[2]
    with open(src) as f:
        out = rewrite(f.read())
    with open(dest, "w") as f:
        f.write(out)
