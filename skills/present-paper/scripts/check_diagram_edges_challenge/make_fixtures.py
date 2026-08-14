#!/usr/bin/env python3
"""Four images: a clipped box, the same box with a margin, a partial touch, and a full bleed.

  clipped.png    a rectangle whose right side sits ON the canvas edge. This is the real defect: on
                 the slide it reads as a box with a side missing.
  margin.png     the same rectangle inset. Must be silent.
  corner.png     ink touching the top edge over a short run only — the version a person misses,
                 because one short cut does not look like anything until you know to look.
  bleed.png      a solid image, ink on all four borders by construction. A photograph behaves this
                 way and must not be reported, or this fires on every screenshot in a deck.

Drawn with Pillow directly rather than matplotlib: the fixture must be exact at the pixel that
matters, and matplotlib's own layout is the thing under test upstream.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

W = H = 240
INK = (20, 30, 60, 255)


def canvas():
    return Image.new("RGBA", (W, H), (255, 255, 255, 255))


def clipped(path: Path) -> None:
    im = canvas()
    d = ImageDraw.Draw(im)
    # x1 == W-1: the right stroke lands on the last column and is half-cut by the render.
    d.rectangle([40, 40, W - 1, H - 60], outline=INK, width=3)
    im.save(path)


def margin(path: Path) -> None:
    im = canvas()
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H - 60], outline=INK, width=3)
    im.save(path)


def corner(path: Path) -> None:
    im = canvas()
    d = ImageDraw.Draw(im)
    d.rectangle([60, 60, W - 60, H - 60], outline=INK, width=3)
    d.line([100, 0, 140, 0], fill=INK, width=2)   # a short run along the top only
    im.save(path)


def bleed(path: Path) -> None:
    Image.new("RGBA", (W, H), (30, 40, 70, 255)).save(path)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out.mkdir(parents=True, exist_ok=True)
    clipped(out / "clipped.png")
    margin(out / "margin.png")
    corner(out / "corner.png")
    bleed(out / "bleed.png")
    print(f"wrote 4 images into {out}")
