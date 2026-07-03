# Challenge — explainability-report rigor gate

A saliency / Grad-CAM analysis is trustworthy only when it passes sanity checks,
reports a quantitative localisation metric, is computed over a cohort, and is framed as
attribution rather than proof of correctness. Given a declarative explainability-report
manifest (JSON), `check_explainability_report.py` must decide — by rule, not from prose —
whether the analysis meets that bar.

## Task
Run the gate on the two synthetic manifests in `fixture/` and reproduce `expected/`:

- `report_weak.json` → two Major verdicts (`NO_SANITY_CHECK`, `NO_LOCALIZATION_METRIC`) plus
  a Minor `CHERRY_PICKED_EXAMPLES`; exit 1 under `--strict`.
- `report_strong.json` → no claims; exit 0.

## Verify
```bash
bash verify.sh   # deterministic, network-free
```
