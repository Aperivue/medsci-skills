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
# A key is alnum + : . _ - / + (per pandoc docs) — but pandoc counts internal punctuation as part of
# the key ONLY when a letter or digit follows it. The old pattern dropped that condition, so a
# citation ending a sentence — which is most of them — swallowed the full stop:
#
#     "...as previously reported @Smith2023."   ->  key "Smith2023."
#
# and the tool then reported the SAME reference as UNDEFINED (no `Smith2023.` in the .bib) and as
# UNUSED (nothing cited `Smith2023`) in a single run. Trailing `;` `,` `]` already terminated the
# match; `.` `-` `/` `+` leaked, and `.` is the one that ends English sentences. `@Sec.2a` stays one
# key, because there the period is followed by an alphanumeric — pandoc's own rule, now encoded.
CITE_RE = re.compile(r"(?<![A-Za-z0-9_])-?@([A-Za-z][\w]*(?:[:.\-/+][\w]+)*)")
BIB_KEY_RE = re.compile(r"^@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)

# Quarto / pandoc-crossref cross-references share the `@` sigil but are not bibliography keys:
# `@fig-flow`, `@tbl-baseline`, `@sec-methods`, `@eq-lik`, and the older `@fig:flow` form. They
# resolve against the document's own labels, and `quarto render` compiles a manuscript full of them
# without complaint — while this checker read every one as an undefined reference and exited 1. The
# repo scaffolds `manuscript/index.qmd` itself (`scripts/init_project.py`), so the toolkit was
# failing manuscripts in the shape it generates.
#
# Excluded from the UNDEFINED verdict, never dropped silently: they are counted and reported. A key
# with one of these prefixes that IS defined in the .bib resolves normally and never reaches this
# exclusion, so a real bibliography entry named `fig-...` is unaffected.
CROSSREF_PREFIXES = (
    "fig", "tbl", "eq", "sec", "lst", "thm", "lem", "cor", "prp", "cnj",
    "def", "exm", "exr", "sol", "rem", "alg", "tip", "nte", "wrn", "imp", "cau",
)
CROSSREF_RE = re.compile(rf"^(?:{'|'.join(CROSSREF_PREFIXES)})[-:]\w", re.IGNORECASE)


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

    # Split the unresolved keys before judging them: a Quarto cross-reference resolves against the
    # document's own labels, not the bibliography, so calling it an undefined citation fails a
    # manuscript that `quarto render` compiles without complaint. Reported, never silently dropped.
    unresolved = sorted(cited - defined)
    crossrefs = [k for k in unresolved if CROSSREF_RE.match(k)]
    undefined = [k for k in unresolved if not CROSSREF_RE.match(k)]
    unused = sorted(defined - cited)

    print(f"[check_citation_keys] cited={len(cited)} defined={len(defined)}")
    if crossrefs:
        print(f"\nCROSS-REFERENCES ({len(crossrefs)}) — Quarto/pandoc-crossref labels, not "
              f"bibliography keys; resolved by the renderer, not checked here:")
        for k in crossrefs:
            print(f"  [@{k}]")
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
