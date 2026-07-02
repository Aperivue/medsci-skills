# Diagnostic Accuracy & Reader-Study Guide

Estimating how well an index test (or an AI model / reader) separates disease from
no-disease against a reference standard. The point estimates are easy to compute; the
ways these analyses fail review are (1) reporting AUC / sensitivity / specificity **without
CIs or on the wrong analysis unit**, (2) a **confidence-weighted / rating** score whose
novelty is never tested against the simpler **unweighted** baseline, and (3) comparing two
AUCs with a **fixed-reader** test when the claim is meant to **generalise to readers**.

---

## When to Use

- **Single index test** vs a reference standard → sensitivity, specificity, PPV, NPV, accuracy
  (each with a 95% CI), and AUC (with a DeLong or bootstrap CI).
- **Two tests / models on the same cases** → a **paired** AUC comparison (DeLong `roc.test`,
  `paired = TRUE`) — never two independent CIs eyeballed for overlap.
- **Multi-reader multi-case (MRMC)** reader study (AI-vs-reader, modality comparison) → an
  MRMC method (Obuchowski–Rockette / DBM) that carries **reader + case** variance; see
  `table-standards/table-types/reader_study.md` and `make-figures` `exemplar_plots/mrmc_roc.md`.
- NOT for: pooling accuracy across studies (that is a DTA meta-analysis — bivariate / HSROC via
  `mada`; see the `/meta-analysis` DTA path); not for rater **agreement** (that is
  `analysis_guides/agreement_reliability.md`).

---

## Every metric with a CI, on a stated analysis unit (the floor)

A bare AUC / sensitivity / specificity is not reportable. Compute the CI, and state the unit
(**per-patient vs per-lesion** — multiple lesions per patient are clustered, exactly as in
`agreement_reliability.md`; a per-lesion count inflates *n*).

```python
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from statsmodels.stats.proportion import proportion_confint

df = pd.read_csv("reader_calls.csv")   # truth (0/1), call (0/1), confidence (1..K), stratum

# sensitivity / specificity / PPV / NPV at the operating point, each with a Wilson CI
tp = int(((df.truth == 1) & (df.call == 1)).sum()); fn = int(((df.truth == 1) & (df.call == 0)).sum())
tn = int(((df.truth == 0) & (df.call == 0)).sum()); fp = int(((df.truth == 0) & (df.call == 1)).sum())
for name, num, den in [("sensitivity", tp, tp+fn), ("specificity", tn, tn+fp),
                       ("PPV", tp, tp+fp), ("NPV", tn, tn+fn)]:
    lo, hi = proportion_confint(num, den, method="wilson")
    print(f"{name} = {num/den:.3f} (95% CI {lo:.3f}-{hi:.3f}), n={den}")
```

PPV and NPV are **prevalence-dependent** — do not transport them to a population with a
different base rate; report sensitivity/specificity (prevalence-invariant) plus the study
prevalence, and recompute predictive values at the target prevalence with Bayes' rule.

---

## The confidence-weighted trap comes first (this, not the AUC, is the issue)

When the novelty is a **confidence-weighted / rating-collapsed** score used as the ROC
predictor, you must (a) confirm the (call × confidence) encoding is **strictly monotone** — a
folded encoding silently collides the most-confident-positive with a negative call — and
(b) report the **unweighted binary-call AUC** beside the weighted one, so the weighting earns
its place. This is the produce-side of self-review / peer-review probe **D9**.

```python
K = int(df.confidence.max())

# intended strictly-monotone composite: negative calls rank below positive calls, and within
# a call higher confidence pushes further from the decision boundary.
def composite(call, conf, K):
    return np.where(call == 1, K + conf, K + 1 - conf)   # neg: 1..K, pos: K+1..2K

# (1) MONOTONIC-ENCODING CHECK — every distinct (call, confidence) must map to a distinct,
#     correctly-ordered score. A collision is the folded-score bug (e.g. real/1 == ai/1).
combos = df[["call", "confidence"]].drop_duplicates().copy()
combos["score"] = composite(combos.call.values, combos.confidence.values, K)
if combos.score.nunique() != len(combos):
    raise ValueError("ENCODING COLLISION — the confidence weighting is not strictly monotone "
                     "(folded-score bug); fix the encoding before computing AUC.")

# (2) UNWEIGHTED BASELINE beside the weighted primary
df["score"] = composite(df.call.values, df.confidence.values, K)
print(f"AUC (confidence-weighted) = {roc_auc_score(df.truth, df.score):.3f}")
print(f"AUC (unweighted binary call) = {roc_auc_score(df.truth, df.call):.3f}")
```

