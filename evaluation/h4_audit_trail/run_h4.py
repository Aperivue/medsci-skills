#!/usr/bin/env python3
"""E5 - Audit-trail completeness audit.

Extracts candidate claims from the three demo manuscripts, classifies them, and
pre-fills the provenance chain (manuscript -> analysis table -> dataset manifest
-> QC artifact) wherever it can be established deterministically. Numerical
claims earn an auto "complete" score only on an exact-cell match against an
analysis table that is in the dataset manifest; everything looser is "partial"
or left for human adjudication. Scores provenance completeness, never claim
quality (Paper-2 boundary).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0]))
sys.path.insert(0, str(HERE))
from _harness.runlog import RunLogger  # noqa: E402
from _harness.workspace import REPO_ROOT, golden_inputs  # noqa: E402
import extract_claims as ec  # noqa: E402


def main() -> int:
    demos = golden_inputs()
    log = RunLogger.start("E5")
    rows = []
    for demo_id, g in demos.items():
        prov = ec.load_provenance(g.root)
        for c in ec.extract(str(g.manuscript)):
            sc = ec.score_claim(c, prov)
            rows.append({
                "demo": demo_id, "claim_id": c.claim_id, "claim_type": c.claim_type,
                "value": c.value, "manuscript_loc": f"L{c.loc_line}",
                "claim_text": c.claim_text, **sc,
            })
        log.add_input(g.manuscript, g.manifest)

    out = log.run_dir / "claims_audit.csv"
    cols = ["demo", "claim_id", "claim_type", "value", "manuscript_loc",
            "qc_artifact", "analysis_table", "source_data_manifest",
            "verified_citation", "provenance_score", "match_confidence",
            "auto_or_manual", "claim_text"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    # summary by type x score
    n = len(rows)
    from collections import Counter
    by_score = Counter(r["provenance_score"] for r in rows)
    by_type = Counter(r["claim_type"] for r in rows)
    num = [r for r in rows if r["claim_type"] == "numerical"]
    num_complete = sum(1 for r in num if r["provenance_score"] == "complete")
    print(f"claims audited: {n}")
    print("  by type:  " + ", ".join(f"{k}={v}" for k, v in sorted(by_type.items())))
    print("  by score: " + ", ".join(f"{k}={v}" for k, v in sorted(by_score.items())))
    if num:
        print(f"  numerical provenance complete: {num_complete}/{len(num)} "
              f"({num_complete / len(num):.0%})")

    # write a compact summary csv too (for the Table 3 summary row)
    summ = log.run_dir / "summary.csv"
    with summ.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["claim_type", "n", "complete", "partial", "manual-only", "missing"])
        for t in sorted(by_type):
            tr = [r for r in rows if r["claim_type"] == t]
            cnt = Counter(r["provenance_score"] for r in tr)
            w.writerow([t, len(tr), cnt.get("complete", 0), cnt.get("partial", 0),
                        cnt.get("manual-only", 0), cnt.get("missing", 0)])

    log.log_component(
        component_type="deterministic_script",
        script_path=str(Path(__file__).relative_to(REPO_ROOT)),
        command_args=[],
        expected_reproducibility="exact",
        rerun_policy="rerun any time; extraction + provenance pre-fill is deterministic",
        input_paths=[g.manuscript for g in demos.values()] + [g.manifest for g in demos.values()],
        output_path=out,
    )
    # also log the human-adjudication component (the non-numerical scores left manual)
    log.log_component(
        component_type="human_adjudication",
        script_path=None, model_name=None, command_args=[],
        expected_reproducibility="non-deterministic",
        rerun_policy="manual rows (figure_table / citation / some analysis_method) need a human reviewer",
        input_paths=[out],
    )
    limitations = (
        "Provenance completeness is scored, NOT claim correctness or quality. "
        "Numerical claims earn 'complete' only on an exact-cell match to an "
        "analysis table that is in the dataset manifest; rounded/substring "
        "matches are 'partial' (match_confidence=loose) for human audit. "
        "figure_table and citation rows are left manual-only by design (the "
        "demos use [UNVERIFIED] placeholder references). This is a sampled, "
        "deterministic pre-fill, not a substitute for human verification."
    )
    log.finalize(metrics_path=out, limitations=limitations, repro_hash_extra=[out, summ])
    print(f"\nwrote {out}")
    print(f"run dir: {log.run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
