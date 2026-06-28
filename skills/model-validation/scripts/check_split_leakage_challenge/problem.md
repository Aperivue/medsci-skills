# Challenge card — split-leakage gate (model-validation)

## Problem
A clinical team receives a trained medical-imaging model from an engineering
collaborator and reports a head-line metric (Dice, AUROC, sensitivity). The single
most common — and most metric-inflating — defect is a data split that is **not
disjoint at the patient level**: the same patient contributes images to both the
training and the test partition. The model then memorises patient-specific anatomy
rather than pathology, and every reported number is optimistic (Kapoor & Narayanan,
*Patterns* 2023; Varoquaux & Cheplygina, *npj Digit Med* 2022; CLAIM 2024
data-partition items). A reviewer cannot see this from the prose — only from the
split itself.

## What the gate does
`scripts/check_split_leakage.py` reads the **emitted split-assignment table**
(`patient_id, split`) and **proves**, by set arithmetic on the IDs, whether any
patient crosses partitions. This is not a heuristic prose lint — it is a fully
decidable data check on the produced artifact. It also confirms the split is
**reproducible** (a recorded random seed), because a split with no seed cannot be
regenerated or re-verified. An ID appearing several times *within one* partition
(multiple images per patient) is fine and does not fire; only an ID spanning
≥ 2 partitions does. Train/training, val/validation, and test/testing/holdout
synonyms are collapsed so a labelling variant never registers as a false overlap.

## Fixture (synthetic only — no real patients, no PII)
- `fixture/splits_leak.csv` — 12 synthetic subjects; **P03** is in train + test and
  **P07** is in train + val → 2 patient-overlap leaks.
- `fixture/splits_clean.csv` — each subject in exactly one partition, with repeat
  images and the `training` / `validation` / `holdout` synonyms, to prove neither a
  within-split repeat nor a label variant trips the gate.
- `fixture/split_seed.txt` — `42`, auto-detected as the recorded split seed.

## Expected
- `expected/leak.txt` — `PATIENT_OVERLAP` (Major), naming P03 (test/train) and the
  two offenders; exit 1 under `--strict`.
- `expected/clean.txt` — `(none)` / OK; exit 0 under `--strict`.

`verify.sh` diffs both stdout outputs against `expected/` and asserts the exit-code
contract (leak → 1, clean → 0). Network-free, torch-free, stdlib-only.
