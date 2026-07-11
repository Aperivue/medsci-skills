# Challenge card — paired-difference-estimator gate (self-review)

## Problem
A reader/Likert study answers an uncertainty comment by adding a "median paired
difference … 0.5 points (95% CI 0.5–0.5)". The tells are deterministic: the median
of an odd number of integer paired differences is one of those integers, so 0.5 is
impossible (it is a Hodges–Lehmann pseudomedian mislabelled as a median); the CI has
zero width; and no estimator or interval method is named, so nothing is reproducible.

## What the gate does
`check_paired_difference_estimator.py` flags `MEDIAN_PARITY` (n odd ∧ integer scale ∧
non-integer reported median difference — allowing a 1/R step when scores are means of
R raters), `DEGENERATE_CI` (equal interval bounds), and `ESTIMATOR_UNNAMED` (a
median-difference effect size + CI with no Hodges–Lehmann / pseudomedian / bootstrap /
Wilcoxon / exact / sign-test named). A value labelled a Hodges–Lehmann pseudomedian is
exempt from the parity check.

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/paired_bad.md` — 0.5 median over n=153 4-point scores, 95% CI 0.5–0.5, no estimator.
- `fixture/paired_ok.md` — Hodges–Lehmann pseudomedian 0.5 (95% CI 0.0 to 1.0), estimator named.

## Expected
- `expected/bad.txt` — `MEDIAN_PARITY` + `DEGENERATE_CI` + `ESTIMATOR_UNNAMED`; exit 1 under `--strict`.
- `expected/ok.txt` — `OK`; exit 0.

`verify.sh` diffs both outputs and asserts the exit-code contract. Network-free, stdlib-only.
