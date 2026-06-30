#!/usr/bin/env python3
"""Confounder-adjustment-set helper for DAG-based covariate selection.

design-study (and `~/.claude/rules` confounding-completeness) tells authors to
"pre-specify the adjustment set from a DAG, not a Table-1 p<0.05 rule" — but shipped
no scaffold to do it. This is that scaffold. Given a causal DAG, an exposure, an
outcome, and a *proposed* adjustment set, it deterministically classifies each
covariate by its DAG role and flags the adjustment errors reviewers reject:

  - MEDIATOR_ADJUSTMENT   — adjusting for a node on a directed X→…→Y path (blocks part
                            of the effect you are trying to estimate).
  - DESCENDANT_ADJUSTMENT — adjusting for a descendant of the exposure (over-adjustment /
                            collider-stratification on the causal pathway).
  - COLLIDER_ADJUSTMENT   — adjusting for a collider (≥2 parents, not a common cause)
                            opens a non-causal path (M-bias).
  - CONFOUNDER_OMITTED    — a common cause of X and Y is NOT in the adjustment set, so a
                            backdoor path is left open.

It also proposes a *candidate* sufficient set — the pre-exposure common causes of X and
Y — which is a valid (if not always minimal) backdoor adjustment set. Finding the
**minimal** sufficient set in general is a graph problem best left to a validated tool;
this helper prints ready-to-run dagitty code for that and never claims minimality.

Soundness: every classification uses only reachability on the directed graph (ancestors
/ descendants), which is unambiguous. It does NOT implement full d-separation, so it will
not certify an arbitrary set as sufficient — it flags the four common, unambiguous errors
and defers optimal minimisation to dagitty.

DAG input (JSON): {"edges": [["C","X"], ["C","Y"], ["X","Y"]]}  (parent → child).
Stdlib-only. Exit codes: 0 clean (or report-only), 1 a Major flag exists (--strict),
2 input/usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _build(edges):
    children: dict[str, set[str]] = {}
    parents: dict[str, set[str]] = {}
    nodes: set[str] = set()
    for a, b in edges:
        children.setdefault(a, set()).add(b)
        parents.setdefault(b, set()).add(a)
        nodes.update((a, b))
    for n in nodes:
        children.setdefault(n, set())
        parents.setdefault(n, set())
    return nodes, children, parents


def _reach(start: str, adj: dict[str, set[str]]) -> set[str]:
    """Nodes reachable from `start` following `adj` (excludes start)."""
    seen: set[str] = set()
    stack = list(adj.get(start, ()))
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(adj.get(n, ()))
    return seen


def classify(edges, exposure: str, outcome: str, adjust: list[str]) -> dict:
    nodes, children, parents = _build(edges)
    for required in (exposure, outcome):
        if required not in nodes:
            raise ValueError(f"node {required!r} not in DAG")

    desc_X = _reach(exposure, children)          # descendants of exposure
    anc_X = _reach(exposure, parents)            # ancestors of exposure
    anc_Y = _reach(outcome, parents)             # ancestors of outcome (full graph)

    mediators = (desc_X & anc_Y) - {exposure, outcome}        # on a directed X→…→Y path

    # Confounder = common cause with a path to Y that does NOT pass through X (an open
    # backdoor). Because X→Y makes every ancestor of X an ancestor of Y, intersecting on
    # the full graph would mis-flag instrument-like A→X→Y nodes. Compute Y's ancestors on
    # the graph with X removed, so only nodes with an X-free path to Y count.
    parents_noX = {n: (p - {exposure}) for n, p in parents.items() if n != exposure}
    anc_Y_noX = _reach(outcome, parents_noX)
    common_causes = (anc_X & anc_Y_noX) - {exposure, outcome} - desc_X  # open-backdoor confounders
    candidate_set = sorted(common_causes)

    claims: list[dict] = []
    for z in adjust:
        if z not in nodes:
            claims.append({"node": z, "role": "unknown",
                           "verdict": "NODE_NOT_IN_DAG", "severity": "Minor",
                           "detail": f"'{z}' is not a node in the DAG"})
            continue
        if z in mediators:
            claims.append({"node": z, "role": "mediator",
                           "verdict": "MEDIATOR_ADJUSTMENT", "severity": "Major",
                           "detail": f"'{z}' lies on a directed {exposure}→…→{outcome} path; "
                                     f"adjusting for it removes part of the causal effect"})
        elif z in desc_X:
            claims.append({"node": z, "role": "descendant_of_exposure",
                           "verdict": "DESCENDANT_ADJUSTMENT", "severity": "Major",
                           "detail": f"'{z}' is a descendant of the exposure; adjusting for it "
                                     f"is over-adjustment (collider-stratification on the pathway)"})
        elif z not in common_causes and len(parents.get(z, ())) >= 2 \
                and z not in anc_X and z not in anc_Y:
            claims.append({"node": z, "role": "collider",
                           "verdict": "COLLIDER_ADJUSTMENT", "severity": "Major",
                           "detail": f"'{z}' is a collider (≥2 parents, not a common cause); "
                                     f"conditioning on it can open a non-causal path (M-bias)"})
    # backdoor left open: a common cause not adjusted for
    for c in sorted(common_causes - set(adjust)):
        claims.append({"node": c, "role": "confounder",
                       "verdict": "CONFOUNDER_OMITTED", "severity": "Major",
                       "detail": f"'{c}' is a common cause of {exposure} and {outcome} but is not "
                                 f"in the adjustment set; a backdoor path is left open"})
    return {
        "exposure": exposure, "outcome": outcome,
        "proposed_adjustment": sorted(adjust),
        "candidate_sufficient_set": candidate_set,
        "mediators": sorted(mediators),
        "descendants_of_exposure": sorted(desc_X),
        "claims": claims,
        "note": "candidate_sufficient_set is the pre-exposure common-cause set — a valid backdoor "
                "set, not necessarily minimal. Minimise/verify with dagitty (see design-study "
                "references/dag_adjustment.md).",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAG-based adjustment-set helper (design-study).")
    ap.add_argument("--dag", required=True, help='JSON: {"edges": [["C","X"], ...]} (parent→child)')
    ap.add_argument("--exposure", required=True)
    ap.add_argument("--outcome", required=True)
    ap.add_argument("--adjust", default="", help="comma-separated proposed adjustment covariates")
    ap.add_argument("--out", help="write the classification JSON here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major flag")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    try:
        data = json.loads(Path(args.dag).read_text(encoding="utf-8"))
        edges = data["edges"] if isinstance(data, dict) else data
        adjust = [z.strip() for z in args.adjust.split(",") if z.strip()]
        result = classify(edges, args.exposure, args.outcome, adjust)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"INPUT-ERR: {e}", file=sys.stderr)
        return 2

    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    majors = [c for c in result["claims"] if c["severity"] == "Major"]
    if not args.quiet:
        print(f"candidate sufficient set (common causes): {result['candidate_sufficient_set'] or '∅'}")
        for c in result["claims"]:
            print(f"  [{c['severity']}] {c['verdict']}: {c['node']} — {c['detail']}")
        print(f"\n{len(majors)} Major adjustment flag(s).")
    return 1 if (args.strict and majors) else 0


if __name__ == "__main__":
    raise SystemExit(main())