If the weighted AUC materially exceeds the unweighted one, the weighting must be justified;
if it does not, report the simpler estimator as primary. A weighted score that changed a
hypothesis's direction versus its unweighted baseline is a **post-lock change to disclose**,
not a silent primary.

---

## AUC confidence intervals and comparing two AUCs

DeLong is the field-standard analytic AUC CI and paired comparison; `pROC` (R) is canonical.

```r
library(pROC)
d  <- read.csv("reader_calls.csv")
rw <- roc(d$truth, d$score, quiet = TRUE)
ci.auc(rw)                                   # DeLong 95% CI for the weighted AUC
ru <- roc(d$truth, d$call,  quiet = TRUE)
roc.test(rw, ru, method = "delong", paired = TRUE)   # paired, SAME cases (fixed-reader)
```

A portable Python bootstrap CI (use when a DeLong implementation is unavailable):

```python
def auc_ci_bootstrap(y, s, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed); y = np.asarray(y); s = np.asarray(s); n = len(y)
    boots = [roc_auc_score(y[i], s[i]) for i in (rng.integers(0, n, n) for _ in range(n_boot))
             if len(np.unique(y[i])) == 2]
    return tuple(np.percentile(boots, [2.5, 97.5]))
```

**Fixed-reader vs MRMC.** A paired DeLong test treats the readers/cases as fixed. If the claim
is that the result **generalises to readers** (a reader sample), a fixed-reader CI understates
uncertainty — use an MRMC method (Obuchowski–Rockette / DBM) that carries reader + case
variance, report per-reader and reader-averaged AUC, and state the unit (per-patient vs
per-lesion) and the superiority/non-inferiority margin. This is probe D9's MRMC lead.

---

## Per-stratum admissibility: produce the table the claim is checked against (D10)

A blanket "no subgroup met AUC ≥ 0.75 with lower bound ≥ 0.70" is falsified by a single tabled
stratum that meets it. Produce the per-stratum AUC + CI and test each row against the rule
rather than asserting a global negative.

```python
rule = lambda auc, lo: (auc >= 0.75) and (lo >= 0.70)
for name, g in df.groupby("stratum"):
    if g.truth.nunique() < 2:                       # single-class stratum: not estimable
        print(f"{name}: not estimable (one class)"); continue
    auc = roc_auc_score(g.truth, g.score); lo, hi = auc_ci_bootstrap(g.truth, g.score)
    print(f"{name}: AUC {auc:.3f} (95% CI {lo:.3f}-{hi:.3f}) "
          f"{'QUALIFIES' if rule(auc, lo) else 'below'}")
```

With *k* strata some crossings are expected — frame qualifying strata as hypothesis-generating
(note the multiplicity), but do **not** deny a row the paper's own table satisfies.

---

## One scale per comparison (D11)

Two values sharing a comparison column (or a row-wise "A vs B") must be computed under the
**same normalisation / definition** — e.g. both volume errors as a standard relative error, not
one relative and one range-normalised. If they are not identical, recompute on a common scale
before any superiority/comparability claim, or footnote "not on the same scale".

---

## Reporting

- Sensitivity, specificity, PPV, NPV, accuracy, and AUC each **with a 95% CI**; the operating
  point and how it was chosen (Youden vs a prespecified clinical threshold — a threshold picked
  on the same data is optimistic and needs a held-out or cross-validated estimate).
- The **analysis unit** (per-patient vs per-lesion) and clustering handling; study prevalence.
- For a weighted-score primary: the **unweighted-baseline AUC** beside it (D9).
- AUC alone is insufficient for a clinical claim — pair discrimination with **calibration** and a
  **decision-curve / net-benefit** pass at the relevant threshold (see the incremental-value
  table type and the `make-figures` decision-curve exemplar).

---

## Common failures (flag at review)

- **AUC / sensitivity / specificity with no CI**, or a per-lesion count reported as if per-patient.
- **Confidence-weighted AUC with no unweighted baseline** and no monotonic-encoding check (D9) —
  the weighting may have created the result or hidden a folded-score bug.
- **Two AUCs compared by CI overlap** instead of a paired DeLong test; a **fixed-reader** CI used
  for a claim that generalises to readers (needs MRMC).
- **"No stratum met the rule" contradicted by the per-stratum table** (D10).
- **Mixed-normalisation head-to-head** in one column (D11).
- **PPV/NPV transported** across a prevalence change.

---

## Anti-Hallucination

- Never hand-type an AUC, sensitivity/specificity, or CI — compute it from the calls CSV with a
  seeded script; carry each estimate together with its CI (never a bare AUC).
- Do not report a weighted-score AUC without the unweighted baseline the code produced.
- Do not quote a DeLong comparison p-value that a paired test on the same cases did not produce.
