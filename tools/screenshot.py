#!/usr/bin/env python3
"""Screenshot apps straight from the badge's framebuffer:  python3 tools/screenshot.py [app ...]

Each app runs once on the badge (via bounded.py), drawing into a buffer we own
instead of the e-ink. update() prints that buffer as hex rather than refreshing
the panel. State comes from the fixtures below and nothing is saved, so your
high scores and badge profiles are never read or written.

Writes docs/images/<app>.png and a grid of them, docs/images/apps.png.
Needs the badge awake (see README) and Pillow.
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image

from bounded import rewrite

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
OUT = os.path.join(ROOT, "docs", "images")
PORT = os.environ.get("PORT", "auto")
WIDTH, HEIGHT = 296, 128
SCALE = 2
PAPER, INK = (234, 232, 224), (28, 28, 30)   # e-ink, not pure white on black

# app: (saved state, button that "woke" it, source substitutions)
SHOTS = {
    "badge": ({"index": 0}, None, [('BADGE_DIR = "/badges"', 'BADGE_DIR = "/shots"')]),
    "p2048": ({"high": 3472, "score": 1288,
               "board": [2, 4, 8, 2, 0, 16, 64, 4, 0, 2, 128, 32, 0, 0, 4, 256]}, None, []),
    # A fresh game has nothing on screen yet: start mid-run instead
    "dino": ({"high": 42}, "BUTTON_UP", [("obstacles = [WIDTH + 40, WIDTH + 200]", "obstacles = [130, 250]"),
                                         ("    score = 0\n", "    score = 12\n")]),
    "snake": ({"high": 17}, "BUTTON_B", [
        ("snake = [(4, ROWS // 2), (3, ROWS // 2), (2, ROWS // 2)]",
         "snake = [(x, 6) for x in range(14, 4, -1)] + [(5, y) for y in range(7, 11)]"
         " + [(x, 10) for x in range(6, 12)]"),
        ("    score = 0\n", "    score = 9\n")]),
    "life": ({"grid": ""}, None, []),
    "timer": ({"work_minutes": 25, "pomodoros": 2, "step": 0, "left": 754}, None, []),
    # On USB the meter shows "On USB power"; pretend otherwise and read the real pack
    "batt": ({}, None, [("return machine.Pin(VBUS_DETECT, machine.Pin.IN).value() == 1", "return False")]),
    "count": ({"which": 0, "counts": [42, 7, 0]}, None, []),
    "dice": ({"die": 6}, "BUTTON_A", []),
    "cheats": ({"sheet": 0, "page": 0}, None, []),
}

PRELUDE = """
import badger2040, badger_os, binascii
_B = badger2040.Badger2040
# `resume` keeps the interpreter between runs, so patch from the originals once
if not hasattr(_B, "_orig_init"):
    _B._orig_init, _B._orig_pressed = _B.__init__, _B.pressed
_buf = bytearray({size})
_init = _B._orig_init
def _shot_init(self, *a, **k):
    _init(self, *a, **k)
    self.display.set_framebuffer(_buf)
badger2040.Badger2040.__init__ = _shot_init
badger2040.Badger2040.update = lambda self: print("SHOT", binascii.hexlify(_buf).decode())
_wake = {wake!r}
_pressed = _B._orig_pressed
def _shot_pressed(self, button):
    global _wake
    if _wake is not None and button == getattr(badger2040, _wake):
        _wake = None
        return True
    return _pressed(self, button)
badger2040.Badger2040.pressed = _shot_pressed
badger_os.state_load = lambda name, data: data.update({state!r})
badger_os.state_save = lambda *a: None
"""

# Fixture profiles for the badge shot: the .example data, never yours
BADGE_FILES = {
    "01.txt": "ACME CORP\nAda Lovelace\nRole\nSoftware Engineer\nTeam\nPlatform\n/badges/badge.jpg\n",
    "02.txt": "SOME CONF 2026\nAda Lovelace\nTalk\nAnalytical Engines\nFind me\n@handle\n\n",
}


def mpremote(*args, **kwargs):
    return subprocess.run(["mpremote", "connect", PORT, "resume", *args], capture_output=True,
                          text=True, stdin=subprocess.DEVNULL, **kwargs)


def decode(hexdata):
    """The panel's buffer is column-major: 16 bytes per column, MSB at the top, 0 = black."""
    buf = bytes.fromhex(hexdata)
    assert len(buf) == WIDTH * HEIGHT // 8, "unexpected buffer size {}".format(len(buf))
    im = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    px = im.load()
    for x in range(WIDTH):
        for y in range(HEIGHT):
            if not (buf[x * (HEIGHT // 8) + y // 8] >> (7 - y % 8)) & 1:
                px[x, y] = INK
    return im.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.NEAREST)


def shoot(app, work):
    state, wake, subs = SHOTS[app]
    with open(os.path.join(ROOT, "examples", app + ".py")) as f:
        source = f.read()
    for old, new in subs:
        assert old in source, "{}: substitution target not found: {}".format(app, old)
        source = source.replace(old, new)
    script = os.path.join(work, app + ".py")
    with open(script, "w") as f:
        f.write(PRELUDE.format(size=WIDTH * HEIGHT // 8, wake=wake, state=state) + rewrite(source))
    result = mpremote("run", script, timeout=120)
    frames = [line.split(" ", 1)[1].strip() for line in result.stdout.splitlines() if line.startswith("SHOT ")]
    if not frames:
        raise SystemExit("{}: no frame captured\n{}{}".format(app, result.stdout[-800:], result.stderr[-800:]))
    return decode(frames[-1])


# The README grid. batt is left out: it only reads true with the pack switched on.
GRID = ("badge", "p2048", "timer", "dino", "snake", "life", "dice", "count", "cheats")


def grid(images, cols=3, gap=16):
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * gap, rows * h + (rows + 1) * gap), (255, 255, 255))
    for i, im in enumerate(images):
        sheet.paste(im, (gap + (i % cols) * (w + gap), gap + (i // cols) * (h + gap)))
    return sheet


def main(apps):
    # Plain mpremote soft-resets into the raw REPL (main.py does not run), which
    # also clears patches left by an earlier run. Everything after uses resume.
    if subprocess.run(["mpremote", "connect", PORT, "exec", "pass"], capture_output=True,
                      stdin=subprocess.DEVNULL).returncode:
        raise SystemExit("Cannot reach the badge - replug it and re-run within a few seconds.")
    if "badge" in apps:
        mpremote("fs", "mkdir", ":/shots")
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in BADGE_FILES.items():
                path = os.path.join(tmp, name)
                with open(path, "w") as f:
                    f.write(text)
                mpremote("fs", "cp", path, ":/shots/" + name)
    try:
        with tempfile.TemporaryDirectory() as work:
            for app in apps:
                shoot(app, work).save(os.path.join(OUT, app + ".png"), optimize=True)
                print("ok    {}".format(app))
    finally:
        if "badge" in apps:
            mpremote("exec", "import os\nfor f in os.listdir('/shots'): os.remove('/shots/' + f)\nos.rmdir('/shots')")
    # Rebuilt from the files on disk, so re-shooting one app keeps the rest
    paths = [os.path.join(OUT, app + ".png") for app in GRID]
    if all(os.path.exists(p) for p in paths):
        grid([Image.open(p) for p in paths]).save(os.path.join(OUT, "apps.png"), optimize=True)
        print("wrote docs/images/apps.png")


if __name__ == "__main__":
    main(sys.argv[1:] or list(SHOTS))
