#!/usr/bin/env python3
"""Refinement regression axis -- did this revision fix without breaking?

self-review is stateless: each run reports the manuscript's current findings, but nothing
compares one run to the last. So when the author revises to fix finding X, the gate
pass-rate goes up ("X resolved") and no one measures whether the fix *introduced* a new
finding Y. The loop looks like it is improving -- fewer of the old problems -- while
quietly accumulating new ones. Worse, a finding that was fixed can reappear a round later
(the "Mirror Loop"): the loop is churning, re-deriving, not converging.

This is NOT a detector -- it finds no defect in the manuscript. It reads a small
run-history **ledger** (one line per self-review run, each line the fingerprints of that
run's findings) plus the current run's `qc/*.json`, and reports the regression axis
*alongside* the pass-rate axis:

  resolved   findings present last run, gone now            (what the revision FIXED)
  carried    findings present both runs                     (still open)
  new        findings present now, absent last run          (what the revision BROKE)
  churn      new findings that were present in an EARLIER    (Mirror Loop: a fixed finding
             run and had been resolved                        resurfaced -> stop churning)

  Verdict:
    CONVERGED      nothing new and nothing carried -- the loop is done
    CHURNING       a resolved finding reappeared -- ungrounded re-derivation, stop the loop
    REGRESSION     the revision introduced new finding(s)
    PROGRESSING    findings resolved, none newly introduced
    INDETERMINATE  first run -- no prior entry to compare against

A finding's fingerprint is `verdict@where` (deterministic; no semantic matching). The gate
is advisory and NEVER blocks -- it is a signal, not a barrier: `--strict` is accepted for
CLI parity but every non-error path exits 0. By default it only classifies (read-only); with
`--append` it also records the current run as the next ledger entry.

INPUTS
  --qc-dir   directory holding the current run's qc/*.json artifacts (required).
  --ledger   the run-history ledger, one JSON object per line (required; created on
             first --append).
  --append   after classifying, append the current run's fingerprints as a new entry.
  --out      optional JSON artifact path.
  --quiet    suppress the stdout summary.
  --strict   accepted for CLI parity; never blocks.

OUTPUT
  A regression summary (stdout) and, with --out, a JSON artifact:
    {tool, qc_dir, ledger, verdict, resolved[], carried[], new[], churn[], recommendation}

Stdlib-only (json / argparse / pathlib / sys). Exit codes: 0 always for a judged or
indeterminate state (advisory), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import _qc_findings  # same-dir helper: read the heterogeneous detector JSON schemas uniformly

TOOL = "refinement_regression"

STOP_HINT = {
    "CONVERGED": "Nothing new and nothing carried -- the loop is done. Stop.",
    "CHURNING": (
        "A previously-resolved finding reappeared ({churn}) -- the loop is re-deriving, not "
        "converging (the Mirror Loop). Stop revising and re-anchor; more passes will not help."
    ),
    "REGRESSION": (
        "The last revision resolved {n_resolved} finding(s) but INTRODUCED {n_new} new one(s) "
        "({new}). Fixing raised the pass-rate while breaking something else -- review the new "
        "findings before continuing."
    ),
    "PROGRESSING": (
        "{n_resolved} finding(s) resolved and none newly introduced -- the revision improved "
        "the manuscript without breaking anything. Continue."
    ),
    "INDETERMINATE": (
        "No prior ledger entry -- this is the first run. Re-run after a revision (with "
        "--append recording each run) to measure regression."
    ),
}


def _current_keys(qc_dir: Path) -> tuple[list[str], list[str]]:
    """Return (sorted finding fingerprints, sorted unparsed gate names) for the current run.
    Reads both the `claims` and `findings` detector schemas via _qc_findings; a detector-keyed
    file whose schema is unrecognised is surfaced (unparsed), not silently dropped — a dropped
    gate would understate what the run found and corrupt the cross-run comparison."""
    keys: set[str] = set()
    unparsed: set[str] = set()
    for path in sorted(qc_dir.glob("*.json")):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        g = _qc_findings.parse_gate(obj)
        if g is None:
            continue
        if not g["parsed"]:
            unparsed.add(g["name"])
            continue
        keys.update(g["keys"])
    return sorted(keys), sorted(unparsed)


def _read_ledger(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("keys"), list):
            entries.append(obj)
    return entries


def classify(current: list[str], entries: list[dict]) -> dict:
    cur = set(current)
    if not entries:
        verdict = "INDETERMINATE"
        resolved = carried = new = churn = []
    else:
        prev = set(entries[-1]["keys"])
        prior_all: set[str] = set()
        for e in entries[:-1]:
            prior_all |= set(e["keys"])
        resolved = sorted(prev - cur)
        carried = sorted(prev & cur)
        new = sorted(cur - prev)
        churn = sorted(set(new) & prior_all)
        if not new and not carried:
            verdict = "CONVERGED"
        elif churn:
            verdict = "CHURNING"
        elif new:
            verdict = "REGRESSION"
        else:
            verdict = "PROGRESSING"

    rec = STOP_HINT[verdict].format(
        n_resolved=len(resolved),
        n_new=len(new),
        new=", ".join(new) if new else "-",
        churn=", ".join(churn) if churn else "-",
    )
    return {
        "tool": TOOL,
        "verdict": verdict,
        "resolved": resolved,
        "carried": carried,
        "new": new,
        "churn": churn,
        "recommendation": rec,
    }


def render(result: dict, qc_dir: str, ledger: str) -> str:
    lines = [
        f"Refinement regression: {result['verdict']}",
        f"  fixed (resolved): {len(result['resolved'])}   still open (carried): {len(result['carried'])}",
        f"  broke (new):      {len(result['new'])}   resurfaced (churn):  {len(result['churn'])}",
    ]
    if result.get("gates_unparsed"):
        lines.append(f"  unparsed gates:   {', '.join(result['gates_unparsed'])}  (unrecognised schema — NOT counted)")
    lines.append(f"  qc dir: {qc_dir}   ledger: {ledger}")
    lines.append(f"  -> {result['recommendation']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Classify a self-review run against the prior run (regression axis) from a run-history ledger.")
    ap.add_argument("--qc-dir", required=True, help="directory holding the current run's qc/*.json artifacts")
    ap.add_argument("--ledger", required=True, help="run-history ledger (one JSON object per line)")
    ap.add_argument("--append", action="store_true", help="append the current run's fingerprints as a new ledger entry")
    ap.add_argument("--out", help="optional JSON artifact path")
    ap.add_argument("--quiet", action="store_true", help="suppress the stdout summary")
    ap.add_argument("--strict", action="store_true", help="accepted for CLI parity; never blocks (advisory)")
    args = ap.parse_args(argv)

    qc_dir = Path(args.qc_dir)
    if not qc_dir.is_dir():
        print(f"error: qc dir not found: {args.qc_dir}", file=sys.stderr)
        return 2
    current, unparsed = _current_keys(qc_dir)
    ledger_path = Path(args.ledger)
    entries = _read_ledger(ledger_path)

    result = classify(current, entries)
    result["gates_unparsed"] = unparsed
    if unparsed:
        result["recommendation"] += (
            f" (WARNING: {len(unparsed)} gate artifact(s) had an unrecognised schema and were not "
            f"counted, so this comparison may miss findings: {', '.join(unparsed)})")

    if args.append:
        run_no = len(entries) + 1
        with ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"run": run_no, "keys": current}) + "\n")

    out = {"qc_dir": str(args.qc_dir), "ledger": str(args.ledger), **result}
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    if not args.quiet:
        print(render(result, str(args.qc_dir), str(args.ledger)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
