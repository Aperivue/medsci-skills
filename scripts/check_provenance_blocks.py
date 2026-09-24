#!/usr/bin/env python3
"""Route grounded-in-a-real-case prose to a human before it ships.

This is NOT a PII detector, and calling it one would set the wrong expectation. The blocklist
(`check_precedent.py`) matches literals: names, emails, submission IDs. A 2026-08-15 repo-wide audit
found that what survives a literal sweep is never a literal. It is the **provenance sentence
attached to a lesson** — the paragraph that grounds a rule in a real case, written with no blocked
token in it, and specific enough that a reader can identify the case.

The worst instance described one peer review in three directions at once: the manuscript's
claimed-versus-measured task, a co-reviewer's report summarised to its length and its argument, and
the editor's decision. Two of those three were never the author's to publish. Nothing fired, because
nothing in the paragraph was on any list.

No regex can decide whether prose identifies someone. So this script does not decide. It finds the
paragraphs where the question is worth asking and hands them to a reader — or to
`llm_provenance_review.sh`, which asks a model the one question a pattern cannot answer. A router,
not a classifier. It is deliberately silent on the other 97.8% of the repository.

Grounding a rule in a real case is the RIGHT instinct and this repository depends on it
("Precedent failure pattern — treat as a lived failure, not hypothetical"). The aim is to keep the
grounding and drop the identification, so nothing here asks anyone to stop writing precedent blocks.

Verdicts:
  PROVENANCE_REVIEW   a provenance block carries >= --threshold specificity signals.

Exit codes: 0 clean / advisory, 1 with --strict when any block is flagged, 2 usage. Stdlib-only.

Usage:
    python3 check_provenance_blocks.py PATH [PATH ...] [--threshold N] [--strict]
                                       [--json OUT] [--quiet]
    git diff --unified=0 | python3 check_provenance_blocks.py --diff -
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------------------------
# A provenance block opens with one of these. Kept broad on purpose: a missed block is a silent
# gap, and a block with no specificity signals costs nothing because it is never reported.
# ---------------------------------------------------------------------------------------------
OPENER = re.compile(
    r"^\s*(?:\*\*)?(?:"
    r"Precedent(?:\s+(?:failure\s+pattern|incident))?"
    r"|Why\s+this\s+is\s+here"
    r"|Motivation"
    r"|Source"
    r"|Verified\s+against"
    r"|사고(?:\s*motivation)?"
    r")\b"
    r"|^\s*(?:This\s+is\s+a\s+lived\s+failure|From\s+an?\s+[a-z][a-z\s/-]{3,40}?"
    r"(?:cycle|review|submission|project|round)\b)"
    r"|\b(?:verified|observed|confirmed|audit\s+performed|last\s+updated)\b[^.\n]{0,30}\b20\d\d-\d\d(?:-\d\d)?",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------------------------
# Specificity signals. Each is something that moves a block from "a thing that happened" toward
# "this thing, which you could look up". High precision matters more than coverage: a signal that
# fires on ordinary methodological prose turns the whole router into noise, and a noisy gate is one
# people route around — the failure this repository names in its own exemplar-review guidance.
# ---------------------------------------------------------------------------------------------
SIGNALS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "DAY_DATE",
        re.compile(r"\b20\d\d-\d\d-\d\d\b"),
        "a day-precision date pins the case to one event; a month is usually enough for staleness",
    ),
    (
        "THIRD_PARTY_REVIEW",
        re.compile(
            r"\bco-?reviewer\b|\bthe\s+other\s+reviewer\b|\bsecond\s+reviewer\b"
            r"|\bthe\s+editor\s+(?:rejected|accepted|decided|desk-?rejected|returned)"
            r"|\beditor'?s?\s+decision\b|\brejected\s+outright\b|\btiers?\s+below\b",
            re.IGNORECASE,
        ),
        "a review is confidential in three directions; a co-reviewer's report and an editor's "
        "decision are not the author's to describe",
    ),
    (
        "SUBMISSION_ID",
        re.compile(r"\b[A-Z]{2,6}(?:-[A-Z])?-\d{2}-\d{3,6}(?:R\d{1,2})?\b"),
        "a submission ID identifies a manuscript under review",
    ),
    (
        "PRECISE_RESULT",
        re.compile(r"\b\d+\.\d{3,}\b|~\s?\d{2,4}\s+words\b"),
        "a result to 3+ decimals, or a word count, is a fingerprint of one dataset or one document",
    ),
]

# ---------------------------------------------------------------------------------------------
# What the signals must NOT fire on. Both exclusions are here because the first version of this
# script fired on all three of them, on this repository's own files, before it ever saw a real
# leak — the cheapest possible test and the one that matters most. A DOI is public by definition:
# Annals of Internal Medicine mints `10.7326/ANNALS-25-02104`, which is a submission ID's shape and
# a decimal's shape at once, and a vendored checklist citing its own source is provenance working
# exactly as intended. A checker that rejects the notation the world already uses gets switched off.
# ---------------------------------------------------------------------------------------------
DOI_SPANS = re.compile(r"\b10\.\d{4,9}/\S+|\bdoi\.org/\S+|\bDOI:?\s*10\.\d{4,9}/\S+", re.IGNORECASE)


def _mask_dois(body: str) -> str:
    """Blank out DOIs before scoring, so a citation cannot look like a result or an ID."""
    return DOI_SPANS.sub(lambda m: " " * len(m.group(0)), body)


SIGNALS += [
    (
        "QUOTED_ASSESSMENT",
        re.compile(
            r"[\"“”][^\"“”\n]{0,80}\b(?:well-known|expected|unconvincing|limited\s+use|"
            r"not\s+novel|incremental|already\s+validated|hard\s+to\s+distinguish)\b",
            re.IGNORECASE,
        ),
        "quoted assessment language reads as a transcript of someone's confidential judgement",
    ),
]

# ---------------------------------------------------------------------------------------------
# TWO TIERS, and the split is measured, not guessed.
#
# The first version of this file had one tier and a threshold of 2, chosen because it gave zero
# standing hits. Running it against the six findings the audit had actually produced caught ZERO of
# them: a threshold tuned for silence is silent. The error was one-directional, toward comfort, and
# it would have shipped a gate whose real function was to make the repository feel covered.
#
# Measured per signal across the 53 provenance blocks in this tree:
#     THIRD_PARTY_REVIEW 0 · SUBMISSION_ID 0 · QUOTED_ASSESSMENT 0     <- nothing legitimate does this
#     DAY_DATE 17 · PRECISE_RESULT 2 · NO_PUBLIC_SOURCE 35             <- ordinary, needs judgement
#
# So: the first three are things no legitimate precedent block in this repository does, and CI can
# refuse them outright. The last three are ordinary — a fetch date, a rounded statistic, a lesson
# with no citation — and no threshold over them separates "identifies someone" from "does not",
# because that distinction is semantic. Those route to a reader, or to llm_provenance_review.sh.
#
# The deterministic layer narrows 1558 files to ~35 blocks. It does not judge them. Any version of
# this file that starts judging them is the version that goes quiet again.
# ---------------------------------------------------------------------------------------------
BLOCKING = {"THIRD_PARTY_REVIEW", "SUBMISSION_ID", "QUOTED_ASSESSMENT"}

PUBLIC_SOURCE = re.compile(r"10\.\d{4,9}/|https?://|\bPMID\b|doi\.org", re.IGNORECASE)

VERDICT = "PROVENANCE_REVIEW"
EXIT_CLEAN, EXIT_FLAGGED, EXIT_USAGE = 0, 1, 2


def blocks(text: str) -> list[tuple[int, str]]:
    """Split into paragraphs; keep those that open a provenance block. Returns (lineno, body)."""
    out: list[tuple[int, str]] = []
    para: list[str] = []
    start = 1
    for lineno, line in enumerate(text.splitlines() + [""], 1):
        if line.strip():
            if not para:
                start = lineno
            para.append(line)
            continue
        if para:
            body = "\n".join(para)
            if OPENER.search(para[0]) or OPENER.search(body):
                out.append((start, body))
            para = []
    return out


def score(body: str) -> list[tuple[str, str, str]]:
    """Return [(signal, matched_text, why)] for every signal present in the block."""
    scored = _mask_dois(body)
    hits = []
    for name, rx, why in SIGNALS:
        m = rx.search(scored)
        if m:
            hits.append((name, m.group(0).strip(), why))
    if not PUBLIC_SOURCE.search(body):
        hits.append((
            "NO_PUBLIC_SOURCE", "(no DOI, URL or PMID in the block)",
            "provenance against a PUBLIC document is self-evidently safe; provenance against a "
            "private event — a submission, a review, an internal script — is the shape that leaks",
        ))
    return hits


def scan(path: Path, threshold: int, mode: str = "route") -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    findings = []
    for lineno, body in blocks(text):
        hits = score(body)
        names = {h[0] for h in hits}
        if mode == "block" and not (names & BLOCKING):
            continue
        if len(hits) < threshold:
            continue
        if True:
            findings.append(
                {
                    "verdict": VERDICT,
                    "file": str(path),
                    "line": lineno,
                    "signals": [h[0] for h in hits],
                    "matched": [h[1] for h in hits],
                    "why": [h[2] for h in hits],
                    "excerpt": body[:240],
                }
            )
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="Files to scan.")
    ap.add_argument("--threshold", type=int, default=1,
                    help="Signals required to report a block (default 1).")
    ap.add_argument("--mode", choices=("block", "route"), default="route",
                    help="'block': only blocks carrying a BLOCKING signal — what CI refuses. "
                         "'route': every candidate, for a reader or llm_provenance_review.sh.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 when any block is flagged.")
    ap.add_argument("--json", dest="json_out", help="Write findings as JSON to this path.")
    ap.add_argument("--quiet", action="store_true", help="Suppress the human-readable report.")
    args = ap.parse_args()

    if not args.paths:
        ap.error("at least one path is required")

    findings: list[dict] = []
    for p in args.paths:
        path = Path(p)
        if path.is_file():
            findings.extend(scan(path, args.threshold, args.mode))

    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(
            json.dumps({"verdict_counts": {VERDICT: len(findings)}, "findings": findings}, indent=2),
            encoding="utf-8",
        )

    if not args.quiet:
        if not findings:
            print("check_provenance_blocks: nothing to report"
                  + (" (no block carries a refuse-outright signal)." if args.mode == "block"
                     else " (no grounded-in-a-real-case block in scope)."))
        else:
            print(f"check_provenance_blocks: {len(findings)} block(s) worth a second read.\n")
            print("These are not accusations. Grounding a rule in a real case is the right")
            print("instinct — the question is only whether the case stays identifiable.\n")
            for f in findings:
                print(f"  {f['file']}:{f['line']}  [{', '.join(f['signals'])}]")
                for m, w in zip(f["matched"], f["why"]):
                    print(f"      {m!r} — {w}")
                print()
            print("Ask of each: could the person, manuscript, review or submission behind this")
            print("be identified from what is written? If yes, keep the lesson and drop the")
            print("identifying half. `scripts/llm_provenance_review.sh` asks a model the same")
            print("question when a pattern cannot answer it.")

    return EXIT_FLAGGED if (findings and args.strict) else EXIT_CLEAN


if __name__ == "__main__":
    sys.exit(main())
