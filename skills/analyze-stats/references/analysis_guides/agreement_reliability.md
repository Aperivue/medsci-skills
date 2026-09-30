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
2. **Keep every measurement and carry the clustering into the CI** — the ICC's targets are the
   rated units (the lesions), so the point estimate uses them; the CI resamples **subjects** (a
   cluster bootstrap), or a variance-components model puts lesions within patients and a rater
   term in the denominator (below).

A pooled-pairwise test can *flip* on correction: e.g. Mann–Whitney p = 0.02 on 448 pooled
pairwise distances became p = 0.59 at the per-aneurysm level (n = 112). **Report the unit of
analysis explicitly**, and when subjects have multiple measurements report a per-subject
sensitivity analysis.

### Produce the pseudoreplication-safe version

```python
import numpy as np
import pandas as pd
import pingouin as pg   # ICC with model/type + CI

# long format: one row per (subject, measurement); rater columns rater1..raterK
df = pd.read_csv("ratings.csv")

# 1) DETECT clustering: more rows than independent subjects
n_rows, n_subjects = len(df), df["subject_id"].nunique()
if n_rows > n_subjects:
    print(f"CLUSTERED: {n_rows} measurements from {n_subjects} subjects "
          f"({n_rows / n_subjects:.1f} per subject) — do NOT pool as independent.")

def icc_table(d, targets):
    t = pg.intraclass_corr(data=d, targets=targets, raters="rater", ratings="score",
                           nan_policy="omit")
    ci = "CI95%" if "CI95%" in t.columns else "CI95"      # renamed in pingouin 0.7
    return t.rename(columns={ci: "CI95"})

def icc_agreement(t):   # ICC(A,1): two-way random, absolute agreement, single rater
    return float(t.loc[t["Type"].isin(["ICC2", "ICC(A,1)"]), "ICC"].iloc[0])

# 2a) PER-SUBJECT AGGREGATION (continuous): mean per subject, then ICC on subject means
per_subj = df.groupby("subject_id")[["rater1", "rater2"]].mean().reset_index()
long_s = per_subj.melt(id_vars="subject_id", var_name="rater", value_name="score")
print(icc_table(long_s, "subject_id")[["Type", "ICC", "CI95"]])   # report Type + CI

# 2b) OR KEEP EVERY MEASUREMENT: the rated target is the lesion, so the point estimate
#     uses lesion-level targets; the clustering goes into the CI by resampling SUBJECTS.
long = df.melt(id_vars=["subject_id", "lesion_id"], value_vars=["rater1", "rater2"],
               var_name="rater", value_name="score")
point = icc_agreement(icc_table(long, "lesion_id"))
rng = np.random.default_rng(42)
subjects = long["subject_id"].unique()
by_subj = {s: g for s, g in long.groupby("subject_id")}
boots = []
for _ in range(1000):
    draw = rng.choice(subjects, size=len(subjects), replace=True)
    b = pd.concat([by_subj[s].assign(lesion_id=by_subj[s]["lesion_id"].astype(str) + f"#{k}")
                   for k, s in enumerate(draw)])        # a subject drawn twice = new targets
    boots.append(icc_agreement(icc_table(b, "lesion_id")))
lo, hi = np.percentile(boots, [2.5, 97.5])
print(f"ICC(A,1), lesion targets = {point:.3f} (95% CI {lo:.3f}-{hi:.3f}, bootstrap over subjects)")
```

The bootstrap holds the raters fixed (it resamples subjects, the independent units). In R, the
same estimand as a variance-components model, with lesions nested in patients and raters
crossed:

```r
library(lme4)
m <- lmer(score ~ 1 + (1 | subject_id) + (1 | subject_id:lesion_id) + (1 | rater), data = long)
v <- as.data.frame(VarCorr(m)); g <- setNames(v$vcov, v$grp)
# ICC(A,1) = (patient + lesion-within-patient) / (patient + lesion + rater + residual)
(g["subject_id"] + g["subject_id:lesion_id"]) / sum(g)
```

Do **not** compute `var_patient / (var_patient + var_residual)` from a model with only a
patient random effect: the lesion-to-lesion variance then sits in the residual and there is no
rater term, so the ratio measures how alike a patient's lesions are, not how well raters agree.
On synthetic data (60 patients x 3 lesions, 2 raters, rater error SD 0.5) that ratio was 0.33
while ICC(A,1) on the lesions was 0.977 (pingouin) and 0.977 (the `lmer` model above).


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
  CI is too narrow; re-run per-subject, or keep the measurements as targets with a subject-level
  (cluster) bootstrap CI (probe O18). A patient-only random-effect ratio is not an ICC.
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
