#!/usr/bin/env python3
"""Refinement terminal-state classifier -- the loop controller for self-review.

self-review runs a stack of *floor* gates (Phases 2.5-2.5f: numerical, citation,
cross-reference, leakage) that minimize rejection-for-cause, and one *ceiling* pass
(Phase 2.5g, check_editorial_impression) that recommends SUBTRACTION so an accurate
manuscript also reads confidently. Run in a loop -- self-review, revise, self-review --
the floor gates converge to a fixed point (0 Major) but nothing tells the author the
loop is *done*. Because every additive gate can always surface one more caveat, an
ungrounded refinement loop drifts: the manuscript over-hardens, the same findings get
re-raised in new words (the "Mirror Loop"), and "no edit needed" is never declared a
valid outcome.

This is NOT a detector -- it finds no defect in the manuscript, so it carries no
`check_`/`detect_`/`derive_` prefix and is not counted in the detector catalog. It reads
the JSON artifacts the other gates already wrote (qc/*.json) and classifies the
*terminal state* of the refinement loop, so the harness has a reproducible stop signal
it cannot rationalize away:

  CONTINUE             a floor gate still reports a Major (rejection-for-cause). Real
                       work remains.
  STOP_OVERHARDENING   floor at its fixed point (0 Major), but the ceiling pass flags
                       accumulation (over-hedging / buried defense). Stop ADDING; the
                       only remaining action is optional SUBTRACTION.
  STOP_MINOR_OPTIONAL  floor at fixed point; only optional Minor polish remains, ceiling
                       clean. Stop the required-work loop; present the Minor items as a
                       menu, do not loop for them.
  STOP_ZERO_EDIT       floor at fixed point (0 Major, 0 Minor), ceiling clean. The
                       manuscript is submission-ready as-is. A zero-edit result is a
                       valid PASS -- do not manufacture changes.
  INDETERMINATE        no gate artifacts found; the floor/ceiling gates have not run.

A floor gate's JSON is recognised by a `summary.n_major`; the ceiling pass by a
`summary.by_action`. The classifier is advisory and NEVER blocks -- it must not
double-gate the floor detectors, which already exit non-zero under --strict on their own
Majors. --strict is accepted for CLI parity but every non-error path exits 0. This is the
counterweight to the additive bias of the whole stack: the one step that can say "stop,
this is done".

INPUTS
  --qc-dir   directory holding the gates' qc/*.json artifacts (required).
  --out      optional JSON artifact path.
  --quiet    suppress the stdout summary.
  --strict   accepted for parity; never blocks.

OUTPUT
  A terminal-state summary (stdout) and, with --out, a JSON artifact:
    {tool, qc_dir, verdict, stop, floor_major, floor_minor, ceiling_findings,
     gates_read[], recommendation}

Stdlib-only (json / argparse / pathlib / sys). Exit codes: 0 always for a judged or
indeterminate state (advisory), 2 input/usage error (--qc-dir missing as an argument).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import _qc_findings  # same-dir helper: read the heterogeneous detector JSON schemas uniformly

TOOL = "refinement_stop"

RECOMMENDATIONS = {
    "CONTINUE": (
        "Floor gates report {floor_major} Major finding(s) (rejection-for-cause). "
        "Genuine work remains -- resolve these before treating the loop as done."
    ),
    "STOP_OVERHARDENING": (
        "Floor is at its fixed point (0 Major). The ceiling pass flags {ceiling_findings} "
        "accumulation signal(s) -- the draft has begun to over-harden. STOP additive "
        "refinement: do NOT run another add-a-caveat/defense pass. The only remaining "
        "action is SUBTRACTION (REMOVE / MOVE / TIGHTEN) and it is optional, not required "
        "for submission."
    ),
    "STOP_MINOR_OPTIONAL": (
        "Floor is at its fixed point (0 Major); {floor_minor} optional Minor item(s) "
        "remain and the ceiling is clean. No required edits -- present the Minor items as "
        "an optional menu; do not treat them as blocking and do not loop for them."
    ),
    "STOP_ZERO_EDIT": (
        "Floor is at its fixed point (0 Major, 0 Minor) and the ceiling is clean. The "
        "manuscript is submission-ready as-is. NO EDITS REQUIRED -- a zero-edit result is "
        "a valid PASS. Do not manufacture changes."
    ),
    "INDETERMINATE": (
        "No gate artifacts found in the qc directory. Run the floor gates "
        "(Phases 2.5-2.5f) and the ceiling pass (Phase 2.5g) first; the terminal state "
        "cannot be judged without them."
    ),
}

STOP_VERDICTS = {"STOP_OVERHARDENING", "STOP_MINOR_OPTIONAL", "STOP_ZERO_EDIT"}


def classify(qc_dir: Path) -> dict:
    floor_major = floor_minor = ceiling_findings = 0
    gates: list[str] = []
    unparsed: list[str] = []
    for path in sorted(qc_dir.glob("*.json")):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        g = _qc_findings.parse_gate(obj)
        if g is None:
            continue
        gates.append(g["name"])
        if not g["parsed"]:
            # a detector-keyed file with an unrecognised schema -- do NOT count it as clean
            unparsed.append(g["name"])
            continue
        if g["kind"] == "ceiling":
            ceiling_findings += g["major"] + g["minor"]
        else:
            floor_major += g["major"]
            floor_minor += g["minor"]

    if not gates:
        verdict = "INDETERMINATE"
    elif floor_major > 0:
        verdict = "CONTINUE"
    elif ceiling_findings > 0:
        verdict = "STOP_OVERHARDENING"
    elif floor_minor > 0:
        verdict = "STOP_MINOR_OPTIONAL"
    else:
        verdict = "STOP_ZERO_EDIT"

    rec = RECOMMENDATIONS[verdict].format(
        floor_major=floor_major,
        floor_minor=floor_minor,
        ceiling_findings=ceiling_findings,
    )
    if unparsed:
        rec += (f" (WARNING: {len(unparsed)} gate artifact(s) had an unrecognised schema and were "
                f"NOT counted -- this verdict may understate the floor: "
                f"{', '.join(sorted(set(unparsed)))})")
    return {
        "tool": TOOL,
        "verdict": verdict,
        "stop": verdict in STOP_VERDICTS,
        "floor_major": floor_major,
        "floor_minor": floor_minor,
        "ceiling_findings": ceiling_findings,
        "gates_read": sorted(set(gates)),
        "gates_unparsed": sorted(set(unparsed)),
        "recommendation": rec,
    }


def render(result: dict, qc_dir_display: str) -> str:
    fixed = "  (fixed point)" if result["floor_major"] == 0 and result["verdict"] != "INDETERMINATE" else ""
    gates = ", ".join(result["gates_read"]) if result["gates_read"] else "(none)"
    lines = [
        f"Refinement terminal-state: {result['verdict']}",
        f"  Floor gates:   {result['floor_major']} Major, {result['floor_minor']} Minor{fixed}",
        f"  Ceiling pass:  {result['ceiling_findings']} finding(s)",
        f"  Gates read:    {gates}",
    ]
    if result.get("gates_unparsed"):
        lines.append(f"  Unparsed:      {', '.join(result['gates_unparsed'])}  (unrecognised schema — NOT counted)")
    lines.append(f"  qc dir:        {qc_dir_display}")
    lines.append(f"  -> {result['recommendation']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Classify the refinement loop's terminal state from qc/*.json gate artifacts."
    )
    ap.add_argument("--qc-dir", required=True, help="directory holding the gates' qc/*.json artifacts")
    ap.add_argument("--out", help="optional JSON artifact path")
    ap.add_argument("--quiet", action="store_true", help="suppress the stdout summary")
    ap.add_argument("--strict", action="store_true", help="accepted for CLI parity; never blocks (advisory)")
    args = ap.parse_args(argv)

    qc_dir = Path(args.qc_dir)
    if not qc_dir.is_dir():
        # Absent qc dir is not a usage error in a pipeline where the gates may not have run
        # yet; report INDETERMINATE and exit 0 so the loop controller degrades gracefully.
        result = {
            "tool": TOOL,
            "verdict": "INDETERMINATE",
            "stop": False,
            "floor_major": 0,
            "floor_minor": 0,
            "ceiling_findings": 0,
            "gates_read": [],
            "gates_unparsed": [],
            "recommendation": RECOMMENDATIONS["INDETERMINATE"],
        }
    else:
        result = classify(qc_dir)

    result_out = {"qc_dir": str(args.qc_dir), **result}
    if args.out:
        Path(args.out).write_text(json.dumps(result_out, indent=2) + "\n", encoding="utf-8")
    if not args.quiet:
        print(render(result, str(args.qc_dir)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
