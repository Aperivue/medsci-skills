# Demo 5 — Evaluation plan (pre-specified)

**Written before any prediction exists.** At the time of writing, folds 0/1/2 are at 17/9/12
epochs of 100, folds 3-4 have not started, and no inference has been run. Everything below is
therefore a commitment, not a description — and where it makes a prediction, the prediction can
be wrong in public.

Skill: `/model-evaluation` (shipped). Gate: `check_metric_reporting.py --task segmentation --strict`.

---

## 1. Analysis unit and task

One case = one patient = one analysis unit. No repeat studies in either dataset, so
per-case and per-patient coincide; no per-lesion metric is reported as per-patient.

Task: binary 3-D segmentation of a single structure (spleen). "Per structure" therefore
degenerates to one structure — which is stated rather than used to skip the requirement.

## 2. Metrics

Per case: **Dice** and **HD95** (boundary metric — Dice alone is not sufficient). Reported as
median with bootstrap 95 % CI over cases (10,000 resamples, seed recorded). A per-case CSV is
emitted for `/analyze-stats`.

Accuracy is not reported, at any point, in any arm. The target occupies 0.2–0.4 % of the volume;
predicting background everywhere scores >99.6 %.

## 3. Ground-truth harmonisation

MSD Task09 labels are already binary (0 background, 1 spleen).

AMOS22 labels are a 15-organ atlas. They are binarised to `label == 1` (spleen) — the index is
read from the shipped `dataset.json`, not assumed. Every other organ index becomes background.

## 4. Cases with no target — decided before the results

Counting the spleen directly across all 360 labelled AMOS cases found **three with no spleen
voxel at all**: `amos_0057`, `amos_0115` (CT) and `amos_0541` (MRI). Dice is undefined when the
reference is empty (0/0), so a rule is needed and it must be fixed now rather than chosen once
the numbers are visible.

- They are **excluded from the Dice and HD95 distributions**, which makes the arm denominators
  **CT 298 / 300** and **MRI 59 / 60**. Both the numerator and the exclusion are reported.
- They are **reported separately** as a false-positive check: predicted spleen volume in mL on a
  case that has none. A model that outputs nothing on all three is behaving correctly; a model
  that hallucinates an organ is a finding worth its own line, not a silent zero folded into a
  mean.
- Whether the absence is a splenectomy or an annotation omission is **not** determined here.
  Either way it is a limitation to state, and it does not change the rule above.

Dropping these silently would have moved the external Dice with nothing on the record to explain
it — which is exactly the failure the shipped profiler could not see until `--target-label`
existed (PR #400).

## 5. The three rungs, and what each can support

| Rung | Data | n | What it establishes |
|---|---|---|---|
| 1 internal | MSD held-out | 9 | the pipeline runs end to end on the source distribution |
| 2 external | AMOS **CT** | 298 (+2 target-free) | performance across centres, vendors, phases |
| 3 modality shift | AMOS **MRI** | 59 (+1 target-free) | a CT-trained model meeting an unseen modality |

**Rung 1 is not an independent test of nnU-Net.** nnU-Net won the 2018 MSD challenge, and its
self-configuring heuristics were developed against that benchmark family. The internal number
demonstrates the pipeline; it does not evidence the method. AMOS22 (2022) post-dates nnU-Net
(2021), so rungs 2 and 3 are where the independent evidence lives. This sentence is in the plan
so it cannot be quietly dropped if rung 1 comes out flattering.

## 6. Pre-registered prediction for rung 3

The model is trained with nnU-Net's `CTNormalization`, whose parameters come from the training
fingerprint: clip to **[-38, 174] HU**, then z-score with **mean 89.8, sd 39.8**.

AMOS MRI voxels are non-negative arbitrary units reaching ~186,000 (`amos_0501`: min 0,
p99 92,299, max 186,452). Pushing that through the CT normaliser clips essentially all tissue to
the 174 ceiling and all background to 0, giving a volume with only two values:

- tissue → (174 − 89.8) / 39.8 = **+2.12**
- background → (0 − 89.8) / 39.8 = **−2.26**

**Prediction: rung-3 Dice collapses toward zero, and the cause is the preprocessing contract
rather than the network failing to generalise visually.** If that is what happens, the honest
conclusion is not "CT-trained models do not transfer to MRI" but "this pipeline's normalisation
is undefined outside the modality it was fitted on" — a narrower and more useful claim. If
rung 3 instead produces a usable Dice, this prediction was wrong and that gets written down.

Note this is also why AMOS's `dataset.json` declaring `"modality": {"0": "CT"}` for a dataset
containing 100 MRI volumes is a real hazard and not a typo: it is the field a pipeline reads to
decide which normaliser to apply.

## 7. Pre-specified subgroups

Chosen from the dataset profile, before any result:

1. **Spleen volume tertile.** MSD spans 56–502 mL; AMOS spans 15–954 mL (CT median 183, MRI
   median 188). Normal is roughly 100–250 mL, so both cohorts contain splenomegaly and the
   external arm is wider at *both* ends than the training distribution. Question fixed in
   advance: does accuracy degrade on enlarged spleens, and does it degrade on very small ones?
2. **Slice thickness.** MSD spans 1.5–8.0 mm within one institution; this is the axis the
   external set was always going to differ on, and it is the axis the resampling decision acts
   on.
3. **Modality** (rungs 2 vs 3) — by construction, not a post-hoc slice.

## 8. Inference configuration

5-fold ensemble, `3d_fullres`, nnU-Net default inference (mirroring TTA on). Reduced training
length (100 epochs vs the default 1000) is disclosed wherever a number from this model is
reported. If any fold fails to complete, the ensemble composition actually used is stated rather
than implied.

## 9. What gets disclosed regardless of outcome

- 100-epoch schedule = one tenth of nnU-Net's default (arithmetic in the journal, Stage 5).
- Single configuration (`3d_fullres`); nnU-Net's own configuration search across 2d /
  3d_lowres / cascade was **not** run, so this is nnU-Net-the-network, not nnU-Net-the-method.
- Internal arm's provenance conflict (§5).
- Target-free case handling and the resulting denominators (§4).
- Training cohort n = 32 after the held-out carve, single institution.
