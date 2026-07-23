#!/usr/bin/env python3
"""Rhetorical-construction density gate — antithesis parallelism and cleft, two
sentence-structure AI tells (self-review §J / humanize P27).

LLM-drafted argumentative prose over-builds two marked constructions that a per-instance
rule cannot flag, because each single occurrence is grammatical and often functional:

  * **antithesis parallelism** — "authority rather than cognition", "not a check but a
    second road", "involvement, not independence". One is a legitimate contrast; a run of
    them is an epigram machine. This was the dominant tell (28 "rather than" in one draft)
    an external reader found in prose that had already cleared the em-dash / passive / word
    sweeps.
  * **cleft / pseudo-cleft** — sentence-initial "What matters is …", "It is X that …". A
    fronting construction the model reaches for to sound weighty.

Neither is wrong once. What marks the machine draft is DENSITY: the reader meets a "rather
than" or a fronted clause every few sentences. So this gate never judges a single instance
— it counts them per 1,000 body words and fires only when the rate AND a raw floor both
clear a threshold set above the rate seen in this project's own published-quality demos
(where "rather than" runs 1.4-3.7 / 1,000 and sentence-initial clefts are absent). A lone
functional "rather than", an "instead of", or one pseudo-cleft therefore never trips it.

Verdicts (both Minor; either can fire independently):
  ANTITHESIS_DENSITY  antithesis markers (rather-than / not-X-but-Y / X-not-Y) per 1,000
                      words exceed the threshold, with the raw count above a floor.
  CLEFT_DENSITY       sentence-initial cleft / pseudo-cleft constructions per 1,000 words
                      exceed the threshold, with the raw count above a floor.

Scope, deliberately conservative on a widely-used skill:
  * Front matter, headings, tables, block quotes, code fences, list items, citation
    markers and inline markup are stripped before measuring (shared _frontmatter helper).
  * "instead of" is NOT counted — it is the functional, non-decorative sibling of "rather
    than" and its presence is not a tell.
  * "not only X but also Y" is excluded from the not-X-but-Y marker (that correlative is
    humanize Pattern 9, a separate check), and conjunctive-adverb / partial-negation forms
    ("however, not all …", "not yet") are excluded from the X-not-Y marker.
  * Silent below --min-words (default 200): a short note has too few words for a rate to
    mean anything.

The rewrite heuristic to apply once flagged (M2, adapted from the SNL-UCSB paper-writing
skill's gate_mechanical.md, MIT): delete the negative half and rewrite the clause in the
positive. If a fact disappears the contrast was functional — keep it; if nothing
disappears it was decoration — cut it. Judge by the manuscript's overall rate, not
instance by instance; keep two or three for emphasis rather than flattening every one.

Exit codes: 0 clean/report-only, 1 with --strict when any Major (none — Minor only),
2 usage. Stdlib-only.

Usage:
    python3 check_rhetorical_density.py --manuscript manuscript.md \
        [--out qc/rhetorical_density.json] [--antithesis-per-1000 6.0] \
        [--cleft-per-1000 2.5] [--min-words 200] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _frontmatter import strip_frontmatter

DETECTOR = "check_rhetorical_density"

FENCE_RE = re.compile(r"```.*?```", re.S)
CITE_RE = re.compile(r"\[@[^\]]+\]|\[\d+(?:[,–-]\d+)*\]")
INLINE_RE = re.compile(r"[*_`]")
WORD_RE = re.compile(r"[A-Za-z0-9']+")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[\"“(]?[A-Z0-9])")

# --- antithesis markers ------------------------------------------------------------------
RATHER_THAN_RE = re.compile(r"\brather than\b", re.I)
# "not X but Y" (X up to three words); "not only … but" is Pattern 9, excluded.
NOT_BUT_RE = re.compile(r"\bnot\s+(?!only\b)[\w'-]+(?:\s+[\w'-]+){0,2}\s+but\b", re.I)
# "X, not Y" contrastive apposition, Y a bare 1-3 word phrase closing the clause.
X_NOT_Y_RE = re.compile(
    r"([\w'-]+),\s+not\s+([\w'-]+)(?:\s+[\w'-]+){0,2}\s*[.;:,]", re.I
)
# Pre-comma words that make "X, not …" a sentence adverb + negation, not an antithesis.
_CONJ_ADVERBS = {
    "however", "therefore", "moreover", "furthermore", "thus", "hence", "nonetheless",
    "nevertheless", "indeed", "finally", "first", "second", "third", "meanwhile",
    "otherwise", "consequently", "accordingly", "similarly", "conversely", "also", "again",
}
# Y-heads that make "not Y" a partial/quantifier negation, not a contrastive noun.
_PARTIAL_NEG = {
    "all", "every", "always", "necessarily", "yet", "just", "merely", "simply", "only",
    "quite", "entirely", "wholly", "fully",
}

# --- cleft markers (applied per sentence) ------------------------------------------------
# pseudo-cleft: "What <>=1 word> is/are/was/were …" (a statement, not a "What is X?" question)
PSEUDO_CLEFT_RE = re.compile(r"^What\s+[\w'-]+(?:\s+[\w'-]+)*?\s+(?:is|are|was|were)\b", re.I)
# it-cleft: "It is/was <focus> that/which/who …"
IT_CLEFT_RE = re.compile(
    r"^It\s+(?:is|was|has\s+been)\s+[\w'-].*?\b(?:that|which|who)\b", re.I
)


def body_text(md: str) -> str:
    """Body prose only: no front matter, headings, tables, block quotes, code, list
    items, citations, or inline markup. Same extractor the aphorism-density gate uses."""
    md = strip_frontmatter(md)
    md = FENCE_RE.sub(" ", md)
    keep = []
    for line in md.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "|", ">", "!", "---")):
            continue
        if re.match(r"^\s*(?:[-*+]|\d+\.)\s", line):
            continue
        keep.append(s)
    txt = " ".join(keep)
    txt = CITE_RE.sub("", txt)
    txt = INLINE_RE.sub("", txt)
    return re.sub(r"\s+", " ", txt).strip()


def sentences(txt: str) -> list:
    return [s.strip() for s in SENT_SPLIT_RE.split(txt) if s.strip()]


def _x_not_y_hits(txt: str) -> list:
    hits = []
    for m in X_NOT_Y_RE.finditer(txt):
        if m.group(1).lower() in _CONJ_ADVERBS:
            continue
        if m.group(2).lower() in _PARTIAL_NEG:
            continue
        hits.append(m.group(0).strip())
    return hits


def analyse(md: str) -> dict:
    body = body_text(md)
    n_words = len(WORD_RE.findall(body))

    anti = (
        [m.group(0) for m in RATHER_THAN_RE.finditer(body)]
        + [m.group(0).strip() for m in NOT_BUT_RE.finditer(body)]
        + _x_not_y_hits(body)
    )
    cleft = []
    for s in sentences(body):
        if s.endswith("?"):
            continue
        if PSEUDO_CLEFT_RE.match(s) or IT_CLEFT_RE.match(s):
            cleft.append(s[:70])

    def rate(n: int) -> float:
        return round(n * 1000.0 / n_words, 2) if n_words else 0.0

    return {
        "words": n_words,
        "antithesis": anti,
        "cleft": cleft,
        "antithesis_per_1000": rate(len(anti)),
        "cleft_per_1000": rate(len(cleft)),
    }


ANTITHESIS_MIN_COUNT = 5
CLEFT_MIN_COUNT = 3


def check(md: str, antithesis_per_1000: float, cleft_per_1000: float, min_words: int) -> dict:
    r = analyse(md)
    findings = []
    if r["words"] >= min_words:
        na, nc = len(r["antithesis"]), len(r["cleft"])
        if na >= ANTITHESIS_MIN_COUNT and r["antithesis_per_1000"] > antithesis_per_1000:
            findings.append({
                "verdict": "ANTITHESIS_DENSITY",
                "severity": "Minor",
                "detail": (
                    f"{na} antithesis constructions in {r['words']} body words "
                    f"({r['antithesis_per_1000']}/1000 > {antithesis_per_1000:.1f} threshold) — "
                    "a run of 'rather than' / 'not X but Y' / 'X, not Y' epigrams; each is "
                    "grammatical but the density is an LLM tell. Delete the negative half and "
                    "rewrite in the positive; if a fact disappears the contrast was functional "
                    "(keep it), if nothing disappears it was decoration (cut it). Keep two or three."
                ),
                "where": "; ".join(m[:40] for m in r["antithesis"][:8]),
            })
        if nc >= CLEFT_MIN_COUNT and r["cleft_per_1000"] > cleft_per_1000:
            findings.append({
                "verdict": "CLEFT_DENSITY",
                "severity": "Minor",
                "detail": (
                    f"{nc} cleft / pseudo-cleft constructions in {r['words']} body words "
                    f"({r['cleft_per_1000']}/1000 > {cleft_per_1000:.1f} threshold) — "
                    "sentence-initial 'What … is …' / 'It is … that …' fronting used for "
                    "weight. Rewrite in plain subject-verb order ('What matters is X' -> 'X "
                    "matters'); keep at most one for genuine emphasis."
                ),
                "where": "; ".join(s[:48] for s in r["cleft"][:8]),
            })
    return {"metrics": {k: r[k] for k in
            ("words", "antithesis_per_1000", "cleft_per_1000")}, "findings": findings,
            "detail": r}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Rhetorical-construction density gate — antithesis + cleft (§J / P27).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--antithesis-per-1000", type=float, default=6.0,
                    help="antithesis markers per 1000 words that trips the flag (default 6.0)")
    ap.add_argument("--cleft-per-1000", type=float, default=2.5,
                    help="cleft constructions per 1000 words that trips the flag (default 2.5)")
    ap.add_argument("--min-words", type=int, default=200,
                    help="stay silent below this many body words (default 200)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any Major (none — this gate is Minor-only)")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    a = ap.parse_args()

    src = Path(a.manuscript)
    if not src.is_file():
        sys.stderr.write(f"error: no such file: {src}\n")
        return 2

    result = check(src.read_text(encoding="utf-8", errors="ignore"),
                   a.antithesis_per_1000, a.cleft_per_1000, a.min_words)
    findings = result["findings"]

    if not a.quiet:
        print("=" * 42)
        print(" Rhetorical-construction density (§J / P27)")
        print("=" * 42)
        print("| Verdict | Severity | Detail |")
        print("|---|---|---|")
        if findings:
            for f in findings:
                print(f"| {f['verdict']} | {f['severity']} | {f['detail']} |")
            for f in findings:
                print(f"\n{f['verdict']} — {f['where']}")
        else:
            print("| (none) | — | antithesis / cleft density within the published range |")
            m = result["metrics"]
            print(f"\nOK: antithesis {m['antithesis_per_1000']}/1000, "
                  f"cleft {m['cleft_per_1000']}/1000 — within range.")

    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "detector": DETECTOR,
            "manuscript": str(src),
            "metrics": result["metrics"],
            "findings": findings,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if not a.quiet:
            print(f"\nwrote {out}")

    return 1 if (a.strict and any(f["severity"] == "Major" for f in findings)) else 0


if __name__ == "__main__":
    sys.exit(main())
