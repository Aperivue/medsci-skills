#!/usr/bin/env python3
"""
infer_colwidths.py — Replace pandoc pipe-table separator rows with dash-ratios
proportional to per-column content width.

Pandoc pipe tables interpret the dash count in the separator row as relative
column widths (when the total exceeds the line width). This script replaces:

    | Label | Long data column            | Other |
    |-------|-----------------------------|-------|

with widths derived from the maximum display-width of header + cells per column.
CJK glyphs count as 2 cells (East-Asian wide), ASCII as 1.

Usage:
    python infer_colwidths.py input.md [--out output.md] [--min 5] [--total 80]

If --out is omitted, writes to stdout.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


def display_width(s: str) -> int:
    """East-Asian-aware char width. Wide/Fullwidth = 2, else = 1."""
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


SEPARATOR_RE = re.compile(r"^\s*\|?[\s:\-|]+\|[\s:\-|]+\s*$")
PIPE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_separator(line: str) -> bool:
    if not SEPARATOR_RE.match(line):
        return False
    cells = split_row(line)
    if len(cells) < 2:
        return False
    for c in cells:
        if not re.match(r"^:?-{3,}:?$", c.strip()):
            return False
    return True


def parse_alignment(sep_cell: str) -> str:
    s = sep_cell.strip()
    left = s.startswith(":")
    right = s.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left"
    return "default"


def make_separator(widths: list[int], aligns: list[str]) -> str:
    parts = []
    for w, a in zip(widths, aligns):
        body = "-" * max(3, w)
        if a == "center":
            cell = ":" + body[1:-1] + ":" if len(body) >= 3 else ":-:"
        elif a == "left":
            cell = ":" + body[1:] if len(body) >= 2 else ":--"
        elif a == "right":
            cell = body[:-1] + ":" if len(body) >= 2 else "--:"
        else:
            cell = body
        parts.append(cell)
    return "| " + " | ".join(parts) + " |"


def find_table_blocks(lines: list[str]) -> list[tuple[int, int, int]]:
    """Return list of (header_idx, sep_idx, end_idx_exclusive) for pipe tables."""
    blocks = []
    i = 0
    while i < len(lines) - 1:
        if PIPE_ROW_RE.match(lines[i]) and is_separator(lines[i + 1]):
            header = i
            sep = i + 1
            j = sep + 1
            while j < len(lines) and PIPE_ROW_RE.match(lines[j]):
                j += 1
            blocks.append((header, sep, j))
            i = j
        else:
            i += 1
    return blocks


def infer_widths_for_block(
    lines: list[str], header: int, sep: int, end: int, min_dashes: int
) -> tuple[list[int], list[str]]:
    header_cells = split_row(lines[header])
    sep_cells = split_row(lines[sep])
    n = len(header_cells)

    aligns = [parse_alignment(c) for c in sep_cells]
    if len(aligns) < n:
        aligns += ["default"] * (n - len(aligns))
    aligns = aligns[:n]

    widths = [display_width(h) for h in header_cells]
    for r in range(sep + 1, end):
        cells = split_row(lines[r])
        for k in range(min(n, len(cells))):
            widths[k] = max(widths[k], display_width(cells[k]))

    widths = [max(min_dashes, w) for w in widths]
    return widths, aligns


def process(text: str, min_dashes: int, scale: float) -> str:
    lines = text.splitlines()
    blocks = find_table_blocks(lines)
    for header, sep, end in blocks:
        widths, aligns = infer_widths_for_block(lines, header, sep, end, min_dashes)
        if scale != 1.0:
            widths = [max(min_dashes, int(round(w * scale))) for w in widths]
        lines[sep] = make_separator(widths, aligns)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="Input markdown file")
    ap.add_argument("--out", type=Path, default=None, help="Output path (default: stdout)")
    ap.add_argument("--min", type=int, default=5, help="Minimum dashes per column (default: 5)")
    ap.add_argument("--scale", type=float, default=1.0, help="Multiply all widths (default: 1.0)")
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8")
    out = process(text, min_dashes=args.min, scale=args.scale)
    if args.out:
        args.out.write_text(out, encoding="utf-8")
        print(f"[infer_colwidths] {args.input} → {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
