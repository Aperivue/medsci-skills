#!/usr/bin/env python3
"""Bound how much of a text a humanize rewrite is allowed to touch (humanize Phase 3).

De-AI editing is subtractive: strip the tells, keep the author's sentences. A model asked to
"make this sound human" will also rewrite paragraphs that had nothing wrong with them, and the
result reads fluently enough that the loss is invisible on review — the author's voice is gone
and nobody can point to the sentence where it went. Pattern-by-pattern fixes touch a small
fraction of the words; a wholesale rewrite touches most of them. That difference is measurable,
so this gate measures it instead of trusting the rewrite to have been restrained.

It also enforces the two invariants the humanize skill declares but never checked: every number
and every citation present before the rewrite must still be present after it.

Verdicts:
  NUMBER_DRIFT (Major)         a numeric token's count changed across the rewrite.
  CITATION_DROP (Major)        a citation present before is absent after.
  EDIT_FOOTPRINT_HIGH (Minor)  more than --warn-pct of the words changed — re-read the diff.

Why the footprint is advisory and the invariants are not: the two invariants are the skill's
own declared contract ("every number, statistic, p-value, confidence interval and clinical fact
must remain identical"; "do not remove or relocate citations"), so a violation is unambiguous.
The footprint percentage has no such backing. Measured on this skill's own fixtures, a *correct*
de-AI pass over an AI-inflated Discussion changed 61% of word tokens — because Patterns 6 and 18
require replacing formulaic limitation and conclusion paragraphs with specific content, which
rewrites whole paragraphs by design. A hard threshold would therefore fail exactly the edits the
skill asks for. The percentage is reported so a human can notice an implausible one; it is not
evidence of over-editing on its own, and the default is deliberately loose.

Exit codes: 0 clean or Minor-only, 1 with --strict when any Major fires, 2 usage error.

Scoped to keep false positives low:
  * Comparison is on WORD tokens, not characters, so punctuation-only fixes (Pattern 13
    em-dash -> parenthesis, Pattern 15 curly -> straight quotes) barely move the number.
  * Citation markers are stripped before numeric extraction, so a reference number is
    checked once as a citation and never again as a number.
  * Fenced code blocks are excluded from both sides.

Stdlib-only.

Usage:
    python3 check_rewrite_fidelity.py --before original.md --after humanized.md \
        [--out qc/rewrite_fidelity.json] [--warn-pct 70] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

DETECTOR_ID = "check_rewrite_fidelity"

FENCE_RE = re.compile(r"```.*?```", re.S)
# Pandoc citation keys and bare numeric markers, e.g. [@smith2020], [12], [3-5], [3–5].
CITEKEY_RE = re.compile(r"\[@[^\]\s]+\]")
NUMMARK_RE = re.compile(r"\[\d+(?:\s*[-–,]\s*\d+)*\]")
WORD_RE = re.compile(r"[A-Za-z0-9''-]+")
# A numeric token: integer, decimal, or percentage. Sign and thousands separators kept out
# so that "1,200" and "1200" compare equal after separator removal.
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _strip_fences(text: str) -> str:
    return FENCE_RE.sub(" ", text)


def _citations(text: str) -> Counter:
    keys = CITEKEY_RE.findall(text)
    marks = NUMMARK_RE.findall(text)
    return Counter(k.strip() for k in keys + marks)


def _numbers(text: str) -> Counter:
    """Numeric tokens with citation markers removed first, so a reference number is not
    double-counted as a statistic."""
    without_cites = NUMMARK_RE.sub(" ", CITEKEY_RE.sub(" ", text))
    without_seps = without_cites.replace(",", "")
    return Counter(NUMBER_RE.findall(without_seps))


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def _changed_fraction(before: list[str], after: list[str]) -> float:
    """Fraction of word tokens that differ, measured against the longer side so that a
    rewrite cannot lower the score by deleting text."""
    if not before and not after:
        return 0.0
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    matched = sum(block.size for block in matcher.get_matching_blocks())
    denom = max(len(before), len(after))
    return 1.0 - (matched / denom) if denom else 0.0


def _diff_counter(before: Counter, after: Counter) -> list[dict]:
    out = []
    for token in sorted(set(before) | set(after)):
        b, a = before.get(token, 0), after.get(token, 0)
        if b != a:
            out.append({"token": token, "before": b, "after": a})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--before", required=True, type=Path, help="text as it was before the rewrite")
    ap.add_argument("--after", required=True, type=Path, help="text after the humanize rewrite")
    ap.add_argument("--out", type=Path, help="write the JSON envelope here")
    ap.add_argument("--warn-pct", type=float, default=70.0,
                    help="Minor above this %% of words changed (default 70; advisory, see module docstring)")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any Major fires")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    for path in (args.before, args.after):
        if not path.is_file():
            print(f"usage error: no such file: {path}", file=sys.stderr)
            return 2

    before_raw = _strip_fences(args.before.read_text(encoding="utf-8"))
    after_raw = _strip_fences(args.after.read_text(encoding="utf-8"))

    changed = _changed_fraction(_words(before_raw), _words(after_raw))
    changed_pct = round(changed * 100, 1)
    num_delta = _diff_counter(_numbers(before_raw), _numbers(after_raw))
    cite_delta = _diff_counter(_citations(before_raw), _citations(after_raw))

    claims: list[dict] = []
    if changed_pct > args.warn_pct:
        claims.append({
            "verdict": "EDIT_FOOTPRINT_HIGH",
            "severity": "Minor",
            "changed_pct": changed_pct,
            "threshold_pct": args.warn_pct,
            "message": (
                f"{changed_pct}% of word tokens changed (advisory threshold {args.warn_pct}%). "
                "A thorough de-AI pass can legitimately reach this level when Patterns 6 and 18 "
                "replace whole paragraphs; re-read the diff and confirm the author's argument, "
                "not just their phrasing, survived."
            ),
        })
    if num_delta:
        claims.append({
            "verdict": "NUMBER_DRIFT",
            "severity": "Major",
            "tokens": num_delta[:40],
            "message": (
                f"{len(num_delta)} numeric token(s) changed count across the rewrite. "
                "Humanize must never alter a number."
            ),
        })
    if cite_delta:
        claims.append({
            "verdict": "CITATION_DROP",
            "severity": "Major",
            "tokens": cite_delta[:40],
            "message": (
                f"{len(cite_delta)} citation(s) changed count across the rewrite. "
                "Humanize must never remove or relocate a citation."
            ),
        })

    envelope = {
        "detector": "check_rewrite_fidelity",
        "before": str(args.before),
        "after": str(args.after),
        "changed_pct": changed_pct,
        "words_before": len(_words(before_raw)),
        "words_after": len(_words(after_raw)),
        "claims": claims,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print(f"{DETECTOR_ID}: {changed_pct}% of words changed "
              f"({len(_words(before_raw))} -> {len(_words(after_raw))})")
        for claim in claims:
            print(f"  [{claim['severity']}] {claim['verdict']}: {claim['message']}")
        if not claims:
            print("  clean: footprint within bounds, numbers and citations preserved")

    if args.strict and any(c["severity"] == "Major" for c in claims):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
