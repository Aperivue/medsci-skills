#!/usr/bin/env python3
"""The two review boxes are for two different readers. This checks they were written that way.

A journal review form has two free-text boxes: Confidential Comments to the Editor and
Comments to the Authors. They are adjacent, unvalidated, and go to different people. Two
things go wrong there, and neither is caught by reading the draft.

  1. THE RECOMMENDATION LEAKS. The recommendation lives only in the editor's box. SKILL.md
     says the blocks "must never be transposed" and Phase 4 asks for a forbidden-word check,
     both as prose. A transposition is not hypothetical: on an Editorial Manager form the two
     boxes were swapped and it was caught only by exporting the submission proof, one step
     from irreversible. Once submitted, the authors read the recommendation grade and the
     confidential remarks, and the editor gets the author-facing text.

  2. THE BOXES ARE THE SAME TEXT. A human writes the editor note at a different altitude from
     the author note: decision-oriented and terse for the editor, developmental and explanatory
     for the authors. Pasting the same sentences into both is a machine tell, and it wastes the
     attention of the one reader who opens both. Measured on a real draft that had passed every
     other gate: 21 shared 6-grams, including one clause copied verbatim. Rewriting the editor
     block in its own register took it to 3.

Technical phrasing always overlaps a little ("every k and Wilcoxon p in the"), so a small
floor is expected and the default threshold sits above it. A single long shared run fires on
its own, because one copied clause is the tell even when the totals look clean.

Verdicts:
  BOX_MISSING (major)                    one of the two blocks is absent
  RECOMMENDATION_IN_AUTHOR_BOX (major)   a recommendation grade appears in the authors' block
  BOX_DUPLICATION (minor)                the two blocks share too much literal text

Usage:
    check_review_boxes.py --review draft.md [--max-shared 8] [--out qc/boxes.json] [--strict]

Exit 0 unless --strict and a major fires. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AUTHOR_HEAD = re.compile(r"^#{1,6}\s*.*comments?\s+to\s+the\s+authors?\b", re.I)
EDITOR_HEAD = re.compile(r"^#{1,6}\s*.*(confidential|comments?\s+to\s+the\s+editor)", re.I)
ANY_HEAD = re.compile(r"^#{1,6}\s+")

# Recommendation grades. Bare "accept"/"reject" are excluded on purpose: "the authors accept
# that ..." is ordinary prose, and a gate that fires on it gets switched off.
RECOMMENDATION = re.compile(
    r"\b(?:major|minor)\s+revision\b"
    r"|\brevise\s+and\s+resubmit\b"
    r"|\breject(?:ion)?\s*(?::|and|with)\s*(?:encourage|resubmi\w+|transfer|no\b)"
    r"|\bi\s+recommend\s+(?:accept\w*|reject\w*|revision)"
    r"|\baccept\s+with\s+minor\b"
    r"|\bmy\s+recommendation\s+is\b",
    re.I,
)

NGRAM = 6
LONG_RUN = 12          # a shared run this long is a copied clause, whatever the total


def _block(lines: list[str], head: re.Pattern) -> list[str] | None:
    start = None
    for i, line in enumerate(lines):
        if head.match(line):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if ANY_HEAD.match(lines[j]):
            end = j
            break
    return lines[start:end]


def tokens(block: list[str]) -> list[str]:
    out: list[str] = []
    fence = False
    for raw in block:
        s = raw.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s or s.startswith("|") or set(s) <= set("-=*_ "):
            continue
        s = re.sub(r"\*\*|__|`|\*", " ", s)
        out.extend(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())
    return out


def _grams(toks: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def longest_shared_run(a: list[str], b: list[str], cap: int = 40) -> list[str]:
    """Longest common contiguous token run, searched downward from `cap`."""
    bset = {}
    for n in range(cap, NGRAM - 1, -1):
        bset = _grams(b, n)
        if not bset:
            continue
        for i in range(len(a) - n + 1):
            g = tuple(a[i:i + n])
            if g in bset:
                return list(g)
    return []


def audit(path: Path, max_shared: int) -> dict:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    auth, edit = _block(lines, AUTHOR_HEAD), _block(lines, EDITOR_HEAD)
    findings: list[dict] = []

    missing = [n for n, b in (("Comments to the Authors", auth),
                              ("Confidential Comments to the Editor", edit)) if b is None]
    if missing:
        findings.append({
            "verdict": "BOX_MISSING", "severity": "major", "evidence": missing,
            "detail": ("A review form has both boxes and the recommendation belongs only in the "
                       "editor's. With one block absent this cannot check where anything landed."),
        })

    hits: list[str] = []
    if auth is not None:
        prose = "\n".join(l for l in auth if not l.strip().startswith("|"))
        hits = sorted({m.group(0).strip().lower() for m in RECOMMENDATION.finditer(prose)})
        if hits:
            findings.append({
                "verdict": "RECOMMENDATION_IN_AUTHOR_BOX", "severity": "major", "evidence": hits,
                "detail": ("A recommendation grade is in the authors' block. Either the two boxes "
                           "are transposed or the grade was stated twice; both are visible to the "
                           "authors and neither is recoverable after submission. Check the "
                           "compiled proof, not just this draft."),
            })

    shared_n, run = 0, []
    if auth is not None and edit is not None:
        ta, te = tokens(auth), tokens(edit)
        shared = _grams(ta, NGRAM) & _grams(te, NGRAM)
        shared_n = len(shared)
        run = longest_shared_run(ta, te)
        if shared_n > max_shared or len(run) >= LONG_RUN:
            findings.append({
                "verdict": "BOX_DUPLICATION", "severity": "minor",
                "evidence": ([f"{shared_n} shared {NGRAM}-grams (threshold {max_shared})"]
                             + ([f'longest shared run ({len(run)}): "{" ".join(run)}"'] if run else [])),
                "detail": ("The editor's note repeats the authors' text. Write the editor block in "
                           "its own register: what was done, what is left, and whether it needs "
                           "another expert round. The editor reads both boxes."),
            })

    return {
        "detector": "check_review_boxes",
        "review": str(path),
        "author_block": auth is not None,
        "editor_block": edit is not None,
        "shared_ngrams": shared_n,
        "longest_shared_run": len(run),
        "recommendation_terms_in_author_block": hits,
        "findings": findings,
        "summary": {"major": sum(1 for f in findings if f["severity"] == "major"),
                    "minor": sum(1 for f in findings if f["severity"] == "minor")},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--review", required=True, type=Path)
    ap.add_argument("--max-shared", type=int, default=8,
                    help=f"tolerated shared {NGRAM}-grams between the two boxes (default 8)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--strict", action="store_true", help="exit 1 if a major verdict fires")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not a.review.is_file():
        raise SystemExit(f"not found: {a.review}")

    rep = audit(a.review, a.max_shared)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not a.quiet:
        print(f"{a.review.name}: author block: {'yes' if rep['author_block'] else 'NO'} | "
              f"editor block: {'yes' if rep['editor_block'] else 'NO'} | "
              f"shared {NGRAM}-grams: {rep['shared_ngrams']} | "
              f"longest shared run: {rep['longest_shared_run']}")
        for f in rep["findings"]:
            print(f"  [{f['severity'].upper()}] {f['verdict']}: {f['detail']}")
            for e in f.get("evidence", []):
                print(f"           - {e}")
        if not rep["findings"]:
            print("  OK - two distinct blocks, recommendation confined to the editor's")

    return 1 if (a.strict and rep["summary"]["major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
