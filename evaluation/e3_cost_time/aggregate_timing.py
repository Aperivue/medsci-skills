#!/usr/bin/env python3
"""E3 - Cost/time feasibility.

Aggregates timing_cost.json across the most recent run of each experiment into a
small feasibility table. Deterministic scripts cost ~0 tokens (report runtime);
LLM-loop harnesses (E2/E9) report token/cost only when actually run.

Writes cost_time.csv to its own run package. Wall-clock is near-exact (varies by
machine/load) and is reported as an observation, not a reproducibility target.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import EVAL_ROOT, REPO_ROOT  # noqa: E402

RUNS = EVAL_ROOT / "runs"
EXPECTED = ["E1", "E4", "E5", "E6", "E7", "E8", "E2", "E9"]


def latest_run(exp: str) -> Path | None:
    cands = sorted(RUNS.glob(f"*_{exp}"))
    return cands[-1] if cands else None


def main() -> int:
    log = RunLogger.start("E3")
    rows = []
    for exp in EXPECTED:
        rd = latest_run(exp)
        if rd is None:
            rows.append({"experiment": exp, "status": "no_run", "wall_clock_s": "",
                         "n_components": "", "manual_steps": "", "token_cost": ""})
            continue
        tc = rd / "timing_cost.json"
        rm = rd / "run_manifest.json"
        wall = ""
        cost = ""
        if tc.is_file():
            d = json.loads(tc.read_text(encoding="utf-8"))
            wall = d.get("wall_clock_s", "")
            cost = d.get("api_cost_usd")
            cost = "" if cost is None else cost
        ncomp = ""
        comp_types = set()
        if rm.is_file():
            m = json.loads(rm.read_text(encoding="utf-8"))
            comps = m.get("components", [])
            ncomp = len(comps)
            comp_types = {c.get("component_type") for c in comps}
        manual = "yes" if "human_adjudication" in comp_types else "no"
        token = "~0 (deterministic)" if "llm_baseline" not in comp_types else (cost or "n/a")
        rows.append({
            "experiment": exp, "status": "run", "wall_clock_s": wall,
            "n_components": ncomp, "manual_steps": manual, "token_cost": token,
        })
        log.add_input(tc)

    out = log.run_dir / "cost_time.csv"
    cols = ["experiment", "status", "wall_clock_s", "n_components", "manual_steps", "token_cost"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print("experiment | status | wall_s | components | manual | token_cost")
    for r in rows:
        print(f"  {r['experiment']:3} | {r['status']:7} | {str(r['wall_clock_s']):>7} | "
              f"{str(r['n_components']):>3} | {r['manual_steps']:>3} | {r['token_cost']}")

    log.log_component(
        component_type="deterministic_script",
        script_path=str(Path(__file__).relative_to(REPO_ROOT)),
        command_args=[],
        expected_reproducibility="near-exact",
        rerun_policy="re-aggregate after a full suite run; wall-clock varies by machine",
        input_paths=[],
        output_path=out,
    )
    limitations = (
        "Wall-clock is a machine-dependent observation (near-exact), not a "
        "reproducibility target. Deterministic harnesses incur ~0 token cost; "
        "E2/E9 report tokens/cost only when actually run (they are NOT_RUN by "
        "default). Aggregates the most recent run per experiment."
    )
    log.finalize(metrics_path=out, limitations=limitations, repro_hash_extra=[out])
    print(f"\nwrote {out}")
    print(f"run dir: {log.run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
