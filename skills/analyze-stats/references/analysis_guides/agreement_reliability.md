# Inter-rater Agreement & Reliability Guide

Quantifying how well two or more raters (or a rater and a reference, or repeated
measurements) **agree**. The coefficient is easy to compute; the two ways these
analyses fail review are (1) treating **clustered** measurements as independent
(pseudoreplication) and (2) confusing **agreement** with **reliability**.

---

## When to Use

- **Cohen's kappa** — 2 raters, categorical (nominal) labels.
- **Weighted kappa** — 2 raters, **ordinal** labels (linear or quadratic weights; disagreement
  by one category counts less than by three).
- **Fleiss' kappa** — ≥3 raters, categorical.
- **Krippendorff's alpha** — any number of raters, any measurement level, tolerates missing data.
- **ICC (intraclass correlation)** — **continuous** measurements; report the model + type (below).
- **Bland–Altman** — two continuous methods/raters: bias (mean difference) + 95% limits of agreement.
- NOT for: a single 2×2 vs a reference standard (that is diagnostic accuracy — see
  `table-types/diagnostic_accuracy.md`); not for a multi-reader AI-vs-human comparison with reader +
  case variance (that is an MRMC reader study — see `table-types/reader_study.md`).

---

## Pseudoreplication comes first (this, not the coefficient, is the issue)

If each **subject contributes more than one measurement** — several lesions, aneurysms, nodules,
slices, or time-points per patient — the rows are **not independent**. Computing agreement on the
**pooled** rows (or on all pairwise distances) uses an inflated *n*, narrows the CI, and gives an
**anti-conservative** p-value. This is the single most common reliability-study error a reviewer
catches (it is flagged by the self-review probe **O18** in `observational_confounding.md`).

Two correct paths — pick one and state it:

1. **Aggregate to the independent unit first**, then compute agreement per subject. This is the
   simplest defensible analysis when a per-subject summary is meaningful (e.g. mean measurement,
   majority label, or one index lesion per subject).
2. **Model the clustering** — a mixed-effects / variance-components ICC with a **subject random
   effect** (or a GEE with an exchangeable working correlation), so the within-subject correlation
   is estimated rather than ignored.

A pooled-pairwise test can *flip* on correction: e.g. Mann–Whitney p = 0.02 on 448 pooled
pairwise distances became p = 0.59 at the per-aneurysm level (n = 112). **Report the unit of
analysis explicitly**, and when subjects have multiple measurements report a per-subject
sensitivity analysis.

### Produce the pseudoreplication-safe version

```python
import pandas as pd
import pingouin as pg   # ICC with model/type + CI

# long format: one row per (subject, measurement); rater columns rater1..raterK
df = pd.read_csv("ratings.csv")

# 1) DETECT clustering: more rows than independent subjects
n_rows, n_subjects = len(df), df["subject_id"].nunique()
if n_rows > n_subjects:
    print(f"CLUSTERED: {n_rows} measurements from {n_subjects} subjects "
          f"({n_rows / n_subjects:.1f} per subject) — do NOT pool as independent.")

# 2a) PER-SUBJECT AGGREGATION (continuous): mean per subject, then ICC on subject means
per_subj = df.groupby("subject_id")[["rater1", "rater2"]].mean().reset_index()
long = per_subj.melt(id_vars="subject_id", var_name="rater", value_name="score")
icc = pg.intraclass_corr(data=long, targets="subject_id", raters="rater", nan_policy="omit")
print(icc[["Type", "ICC", "CI95%"]])   # report Type (e.g. ICC2/ICC2k) + CI

# 2b) OR MODEL THE CLUSTERING (keep every measurement, subject random effect)
import statsmodels.formula.api as smf
df_long = df.melt(id_vars="subject_id", value_vars=["rater1", "rater2"],
                  var_name="rater", value_name="score")
m = smf.mixedlm("score ~ 1", data=df_long, groups=df_long["subject_id"])
res = m.fit()
var_between = float(res.cov_re.iloc[0, 0]); var_resid = float(res.scale)
icc_clustered = var_between / (var_between + var_resid)
print(f"variance-components ICC (subject random effect) = {icc_clustered:.3f}")
```

---

## ICC: state the model and the type (they are not interchangeable)

- **Model**: one-way random (raters differ per subject), two-way random (same raters, generalise to
  a rater population), two-way mixed (same raters, these raters only).
- **Type**: **agreement** vs **consistency** (agreement penalises systematic rater bias; consistency
  does not), and **single** vs **average** measurement (average-of-k is higher — only report it if
  the clinical use averages k raters).
- Report as e.g. **ICC(2,1) = 0.82 (95% CI 0.74–0.88), two-way random, absolute agreement, single
  rater**. An ICC with no model/type is not interpretable.

---

## Agreement is not reliability

- **Agreement** = do raters give the *same value* (absolute; Bland–Altman bias, absolute-agreement ICC).
- **Reliability** = can raters *rank/discriminate subjects* consistently (relative; consistency ICC,
  Pearson/Spearman). A method can be highly reliable yet have poor agreement (a constant offset).
  State which one the clinical claim needs, and use the matching coefficient.

---

## Reporting

- The coefficient **with a 95% CI** (bootstrap or analytic), the model/type (for ICC), and the
  **unit of analysis** (per-subject vs per-lesion, and the clustering handling).
- The interpretation band used (e.g. Landis–Koch), but do not over-interpret a point estimate whose
  CI spans two bands.
- For continuous methods: Bland–Altman **bias + 95% limits of agreement**, not just a correlation.

---

## Common failures (flag at review)

- **Pooled/pairwise agreement on clustered data** (pseudoreplication) — the headline coefficient's
  CI is too narrow; re-run per-subject or with a subject random effect (probe O18).
- **ICC reported with no model/type** — uninterpretable; the same data yields different ICCs.
- **Reliability coefficient used to claim agreement** (or vice versa) — a high consistency ICC does
  not establish that the two methods are interchangeable.
- **Correlation (r) reported as agreement** for two methods — r ignores a constant/proportional bias;
  Bland–Altman is required.
- **Kappa on ordinal labels unweighted** — treats a one-category disagreement as a full disagreement.

---

## Anti-Hallucination

- Never hand-type a coefficient or CI — compute it from the ratings CSV with a seeded script.
- Do not quote an ICC without the model/type actually estimated by the code.
- If subjects have multiple measurements, the per-subject sensitivity analysis is **mandatory** —
  do not report only the pooled number.
