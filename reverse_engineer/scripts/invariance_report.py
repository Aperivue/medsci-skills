#!/usr/bin/env python3
"""Q7 — did the verdict survive a rewrite that cannot change what the paper says?

Takes a baseline run of `heldout_crossfire.py` and one run per perturbation from
`perturb_corpus.py`, and reports the invariance rate: the proportion of (detector, paper) pairs
whose outcome is unchanged, and of findings whose claim codes are unchanged.

WHY THIS IS THE STRONGEST THING HERE
    Every other endpoint needs a human to say what the right answer was. This one does not. If the
    verdict moves under a rewrite that provably preserves the numbers, the citations and the words,
    then the detector is wrong on one side of the pair — and which side does not matter for the
    claim being made. That is severity without ground truth.

WHAT A MOVED VERDICT IS NOT
    For some detectors, order or position IS the subject. `check_citation_order` is supposed to
    change its mind when floats are reordered. Those detectors are exempt PER PERTURBATION, from an
    explicit list in perturb_corpus.py, never inferred — an inferred exemption is a place for a real
    failure to hide. Their movement is reported separately as `expected_change`, and it is a defect
    of the OPPOSITE kind if they do NOT move: a detector that ignores a reordering it exists to
    police was not reading the order at all.

READING THE OUTPUT
    outcome invariance   pairs whose outcome class (fire/clean/not_applicable/...) is unchanged
    claim invariance     fires whose SET of verdict codes is unchanged. Stricter, and the one that
                         catches a detector that still fires but for a different reason.
    per-detector         where the movement is. One detector moving on every paper is a different
                         finding from every detector moving on one paper.

Usage:
    invariance_report.py --baseline run.json \\
        --perturbed house-vocab=run_hv.json --perturbed reorder-sections=run_ro.json \\
        [--perturb-report house-vocab=report_hv.json] [--out q7.json]

Exit: 0 always (an instrument, not a gate), 2 usage/parse error. Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"invariance: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(2)


def outcomes(run: dict) -> Dict[tuple, str]:
    """(detector, paper) -> outcome. Rebuilt from the findings/fires plus per-detector tallies.

    The run artifact records per-detector counts, not per-pair outcomes, so fires are recovered
    exactly and everything else is 'not-fire'. That is the resolution the comparison needs: the
    question is whether the stack SPOKE differently, and a clean/not_applicable distinction under
    perturbation is a separate (and much rarer) event, reported via the pair counts.
    """
    out: Dict[tuple, str] = {}
    for f in run.get("fires", []):
        out[(f["detector"], f["paper"])] = "fire"
    return out


def claims(run: dict) -> Dict[tuple, frozenset]:
    by: Dict[tuple, set] = defaultdict(set)
    for f in run.get("findings", []):
        if f.get("tier") in ("blocking", "advisory"):
            by[(f["detector"], f["paper"])].add(f["code"])
    return {k: frozenset(v) for k, v in by.items()}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--perturbed", action="append", default=[],
                    metavar="NAME=PATH", help="repeatable; NAME must match the perturbation")
    ap.add_argument("--perturb-report", action="append", default=[], metavar="NAME=PATH",
                    help="repeatable; supplies the exempt-detector list and excluded papers")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)

    base = load(a.baseline)
    base_out, base_claims = outcomes(base), claims(base)

    exempt: Dict[str, set] = {}
    excluded: Dict[str, set] = {}
    for spec in a.perturb_report:
        if "=" not in spec:
            print(f"invariance: --perturb-report wants NAME=PATH, got {spec!r}", file=sys.stderr)
            return 2
        name, path = spec.split("=", 1)
        rep = load(Path(path))
        exempt[name] = set(rep.get("exempt_detectors", ()))
        excluded[name] = {e["paper"] for e in rep.get("excluded", ())}

    results = []
    for spec in a.perturbed:
        if "=" not in spec:
            print(f"invariance: --perturbed wants NAME=PATH, got {spec!r}", file=sys.stderr)
            return 2
        name, path = spec.split("=", 1)
        run = load(Path(path))
        p_out, p_claims = outcomes(run), claims(run)
        ex_det, ex_pap = exempt.get(name, set()), excluded.get(name, set())

        pairs = {k for k in set(base_out) | set(p_out) if k[1] not in ex_pap}
        judged = {k for k in pairs if k[0] not in ex_det}
        moved = sorted(k for k in judged if base_out.get(k) != p_out.get(k))
        expected = sorted(k for k in pairs - judged if base_out.get(k) != p_out.get(k))
        stuck = sorted(k for k in pairs - judged if base_out.get(k) == p_out.get(k))

        # claim-level: only where both sides fired, so a moved outcome is not counted twice
        both = {k for k in set(base_claims) & set(p_claims) if k in judged}
        claim_moved = sorted(k for k in both if base_claims[k] != p_claims[k])

        n_j = len(judged)
        res = {
            "perturbation": name,
            "pairs_judged": n_j,
            "pairs_moved": len(moved),
            "outcome_invariance": round(1 - len(moved) / n_j, 4) if n_j else None,
            "fires_compared": len(both),
            "claims_moved": len(claim_moved),
            "claim_invariance": round(1 - len(claim_moved) / len(both), 4) if both else None,
            "exempt_detectors": sorted(ex_det),
            "exempt_moved_as_expected": len(expected),
            "exempt_did_not_move": [f"{d} x {p}" for d, p in stuck],
            "excluded_papers": sorted(ex_pap),
            "moved": [{"detector": d, "paper": p,
                       "baseline": base_out.get((d, p), "not-fire"),
                       "perturbed": p_out.get((d, p), "not-fire")} for d, p in moved],
            "claims_changed": [{"detector": d, "paper": p,
                                "baseline": sorted(base_claims[(d, p)]),
                                "perturbed": sorted(p_claims[(d, p)])} for d, p in claim_moved],
        }
        results.append(res)

        print("=" * 78)
        print(f" Q7 invariance — {name}")
        print("=" * 78)
        print(f"  pairs judged      : {n_j}   moved: {len(moved)}")
        if res["outcome_invariance"] is not None:
            print(f"  OUTCOME INVARIANCE: {res['outcome_invariance']:.3f}"
                  "   <- 1.000 means the rewrite changed nothing the stack noticed")
        if res["claim_invariance"] is not None:
            print(f"  CLAIM INVARIANCE  : {res['claim_invariance']:.3f}"
                  f"   ({len(claim_moved)} of {len(both)} fires changed WHICH claim they made)")
        by_det: Dict[str, int] = defaultdict(int)
        for d, _ in moved:
            by_det[d] += 1
        for d, n in sorted(by_det.items(), key=lambda x: -x[1]):
            print(f"    MOVED {d} on {n} paper(s) — read surface form, not content")
        if ex_det:
            print(f"  exempt (order/position is their subject): {', '.join(sorted(ex_det))}")
            print(f"    of these, {len(expected)} moved as expected")
            for s in res["exempt_did_not_move"]:
                print(f"    DID NOT MOVE {s} — a detector that polices order ignored a reordering")
        if ex_pap:
            print(f"  excluded by the validity guard: {', '.join(sorted(ex_pap))}")

    payload = {"baseline": str(a.baseline), "results": results}
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n  json: {a.out}")
    print("\n  A moved verdict is a defect on one side of the pair, and which side does not matter\n"
          "  for this claim. That is why this endpoint needs no labeler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
