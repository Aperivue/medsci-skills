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
# Only these words decide a label when they LEAD a longer label
# ("Exclude: wrong study type", "Excluded - not eligible"). yes/no/y/n/1/0/
# true/false count only as the whole label: "No decision yet", "No consensus",
# "0 - pending", "N/A" and "Yes (pending)" are not adjudications.
LEADING_INCLUDE = {"include", "included", "eligible"}
LEADING_EXCLUDE = {"exclude", "excluded", "ineligible"}


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

    The whole normalized label is tried first (`include-qualitative`, `no`, `Y`).
    Only an unambiguous decision word may decide a longer label as its leading
    word (`Exclude: wrong study type` -> `exclude`); yes/no/y/n/1/0/true/false
    must be the whole label, so `No decision yet` or `N/A` is not an exclusion.
    A substring test would read `y`/`1`/`eligible` inside `Exclude: wrong study
    type` or `ineligible` and count an excluded record as included. Anything
    else is `unknown` -- the caller refuses to reconcile rather than guess.
    """
    v = " ".join(value.split()).lower()
    if not v:
        return "unknown"
    # A 0/1 column read through pandas or Excel as floats is written "1.0"/"0.0".
    num = re.fullmatch(r"([01])\.0+", v)
    if num:
        v = num.group(1)
    if v in INCLUDE_VALUES:
        return "include"
    if v in EXCLUDE_VALUES:
        return "exclude"
    lead = re.match(r"[a-z0-9]+", v)
    word = lead.group(0) if lead else ""
    if word in LEADING_INCLUDE:
        return "include"
    if word in LEADING_EXCLUDE:
        return "exclude"
    return "unknown"


def digit_key(value: str) -> str:
    """First digit run of an ID (`Study 1` -> `1`), else the ID itself."""
    match = re.search(r"\d+", value)
    return match.group(0) if match else value


def style_key(value: str) -> str:
    """An ID with case, whitespace and punctuation removed (`Smith 2020` ->
    `smith2020`, `#12` -> `12`). Every letter and digit is kept, so
    `Smith2020_1` and `Smith2020_2` stay distinct (no digit-run collapse)."""
    return "".join(ch for ch in value.lower() if ch.isalnum())


def style_matches(ids: set[str], universe: set[str]) -> dict[str, str]:
    """{id: other_id} for each id in `ids` whose style_key equals that of
    exactly one record in `universe` other than itself."""
    by_style: dict[str, list[str]] = {}
    for u in universe:
        by_style.setdefault(style_key(u), []).append(u)
    out: dict[str, str] = {}
    for i in ids:
        cands = [u for u in by_style.get(style_key(i), []) if u != i]
        if len(cands) == 1:
            out[i] = cands[0]
    return out


def match_table1_ids(
    table1_ids: set[str], qualitative: set[str], known: set[str]
) -> tuple[set[str], dict[str, str], dict[str, str]]:
    """Map Table 1 IDs onto qualitative IDs. A verbatim match wins. Next, an ID
    that differs from exactly one screened or consensus record only in case,
    whitespace or punctuation (`Smith 2020` vs `Smith2020`) is that record --
    whether or not it is qualitative, so an excluded record still surfaces as
    TABLE1_NOT_IN_QUALITATIVE. A Table 1 ID
    that verbatim names any other screened or consensus record (e.g. an
    excluded `Smith2020_2`) is never re-mapped. Otherwise a Table 1 ID is
    matched by its first digit run (`Study 1` -> `1`, the matching every table
    used before IDs became verbatim) only when exactly one record among ALL
    screened and consensus IDs (`known`) has that digit run and that record is
    in the qualitative set. Candidates come from every known record, not only
    the qualitative ones, so an excluded sibling report (`Smith2020_2` beside an
    included `Smith2020_1`) makes the digit run ambiguous instead of collapsing
    onto the included sibling. An ambiguous or absent digit run leaves the ID
    unmatched, so it is reported rather than silently merged. Returns the mapped
    set, the {table1_id: record_id} pairs matched by ID style, and the
    {table1_id: qualitative_id} pairs matched by digit run."""
    universe = set(known) | set(qualitative)
    by_key: dict[str, list[str]] = {}
    for q in universe:
        by_key.setdefault(digit_key(q), []).append(q)
    via_style = style_matches({t for t in table1_ids if t not in universe}, universe)
    mapped: set[str] = set()
    via_digits: dict[str, str] = {}
    for t in table1_ids:
        if t in universe:
            mapped.add(t)
            continue
        if t in via_style:
            mapped.add(via_style[t])
            continue
        cands = by_key.get(digit_key(t), [])
        if len(cands) == 1 and cands[0] in qualitative:
            mapped.add(cands[0])
            via_digits[t] = cands[0]
        else:
            mapped.add(t)
    return mapped, via_style, via_digits


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
            f"{path}: unrecognized decision label(s): {detail}. Accepted as the whole label: "
            f"include={sorted(INCLUDE_VALUES)} exclude={sorted(EXCLUDE_VALUES)}; as the leading "
            f"word of a longer label: include={sorted(LEADING_INCLUDE)} "
            f"exclude={sorted(LEADING_EXCLUDE)}"
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
        consensus_decisions = {}
        consensus_exclude = set()
        consensus_include = set()

    if args.table1:
        table1_ids, _ = ids_from_table(
            Path(args.table1), args.table1_id_col, None, include_only=False, require_decisions=False
        )
    else:
        table1_ids = set()

    qualitative = (screening_include - consensus_exclude) | consensus_include
    known_ids = set(screening_decisions) | set(consensus_decisions)
    bivariate, table1_matched_by_style, table1_matched_by_digits = match_table1_ids(
        table1_ids, qualitative, known_ids
    )
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
        "table1_matched_by_id_style": {t: table1_matched_by_style[t] for t in sorted(table1_matched_by_style)},
        "table1_matched_by_digit_run": {t: table1_matched_by_digits[t] for t in sorted(table1_matched_by_digits)},
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
        # Advisory only: a lost ID that differs from a consensus ID only in case,
        # whitespace or punctuation is probably the same record written in another
        # ID style. It is NOT matched -- the loss still blocks until the IDs agree.
        style_pairs = style_matches(stage_transfer_loss, consensus_ids - screening_include)
        issue = {
            "code": "STAGE_TRANSFER_LOSS",
            "ids": sorted(stage_transfer_loss, key=lambda x: (len(x), x)),
            "detail": (
                "Included at screening but absent from the consensus artifact -- neither "
                "included nor excluded, so no adjudication is recorded. Either restore these "
                "records to the consensus stage, or record an explicit exclusion decision for "
                "each. Do not leave them to flow into the narrative-only set. IDs are "
                "compared verbatim: if the two sheets write the same record differently "
                "(e.g. '#12' vs '12'), make the ID style match."
            ),
        }
        if style_pairs:
            issue["likely_id_style_mismatch"] = {k: style_pairs[k] for k in sorted(style_pairs)}
            issue["detail"] += (
                " Likely cause for " + ", ".join(f"{k!r} (consensus has {v!r})"
                                                 for k, v in sorted(style_pairs.items()))
                + ": probably the same record written in another ID style; make the IDs match."
            )
        payload["blocking_issues"].append(issue)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["totals"], indent=2))
    return 1 if payload["blocking_issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
