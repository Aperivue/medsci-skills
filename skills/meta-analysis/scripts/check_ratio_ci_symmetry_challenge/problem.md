# Challenge — ratio CIs that cannot be right, or are not Wald

## The defect this gate catches

Ratio measures (OR, RR, HR, IRR) are pooled on the log scale, and the per-study
standard error is usually back-derived from the transcribed CI:
`SE = (log(upper) - log(lower)) / (2 z)`. A slip in one bound (`3.96` for
`2.96`) passes every type check, changes that study's SE and so its weight, and
nothing downstream notices.

A Wald CI for a ratio is symmetric about the estimate on the log scale. A
transcribed CI that stays asymmetric after every printed value is allowed to move
within its rounding interval is either a transcription error or a CI from another
method (profile likelihood, exact, bootstrap). The gate cannot tell which, so the
claim is Minor and asks for a check; declaring the method in `ci_method` skips it.
A CI that cannot exist at all (a negative value, or a lower bound above the
estimate even within rounding) is Major.

## Fixtures

**Positive** (`fixture/extraction_positive.csv`):

- Study A: `OR 2.00 (1.35, 3.96)`, the Wald CI `1.35, 2.96` (R:
  `exp(log(2) + c(-1,1)*qnorm(0.975)*0.2)`) with the upper bound mistyped
  → `RATIO_CI_ASYMMETRIC` (Minor).
- Study B: `OR 4.78 (0.31, 291.37)`, the conditional MLE and exact CI of
  R `fisher.test(matrix(c(3,1,7,12),2))`, with `ci_method` left blank
  → `RATIO_CI_ASYMMETRIC` (Minor).
- Study C: `RR 1.20 (1.35, 1.80)`, lower bound above the estimate
  → `RATIO_CI_IMPOSSIBLE` (Major).
- Study D: `HR 0.59 (-0.42, 0.82)`, a negative bound → `RATIO_CI_IMPOSSIBLE` (Major).

Exit 1 under `--strict`.

**Negative** (`fixture/extraction_negative.csv`): the Study A Wald CI as
printed; the hazard ratio for `sex` from R
`coxph(Surv(time, status) ~ sex, data = lung)` (`0.59 (0.42, 0.82)`); a 90% CI
(`exp(log(0.8) + c(-1,1)*qnorm(0.95)*0.1)` printed to three decimals); the
positive fixture's Study B exact CI, here as Study D with
`ci_method: exact (conditional MLE)`; Study E, `OR 9.00 (1.47, 81.43)` with
`ci_method: profile likelihood`, from R 4.3.3 with MASS:
`d <- data.frame(x = c(0, 1), yes = c(2, 9), no = c(8, 4));`
`f <- glm(cbind(yes, no) ~ x, family = binomial, data = d);`
`exp(coef(f)["x"]); exp(confint(f, "x"))` (it is flagged as asymmetric when
`ci_method` is left blank); `OR 1.0 (1.0, 1.1)`, which
looks asymmetric as printed but is symmetric within one-decimal rounding (R:
`exp(log(1.04) + c(-1,1)*qnorm(0.975)*0.03)`); and a mean difference, which is
not a ratio row. No claim, exit 0, and the derived SEs match R.

## Verify

`bash verify.sh` — deterministic, network-free.
