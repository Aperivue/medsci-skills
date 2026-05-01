#!/usr/bin/env python3
"""check_citation_keys.py — Validate pandoc-style [@bibkey] citations against a .bib file.

Reports:
  - keys cited in markdown but missing from .bib (UNDEFINED)
  - keys present in .bib but never cited (UNUSED)
  - exit code 1 if any UNDEFINED, 0 otherwise

Usage:
  check_citation_keys.py manuscript.md references.bib
"""
from __future__ import annotations

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
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    md = Path(sys.argv[1])
    bib = Path(sys.argv[2])
    if not md.exists():
        print(f"ERROR: markdown not found: {md}", file=sys.stderr)
        return 2
    if not bib.exists():
        print(f"ERROR: bib not found: {bib}", file=sys.stderr)
        return 2

    cited = extract_md_keys(md)
    defined = extract_bib_keys(bib)

    undefined = sorted(cited - defined)
    unused = sorted(defined - cited)

    print(f"[check_citation_keys] cited={len(cited)} defined={len(defined)}")
    if undefined:
        print(f"\nUNDEFINED ({len(undefined)}) — cited in markdown but not in .bib:")
        for k in undefined:
            print(f"  [@{k}]")
    if unused:
        print(f"\nUNUSED ({len(unused)}) — defined in .bib but never cited:")
        for k in unused:
            print(f"  {k}")
    if not undefined and not unused:
        print("OK: all cited keys defined and all defined keys used.")

    return 1 if undefined else 0


if __name__ == "__main__":
    sys.exit(main())
