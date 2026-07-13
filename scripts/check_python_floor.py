#!/usr/bin/env python3
"""Everything a user runs must parse on the oldest Python we promise them.

The README says **Python 3.9+**. CI runs 3.11. This machine runs 3.14. Nothing checks 3.9 — so a
`match` statement, or a `X | Y` outside an annotation, would sail through every gate we have and
break only on the computer of a clinician who never tells us, because when a research tool errors
out a physician does not file a bug: they close the window and go back to doing it by hand.

That gap is not hypothetical. On 2026-07-13 a backslash inside an f-string (legal on 3.12+, a
syntax error before it) shipped from a 3.14 machine and was caught only because CI happened to run
3.11. One version lower and it would have been invisible.

This parses every script that reaches a user — the installers and the skill scripts the agent runs
on their machine — under the promised floor, and fails if any of them would not even load. It does
not check the repository's own maintainer tooling (`scripts/`), which never leaves this repo and
may use whatever CI runs.

Usage:
    check_python_floor.py [--floor 3.9] [--strict]

Stdlib only.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# What actually reaches a user's machine: the classroom ZIP payload (installers/ + skills/) and the
# npm package. `scripts/` is maintainer tooling and is deliberately not shipped.
SHIPPED = [
    ("installers", "*.py"),
    ("skills", "*/scripts/*.py"),
]

SKIP_PARTS = {"__pycache__", "tests", ".pytest_cache"}


def shipped_files() -> list[Path]:
    out: list[Path] = []
    for base, pattern in SHIPPED:
        for p in sorted((ROOT / base).glob(pattern)):
            if p.is_file() and not SKIP_PARTS.intersection(p.parts):
                out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--floor", default="3.9", help="the oldest Python we promise (default: the README's 3.9)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any violation (CI gate)")
    a = ap.parse_args()

    try:
        major, minor = (int(x) for x in a.floor.split("."))
    except ValueError:
        raise SystemExit(f"--floor must look like 3.9, not {a.floor!r}")

    files = shipped_files()
    if not files:
        raise SystemExit("found no shipped python files — the globs are wrong, and this gate is a no-op")

    bad: list[tuple[Path, int, str]] = []
    for p in files:
        try:
            ast.parse(p.read_text(encoding="utf-8"), feature_version=(major, minor))
        except SyntaxError as exc:
            bad.append((p, exc.lineno or 0, exc.msg))

    if bad:
        print(f"PYTHON_FLOOR: {len(bad)} shipped file(s) do not parse on Python {a.floor}\n")
        for p, line, msg in bad:
            print(f"  {p.relative_to(ROOT)}:{line}")
            print(f"      {msg}")
        print(
            f"\nThe README promises Python {a.floor}+. A file that will not parse there does not fail "
            "politely on\na clinician's computer — it fails with a traceback, and they close the window."
        )
        return 1 if a.strict else 0

    print(f"OK: all {len(files)} shipped script(s) parse on Python {a.floor} (the floor we promise).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
