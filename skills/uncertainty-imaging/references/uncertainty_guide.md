# Uncertainty / OOD guide (uncertainty-imaging)

Load-on-demand notes for adding a defensible uncertainty / out-of-distribution (OOD) /
abstention layer to a deployment-framed medical-imaging model. Integrate the libraries
named here — do not reimplement them.

## Which uncertainty method

| Method | What it gives | Cost | Use when |
|---|---|---|---|
| **Conformal prediction** (MAPIE) | Distribution-free prediction sets/intervals at a nominal coverage | 1 model + a calibration set | You have a held-out calibration set; the strongest default. **Validate empirical coverage.** |
| **Deep ensembles** (Lakshminarayanan 2017) | Best-quality epistemic uncertainty | K× training | You can afford K independent members (distinct seeds/inits). |
| **MC-dropout** (Gal 2016) | Cheap approximate epistemic uncertainty | T× inference | A dropout network already exists; keep dropout **on** at inference. |
| **Last-layer Laplace** (laplace-torch) | Post-hoc Bayesian on the final layer | Light | You want a Bayesian estimate without retraining. |

Aleatoric (data noise) vs epistemic (model ignorance) differ: epistemic shrinks with more
data and is what flags OOD/novel cases; ensembles and Bayesian methods capture it, a single
softmax does not.

## Conformal prediction — the coverage check is the point
Conformal guarantees marginal coverage **only under exchangeability**, which clinical data
routinely violates (scanner drift, temporal shift, site mix). So the guarantee is a promise
until you **measure achieved coverage** on a held-out calibration/test split against the
nominal target (e.g. nominal 90% → empirical 88–92%). Report the interval width too — a set
that always contains every class is vacuously "covered". For classification use APS/RAPS;
for regression use CQR. `CONFORMAL_NO_COVERAGE_VALIDATION` fires when coverage is unmeasured.

## Deep ensembles — members must be independent
The uncertainty comes from **disagreement between members**, which requires each member to be
trained from a **distinct seed / initialisation** (and ideally data order). K = 5 is the
common default. Members that share a seed collapse to near-identical predictions and
under-estimate epistemic uncertainty (`ENSEMBLE_NOT_INDEPENDENT`). Snapshot ensembles are
cheaper but weaker — disclose which you used.

## MC-dropout — dropout must stay on
MC-dropout samples T stochastic forward passes with dropout **active at inference**
(`model.train()` on the dropout layers, or functional dropout with `training=True`). With
dropout off (the default `model.eval()`), every pass is identical and the "uncertainty" is a
point prediction (`MCDROPOUT_DISABLED_AT_INFERENCE`). This is the one place the lane's usual
"infer under eval mode" rule is deliberately overridden — and only for the dropout layers.

## OOD detection — evaluate on held-out OOD data
An OOD score (energy, Mahalanobis distance on penultimate features, ODIN, or max-softmax) is
only as good as its **operating point on data known to be OOD** — a different scanner, site,
or pathology than training. Report detection AUROC / FPR@95%TPR on that held-out OOD set and
the threshold you would deploy. An OOD claim tested only in-distribution is unmeasured
(`OOD_NO_HELDOUT_SET`). Near-OOD (same modality, unseen pathology) is much harder than
far-OOD (a chest X-ray fed to a brain-MR model) — say which you tested.

## Selective prediction — pre-specify the operating point
Abstention (reject option) trades coverage for accuracy: below a confidence/uncertainty
threshold the model defers to a human. Choosing that threshold **after** seeing the test
accuracy inflates the reported accuracy-at-coverage. Pre-specify the target coverage or risk,
report the **risk–coverage curve** (and AURC), and state who handles abstained cases
(`SELECTIVE_NO_TARGET`).

## Calibration under shift
In-distribution calibration decays under deployment shift (Ovadia 2019). Report calibration
(ECE / a reliability diagram) and conformal coverage on **shifted or external** data, not
in-distribution only (`NO_CALIBRATION_UNDER_SHIFT`). Temporal (later-year) or external-site
data is the realistic stress; synthetic corruptions (noise, blur) are a weaker supplement.

## Reporting
Fill the uncertainty manifest and hand off to `/model-evaluation` (executed calibration /
subgroup) and `/analyze-stats` (calibration curve, risk–coverage plot). Deployment-framed
claims are governed by **TRIPOD+AI** and **DECIDE-AI** (early-stage clinical evaluation +
monitoring) — `/check-reporting` covers the items. State the method, the validation set, the
achieved coverage/AUROC, and the abstention policy; do not report a bare accuracy under a
deployment claim.

## Manifest schema
```json
{
  "task": "classification",
  "deployment_claim": true,
  "uncertainty_method": "conformal",         // conformal / mc_dropout / deep_ensemble / bayesian / none
  "coverage_target": 0.90,
  "coverage_validated": true,
  "ensemble_members": 5,
  "ensemble_independent": true,
  "mc_dropout_active_at_inference": true,
  "ood_method": "mahalanobis",               // energy / mahalanobis / odin / msp / none
  "ood_heldout_set": "external-ood-cohort",
  "selective_prediction": true,
  "selective_target": 0.95,
  "calibration_under_shift": true
}
```

## Hand-offs
- Point-predictor metrics + calibration this layer sits on → `/model-evaluation` → `/analyze-stats`.
- The split / validation-design audit → `/model-validation` (DECIDE-AI monitoring seam).
- Reporting fit → `/check-reporting` (TRIPOD+AI / DECIDE-AI).
