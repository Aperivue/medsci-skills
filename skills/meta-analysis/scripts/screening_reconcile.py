#!/usr/bin/env python3
"""Reconcile meta-analysis screening ID sets into a canonical JSON artifact.

Exit codes: 0 reconciled, 1 blocking issue (e.g. STAGE_TRANSFER_LOSS),
2 a screening/consensus decision label is unrecognized (or no decision column),
so the record cannot be classified as include or exclude.
"""

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
    """Record IDs are compared verbatim (surrounding whitespace trimmed, inner runs
    collapsed). No digit extraction: `Smith2020_1` and `Smith2020_2` are different
    records, and reducing both to `2020` hides a lost study."""
    return " ".join(value.split())


def decision_kind(value: str) -> str:
    """Classify a decision label by EXACT token, never by substring.

    The whole normalized label is tried first (`include-qualitative`), then its
    leading word (`Exclude: wrong study type` -> `exclude`). A substring test would
    read `y`/`1`/`eligible` inside `Exclude: wrong study type` or `ineligible` and
    count an excluded record as included. Anything else is `unknown` -- the caller
    refuses to reconcile rather than guess.
    """
    v = value.strip().lower()
    if not v:
        return "unknown"
    lead = re.match(r"[a-z0-9]+", v)
    for candidate in (v, lead.group(0) if lead else ""):
        if candidate in INCLUDE_VALUES:
            return "include"
        if candidate in EXCLUDE_VALUES:
            return "exclude"
    return "unknown"


class UnrecognizedDecisions(ValueError):
    pass


def ids_from_table(
    path: Path,
    id_col_arg: str | None,
    decision_col_arg: str | None,
    include_only: bool,
    require_decisions: bool = True,
) -> tuple[set[str], dict[str, str]]:
    rows = read_table(path)
    id_col = id_col_arg or find_col(rows, ["id", "record_id", "study_id", "ref_id"])
    if not id_col:
        raise ValueError(f"Could not identify ID column in {path}")
    decision_col = decision_col_arg or find_col(rows, ["decision", "verdict", "include", "screening", "consensus", "outcome"])
    if require_decisions and rows and not decision_col:
        raise UnrecognizedDecisions(
            f"{path}: no decision column found; pass the matching --*-decision-col"
        )
    ids: set[str] = set()
    decisions: dict[str, str] = {}
    unrecognized: dict[str, list[str]] = {}
    for row in rows:
        rid = norm_id(row.get(id_col, ""))
        if not rid:
            continue
        decision = row.get(decision_col, "") if decision_col else ""
        kind = decision_kind(decision)
        if require_decisions and kind == "unknown":
            unrecognized.setdefault(decision.strip() or "<blank>", []).append(rid)
        decisions[rid] = decision
        if include_only:
            if kind == "include":
                ids.add(rid)
        else:
            ids.add(rid)
    if unrecognized:
        detail = "; ".join(f"{label!r} (ids: {', '.join(v[:5])}{', ...' if len(v) > 5 else ''})"
                           for label, v in sorted(unrecognized.items()))
        raise UnrecognizedDecisions(
            f"{path}: unrecognized decision label(s): {detail}. Accepted (exact, or as the "
            f"leading word): include={sorted(INCLUDE_VALUES)} exclude={sorted(EXCLUDE_VALUES)}"
        )
    return ids, decisions


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile MA screening ID sets.")
    parser.add_argument("--screening", required=True, help="TSV/CSV with screening decisions")
    parser.add_argument("--consensus", help="TSV/CSV with final consensus decisions")
    parser.add_argument("--table1", help="TSV/CSV containing bivariate/Table 1 study IDs")
    parser.add_argument("--output", default="2_Screening/screening_consensus.json")
    parser.add_argument("--screening-id-col")
    parser.add_argument("--screening-decision-col")
    parser.add_argument("--consensus-id-col")
    parser.add_argument("--consensus-decision-col")
    parser.add_argument("--table1-id-col")
    args = parser.parse_args()

    screening_path = Path(args.screening)
    try:
        screening_include, screening_decisions = ids_from_table(
            screening_path, args.screening_id_col, args.screening_decision_col, include_only=True
        )
        if args.consensus:
            consensus_ids, consensus_decisions = ids_from_table(
                Path(args.consensus), args.consensus_id_col, args.consensus_decision_col, include_only=False
            )
    except UnrecognizedDecisions as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.consensus:
        consensus_exclude = {rid for rid, dec in consensus_decisions.items() if decision_kind(dec) == "exclude"}
        consensus_include = {rid for rid, dec in consensus_decisions.items() if decision_kind(dec) == "include"}
    else:
        consensus_ids = set()
        consensus_exclude = set()
        consensus_include = set()

    if args.table1:
        table1_ids, _ = ids_from_table(
            Path(args.table1), args.table1_id_col, None, include_only=False, require_decisions=False
        )
    else:
        table1_ids = set()

    qualitative = (screening_include - consensus_exclude) | consensus_include
    bivariate = table1_ids
    narrative_only = qualitative - bivariate

    # A record that passed screening and was EXCLUDED at consensus carries a decision.
    # A record that passed screening and is ABSENT from the consensus artifact carries
    # none -- it fell out of the pipeline. Both leave `consensus_exclude` empty for that
    # id, so without this split the second case flows into `qualitative` and then into
    # `narrative_only`, where it is indistinguishable from a study legitimately lacking
    # extractable data. That is how an eligible study is lost silently.
    if args.consensus:
        stage_transfer_loss = screening_include - consensus_ids
    else:
        stage_transfer_loss = set()
    narrative_only_unadjudicated = narrative_only & stage_transfer_loss
    narrative_only_adjudicated = narrative_only - stage_transfer_loss

    payload = {
        "schema_version": 2,
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
            "narrative_only_adjudicated": sorted(narrative_only_adjudicated, key=lambda x: (len(x), x)),
            "narrative_only_unadjudicated": sorted(narrative_only_unadjudicated, key=lambda x: (len(x), x)),
            "stage_transfer_loss": sorted(stage_transfer_loss, key=lambda x: (len(x), x)),
        },
        "totals": {
            "k_screening_include": len(screening_include),
            "k_consensus_exclude": len(consensus_exclude),
            "k_consensus_include": len(consensus_include),
            "k_qualitative": len(qualitative),
            "k_bivariate": len(bivariate),
            "k_narrative_only": len(narrative_only),
            "k_narrative_only_adjudicated": len(narrative_only_adjudicated),
            "k_narrative_only_unadjudicated": len(narrative_only_unadjudicated),
            "k_stage_transfer_loss": len(stage_transfer_loss),
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

    if stage_transfer_loss:
        payload["blocking_issues"].append(
            {
                "code": "STAGE_TRANSFER_LOSS",
                "ids": sorted(stage_transfer_loss, key=lambda x: (len(x), x)),
                "detail": (
                    "Included at screening but absent from the consensus artifact -- neither "
                    "included nor excluded, so no adjudication is recorded. Either restore these "
                    "records to the consensus stage, or record an explicit exclusion decision for "
                    "each. Do not leave them to flow into the narrative-only set."
                ),
            }
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["totals"], indent=2))
    return 1 if payload["blocking_issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
