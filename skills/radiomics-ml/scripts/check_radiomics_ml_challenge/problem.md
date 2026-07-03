# Challenge — radiomics / classical-ML pipeline-rigor gate

A radiomics + tree-ensemble study (features → random forest / XGBoost → clinical outcome)
is trustworthy only with nested CV, dimensionality control, in-fold feature selection,
stability filtering, calibration, and external validation. Given a declarative pipeline
manifest (JSON), `check_radiomics_ml.py` must decide — by rule, not from prose — whether
the pipeline meets that bar.

## Task
Run the gate on the two synthetic manifests in `fixture/` and reproduce `expected/`:

- `pipeline_weak.json` → three Major verdicts (`NO_NESTED_CV`, `HIGH_DIM_LOW_EVENTS`,
  `SELECTION_OUTSIDE_CV`) plus three Minor (`NO_FEATURE_STABILITY`, `NO_CALIBRATION`,
  `NO_EXTERNAL_VALIDATION`); exit 1 under `--strict`.
- `pipeline_strong.json` → no claims; exit 0.

## Verify
```bash
bash verify.sh   # deterministic, network-free
```
