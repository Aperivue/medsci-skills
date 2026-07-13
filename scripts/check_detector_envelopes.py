#!/usr/bin/env python3
"""Every detector's JSON output must name the detector that produced it.

A verification layer whose artifacts cannot be traced back to the check that produced
them is only half a verification layer. Until now the qc/*.json envelopes carried the
findings but not the finding's author: a consumer aggregating a project's qc directory —
a dashboard, an audit trail, the review-harvest precision ledger — had to infer the
detector from the *filename*, which is chosen freely at the call site (`--out qc/cs3.json`,
`--out qc/v13_scope.json`). Two runs of one detector under different filenames read as two
detectors; one detector run under an unexpected filename read as none.

So the contract is: any detector that emits JSON emits `"detector": "<its own id>"` in the
envelope. This gate enforces it statically, so a new detector cannot ship without it.

It is deliberately a source check rather than an execution check: detectors need fixtures,
credentials, and sometimes a network to run, but the envelope key is a literal in the
source and can be verified without any of that.

Exit 0 when every JSON-emitting detector self-identifies. With --strict, exit 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Same discovery globs as validate_catalog_consistency.py / gen_detectors_catalog_json.py,
# so this gate covers exactly the counted detector suite.
DETECTOR_GLOBS = ("check_*.py", "detect_*.py", "derive_*.py", "verify_refs.py")

# A detector that never writes JSON has no envelope to label. Listed explicitly rather
# than inferred, so that adding a JSON output to one of them trips this gate.
NO_JSON_OUTPUT = {
    "check_checklist_exists",
    "check_citation_keys",
}


def detectors() -> list[Path]:
    return sorted(
        p for g in DETECTOR_GLOBS for p in (ROOT / "skills").glob(f"*/scripts/{g}")
    )


def audit() -> list[str]:
    problems: list[str] = []
    for p in detectors():
        stem = p.stem
        src = p.read_text(encoding="utf-8")
        writes_json = "json.dump" in src
        identifies = re.search(rf'"detector"\s*:\s*"{re.escape(stem)}"', src) is not None

        if stem in NO_JSON_OUTPUT:
            if writes_json:
                problems.append(
                    f"{p.relative_to(ROOT)}: listed as emitting no JSON, but it calls json.dump* — "
                    'remove it from NO_JSON_OUTPUT and add "detector": "%s" to the envelope' % stem
                )
            continue

        if not writes_json:
            problems.append(
                f"{p.relative_to(ROOT)}: emits no JSON. If that is intended, add '{stem}' to "
                "NO_JSON_OUTPUT in this script (with a reason); otherwise give it a JSON envelope."
            )
        elif not identifies:
            problems.append(
                f'{p.relative_to(ROOT)}: JSON envelope does not carry "detector": "{stem}". '
                "A qc artifact must name the detector that wrote it — the filename is chosen by "
                "the caller and cannot be trusted to identify it."
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="exit 1 on any violation (CI gate)")
    a = ap.parse_args()

    found = detectors()
    problems = audit()
    if problems:
        print(f"DETECTOR_ENVELOPE_DRIFT: {len(problems)} problem(s) across {len(found)} detectors\n")
        for p in problems:
            print(f"  - {p}")
        return 1 if a.strict else 0

    labeled = len(found) - len(NO_JSON_OUTPUT)
    print(f"OK: all {labeled} JSON-emitting detectors self-identify ({len(found)} detectors scanned).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
