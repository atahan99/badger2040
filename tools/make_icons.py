#!/usr/bin/env python3
"""Generate the 52x52 1-bit launcher icons that BadgerOS expects.

Run:  python3 tools/make_icons.py
Writes examples/icon-<app>.png, matching the stock icons' format
(mode "1", white background, black artwork).
"""
import os
from PIL import Image, ImageDraw

SIZE = 52
OUT = os.path.join(os.path.dirname(__file__), os.pardir, "examples")

BLACK, WHITE = 0, 1


def canvas():
    im = Image.new("1", (SIZE, SIZE), WHITE)
    return im, ImageDraw.Draw(im)


def badge():
    im, d = canvas()
    d.rectangle((2, 6, 49, 45), outline=BLACK, width=2)
    d.ellipse((9, 14, 23, 28), outline=BLACK, width=2)          # head
    d.arc((5, 28, 27, 46), 180, 360, fill=BLACK, width=3)       # shoulders
    for i, y in enumerate((18, 26, 34)):                        # text lines
        d.rectangle((30, y, 45 - i * 4, y + 3), fill=BLACK)
    return im


def dino():
    im, d = canvas()
    d.rectangle((30, 8, 45, 22), fill=BLACK)     # head
    d.rectangle((41, 12, 43, 14), fill=WHITE)    # eye
    d.rectangle((26, 20, 40, 38), fill=BLACK)    # body
    d.rectangle((14, 22, 27, 28), fill=BLACK)    # tail
    d.rectangle((28, 38, 32, 47), fill=BLACK)    # back leg
    d.rectangle((35, 38, 39, 47), fill=BLACK)    # front leg
    d.rectangle((24, 26, 27, 32), fill=BLACK)    # arm
    return im


def life():
    im, d = canvas()
    cell, gap, n = 10, 2, 4
    glider = {(1, 0), (2, 1), (0, 2), (1, 2), (2, 2), (3, 3)}
    for gy in range(n):
        for gx in range(n):
            x = 3 + gx * (cell + gap)
            y = 3 + gy * (cell + gap)
            box = (x, y, x + cell, y + cell)
            if (gx, gy) in glider:
                d.rectangle(box, fill=BLACK)
            else:
                d.rectangle(box, outline=BLACK, width=1)
    return im


def snake():
    im, d = canvas()
    body = [(8, 42), (8, 20), (20, 20), (20, 34), (34, 34), (34, 12)]
    d.line(body, fill=BLACK, width=6, joint="curve")
    d.rectangle((30, 6, 38, 14), fill=BLACK)     # head
    d.ellipse((40, 36, 48, 44), fill=BLACK)      # food
    return im


def p2048():
    im, d = canvas()
    d.rectangle((2, 2, 49, 49), outline=BLACK, width=2)
    for gy in range(2):
        for gx in range(2):
            x, y = 6 + gx * 22, 6 + gy * 22
            box = (x, y, x + 18, y + 18)
            if (gx + gy) % 2:
                d.rectangle(box, fill=BLACK)
            else:
                d.rectangle(box, outline=BLACK, width=2)
    return im


def timer():
    im, d = canvas()
    d.ellipse((6, 12, 46, 48), outline=BLACK, width=3)   # tomato
    d.line((26, 30, 26, 20), fill=BLACK, width=3)        # hands
    d.line((26, 30, 36, 34), fill=BLACK, width=3)
    d.line((20, 10, 32, 10), fill=BLACK, width=3)        # leaf
    d.line((26, 6, 26, 13), fill=BLACK, width=3)
    return im


def batt():
    im, d = canvas()
    d.rectangle((6, 14, 42, 44), outline=BLACK, width=3)   # cell body
    d.rectangle((42, 24, 47, 34), fill=BLACK)              # terminal nub
    d.rectangle((11, 19, 30, 39), fill=BLACK)              # charge level
    return im


def cheats():
    im, d = canvas()
    d.rectangle((4, 8, 40, 47), outline=BLACK, width=2)    # back card
    d.rectangle((12, 4, 48, 43), fill=WHITE, outline=BLACK, width=2)
    for i, y in enumerate((12, 20, 28, 36)):               # lines of text
        d.rectangle((17, y, 43 - i * 5, y + 2), fill=BLACK)
    return im


def count():
    im, d = canvas()
    for i in range(4):                                     # four tally marks
        x = 8 + i * 8
        d.line((x, 10, x, 42), fill=BLACK, width=3)
    d.line((4, 42, 40, 10), fill=BLACK, width=3)           # the fifth, struck
    return im


def dice():
    im, d = canvas()
    d.rectangle((6, 6, 45, 45), outline=BLACK, width=3)
    for x, y in ((15, 15), (36, 15), (26, 26), (15, 36), (36, 36)):
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=BLACK)
    return im


ICONS = {
    "badge": badge,
    "dino": dino,
    "life": life,
    "snake": snake,
    "p2048": p2048,
    "timer": timer,
    "batt": batt,
    "cheats": cheats,
    "count": count,
    "dice": dice,
}

if __name__ == "__main__":
    for name, fn in ICONS.items():
        path = os.path.normpath(os.path.join(OUT, "icon-{}.png".format(name)))
        fn().save(path, optimize=True)
        print("{:>28}  {} bytes".format(path, os.path.getsize(path)))
