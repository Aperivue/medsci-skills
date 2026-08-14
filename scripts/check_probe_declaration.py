#!/usr/bin/env python3
"""A domain-probe module must declare the probes it actually contains.

Four modules were found under-declaring themselves: `ai_overclaiming` carried AO0-AO7 and
its title said AO0-AO6; `sr_ma` carried P0-P19, its title said P0-P17, and its body still
called itself "an 11-probe checklist (P1-P11)". Six probes sat below a title that told a
reviewer they were not there.

That is the same defect the vendored-checklist audit spent a week removing from other
people's instruments -- a file whose declaration does not match its contents -- and it is
worse here, because the title is the scope a reviewer takes on trust when they load the
module. SKILL.md happened to hold the correct range; the module a reviewer actually reads
held the stale one.

This gate compares three things per module and requires them to agree:

  1. the range declared in the H1 title, e.g. `# ... probes (AO0-AO7)`
  2. the probe IDs actually defined in the body (a bolded ID at the start of a line)
  3. the count declared in any "N-probe checklist" phrase, if the body has one

It also reports a gap in the numbering. A gap is not automatically wrong -- a retired probe
may be deliberately skipped -- but it must be visible, because silently closing one
renumbers every probe after it, and reviewers cite probes by number.

Notation: the title may use an en dash or a hyphen, and may repeat the prefix on the right
(`AO0-AO7`) or not (`AO0-7`). Accepting only one spelling is this repository's most common
detector defect, so all four forms parse.

Stdlib only. Usage:
    python3 scripts/check_probe_declaration.py [--strict] [--dir DIR]

Exit 0 when every module agrees with itself (with --strict, 1 on any violation; 2 on a
read error or an empty scan).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "skills" / "peer-review" / "references" / "domain-probes"

# `# Survival / Prognostic Model probes (S1-S9)` -- en dash or hyphen, prefix optional on
# the right-hand side.
TITLE_RE = re.compile(
    r"^#\s+.*\((?P<pref>[A-Z]{1,3})(?P<lo>\d{1,2})\s*[–—-]\s*(?P=pref)?(?P<hi>\d{1,2})\)\s*$",
    re.M,
)
# A probe is DEFINED where its bolded ID opens a line; elsewhere it is only referenced, and
# a reference must not be able to fill a gap.
DEF_RE = re.compile(r"^\**\s*\*\*([A-Z]{1,3})(\d{1,2})\b", re.M)
# "A 7-probe checklist", "plus an 11-probe checklist"
COUNT_RE = re.compile(r"\b(?:an?|plus an?)\s+(\d{1,2})-probe checklist\b", re.I)
# Several modules number a gate probe zero and exclude it from the count -- "a 7-probe
# checklist (AO1-AO7, with AO0 as a gate)", "gate (P0) plus a 19-probe checklist". That is
# the repository's own convention, so the count check has to know it; a checker that only
# accepts its own preferred spelling is this repository's most common detector defect, and
# the first draft of THIS gate reported both of those modules as wrong.
GATE_PROBE_RE = re.compile(r"\b(?:with\s+)?[A-Z]{1,3}0\b[^.\n]{0,40}\bas a gate\b|\bgate\s*\([A-Z]{1,3}0\)", re.I)


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    title = TITLE_RE.search(text)
    if not title:
        # Not every reference file is a probe module; only complain when one clearly is.
        if DEF_RE.search(text):
            problems.append("has probe definitions but no `# ... (X1-X9)` range in its H1 title")
        return problems

    pref, lo, hi = title["pref"], int(title["lo"]), int(title["hi"])
    nums = sorted({int(n) for p, n in DEF_RE.findall(text) if p == pref})
    if not nums:
        problems.append(f"title declares {pref}{lo}-{pref}{hi} but no {pref}n probe is defined")
        return problems

    if nums[0] != lo or nums[-1] != hi:
        problems.append(
            f"title declares {pref}{lo}-{pref}{hi}, body defines {pref}{nums[0]}-{pref}{nums[-1]}"
            f" -- {len([n for n in nums if not lo <= n <= hi])} probe(s) outside the declared range"
        )

    gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]
    if gaps:
        problems.append(
            f"numbering gap: {', '.join(f'{pref}{g}' for g in gaps)} not defined. "
            "Keep the gap and say why, or the numbers after it shift and citations break"
        )

    declared = COUNT_RE.search(text)
    if declared:
        n = int(declared[1])
        has_gate = bool(GATE_PROBE_RE.search(text)) and nums[0] == 0
        allowed = {len(nums)} | ({len(nums) - 1} if has_gate else set())
        if n not in allowed:
            expected = f"{len(nums)}" + (f" (or {len(nums) - 1} excluding the gate probe)" if has_gate else "")
            problems.append(
                f'body says "{n}-probe checklist" but {len(nums)} probes are defined -- expected {expected}'
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any violation")
    args = ap.parse_args()

    if not args.dir.is_dir():
        print(f"error: not a directory: {args.dir}", file=sys.stderr)
        return 2

    files = sorted(args.dir.glob("*.md"))
    if not files:
        # An empty scan passes every assertion while checking nothing.
        print(f"error: no .md modules found in {args.dir}", file=sys.stderr)
        return 2

    print("=" * 41)
    print(" Probe Declaration (title vs contents)")
    print("=" * 41)
    try:
        shown = args.dir.relative_to(ROOT)
    except ValueError:
        # --dir may point outside the repo (the challenge card builds fixtures in a tmpdir).
        shown = args.dir
    print(f"  scanned: {len(files)} module(s) in {shown}")

    violations = 0
    for f in files:
        try:
            problems = check(f)
        except OSError as exc:
            print(f"error: cannot read {f}: {exc}", file=sys.stderr)
            return 2
        for p in problems:
            violations += 1
            print(f"  {f.name}: {p}")

    print()
    if violations:
        print(f"PROBE_DECLARATION_DRIFT: {violations} violation(s).")
        print("A module's title is the scope a reviewer takes on trust. Fix the title, the")
        print("body count, or the missing probe -- whichever is actually wrong.")
        return 1 if args.strict else 0

    print(f"OK: all {len(files)} module(s) declare the probes they contain.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
