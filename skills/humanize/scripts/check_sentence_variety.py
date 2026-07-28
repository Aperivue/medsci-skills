#!/usr/bin/env python3
"""Verify the sentence-length variety the humanize skill already prescribes (Fix rule 7).

SKILL.md Phase 3 tells the rewriter: "Mix short declarative sentences (8-12 words) with longer
ones (25-35 words). Avoid uniform length." Until now nothing checked whether the rewrite obeyed
it, and a de-AI pass tends to flatten rhythm rather than restore it — the model shortens the
long sentences and pads the short ones toward a comfortable middle, which is itself a tell.

The threshold is not borrowed from any corpus. It is the skill's own specification: a text that
prescribes a mix of short and long sentences and then contains none of one kind has failed its
own rule. So this gate fires only on that unambiguous case — an absent band — and reports the
distribution for everything else rather than inventing a cutoff.

Verdict:
  SENTENCE_UNIFORM (Minor)  the prose contains no short sentences (<= --short-max words) or no
                            long ones (>= --long-min), i.e. every sentence sits in the middle
                            band. Break up or combine sentences until both bands are populated.

Scoped to keep false positives low:
  * Headings, list items, table rows, code fences, and YAML front matter are excluded — their
    lengths say nothing about prose rhythm.
  * Common academic abbreviations (et al., e.g., i.e., vs., Fig., approx.) and decimals do not
    split a sentence.
  * Citation markers are removed before counting, so [@key] and [12] never inflate a length.
  * Silent below --min-sentences (default 15): an abstract or a short note has too few
    sentences for rhythm to mean anything.

Exit codes: 0 clean or Minor-only, 1 with --strict when any Major fires (none — Minor only),
2 usage error. Stdlib-only.

Usage:
    python3 check_sentence_variety.py --manuscript manuscript.md \
        [--out qc/sentence_variety.json] [--short-max 12] [--long-min 25] \
        [--min-sentences 15] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

DETECTOR_ID = "check_sentence_variety"

FENCE_RE = re.compile(r"```.*?```", re.S)
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
SKIP_LINE_RE = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+\.\s|\||>\s|!\[|\[.*\]:)")
CITE_RE = re.compile(r"\[@[^\]\s]+\]|\[\d+(?:\s*[-–,]\s*\d+)*\]")
WORD_RE = re.compile(r"[A-Za-z0-9''-]+")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[\"'(]?[A-Z0-9])")

# Abbreviations whose trailing period must not end a sentence. Order matters: longer first.
ABBREVIATIONS = (
    "et al.", "e.g.", "i.e.", "cf.", "vs.", "approx.", "Fig.", "Figs.", "Tab.", "No.",
    "Dr.", "Prof.", "St.", "Sr.", "Jr.", "Inc.", "Ltd.", "min.", "max.", "sec.",
)
_SENTINEL = "\x00ABBR%d\x00"
_DOT = "\x00DOT\x00"


def _prose_lines(text: str) -> str:
    """Body prose only: drop front matter, fences, headings, lists, tables, block quotes."""
    text = FRONTMATTER_RE.sub("", text)
    text = FENCE_RE.sub(" ", text)
    kept = [ln for ln in text.splitlines() if ln.strip() and not SKIP_LINE_RE.match(ln)]
    return " ".join(kept)


def _split_sentences(prose: str) -> list[str]:
    masked = prose
    for i, abbr in enumerate(ABBREVIATIONS):
        masked = masked.replace(abbr, _SENTINEL % i)
    # Protect decimals ("0.05", "P = .03") from the splitter. A lambda replacement is used
    # because a NUL byte cannot appear in an re.sub template string.
    masked = re.sub(r"(\d)\.(\d)", lambda m: m.group(1) + _DOT + m.group(2), masked)
    masked = re.sub(r"(?<=[=<>]\s)\.(\d)", lambda m: _DOT + m.group(1), masked)

    parts = SENT_SPLIT_RE.split(masked)

    out = []
    for part in parts:
        restored = part.replace(_DOT, ".")
        for i, abbr in enumerate(ABBREVIATIONS):
            restored = restored.replace(_SENTINEL % i, abbr)
        restored = restored.strip()
        if restored:
            out.append(restored)
    return out


def _word_count(sentence: str) -> int:
    return len(WORD_RE.findall(CITE_RE.sub(" ", sentence)))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manuscript", required=True, type=Path)
    ap.add_argument("--out", type=Path, help="write the JSON envelope here")
    ap.add_argument("--short-max", type=int, default=12, help="a short sentence is <= this (SKILL.md rule 7)")
    ap.add_argument("--long-min", type=int, default=25, help="a long sentence is >= this (SKILL.md rule 7)")
    ap.add_argument("--min-sentences", type=int, default=15, help="stay silent below this many sentences")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not args.manuscript.is_file():
        print(f"usage error: no such file: {args.manuscript}", file=sys.stderr)
        return 2

    sentences = _split_sentences(_prose_lines(args.manuscript.read_text(encoding="utf-8")))
    lengths = [n for n in (_word_count(s) for s in sentences) if n > 0]

    claims: list[dict] = []
    stats: dict = {"sentences": len(lengths)}

    if len(lengths) >= args.min_sentences:
        short = [n for n in lengths if n <= args.short_max]
        long_ = [n for n in lengths if n >= args.long_min]
        stats.update({
            "short_count": len(short),
            "long_count": len(long_),
            "median_words": round(statistics.median(lengths), 1),
            "min_words": min(lengths),
            "max_words": max(lengths),
            "stdev_words": round(statistics.pstdev(lengths), 1),
        })
        if not short or not long_:
            missing = "short" if not short else "long"
            band = (f"<= {args.short_max} words" if not short else f">= {args.long_min} words")
            claims.append({
                "verdict": "SENTENCE_UNIFORM",
                "severity": "Minor",
                "missing_band": missing,
                "message": (
                    f"No {missing} sentences ({band}) across {len(lengths)} sentences "
                    f"(median {stats['median_words']}, range {stats['min_words']}-{stats['max_words']}). "
                    "SKILL.md Fix rule 7 requires both bands; uniform length is itself an AI tell."
                ),
            })
    else:
        stats["skipped"] = f"only {len(lengths)} sentences (< --min-sentences {args.min_sentences})"

    envelope = {
        "detector": "check_sentence_variety",
        "manuscript": str(args.manuscript),
        "short_max": args.short_max,
        "long_min": args.long_min,
        "stats": stats,
        "claims": claims,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        if "skipped" in stats:
            print(f"{DETECTOR_ID}: skipped — {stats['skipped']}")
        else:
            print(f"{DETECTOR_ID}: {stats['sentences']} sentences, median {stats['median_words']} words, "
                  f"{stats['short_count']} short / {stats['long_count']} long")
        for claim in claims:
            print(f"  [{claim['severity']}] {claim['verdict']}: {claim['message']}")
        if not claims and "skipped" not in stats:
            print("  clean: both short and long sentence bands are populated")

    if args.strict and any(c["severity"] == "Major" for c in claims):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
