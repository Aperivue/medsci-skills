#!/usr/bin/env python3
"""check_citation_keys.py — Validate pandoc-style [@bibkey] citations against a .bib file.

Reports:
  - keys cited in markdown but missing from .bib (UNDEFINED) — always fail
  - keys present in .bib but never cited (UNUSED) — warn by default,
    suppress with --allow-unused, or escalate with --strict-unused

Usage:
  check_citation_keys.py manuscript.md references.bib
  check_citation_keys.py manuscript.md references.bib --allow-unused
  check_citation_keys.py manuscript.md references.bib --strict-unused

Why --allow-unused exists:
  During early drafting, the .bib often holds a working set of candidate
  references that have not yet been cited in the manuscript. UNUSED output
  is noise in that phase and makes the diagnostic harder to read. Pass
  --allow-unused to suppress UNUSED reporting entirely; UNDEFINED remains a
  hard failure.

Why --strict-unused exists:
  At submission-package freeze time, UNUSED entries usually represent
  forgotten edits (a citation was removed from the manuscript but the .bib
  entry remains). Pass --strict-unused to treat any UNUSED entry as a
  build failure so the freeze gate catches it.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# pandoc citation syntax: [@key], [@key, p. 3], [@key1; @key2], [-@key] (suppress author)
# A key is alnum + : . _ - / +  (per pandoc docs)
CITE_RE = re.compile(r"(?<![A-Za-z0-9_])-?@([A-Za-z][\w:.\-/+]*)")
BIB_KEY_RE = re.compile(r"^@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)


def extract_md_keys(md_path: Path) -> set[str]:
    text = md_path.read_text(encoding="utf-8")
    # strip code fences to avoid false positives
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]+`", "", text)
    return set(CITE_RE.findall(text))


def extract_bib_keys(bib_path: Path) -> set[str]:
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    return set(BIB_KEY_RE.findall(text))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("markdown", type=Path, help="Path to manuscript.md")
    parser.add_argument("bib", type=Path, help="Path to references.bib")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--allow-unused",
        action="store_true",
        help="Suppress UNUSED reporting entirely (drafting mode).",
    )
    group.add_argument(
        "--strict-unused",
        action="store_true",
        help="Treat any UNUSED entry as a build failure (submission gate).",
    )
    args = parser.parse_args()

    if not args.markdown.exists():
        print(f"ERROR: markdown not found: {args.markdown}", file=sys.stderr)
        return 2
    if not args.bib.exists():
        print(f"ERROR: bib not found: {args.bib}", file=sys.stderr)
        return 2

    cited = extract_md_keys(args.markdown)
    defined = extract_bib_keys(args.bib)

    undefined = sorted(cited - defined)
    unused = sorted(defined - cited)

    print(f"[check_citation_keys] cited={len(cited)} defined={len(defined)}")
    if undefined:
        print(f"\nUNDEFINED ({len(undefined)}) — cited in markdown but not in .bib:")
        for k in undefined:
            print(f"  [@{k}]")
    show_unused = unused and not args.allow_unused
    if show_unused:
        label = "UNUSED" if not args.strict_unused else "UNUSED (--strict-unused: treated as failure)"
        print(f"\n{label} ({len(unused)}) — defined in .bib but never cited:")
        for k in unused:
            print(f"  {k}")
    if not undefined and not show_unused:
        if args.allow_unused and unused:
            print(f"OK: all cited keys defined ({len(unused)} UNUSED suppressed by --allow-unused).")
        else:
            print("OK: all cited keys defined and all defined keys used.")

    exit_code = 0
    if undefined:
        exit_code = 1
    elif unused and args.strict_unused:
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
