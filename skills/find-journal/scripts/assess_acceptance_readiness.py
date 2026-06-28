#!/usr/bin/env python3
"""Acceptance-readiness pre-flight for /find-journal (Phase 2.5).

A deterministic, stdlib-only lexical scan of a manuscript (or abstract) markdown
file that surfaces the signals editors actually reject on BEFORE scope is even
considered: design-ceiling, unfixable validity defects, importance/novelty risk,
and endpoint-vs-claim mismatch.

Why this exists
---------------
Empirically the #1 desk-rejection driver is lack of novelty/importance (~52%),
ahead of scope mismatch; and across a curated editor-decision corpus the recurring
pattern is that an *unfixable* design-ceiling defect floors the outcome at REJECT
regardless of how polished everything fixable is. `/find-journal` already optimises
scope fit; this script supplies the missing **acceptance-feasibility** axis so the
skill can gate the venue TIER a manuscript's design can credibly support.

This is an ADVISORY heuristic, not an acceptance prediction and not auto-fixable.
It flags lexical signals for a human (or the skill's LLM phase) to weigh; it never
rewrites the manuscript. Acceptance likelihood has no reliable data source and ML
predictors cap well below certainty, so the output is a risk/ceiling band with
reasons — never a probability.

Usage
-----
  python3 assess_acceptance_readiness.py MANUSCRIPT.md
  python3 assess_acceptance_readiness.py --json MANUSCRIPT.md

Exit code is always 0 (advisory). Output is deterministic (sorted, stable) so it
can be golden-mastered in a network-free challenge card.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Category display order (also the tie-break order in the sorted flag list).
CATEGORIES = ("DESIGN_CEILING", "UNFIXABLE_DEFECT", "IMPORTANCE_RISK", "CLAIM_MISMATCH")
CAT_ORDER = {c: i for i, c in enumerate(CATEGORIES)}

# Each detector: (category, compiled regex, label, rationale).
# Regexes are case-insensitive and intentionally conservative — a flag is a
# prompt to verify, so a miss is safer than a false alarm. Keep them lexical and
# stable; do not depend on sentence parsing.
_D = lambda p: re.compile(p, re.IGNORECASE)

DETECTORS = [
    # --- DESIGN_CEILING: the design cannot support the claimed altitude ---
    ("DESIGN_CEILING", _D(r"\bcross[-\s]?sectional\b"),
     "cross-sectional design",
     "cross-sectional data cannot support prognostic, causal, or surveillance claims"),
    ("DESIGN_CEILING", _D(r"\b(?:surrogate|proxy)\b|\bFIB[-\s]?4\b|\bnon[-\s]?invasive (?:surrogate|marker)\b"),
     "surrogate / non-invasive marker as endpoint",
     "a surrogate endpoint without a hard clinical or histologic endpoint caps clinical-impact claims"),
    ("DESIGN_CEILING", _D(r"\bsingle[-\s]?cent(?:er|re)\b"),
     "single-center",
     "high-impact venues expect multi-center cohorts or external validation"),
    ("DESIGN_CEILING", _D(r"\b(?:no|without|lack(?:ing|ed|s)?(?: of)?) (?:an? )?external validation\b"
                          r"|\bexternal validation (?:was )?(?:not|never) (?:performed|done|available|conducted)\b"),
     "no external validation",
     "a prediction/diagnostic model without external validation rarely clears a top venue"),
    ("DESIGN_CEILING", _D(r"\b(?:pilot|preliminary|proof[-\s]?of[-\s]?concept|feasibility)\b"),
     "pilot / preliminary framing",
     "appropriate for tolerant venues; high-impact originals expect a definitive design"),

    # --- UNFIXABLE_DEFECT: validity threats editors reject on, not revisable ---
    ("UNFIXABLE_DEFECT", _D(r"\b(?:data|information) leakage\b|\btrain(?:ing)?[-/\s]test (?:overlap|contamination)\b"
                            r"|\btarget[-\s]?derived\b"),
     "possible data leakage",
     "leakage is an unfixable validity threat; in-sample performance becomes uninterpretable"),
    ("UNFIXABLE_DEFECT", _D(r"\bcircular(?:ity)?\b|\bself[-\s]?fulfilling\b"),
     "circular design / validation",
     "predicting a label from inputs that encode it is structurally guaranteed, not a finding"),
    ("UNFIXABLE_DEFECT", _D(r"\bno (?:comparator|baseline)\b|\bwithout (?:a )?(?:comparator|baseline)\b"
                            r"|\bno (?:standard|established) baseline\b"),
     "missing comparator / baseline",
     "without a field-standard comparator the contribution cannot be judged"),
    ("UNFIXABLE_DEFECT", _D(r"\bsingle[-\s]?vendor\b|\bsingle[-\s]?scanner\b|\bone (?:vendor|scanner|device)\b"
                            r"|\bvendor[-\s]?locked\b"),
     "single-vendor / single-scanner",
     "vendor-locked acquisition is a hard generalizability ceiling"),

    # --- IMPORTANCE_RISK: the novelty/importance gate (top desk-reject cause) ---
    ("IMPORTANCE_RISK", _D(r"\bshow(?:ed|s|n)? no\b|\bno (?:significant )?(?:association|difference|synerg(?:y|ies)|effect|benefit)\b"
                           r"|\bdid not (?:differ|improve|change|increase|reduce)\b|\bnull (?:result|finding)\b"),
     "negative / null framing",
     "a null/negative result needs explicit importance justification; low-impact nulls are desk-rejected"),
    ("IMPORTANCE_RISK", _D(r"\bincremental\b|\bmarginal\b|\bmodest improvement\b|\bslight(?:ly)? (?:better|higher|improved)\b"),
     "incremental-gain framing",
     "incremental contribution is the single most common desk-rejection reason (~52%)"),
    ("IMPORTANCE_RISK", _D(r"\bsimilar to (?:previous|prior)\b|\bconsistent with (?:existing|prior) (?:work|literature)\b"
                           r"|\bme[-\s]?too\b"),
     "me-too positioning",
     "framing the work as confirmatory of prior literature signals weak novelty"),

    # --- CLAIM_MISMATCH: action verb that the endpoint may not support ---
    # Emitted only when a DESIGN_CEILING signal also appears in the document
    # (computed below), so the manuscript that legitimately earns the claim is
    # not flagged.
    ("CLAIM_MISMATCH", _D(r"\b(?:we )?recommend\b|\bdefer\b|\bwithhold\b|\bguide(?:s|d)? (?:management|treatment|therapy)\b"
                          r"|\bsurveillance\b|\brescreen\b|\binitiate (?:treatment|therapy)\b|\bchange(?:s|d)? management\b"
                          r"|\bactionable\b|\bpersonalized risk\b"),
     "management / surveillance claim",
     "verify the endpoint supports this action verb; a cross-sectional/surrogate design cannot"),
]

# Detectors whose presence marks the document as having a design ceiling, which
# in turn enables CLAIM_MISMATCH emission.
_CEILING_TRIGGER_LABELS = {
    "cross-sectional design",
    "surrogate / non-invasive marker as endpoint",
    "pilot / preliminary framing",
}

VERDICT_NONE = "NO STRUCTURAL CEILING DETECTED BY LEXICAL SCAN"
VERDICT_IMPORTANCE = "IMPORTANCE-FRAMING REVIEW RECOMMENDED"
VERDICT_SPECIALTY = "SPECIALTY / TOLERANT-VENUE OR DESIGN FIX RECOMMENDED"
VERDICT_HIGH = "HIGH-IMPACT VENUE UNLIKELY WITHOUT A DESIGN CHANGE"


def scan(text: str):
    """Return a sorted list of flags: (line_no, category, label, rationale)."""
    lines = text.splitlines()
    raw = []
    doc_has_ceiling = False
    # First pass: every detector except CLAIM_MISMATCH, and learn doc_has_ceiling.
    for lineno, line in enumerate(lines, start=1):
        for category, rx, label, rationale in DETECTORS:
            if category == "CLAIM_MISMATCH":
                continue
            if rx.search(line):
                raw.append((lineno, category, label, rationale))
                if label in _CEILING_TRIGGER_LABELS:
                    doc_has_ceiling = True
    # Second pass: CLAIM_MISMATCH only when the document carries a ceiling signal.
    if doc_has_ceiling:
        for lineno, line in enumerate(lines, start=1):
            for category, rx, label, rationale in DETECTORS:
                if category != "CLAIM_MISMATCH":
                    continue
                if rx.search(line):
                    raw.append((lineno, category, label, rationale))
    # Dedupe identical (line, category, label) and sort deterministically.
    seen = set()
    flags = []
    for lineno, category, label, rationale in raw:
        key = (lineno, category, label)
        if key in seen:
            continue
        seen.add(key)
        flags.append((lineno, category, label, rationale))
    flags.sort(key=lambda f: (f[0], CAT_ORDER[f[1]], f[2]))
    return flags


def verdict(counts):
    if counts["UNFIXABLE_DEFECT"] > 0 or counts["DESIGN_CEILING"] >= 2:
        return VERDICT_HIGH
    if counts["DESIGN_CEILING"] >= 1 or counts["CLAIM_MISMATCH"] >= 1:
        return VERDICT_SPECIALTY
    if counts["IMPORTANCE_RISK"] >= 1:
        return VERDICT_IMPORTANCE
    return VERDICT_NONE


def render_text(basename: str, flags, counts, verd) -> str:
    out = []
    out.append("ACCEPTANCE-READINESS PRE-FLIGHT")
    out.append(f"file: {basename}")
    out.append("note: advisory lexical scan — flags cap the venue tier a design can support;")
    out.append("      not an acceptance prediction and not auto-fixable.")
    out.append("")
    out.append("flags:")
    if flags:
        for lineno, category, label, rationale in flags:
            out.append(f"  L{lineno}  [{category}] {label} :: {rationale}")
    else:
        out.append("  (none)")
    out.append("")
    out.append(
        "summary: design_ceiling={DESIGN_CEILING} unfixable_defect={UNFIXABLE_DEFECT} "
        "importance_risk={IMPORTANCE_RISK} claim_mismatch={CLAIM_MISMATCH} total={total}".format(
            total=sum(counts.values()), **counts
        )
    )
    out.append(f"ceiling: {verd}")
    return "\n".join(out)


def build_report(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    flags = scan(text)
    counts = {c: 0 for c in CATEGORIES}
    for _lineno, category, _label, _rationale in flags:
        counts[category] += 1
    verd = verdict(counts)
    return flags, counts, verd


def main(argv=None):
    ap = argparse.ArgumentParser(description="Acceptance-readiness pre-flight (advisory).")
    ap.add_argument("manuscript", help="path to a manuscript / abstract markdown file")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args(argv)

    path = Path(args.manuscript)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    flags, counts, verd = build_report(path)

    if args.json:
        payload = {
            "file": path.name,
            "advisory": True,
            "fixable_by_ai": False,
            "flags": [
                {"line": ln, "category": cat, "label": lab, "rationale": rat}
                for ln, cat, lab, rat in flags
            ],
            "summary": {**counts, "total": sum(counts.values())},
            "ceiling": verd,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False))
    else:
        print(render_text(path.name, flags, counts, verd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
