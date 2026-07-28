# Challenge — dataset-profile gate

A medical-imaging dataset carries facts that decide a study before any model exists:
how heterogeneous the acquisition is, how rare the target is, whether the labels are
intact, and whether the split you intend to call a *test set* actually has ground truth.
Given a **dataset profile** (JSON, one record per case) plus the researcher's declared
plan, `check_dataset_profile.py` must decide — by rule and by arithmetic over the case
records, never from prose and never by opening an image — which of those facts block
the study as planned.

## Task
Run the gate on the two synthetic profiles in `fixture/` and reproduce `expected/`:

- `profile_defect.json` → five Major verdicts (`LABEL_SHAPE_MISMATCH`, `LABEL_EMPTY`,
  `LABEL_VALUE_UNEXPECTED`, `TEST_SET_UNLABELLED`, `ACCURACY_UNDER_IMBALANCE`) plus five
  Minor flags (`LABEL_MISSING`, `SPACING_HETEROGENEOUS`, `ORIENTATION_MIXED`,
  `INTENSITY_SCALE_INCONSISTENT`, `EXTREME_IMBALANCE`); exit 1 under `--strict`.
- `profile_clean.json` → no claims; exit 0. Note that this dataset is **just as
  heterogeneous** — the same 5.3x through-plane spacing spread, the same two orientation
  codes — and nothing fires, because resampling and reorientation are declared. The gate
  flags an *undeclared* decision, not variability itself.

## Verify
```bash
bash verify.sh   # deterministic, network-free
```
