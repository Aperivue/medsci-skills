# Demo 5 — MSD → AMOS spleen segmentation, and the gate that had to fail

The other demos show green checkmarks. **This one shows the toolkit rejecting something, and the
author being wrong.**

nnU-Net v2 trained on 32 MSD Task09 cases, evaluated on three labelled rungs of increasing distance.
Nine days on a GPU cluster. **Tooling demonstration, not a clinical claim.**

| Rung | Cohort | n scored | Dice median [95% CI] |
|---|---|---:|---|
| 1 internal | MSD held-out | 9 | 0.9595 [0.9367–0.9734] |
| 2 genuine external | AMOS **CT** | 298 / 300 | 0.8932 [0.8633–0.9108] |
| 3 modality shift | AMOS **MRI** | 59 / 60 | **0.0152** [0.0000–0.0626] |

## The one thing to look at

**The obvious way of using nnU-Net fails this repository's own gate, and `reproduce.sh` checks that
it fails.** nnU-Net fits its resampling target and intensity statistics from whatever sits in its raw
directory — the fit scope is a copy decision, not a flag. Drop every case in and split afterwards and
the fingerprint is fit on your held-out set:

```
$ bash reproduce.sh
[3/5] the counterfactual — the SAME gate must REJECT the obvious way of using nnU-Net
      PREPROCESS_BEFORE_SPLIT  Major  resample fitted before the split
      PREPROCESS_BEFORE_SPLIT  Major  clip_percentile fitted before the split
      PREPROCESS_BEFORE_SPLIT  Major  standardize fitted before the split
      -> rejected, as it must be.
```

A gate you only ever see pass is not evidence of anything. This one ships with the input that makes
it fail.

## Why rung 3 collapsed, and what it cost

The trained `plans.json` carries `CTNormalization` into inference, and `nnUNetv2_predict` has no
argument that declares the incoming modality. So a Hounsfield-unit clip was applied to images that
are not in Hounsfield units: **0 of 60 MRI cases contain a negative voxel** against 300 of 300 on CT.
The run exited 0 and returned a file for every case — 20 of them empty.

Two counterfactual arms, each changing one thing and neither retraining, put a number on it:

| arm | change | Dice |
|---|---|---|
| 3b | rescale the **input** into the plan's domain | 0.3016 |
| 3c | swap the **normaliser** to a z-score | 0.2870 |

They are indistinguishable (−0.0146, interval spans zero; per-case r = 0.939). **So of the −0.878
separating external CT from MRI, 0.29 Dice is the intensity domain and 0.59 a representation that
does not transfer** — the two account for that gap in full. The further 0.07 down to the internal arm
is a CT-to-CT cohort shift, not modality. Both predictions were written before their runs and the
second was wrong in direction and is kept — though this repository cannot prove that ordering, and
[`CASE_STUDY.md`](CASE_STUDY.md) says so.

**The uncomfortable part:** `/profile-imaging` had already flagged the mixed intensity scale before
training — as a **Minor**, in a directory no later step reads.

## Run it

```bash
bash reproduce.sh     # gates + the counterfactual that must fail + the full analysis, on a laptop
```

Training needs ~50 GPU-hours and two ~25 GB public datasets; those tiers are printed, not faked.

## Read more

- **[`CASE_STUDY.md`](CASE_STUDY.md)** — the full account, including what was wrong and got corrected
- **[`FRICTION.md`](FRICTION.md)** — every point in nine days that needed engineering knowledge
- **[`qc/self_review.md`](qc/self_review.md)** — a cross-substrate review panel that returned a
  Reject, and the eight findings accepted from it
- [`manuscript/`](manuscript/) · [`COUNTERFACTUAL_PLAN.md`](COUNTERFACTUAL_PLAN.md) ·
  [`presentation/`](presentation/) · [`EVALUATION_PLAN.md`](EVALUATION_PLAN.md)
