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

It also fails when the lock disagrees with ITSELF or the TSV with itself,
because `final_pool_n` is the k the manuscript reports (SKILL.md 3f.5):
  * `final_pool_n` != |include_uids ∪ mixed_uids|, or `include_count` /
    `exclude_count` / `mixed_count` != the length of the matching UID list
    (each checked only when the field is present);
  * a non-empty `sha256` that does not equal SHA-256 of the sorted
    include+exclude+mixed UIDs joined with newlines (template recipe);
  * a UID listed in more than one of include/exclude/mixed in the lock;
  * a UID carrying two different decisions in the adjudication TSV.

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
      "lock_integrity_errors": ["final_pool_n is 10 but include_uids ∪ mixed_uids has 3"],
      "tsv_conflicting_uids": {"UID_003": ["EXCLUDE", "INCLUDE"]},
      "match": false
    }

Exit codes
==========
  0  lock and TSV agree on the UID set, and both are internally consistent
  1  disagreement, lock integrity error, or conflicting TSV decisions
     (PR T1-5 blocks extraction)
  2  invocation error (missing files, missing columns)

Read-only script. No file modification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


def load_lock(lock_path: Path) -> dict:
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
    return data


def _uid_list(data: dict, key: str) -> list[str]:
    return [str(u).strip() for u in (data.get(key) or [])]


def lock_integrity_errors(data: dict) -> list[str]:
    """Checks the lock against itself: declared counts vs UID lists, the
    tamper-evidence hash, and UIDs filed under more than one decision."""
    errors: list[str] = []
    inc = _uid_list(data, "include_uids")
    exc = _uid_list(data, "exclude_uids")
    mix = _uid_list(data, "mixed_uids")

    pool = set(inc) | set(mix)
    declared = data.get("final_pool_n")
    if declared is not None and _as_int(declared) != len(pool):
        errors.append(
            f"final_pool_n is {declared} but include_uids ∪ mixed_uids has {len(pool)} UID(s)"
        )
    for field, lst, name in (
        ("include_count", inc, "include_uids"),
        ("exclude_count", exc, "exclude_uids"),
        ("mixed_count", mix, "mixed_uids"),
    ):
        val = data.get(field)
        if val is not None and _as_int(val) != len(lst):
            errors.append(f"{field} is {val} but {name} lists {len(lst)} UID(s)")
    for name, lst in (("include_uids", inc), ("exclude_uids", exc), ("mixed_uids", mix)):
        dups = sorted({u for u in lst if lst.count(u) > 1})
        if dups:
            errors.append(f"{name} lists UID(s) more than once: {', '.join(dups[:10])}")
    sets = {"include": set(inc), "exclude": set(exc), "mixed": set(mix)}
    names = sorted(sets)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            both = sorted(sets[a] & sets[b])
            if both:
                errors.append(f"UID(s) in both {a}_uids and {b}_uids: {', '.join(both[:10])}")

    recorded = str(data.get("sha256") or "").strip().lower()
    if recorded:
        actual = hashlib.sha256("\n".join(sorted(inc + exc + mix)).encode("utf-8")).hexdigest()
        if recorded != actual:
            errors.append(
                f"sha256 {recorded[:16]}... does not match the UID lists ({actual[:16]}...); "
                f"the lock was edited after freezing, or the hash was never computed"
            )
    return errors


def _as_int(value) -> object:
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def load_lock_uids(lock_path: Path, label_set: list[str], data: dict | None = None) -> set[str]:
    if data is None:
        data = load_lock(lock_path)
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
    conflicts: dict[str, list[str]] | None = None,
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
        seen: dict[str, set[str]] = {}
        for row in reader:
            decision = (row.get(decision_col) or "").strip()
            uid = (row.get(uid_col) or "").strip()
            if uid and decision:
                seen.setdefault(uid, set()).add(decision)
            if decision in label_set and uid:
                uids.add(uid)
        if conflicts is not None:
            # One UID, rows that disagree on pool membership (one decision in the
            # label set, another not): the sheet cannot say whether the study is in
            # the pool, whatever set comparison then shows. Rows that differ only
            # in wording on the same side ("EXCLUDE" / "EXCLUDE (duplicate)") are
            # not a conflict.
            for uid, decs in seen.items():
                if len({d in label_set for d in decs}) > 1:
                    conflicts[uid] = sorted(decs)
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
    lock_data = load_lock(args.lock)
    lock_uids = load_lock_uids(args.lock, labels, lock_data)
    integrity = lock_integrity_errors(lock_data)
    conflicts: dict[str, list[str]] = {}
    tsv_uids = load_tsv_uids(
        args.adjudication_tsv, args.decision_col, args.uid_col, label_set, conflicts
    )

    in_lock_only = sorted(lock_uids - tsv_uids)
    in_tsv_only = sorted(tsv_uids - lock_uids)
    match = not in_lock_only and not in_tsv_only and not integrity and not conflicts

    report = {
        "submission_safe": match,
        "match": match,
        "lock_include_n": len(lock_uids),
        "tsv_include_n": len(tsv_uids),
        "in_lock_not_tsv": in_lock_only,
        "in_tsv_not_lock": in_tsv_only,
        "lock_integrity_errors": integrity,
        "tsv_conflicting_uids": {u: conflicts[u] for u in sorted(conflicts)},
        "include_labels": labels,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"detector": "check_pool_consistency", **report}, indent=2), encoding="utf-8")

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
            if integrity:
                print(f"  Lock integrity errors ({len(integrity)}):")
                for e in integrity:
                    print(f"    - {e}")
            if conflicts:
                print(f"  UIDs with conflicting TSV decisions ({len(conflicts)}):")
                for u in sorted(conflicts)[:10]:
                    print(f"    - {u}: {', '.join(conflicts[u])}")

    return 0 if match else 1


if __name__ == "__main__":
    sys.exit(main())
