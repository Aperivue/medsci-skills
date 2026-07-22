#!/usr/bin/env python3
"""Aphorism-density gate — a prose-rhythm AI tell (self-review §J / humanize P26).

LLM-drafted argumentative prose writes in epigrams. Every sentence lands; almost none
merely explains. Two things co-occur and are individually measurable:

  * the **negative definition** — "Authority is not cognition." "Involvement is not
    independence." A short sentence whose whole content is `X is not Y`.
  * a high share of **very short declaratives** used as punchlines ("It did not."
    "It is not one." "It cost more than it paid.").

Human academic prose has both, sparingly, for emphasis. What marks the machine draft is
density: the reader gets a closing line every few sentences and never a sentence that
simply carries information forward. The fix is not to delete the epigrams — two or three
are what a reader remembers — but to restore the explanatory sentences between them.

Verdict:
  APHORISM_DENSITY (Minor)  BOTH the negative-definition rate AND the short-declarative
                            share exceed thresholds calibrated on published prose.

Scope, deliberately conservative on a widely-used skill:
  * Requires BOTH signals. Either alone is ordinary style; together they are the tell.
  * The negative-definition pattern only counts inside a SHORT sentence, so ordinary
    negation in a long explanatory sentence ("the bound is not derived from multiplicity,
    because ...") never counts.
  * Headings, tables, block quotes, code fences and citation markers are stripped first.
  * Reports the offending sentences so the author can absorb them rather than hunt.

Thresholds are calibrated against a corpus of published Perspectives (see --calibrate),
not chosen a priori. Across eight published npj Digital Medicine Perspectives, cleaned to
body prose and measured with this same code, the negative-definition rate ran 0.00-0.45%
of sentences (seven of eight were 0.00%) and the short-declarative share 0.94-10.47%.
The defaults sit above both observed maxima, so prose inside the published range does not
fire. Regenerate with --calibrate if you have your own corpus; the numbers above are from
argumentative Perspectives and a different genre may sit elsewhere.

Exit codes: 0 clean/report-only, 1 with --strict when any Major (none — Minor only),
2 usage. Stdlib-only.

Usage:
    python3 check_aphorism_density.py --manuscript manuscript.md \
        [--out qc/aphorism_density.json] [--neg-def-pct 0.9] [--short-pct 13.0] \
        [--min-sentences 40] [--strict] [--quiet]
    python3 check_aphorism_density.py --calibrate corpus/*.txt
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import statistics
import sys
from pathlib import Path

from _frontmatter import strip_frontmatter

FENCE_RE = re.compile(r"```.*?```", re.S)
CITE_RE = re.compile(r"\[@[^\]]+\]|\[\d+(?:[,–-]\d+)*\]")
INLINE_RE = re.compile(r"[*_`]")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“])")

# `X is not Y` where the complement is a bare noun phrase, not a clause or a
# prepositional phrase. "Authority is not cognition." counts; "the bound is not
# derived from multiplicity" does not (participle), nor does "is not in the frame" (PP).
NEG_DEF_RE = re.compile(
    r"\b\w[\w'-]*\s+(?:is|are|was|were)\s+not\s+"
    r"(?:a|an|the\s+)?[\w'-]+(?:\s+[\w'-]+){0,2}\s*[.,;]",
    re.I,
)
_PARTICIPLE_OR_PP = re.compile(
    r"\b(?:is|are|was|were)\s+not\s+"
    r"(?:\w+(?:ed|ing)\b|in|on|at|by|for|from|to|with|about|under|over|within|between)\b",
    re.I,
)

SHORT_MAX_WORDS = 9          # "very short declarative"
NEG_DEF_MAX_WORDS = 14       # a negative definition only counts inside a short sentence
MIN_SENTENCES = 40           # below this a rate is noise


def body_text(md: str) -> str:
    """Body prose only: no headings, tables, block quotes, code, citations, markup."""
    md = strip_frontmatter(md)   # a `status:`/build-note YAML block is not prose rhythm
    md = FENCE_RE.sub(" ", md)
    keep = []
    for line in md.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "|", ">", "!", "---")):
            continue
        if re.match(r"^\s*(?:[-*+]|\d+\.)\s", line):   # list items are not prose rhythm
            continue
        keep.append(s)
    txt = " ".join(keep)
    txt = CITE_RE.sub("", txt)
    txt = INLINE_RE.sub("", txt)
    return re.sub(r"\s+", " ", txt).strip()


def sentences(txt: str) -> list[str]:
    return [s.strip() for s in SENT_SPLIT_RE.split(txt) if len(s.split()) >= 2]


def analyse(md: str) -> dict:
    sents = sentences(body_text(md))
    n = len(sents)
    if not n:
        return {"sentences": 0, "neg_def": [], "short": [], "neg_def_pct": 0.0, "short_pct": 0.0}
    neg, short = [], []
    for s in sents:
        w = len(s.split())
        if w <= SHORT_MAX_WORDS:
            short.append(s)
        if w <= NEG_DEF_MAX_WORDS and NEG_DEF_RE.search(s) and not _PARTICIPLE_OR_PP.search(s):
            neg.append(s)
    return {
        "sentences": n,
        "neg_def": neg,
        "short": short,
        "neg_def_pct": round(100.0 * len(neg) / n, 2),
        "short_pct": round(100.0 * len(short) / n, 2),
        "mean_sentence_words": round(statistics.mean(len(s.split()) for s in sents), 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript")
    ap.add_argument("--calibrate", nargs="+", help="plain-text corpus files; print rates and exit")
    ap.add_argument("--out")
    ap.add_argument("--neg-def-pct", type=float, default=0.9)
    ap.add_argument("--short-pct", type=float, default=13.0)
    ap.add_argument("--min-sentences", type=int, default=MIN_SENTENCES,
                    help="floor below which a rate is treated as noise (tests lower it)")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if a.calibrate:
        paths = [p for pat in a.calibrate for p in sorted(glob.glob(pat))]
        rows = []
        for p in paths:
            r = analyse(Path(p).read_text(encoding="utf-8", errors="ignore"))
            if r["sentences"] < MIN_SENTENCES:
                continue
            rows.append((Path(p).name, r))
            print(f"{Path(p).name[:40]:<42}{r['sentences']:>5}"
                  f"{r['neg_def_pct']:>8.2f}%{r['short_pct']:>8.2f}%{r['mean_sentence_words']:>8.1f}")
        if rows:
            nd = [r["neg_def_pct"] for _, r in rows]
            sh = [r["short_pct"] for _, r in rows]
            print(f"{'median':<42}{'':>5}{statistics.median(nd):>8.2f}%{statistics.median(sh):>8.2f}%")
            print(f"{'max':<42}{'':>5}{max(nd):>8.2f}%{max(sh):>8.2f}%")
        return 0

    if not a.manuscript:
        sys.stderr.write("error: --manuscript or --calibrate is required\n")
        return 2
    src = Path(a.manuscript)
    if not src.exists():
        sys.stderr.write(f"error: no such file: {src}\n")
        return 2

    r = analyse(src.read_text(encoding="utf-8", errors="ignore"))
    fired = (
        r["sentences"] >= a.min_sentences
        and r["neg_def_pct"] > a.neg_def_pct
        and r["short_pct"] > a.short_pct
    )
    findings = []
    if fired:
        findings.append({
            "check": "APHORISM_DENSITY",
            "severity": "Minor",
            "detail": (
                f"prose reads as a run of epigrams: {len(r['neg_def'])} negative definitions "
                f"({r['neg_def_pct']}% of sentences, threshold {a.neg_def_pct}%) and "
                f"{len(r['short'])} very short declaratives ({r['short_pct']}%, threshold "
                f"{a.short_pct}%); mean sentence {r['mean_sentence_words']} words. "
                "Absorb most of them into the neighbouring sentence and restore the "
                "explanatory prose between; keep two or three for emphasis."
            ),
            "negative_definitions": r["neg_def"][:12],
            "short_declaratives": r["short"][:12],
        })

    if not a.quiet:
        print("=" * 42)
        print(" Aphorism density (§J / P26)")
        print("=" * 42)
        print("| Check | Severity | Detail |")
        print("|---|---|---|")
        if findings:
            for f in findings:
                print(f"| {f['check']} | {f['severity']} | {f['detail']} |")
            print("\nnegative definitions:")
            for s in r["neg_def"][:12]:
                print(f"  • {s}")
            print("\nvery short declaratives:")
            for s in r["short"][:12]:
                print(f"  • {s}")
        else:
            print("| (none) | — | sentence rhythm within the published range |")
            print("\nOK: sentence rhythm within the published range.")

    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"detector": "check_aphorism_density", "manuscript": str(src), "metrics": {
            k: r[k] for k in ("sentences", "neg_def_pct", "short_pct", "mean_sentence_words")
        }, "findings": findings}, indent=2) + "\n")
        if not a.quiet:
            print(f"\nwrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
