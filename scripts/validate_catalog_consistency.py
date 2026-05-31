#!/usr/bin/env python3
"""Catalog-count consistency check (codex Improvement A).

Counts cited in public docs (skill count, reporting-guideline count, journal-
profile counts) were hand-maintained in multiple places and drifted (README once
said "22 guidelines" while orchestrate said "15"; more recently every doc said
"33 reporting guidelines" while only 32 are enumerated and vendored). This makes
the counts a single source of truth and fails CI on drift.

Three layers:
  1. Recompute every count from disk (the real ground truth).
  2. Assert metadata/catalog_counts.json matches disk — the SSOT cannot lie.
  3. Assert the count claims in README / orchestrate / check-reporting match the
     SSOT. Guideline claims are matched by the word "guideline"; the skill self-
     count by the "skills that actually work" tagline — so comparison/marketing
     lines about *other* repos ("400-900 skills", "869 skills") are never touched.

Exit 0 when everything agrees; non-zero on any drift. Stdlib-only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SSOT = ROOT / "metadata" / "catalog_counts.json"


def disk_counts() -> dict[str, int]:
    skills = sum(1 for p in (ROOT / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    checklists = len(list((ROOT / "skills" / "check-reporting" / "references" / "checklists").glob("*.md")))
    find_prof = len(list((ROOT / "skills" / "find-journal" / "references" / "journal_profiles").glob("*.md")))
    write_prof = len(list((ROOT / "skills" / "write-paper" / "references" / "journal_profiles").glob("*.md")))
    return {
        "skills": skills,
        "reporting_guidelines": checklists,
        "journal_profiles_find": find_prof,
        "journal_profiles_write": write_prof,
    }


# Files that carry the catalog-total guideline claim. Scoped explicitly rather
# than scanning all .md: phrases like "PRISMA 2020 guidelines" (version year) or
# "4 reporting guidelines in one tool" (a flow-diagram subset in figure_specs.md)
# are NOT catalog totals and would false-positive a blanket scan. A new doc that
# cites the catalog total must be added here. CHANGELOG is deliberately absent —
# it is a dated record that legitimately quotes superseded counts.
GUIDELINE_CLAIM_FILES = [
    "README.md",
    "skills/orchestrate/SKILL.md",
    "skills/check-reporting/SKILL.md",
    "skills/make-figures/references/reporting_guideline_figure_map.md",
]
SKILLS_TAGLINE_FILES = ["README.md"]


def doc_claims() -> list[tuple[str, int, int, str]]:
    """Return (file, claimed, expected, context) for every count claim found.

    Guideline claims use a 1-2 digit count (4-digit version years like "2020" are
    excluded) followed by "[reporting] guidelines". The skill self-count is matched
    only by the README "skills that actually work" tagline, so comparison lines
    about other repos ("400-900 skills") are never touched.
    """
    out: list[tuple[str, int, int, str]] = []
    truth = disk_counts()
    g = truth["reporting_guidelines"]
    s = truth["skills"]

    guide_re = re.compile(r"\b(\d{1,2})\s+(?:reporting\s+)?guidelines\b")
    skills_re = re.compile(r"\*\*(\d+)\s+skills that actually work")

    for rel in GUIDELINE_CLAIM_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in guide_re.finditer(line):
                out.append((rel, int(m.group(1)), g, f"L{i} guidelines"))

    for rel in SKILLS_TAGLINE_FILES:
        f = ROOT / rel
        if not f.exists():
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in skills_re.finditer(line):
                out.append((rel, int(m.group(1)), s, f"L{i} skills tagline"))
    return out


def main() -> int:
    truth = disk_counts()

    print("=" * 41)
    print(" Catalog-Count Consistency")
    print("=" * 41)
    for k, v in truth.items():
        print(f"  disk: {k} = {v}")

    failures = 0

    # Layer 2 — SSOT must match disk.
    if not SSOT.exists():
        print(f"\nFAIL: SSOT missing: {SSOT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    ssot = json.loads(SSOT.read_text(encoding="utf-8"))
    for key, val in truth.items():
        if ssot.get(key) != val:
            print(f"\nFAIL: SSOT {key}={ssot.get(key)} != disk {val}", file=sys.stderr)
            failures += 1

    # Layer 3 — doc claims must match disk.
    for rel, claimed, expected, ctx in doc_claims():
        if claimed != expected:
            print(f"\nFAIL: {rel} {ctx}: claims {claimed}, expected {expected}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"\nCATALOG_COUNT_DRIFT: {failures} mismatch(es).", file=sys.stderr)
        return 1
    print("\nOK: SSOT and all doc count claims agree with disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
