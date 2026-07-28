# MedSci Skills — Evaluation Harness Suite

This directory validates the **instrument** (MedSci Skills) itself: the
deterministic detectors, the reproducibility machinery, the audit trail, host
portability, and public-metadata integrity. It is the reproducible evidence
package behind the companion methods/architecture preprint.

## Scope boundary (important)

These harnesses validate the **tool**, never the *quality* of any manuscript.
They do **not** measure manuscript publishability, editor distinguishability,
human-editing value, or safety-error rates. Those questions belong to a
separate, blinded evaluation study with independent editors and are out of
scope here by design.

## Harnesses

| Exp | Harness | What it validates | Determinism |
|-----|---------|-------------------|-------------|
| E1 | `h1_seeded_defects/` | Detector recall on programmatically injected defects + clean false-positive rate | exact (offline) |
| E2 | `h2_llm_baseline/` | Deterministic detectors vs a generic LLM review prompt on the same defects | non-deterministic — **ships, NOT_RUN by default** |
| E3 | `e3_cost_time/` | Runtime / manual-step / cost feasibility | near-exact (timing) |
| E4 | `h3_fresh_clone/` | Clean-checkout reproducibility of the three demo manifests | exact |
| E5 | `h4_audit_trail/` | Provenance-trace completeness of demo manuscript claims | exact extract + human score |
| E6 | `h5_portability/` | Installation-contract + documented host-target portability smoke test | exact |
| E7 | `h6_inventory_drift/run_e7_inventory.py` | Coverage inventory of the deterministic detectors (fixtures/tests/demo outputs) | exact |
| E8 | `h6_inventory_drift/run_e8_drift.py` | Public-metadata drift is caught by the catalog validator | exact |
| E9 | `h7_selfreview_convergence/` | Whether the self-review loop reduces its own actionable findings (internal QC convergence) | non-deterministic — **ships, NOT_RUN by default** |

## Coverage status, and the planned refresh

The harnesses above are **v3.8-era**: E1 rests on 19 `DefectSpec` rows / 17 offline injectors and
E7 is n=21, while the current catalog is **80 detectors**. Detectors added since are covered by
per-detector CI challenge cards — regression tripwires, not a benchmark.

[`REFRESH_PROTOCOL.md`](REFRESH_PROTOCOL.md) pre-registers the refresh that closes that gap:
family-stratified coverage of all 80 detectors with hard negatives (Arm A), an alert-burden
measurement on clean manuscripts (Arm B), and an out-of-band real-use precision ledger (Arm C).
It is a protocol only — **no results exist yet** — and it records two constraints up front: an
injection benchmark cannot report precision (there is no defined defect prevalence), and the
clean-manuscript arm should not be run to completion while the only available adjudicator is the
person who wrote the detectors.

## Running

```bash
# Deterministic, self-contained suite (no API key, no network needed):
bash evaluation/run_all.sh

# Include the non-deterministic LLM-loop harnesses (needs an API key / runner):
bash evaluation/run_all.sh --with-llm
```

Each run writes a self-describing package under `runs/<timestamp>_<exp>/`
(see `_harness/runlog.py`): `run_manifest.json` (per-component determinism
class + input/output hashes), `commands.sh`, `environment.txt`,
`git_commit.txt`, `input_files_manifest.json`, `metrics.csv`, `timing_cost.json`,
`limitations.md`, and preserved raw `detector_outputs/`.

## Invariants

- Harnesses **never** write to the real `demo/` directories or repo files; all
  mutation happens inside `medsci-eval-*` temp copies guarded by
  `_harness/workspace.safe_write`.
- Detectors run with a scrubbed environment (`LC_ALL=C`, `PYTHONHASHSEED=0`).
- The reproducibility hash covers only deterministic artifacts (`metrics.csv`,
  `detector_outputs/`, `injected_defects.jsonl`); environment/timing/git files
  are excluded because they legitimately vary.
- Stdlib-only, except `version_dataset.py` (E4) which needs `pandas`.
