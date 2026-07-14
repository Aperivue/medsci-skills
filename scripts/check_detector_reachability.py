#!/usr/bin/env python3
"""A detector nothing calls is a detector that never runs.

We count 64 detectors. We test them in CI. We give each one a challenge card with a positive and a
negative fixture, and a JSON envelope that names itself. All of that proves a detector **works**.

None of it proves the skill **calls** it.

On 2026-07-14 a sweep found five — `check_table_percentages`, `check_reported_p_from_counts`,
`check_dta_denominators`, `check_nested_group_comparison`, `check_paired_difference_estimator` —
that were shipped in v5.20.0 with challenge cards, CI steps, catalog entries and a release note, and
that **`self-review/SKILL.md` never mentioned**. They passed every gate we had and had never once run
on a real manuscript. They were counted in the number we publish.

This is the same disease as a green test that would not catch the defect, one level up: the gate was
verifying the tool instead of the *use* of the tool.

A detector is REACHABLE if:
  * some SKILL.md invokes it by filename, or
  * a non-test script that is itself reachable invokes it (e.g. a preflight gate that runs a bundle).

A challenge card, a test, or a CI step does NOT make it reachable. Those prove it works in a
laboratory. They are exactly what these five had.

Usage:
    check_detector_reachability.py [--strict]

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

# Same discovery globs as gen_detectors_catalog_json.py / validate_catalog_consistency.py: whatever
# counts as a detector for the number we publish must count as one here, or the gate has a hole
# exactly where the marketing is.
DETECTOR_GLOBS = ("check_*.py", "detect_*.py", "derive_*.py")
EXTRA_DETECTORS = ("verify-refs/scripts/verify_refs.py",)

# Files that prove a detector WORKS but never cause it to RUN for a user.
TEST_MARKERS = ("/tests/", "_challenge/", "/challenge/")

# A detector may legitimately be reached only through another script — but that script has to be one
# a skill actually runs. Named here so the exemption is a decision, not an accident.
BUNDLE_RUNNERS = {
    "preflight_gate.py",       # sync-submission: runs a bundle of checks before upload
    "pre_submission_gate.sh",  # manage-refs: the 5-stage submission gate
}


def detectors() -> list[Path]:
    out: list[Path] = []
    for g in DETECTOR_GLOBS:
        out += sorted(SKILLS.glob(f"*/scripts/{g}"))
    for extra in EXTRA_DETECTORS:
        p = SKILLS / extra
        if p.is_file():
            out.append(p)
    return sorted(set(out))


def invocation_sites() -> list[Path]:
    """Everything that can cause a detector to run for a real user."""
    sites = list(SKILLS.glob("*/SKILL.md"))
    for name in BUNDLE_RUNNERS:
        sites += list(SKILLS.glob(f"*/scripts/{name}"))
    return sites


def unreachable() -> list[tuple[str, str, list[str]]]:
    sites = invocation_sites()
    blobs = {p: p.read_text(encoding="utf-8", errors="ignore") for p in sites}

    out: list[tuple[str, str, list[str]]] = []
    for d in detectors():
        name = d.name
        skill = d.parts[d.parts.index("skills") + 1]

        callers = [p for p, text in blobs.items() if name in text]
        if callers:
            continue

        # Where IS it mentioned? That tells the maintainer whether it was forgotten or is new.
        mentions = [
            str(p.relative_to(ROOT))
            for p in SKILLS.rglob("*")
            if p.is_file() and p != d and not p.is_dir()
            and p.suffix in {".md", ".sh", ".py", ".yml"}
            and name in p.read_text(encoding="utf-8", errors="ignore")
        ]
        lab_only = [m for m in mentions if any(t in "/" + m for t in TEST_MARKERS)]
        out.append((skill, name, lab_only or mentions))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true", help="exit 1 if any detector is unreachable")
    a = ap.parse_args()

    total = len(detectors())
    bad = unreachable()

    if not bad:
        print(f"OK: all {total} detectors are invoked by a SKILL.md (directly or via a bundle runner).")
        return 0

    print(f"DETECTOR_UNREACHABLE: {len(bad)} of {total} detectors are never invoked by any skill.\n")
    for skill, name, where in bad:
        print(f"  {skill}/{name}")
        if where:
            shown = ", ".join(where[:3])
            print(f"      mentioned only in: {shown}")
            print("      — a challenge card and a CI step prove it WORKS. They do not make it RUN.")
        else:
            print("      — not mentioned anywhere. Dead code.")
        print()
    print("Fix: invoke it from its skill's SKILL.md (the phase where it belongs), or — if it is")
    print("reached through a bundle runner — add that runner to BUNDLE_RUNNERS in this script.")
    print("\nA detector that never runs is still counted in the number we publish. That makes the")
    print("number a claim about our repository rather than about anyone's manuscript.")
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
