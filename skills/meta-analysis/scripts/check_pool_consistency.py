#!/usr/bin/env python3
"""
check_pool_consistency.py — Phase 4 entry gate.

Asserts UID-set equality between (a) the frozen `FINAL_POOL_LOCK.yaml`
and (b) the actual round-3 adjudication TSV that feeds extraction. Blocks
Phase 4 (data extraction) until the two agree.

Why this gate exists
====================
Cross-project precedent (anonymized): an LLM reporting-quality SR carried
five documents that disagreed on INCLUDE/EXCLUDE counts. Three EXCLUDE
rows existed in the downstream extraction sheet without matching INCLUDE
decisions. The drift traced to a post-freeze adjudication change that
propagated to the extraction TSV but not the lock — or the other way
around. Either direction is fatal at peer review.

The gate fails CLOSED: if the lock and the extraction sheet disagree on
even one UID, extraction is blocked.

Inputs
======

  --lock PATH              FINAL_POOL_LOCK.yaml (Phase 3f.5 artifact)
  --adjudication-tsv PATH  round3_adjudication.tsv (Phase 3c artifact)
  --decision-col NAME      column holding the decision label
                           (default: "round3_decision")
  --uid-col NAME           column holding the UID (default: "uid")
  --include-labels LIST    decisions counted as INCLUDE
                           (default: "INCLUDE,INCLUDE_MIXED")
  --out PATH               JSON report (default: qc/pool_consistency.json)

Output JSON
===========

    {
      "submission_safe": false,
      "lock_include_n": 42,
      "tsv_include_n": 43,
      "in_lock_not_tsv": ["UID_007"],
      "in_tsv_not_lock": ["UID_055"],
      "match": false
    }

Exit codes
==========
  0  lock and TSV agree on the UID set
  1  disagreement (PR T1-5 blocks extraction)
  2  invocation error (missing files, missing columns)

Read-only script. No file modification.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def load_lock_uids(lock_path: Path, label_set: list[str]) -> set[str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        print(
            "ERROR: PyYAML required for --lock parsing. pip install PyYAML",
            file=sys.stderr,
        )
        sys.exit(2)
    data = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print(f"ERROR: lock file not a mapping: {lock_path}", file=sys.stderr)
        sys.exit(2)
    # INCLUDE_MIXED maps to mixed_uids in the lock template.
    uids: set[str] = set()
    if "INCLUDE" in label_set:
        uids.update(str(u) for u in (data.get("include_uids") or []))
    if "INCLUDE_MIXED" in label_set:
        uids.update(str(u) for u in (data.get("mixed_uids") or []))
    if "MIXED" in label_set:
        uids.update(str(u) for u in (data.get("mixed_uids") or []))
    if "EXCLUDE" in label_set:
        uids.update(str(u) for u in (data.get("exclude_uids") or []))
    return uids


def load_tsv_uids(
    tsv_path: Path,
    decision_col: str,
    uid_col: str,
    label_set: set[str],
) -> set[str]:
    # Allow .tsv or .csv (sniff by extension).
    delim = "," if tsv_path.suffix.lower() == ".csv" else "\t"
    with tsv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delim)
        if reader.fieldnames is None:
            print(f"ERROR: empty TSV: {tsv_path}", file=sys.stderr)
            sys.exit(2)
        if uid_col not in reader.fieldnames:
            print(
                f"ERROR: uid column {uid_col!r} not in TSV columns "
                f"{reader.fieldnames!r}",
                file=sys.stderr,
            )
            sys.exit(2)
        if decision_col not in reader.fieldnames:
            print(
                f"ERROR: decision column {decision_col!r} not in TSV columns "
                f"{reader.fieldnames!r}",
                file=sys.stderr,
            )
            sys.exit(2)
        uids: set[str] = set()
        for row in reader:
            decision = (row.get(decision_col) or "").strip()
            if decision in label_set:
                uid = (row.get(uid_col) or "").strip()
                if uid:
                    uids.add(uid)
        return uids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 4 entry gate: asserts UID-set equality between the frozen "
            "FINAL_POOL_LOCK.yaml and the round-3 adjudication TSV."
        )
    )
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--adjudication-tsv", type=Path, required=True)
    parser.add_argument("--decision-col", default="round3_decision")
    parser.add_argument("--uid-col", default="uid")
    parser.add_argument(
        "--include-labels",
        default="INCLUDE,INCLUDE_MIXED",
        help="Comma-separated decision labels counted as included.",
    )
    parser.add_argument("--out", type=Path, default=Path("qc/pool_consistency.json"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not args.lock.is_file():
        print(f"ERROR: lock not found: {args.lock}", file=sys.stderr)
        return 2
    if not args.adjudication_tsv.is_file():
        print(f"ERROR: TSV not found: {args.adjudication_tsv}", file=sys.stderr)
        return 2

    labels = [s.strip() for s in args.include_labels.split(",") if s.strip()]
    label_set = set(labels)
    lock_uids = load_lock_uids(args.lock, labels)
    tsv_uids = load_tsv_uids(
        args.adjudication_tsv, args.decision_col, args.uid_col, label_set
    )

    in_lock_only = sorted(lock_uids - tsv_uids)
    in_tsv_only = sorted(tsv_uids - lock_uids)
    match = not in_lock_only and not in_tsv_only

    report = {
        "submission_safe": match,
        "match": match,
        "lock_include_n": len(lock_uids),
        "tsv_include_n": len(tsv_uids),
        "in_lock_not_tsv": in_lock_only,
        "in_tsv_not_lock": in_tsv_only,
        "include_labels": labels,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not args.quiet:
        if match:
            print(f"PASS: lock and TSV agree ({len(lock_uids)} UIDs).")
        else:
            print(
                f"FAIL: lock includes {len(lock_uids)} UIDs, TSV includes "
                f"{len(tsv_uids)} UIDs."
            )
            if in_lock_only:
                print(f"  In lock but not TSV ({len(in_lock_only)}):")
                for u in in_lock_only[:10]:
                    print(f"    - {u}")
                if len(in_lock_only) > 10:
                    print(f"    ... and {len(in_lock_only) - 10} more")
            if in_tsv_only:
                print(f"  In TSV but not lock ({len(in_tsv_only)}):")
                for u in in_tsv_only[:10]:
                    print(f"    - {u}")
                if len(in_tsv_only) > 10:
                    print(f"    ... and {len(in_tsv_only) - 10} more")

    return 0 if match else 1


if __name__ == "__main__":
    sys.exit(main())
