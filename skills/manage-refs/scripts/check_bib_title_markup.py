#!/usr/bin/env python3
"""Publisher markup in a .bib title corrupts the rendered bibliography.

CrossRef ships titles with markup — `<scp>WHO</scp>`, `<i>IDH</i>`, `<sub>1</sub>` —
and a DOI-add stores them verbatim. Downstream, Better BibTeX either escapes the tags
(`{$<$}scp{$>$}`) or strips them without restoring the space they were standing in, and
the reference list renders as garbage:

    The 2021 {$<$}scp{$>$}WHO{$<$}/scp{$>$} Classification of Tumors...
    Glioma Groups Based on 1p/19q,IDH, andTERTPromoter Mutations

Nothing catches this. `/verify-refs` checks whether the reference is *true* (DOI, authors);
`check_citation_keys` checks whether the key *resolves*. Neither looks at the title as it
will be printed, so the corruption is found — if it is found at all — by eyeballing the
rendered document, which is exactly the reading nobody does on the reference list.

Verdicts:
  TITLE_MARKUP (major)  raw or escaped publisher markup survives in the title
  TITLE_FUSION (major)  a tag was stripped without restoring its space, welding two words
                        together (`andTERT`, `,IDH`)

The fusion check is deliberately narrow: it fires on an English function word or a comma
welded to an acronym, not on any lowercase-then-uppercase transition — `mRNA`, `hTERT`,
`nnU-Net`, `pH`, `1,2-dichloroethane` are ordinary and must not be flagged. The point of a
gate is that a clean run means something.

Usage:
    check_bib_title_markup.py --bib refs.bib [--out qc/bib_title_markup.json] [--strict]

Exit 0 when every title is clean (or, without --strict, always). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Raw HTML/XML tags and their BibTeX-escaped forms. `{$<$}` is what BBT writes when it
# escapes a `<` it does not understand.
MARKUP = re.compile(
    r"</?(?:i|b|em|strong|scp|sub|sup|span|p|br)\b[^>]*>"   # raw tags
    r"|\{\$<\$\}|\{\$>\$\}"                                  # BBT-escaped angle brackets
    r"|&lt;|&gt;|&amp;(?![a-z]+;)",                          # HTML entities
    re.IGNORECASE,
)

# A tag stripped without restoring its space welds an English function word — or a comma —
# directly onto the acronym the tag was wrapping. `and<i>TERT</i>` -> `andTERT`.
FUNCTION_WORDS = (
    "and|or|the|in|of|with|for|by|on|at|from|to|as|an|a|is|are|was|were|via|per|"
    "between|among|versus|vs"
)
FUSION_WORD = re.compile(rf"\b({FUNCTION_WORDS})([A-Z]{{2,}})", re.UNICODE)
# A comma glued straight onto a letter. Legitimate titles always put a space after a comma;
# a numeric comma (`1,2-dichloroethane`, `10,000`) is not matched because a digit follows.
FUSION_COMMA = re.compile(r",(?=[A-Za-z])")

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.DOTALL)
TITLE = re.compile(r"^\s*(?:title|booktitle)\s*=\s*[{\"](.+?)[}\"]\s*,?\s*$", re.MULTILINE | re.IGNORECASE)


def findings_for(key: str, title: str) -> list[dict]:
    out: list[dict] = []
    for m in MARKUP.finditer(title):
        out.append(
            {
                "verdict": "TITLE_MARKUP",
                "severity": "major",
                "key": key,
                "match": m.group(0),
                "title": title,
                "detail": (
                    f"publisher markup {m.group(0)!r} survives in the title of `{key}`; it will "
                    "render literally (or be stripped, welding the neighbouring words). Unwrap the "
                    "tag in the reference manager — do not hand-edit the rendered bibliography."
                ),
            }
        )
    for m in FUSION_WORD.finditer(title):
        out.append(
            {
                "verdict": "TITLE_FUSION",
                "severity": "major",
                "key": key,
                "match": m.group(0),
                "title": title,
                "detail": (
                    f"`{m.group(0)}` in the title of `{key}`: a markup tag was stripped without "
                    "restoring the space it occupied, welding a word onto an acronym. Restore the "
                    "space at the source (the reference manager), not in the rendered output."
                ),
            }
        )
    if FUSION_COMMA.search(title):
        m = FUSION_COMMA.search(title)
        ctx = title[max(0, m.start() - 12) : m.start() + 12]
        out.append(
            {
                "verdict": "TITLE_FUSION",
                "severity": "major",
                "key": key,
                "match": ctx,
                "title": title,
                "detail": (
                    f"comma glued to a word in the title of `{key}` (…{ctx}…) — the space a stripped "
                    "tag was holding. Restore it at the source."
                ),
            }
        )
    return out


def audit(bib: Path) -> dict:
    text = bib.read_text(encoding="utf-8", errors="replace")
    findings: list[dict] = []
    titles = 0
    for _, key, body in ENTRY.findall(text):
        m = TITLE.search(body)
        if not m:
            continue
        titles += 1
        findings.extend(findings_for(key.strip(), m.group(1).strip()))

    return {
        "detector": "check_bib_title_markup",
        "bib": str(bib),
        "titles_checked": titles,
        "findings": findings,
        "summary": {
            "TITLE_MARKUP": sum(1 for f in findings if f["verdict"] == "TITLE_MARKUP"),
            "TITLE_FUSION": sum(1 for f in findings if f["verdict"] == "TITLE_FUSION"),
        },
        "submission_safe": not findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bib", required=True, type=Path, help="the .bib file to lint")
    ap.add_argument("--out", type=Path, help="write the JSON audit record here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any title is corrupted")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not a.bib.is_file():
        raise SystemExit(f"not found: {a.bib}")

    rep = audit(a.bib)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not a.quiet:
        print(f"{a.bib.name}: {rep['titles_checked']} title(s) checked")
        for f in rep["findings"]:
            print(f"  [{f['severity'].upper()}] {f['verdict']}: {f['detail']}")
        if not rep["findings"]:
            print("  OK — no publisher markup or tag-strip fusion in any title")

    return 1 if (a.strict and rep["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
