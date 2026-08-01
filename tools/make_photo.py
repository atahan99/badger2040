#!/usr/bin/env python3
"""Turn any photo into a 104x128 1-bit image for the badge.

    python3 tools/make_photo.py ~/Desktop/me.jpg badges/photo.png

Crops to the badge's aspect ratio, then Floyd-Steinberg dithers. Tweak
--contrast if the result comes out muddy; portraits usually want 1.3-1.8.
"""
import argparse
from PIL import Image, ImageEnhance, ImageOps

WIDTH, HEIGHT = 104, 128

parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("dest", nargs="?", default="badges/photo.png")
parser.add_argument("--contrast", type=float, default=1.4)
parser.add_argument("--no-autocontrast", action="store_true")
args = parser.parse_args()

im = Image.open(args.source).convert("L")
im = ImageOps.fit(im, (WIDTH, HEIGHT), method=Image.LANCZOS)
if not args.no_autocontrast:
    im = ImageOps.autocontrast(im, cutoff=2)
im = ImageEnhance.Contrast(im).enhance(args.contrast)
im.convert("1", dither=Image.FLOYDSTEINBERG).save(args.dest, optimize=True)

print("wrote {} ({}x{})".format(args.dest, WIDTH, HEIGHT))
