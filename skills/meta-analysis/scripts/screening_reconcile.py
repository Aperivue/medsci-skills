#!/usr/bin/env python3
"""Reconcile meta-analysis screening ID sets into a canonical JSON artifact."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


INCLUDE_VALUES = {"include", "included", "yes", "y", "1", "true", "eligible", "include-qualitative"}
EXCLUDE_VALUES = {"exclude", "excluded", "no", "n", "0", "false", "ineligible"}


def read_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh, delimiter=delimiter)]


def find_col(rows: list[dict[str, str]], candidates: list[str]) -> str | None:
    if not rows:
        return None
    lower = {k.lower(): k for k in rows[0].keys()}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    for key in rows[0].keys():
        lk = key.lower()
        if any(cand.lower() in lk for cand in candidates):
            return key
    return None


def norm_id(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    match = re.search(r"\d+", value)
    return match.group(0) if match else value


def decision_kind(value: str) -> str:
    v = value.strip().lower()
    if any(token in v for token in INCLUDE_VALUES):
        return "include"
    if any(token in v for token in EXCLUDE_VALUES):
        return "exclude"
    return "unknown"


def ids_from_table(path: Path, id_col_arg: str | None, decision_col_arg: str | None, include_only: bool) -> tuple[set[str], dict[str, str]]:
    rows = read_table(path)
    id_col = id_col_arg or find_col(rows, ["id", "record_id", "study_id", "ref_id"])
    if not id_col:
        raise ValueError(f"Could not identify ID column in {path}")
    decision_col = decision_col_arg or find_col(rows, ["decision", "verdict", "include", "screening", "consensus", "outcome"])
    ids: set[str] = set()
    decisions: dict[str, str] = {}
    for row in rows:
        rid = norm_id(row.get(id_col, ""))
        if not rid:
            continue
        decision = row.get(decision_col, "") if decision_col else ""
        kind = decision_kind(decision)
        decisions[rid] = decision
        if include_only:
            if kind == "include":
                ids.add(rid)
        else:
            ids.add(rid)
    return ids, decisions


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile MA screening ID sets.")
    parser.add_argument("--screening", required=True, help="TSV/CSV with screening decisions")
    parser.add_argument("--consensus", help="TSV/CSV with final consensus decisions")
    parser.add_argument("--table1", help="TSV/CSV containing bivariate/Table 1 study IDs")
    parser.add_argument("--output", default="2_Screening/screening_consensus_final.json")
    parser.add_argument("--screening-id-col")
    parser.add_argument("--screening-decision-col")
    parser.add_argument("--consensus-id-col")
    parser.add_argument("--consensus-decision-col")
    parser.add_argument("--table1-id-col")
    args = parser.parse_args()

    screening_path = Path(args.screening)
    screening_include, screening_decisions = ids_from_table(
        screening_path, args.screening_id_col, args.screening_decision_col, include_only=True
    )

    if args.consensus:
        consensus_ids, consensus_decisions = ids_from_table(
            Path(args.consensus), args.consensus_id_col, args.consensus_decision_col, include_only=False
        )
        consensus_exclude = {rid for rid, dec in consensus_decisions.items() if decision_kind(dec) == "exclude"}
        consensus_include = {rid for rid, dec in consensus_decisions.items() if decision_kind(dec) == "include"}
    else:
        consensus_ids = set()
        consensus_exclude = set()
        consensus_include = set()

    if args.table1:
        table1_ids, _ = ids_from_table(Path(args.table1), args.table1_id_col, None, include_only=False)
    else:
        table1_ids = set()

    qualitative = (screening_include - consensus_exclude) | consensus_include
    bivariate = table1_ids
    narrative_only = qualitative - bivariate

    payload = {
        "schema_version": 1,
        "sources": {
            "screening": str(screening_path),
            "consensus": args.consensus,
            "table1": args.table1,
        },
        "sets": {
            "screening_include": sorted(screening_include, key=lambda x: (len(x), x)),
            "consensus_exclude": sorted(consensus_exclude, key=lambda x: (len(x), x)),
            "consensus_include": sorted(consensus_include, key=lambda x: (len(x), x)),
            "qualitative": sorted(qualitative, key=lambda x: (len(x), x)),
            "bivariate": sorted(bivariate, key=lambda x: (len(x), x)),
            "narrative_only": sorted(narrative_only, key=lambda x: (len(x), x)),
        },
        "totals": {
            "k_screening_include": len(screening_include),
            "k_consensus_exclude": len(consensus_exclude),
            "k_consensus_include": len(consensus_include),
            "k_qualitative": len(qualitative),
            "k_bivariate": len(bivariate),
            "k_narrative_only": len(narrative_only),
        },
        "blocking_issues": [],
    }

    if bivariate and not bivariate <= qualitative:
        payload["blocking_issues"].append(
            {
                "code": "TABLE1_NOT_IN_QUALITATIVE",
                "ids": sorted(bivariate - qualitative, key=lambda x: (len(x), x)),
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["totals"], indent=2))
    return 1 if payload["blocking_issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
