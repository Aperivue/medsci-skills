#!/usr/bin/env python3
"""Feature-selection-outside-CV leakage gate (self-review Phase 2.5 / data-prep).

For a classifier / NLP / tabular manuscript, if feature selection, vocabulary
construction, log-odds / univariate filtering, or a threshold is chosen on the WHOLE
dataset and only THEN cross-validation is run, the CV performance is optimistically
inflated: the selection has already seen the held-out folds. The fix is to nest the
selection inside each training fold (nested CV). This is a class a statistical
reviewer catches deterministically, and it is distinct from patient-vs-image split
leakage (`model-validation/check_split_leakage.py`).

Verdict:
  CV_SELECTION_LEAKAGE (Major)  a feature-selection / vocabulary / threshold step
                                co-occurs with a cross-validation description AND no
                                fold-nesting disclosure ("within each fold", "nested
                                CV", "inside the training fold") is present. The
                                headline CV metric is likely optimistic.

Conservative by construction: fires only when BOTH a selection token AND a CV token
appear AND no nesting-disclosure token is anywhere in the document. A single
"within each training fold" / "nested cross-validation" sentence suppresses it.

Exit codes: 0 clean/report-only, 1 with --strict when any Major, 2 usage. Stdlib-only.

Usage:
    python3 check_cv_leakage.py --manuscript manuscript.md \
        [--out qc/cv_leakage.json] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A data-driven selection / construction step that must be nested inside CV.
SELECTION = re.compile(
    r"\bfeature\s+selection\b|\bselected\s+(?:the\s+)?(?:top\s+)?\d+\s+(?:features|variables|predictors)"
    r"|\blog[-\s]?odds\b|\bvocabulary\s+(?:construction|was\s+built|building)\b|\bbuilt\s+(?:a\s+)?vocabulary"
    r"|\bfeature\s+ranking\b|\bunivariate\s+(?:filter|screening|selection)\b|\btop[-\s]?k\s+features"
    r"|\bmutual[-\s]information\s+(?:selection|ranking)\b|\bchi[-\s]?square(?:d)?\s+selection"
    r"|\b(?:selected|chose|retained|kept)\s+(?:the\s+)?(?:most\s+)?(?:informative|discriminative|predictive)\s+features"
    r"|\bthreshold(?:ed|ing)?\b[^.\n]{0,40}\b(?:on|over|across|using)\s+the\s+(?:entire|full|whole|complete)\s+(?:data|dataset|cohort|corpus)"
    r"|\b(?:LASSO|elastic[-\s]net|recursive\s+feature\s+elimination|RFE|Boruta)\b",
    re.IGNORECASE)

# A cross-validation evaluation.
CV = re.compile(
    r"\bcross[-\s]?validat(?:ion|ed)\b|\b\d+[-\s]?fold\b|\bk[-\s]?fold\b"
    r"|\bleave[-\s]one[-\s]out\b|\bLOOCV\b|\bstratified\s+(?:\d+[-\s]?)?fold",
    re.IGNORECASE)

# Disclosure that the selection is correctly nested inside the CV training folds.
NESTING = re.compile(
    r"\bnested\s+(?:cross[-\s]?validat|CV)\b"
    r"|\bwithin\s+each\s+(?:training\s+)?fold\b|\binside\s+(?:the\s+)?training\s+(?:fold|partition|split)"
    r"|\bper[-\s]?fold\b|\bfold[-\s]specific\b|\bfor\s+each\s+(?:training\s+)?fold\b"
    r"|\bon\s+the\s+training\s+(?:fold|partition|split|set)\s+only\b"
    r"|\brefit(?:ted)?\s+within\b|\brepeated\s+(?:in|within|inside)\s+each\s+fold"
    r"|\bselection\s+was\s+(?:performed|done|repeated)\s+(?:in|within|inside)\s+each\b",
    re.IGNORECASE)


def check(text: str) -> list[dict]:
    sel = SELECTION.search(text)
    cv = CV.search(text)
    if not (sel and cv):
        return []
    if NESTING.search(text):
        return []  # nesting is disclosed
    return [{
        "verdict": "CV_SELECTION_LEAKAGE",
        "severity": "Major",
        "detail": (f"a data-driven selection step ('{sel.group(0).strip()}') co-occurs with "
                   f"cross-validation ('{cv.group(0).strip()}') but no fold-nesting is disclosed "
                   f"(no 'within each fold' / 'nested CV'); if the selection was fit on the full "
                   f"dataset the CV metric is optimistically inflated — nest it in each training fold"),
        "where": text[max(0, sel.start() - 30):sel.end() + 50].replace("\n", " ").strip()[:170],
    }]


def analyze(manuscript: str) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"))
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {"n_claims": len(claims), "n_major": n_major, "n_flag": len(claims) - n_major,
                    "verdict": "MAJOR_CANDIDATE" if n_major else "OK"},
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | no feature-selection-outside-CV leakage detected |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Feature-selection-outside-CV leakage gate (Phase 2.5 / data-prep).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)

    if not args.quiet:
        print("=" * 44)
        print(" CV selection-leakage (§2.5 / data-prep)")
        print("=" * 44)
        print(render(result))
        print()
        if result["summary"]["n_major"]:
            print("MAJOR candidate: a selection step co-occurs with CV and no fold-nesting is disclosed.")
        else:
            print("OK: no feature-selection-outside-CV leakage detected.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_cv_leakage", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
