#!/usr/bin/env python3
"""Step B helper — scaffold / validate a per-paper analysis.

The analysis captures *patterns* (study type, applicable reporting guideline, what makes
the sections strong, the concerns a sharp reviewer would raise) — in the agent's own
words, never copied source prose. This helper only scaffolds the JSON shape and validates
it; the content is written by the agent per PLAYBOOK Step B.

Usage:
    python3 reverse_engineer/scripts/analyze_paper.py --scaffold <record_id>
    python3 reverse_engineer/scripts/analyze_paper.py --validate <record_id>
    python3 reverse_engineer/scripts/analyze_paper.py --validate-all
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = RE_DIR.parent
ANALYSIS_DIR = REPO_ROOT / "_corpus" / "analysis"

REQUIRED_KEYS = [
    "record_id",
    "study_type",
    "reporting_guideline",
    "methods_strengths",
    "results_strengths",
    "discussion_strengths",
    "figure_table_notes",
    "reviewer_concerns",
]
LIST_KEYS = [
    "methods_strengths",
    "results_strengths",
    "discussion_strengths",
    "figure_table_notes",
    "reviewer_concerns",
]


def scaffold(rid: str) -> int:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    path = ANALYSIS_DIR / f"{rid}.json"
    if path.exists():
        print(f"exists: {path} (not overwriting)")
        return 0
    template = {
        "record_id": rid,
        "study_type": "",
        "reporting_guideline": "",
        "methods_strengths": [],
        "results_strengths": [],
        "discussion_strengths": [],
        "figure_table_notes": [],
        "reviewer_concerns": [],
        "_instructions": "Fill in your own words. Patterns only — no copied source prose. Remove this key when done.",
    }
    path.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    print(f"scaffolded: {path}")
    return 0


def validate_one(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{path.name}: invalid JSON ({e})"]
    if "_instructions" in data:
        errs.append(f"{path.name}: remove the '_instructions' key when analysis is complete")
    for k in REQUIRED_KEYS:
        if k not in data:
            errs.append(f"{path.name}: missing key '{k}'")
    for k in LIST_KEYS:
        if k in data:
            if not isinstance(data[k], list):
                errs.append(f"{path.name}: '{k}' must be a list")
            elif not data[k]:
                errs.append(f"{path.name}: '{k}' is empty")
    if data.get("reviewer_concerns") == []:
        pass  # already flagged above
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold/validate a per-paper analysis JSON.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scaffold", metavar="RECORD_ID")
    g.add_argument("--validate", metavar="RECORD_ID")
    g.add_argument("--validate-all", action="store_true")
    args = ap.parse_args()

    if args.scaffold:
        return scaffold(args.scaffold)

    if args.validate:
        path = ANALYSIS_DIR / f"{args.validate}.json"
        if not path.exists():
            sys.exit(f"not found: {path}")
        errs = validate_one(path)
    else:
        if not ANALYSIS_DIR.exists():
            print("no analysis directory yet — nothing to validate")
            return 0
        errs = []
        for path in sorted(ANALYSIS_DIR.glob("*.json")):
            errs.extend(validate_one(path))

    if errs:
        print("INVALID:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("OK: analysis shape valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
