# Rung 3b — the counterfactual arm, pre-specified

**Written before the arm was run.** Dated 2026-08-01, after rung 3 was scored and after the review
panel, but before any rung-3b prediction existed. The chronology caveat that applies to
`EVALUATION_PLAN.md` applies here too: this file's ordering relative to the results is documented by
the authors, not provable from the repository.

## Why this arm exists

The review panel's second Fatal finding was that the study asserted a cause its design could not
identify:

> Table 4 shows that `CTNormalization` transforms CT and MRI differently, but it does not show that
> this transformation *caused* the MRI Dice collapse rather than the CT-trained representation's
> inability to segment MRI, or an interaction between both. No correctly configured MRI
> counterfactual was attempted.

That is correct, and it cannot be answered by rewording. It needs one more arm.

## The intervention, and what it must not change

**One thing changes: the intensity scale of the input.** Same checkpoint, same five folds, same
ensemble, same test-time augmentation, same postprocessing, same ground truth, same metrics, same
denominator rules. Nothing about the model is retrained or re-tuned.

Each MRI volume is affinely mapped so that the intensity range the trained plan expects to see is
the range the image actually occupies:

- Compute the 0.5th and 99.5th percentiles of the MRI's **in-body** voxels (`value > 0`; AMOS MRI air
  is exactly 0, so this is the body without needing a segmentation).
- Map that range linearly onto the CT fingerprint's foreground range, `[-38, 174]` HU, read from the
  trained `plans.json` rather than typed in.
- Leave air at 0 mapped below the floor, where it clips — which is what CT air does.

After this mapping the plan's `CTNormalization` performs on MRI the operation it performs on CT:
the clip stops discarding most of the body, and the z-score lands soft tissue near where the network
was trained to find it. **The normaliser is not bypassed or replaced.** It is given input in the
domain it assumes, which is the whole point.

## Why this mapping and not another

A percentile match is the weakest intervention that fixes the declared defect. Alternatives were
rejected in advance:

- **Histogram matching to a CT template** would import CT tissue-contrast structure into the MRI and
  would confound the question — a recovery could then be the template's doing.
- **Retraining or fine-tuning on MRI** answers a different question entirely (can this architecture
  learn MRI?) and destroys the comparison, because the representation would no longer be the one
  that failed.
- **Z-scoring each MRI volume independently** (`ZScoreNormalization`, what nnU-Net would have chosen
  had the dataset been declared MR) is a reasonable alternative and is *not* run here, because it
  changes the normaliser rather than the input and so tests a different counterfactual. It is named
  as the obvious follow-up.

## Prediction, written before the run

Percentile matching restores the *dynamic range* the network expects but **cannot** restore CT
tissue contrast: in CT, the [-38, 174] window separates fat, muscle, spleen and vessel by physics,
and no affine map makes an MRI sequence's contrast agree with that ordering. So:

**Predicted: a partial recovery. Median Dice rises clearly above the 0.0152 of rung 3, and stays far
below the 0.8932 of the CT arm. A plausible interval is 0.1 to 0.6, and if pressed for one number,
around 0.3.**

Interpretation fixed in advance, so the result cannot be read whichever way flatters the paper:

| Outcome | What it establishes |
|---|---|
| Dice recovers to near the CT arm | The normalisation contract was the dominant cause. The paper's original framing was right and its hedge too strong. |
| Dice recovers substantially but not near CT (**predicted**) | Both mechanisms are real. Normalisation is a necessary part of the explanation and not the whole of it; the representation does not fully transfer. |
| Dice stays near zero | The normalisation incompatibility, though real and measured, was **not** the operative cause. The paper's identification paragraph is vindicated and its emphasis on the normaliser must be reduced. |

The third outcome would be the most damaging to the current write-up, and it is the reason this arm
is worth running rather than arguing about.

## What this arm still will not establish

It compares two input scalings of one model on one modality pair. It does not measure how often
this failure mode occurs in the wild, does not involve an independent user, and does not make the
single worked example generalisable. The panel's third Fatal finding stands regardless of what
rung 3b returns.

---

## Outcome (2026-08-01, appended after the run — the prediction above is unedited)

**Rung 3b median Dice 0.3016 (95% CI 0.1744–0.4048)**, against rung 3's 0.0152 (0.0000–0.0626).
Empty predictions fell from 20 of 60 to 15. Differences in population medians, both arms resampled
independently:

| contrast | difference [95% CI] |
|---|---|
| 3b − 3 (rescaled − as shipped) | **+0.2864** [+0.1204, +0.4048] |
| 3b − 2 (rescaled − external CT) | **−0.5916** [−0.7259, −0.4674] |
| 3b − 1 (rescaled − internal) | −0.6579 [−0.7924, −0.5392] |

Neither interval crosses zero.

**This is the second row of the interpretation table: both mechanisms are real.** Of the −0.878
separating external CT from MRI, roughly **0.29 is attributable to the preprocessing contract** and
roughly **0.59 to a representation that does not transfer**; the two account for that gap in full.
Measured against *internal* instead, the residual after rescaling is the larger −0.6579 row above,
because that comparison also carries the same-modality internal-to-external CT drop — which is why
0.29 and 0.59 do not sum to the −0.944 headline. Fixing the input scale — no retraining, same
checkpoint, same folds, same TTA — multiplied median Dice by twenty, and still left the arm far below
the CT cohort.

The written prediction ("partial recovery, 0.1 to 0.6, around 0.3 if pressed") was right in direction
and in rough magnitude. It was a wide interval and a single prediction; it is recorded as a
calibration data point, not as evidence that the reasoning behind it was sound.

**What changes in the manuscript.** The identification hedge — "documented and sufficient to account
for the magnitude, not isolated as the sole cause" — is replaced by the measured decomposition. That
is a *stronger* result than the hedge, and a weaker one than the original draft's "located the
cause": the normalisation contract is a major cause and not the only one.

**What does not change.** This still compares two input scalings of one model on one modality pair.
The panel's finding that a single authored example cannot ground general claims about tooling stands
untouched.

---

# Rung 3c — the normaliser counterfactual, pre-specified

**Written before the arm was run**, 2026-08-01, after rung 3b was scored. Same chronology caveat.

## Why a second counterfactual

Rung 3b fixed the **input** so the CT normaliser would behave. It left the obvious alternative
unasked: what if the **normaliser itself** had been the right one? nnU-Net picks
`ZScoreNormalization` when a dataset declares a non-CT modality, and AMOS's `dataset.json` declares
`"modality": {"0": "CT"}` for a collection containing 100 MRI volumes. So this arm asks what the
pipeline would have done had that one field been correct.

The two arms are not redundant. 3b keeps the wrong normaliser and repairs its input; 3c keeps the
original input and replaces the normaliser. If they land in the same place, the mechanism is the
intensity domain and nothing else. If they differ, the *form* of the transform matters too — a
per-volume z-score preserves the full intensity distribution, while a percentile match into a fixed
window compresses it into 213 levels and discards the tails.

## The intervention, and what it must not change

`normalization_schemes` in the trained `plans.json` is patched from `["CTNormalization"]` to
`["ZScoreNormalization"]`, in a **copy** of the results directory. Nothing else changes: the same
five fold checkpoints, the same target spacing, the same patch size, the same ensemble, the same
test-time augmentation, the **original unrescaled MRI images**, the same ground truth, the same
metric rules. The weights never see a gradient.

This is deliberately a *misuse* of nnU-Net in one narrow sense — the plan a model was trained under
is not meant to be edited afterwards — and that is exactly the point: it isolates the normalisation
choice from everything the fingerprint otherwise fixes. A model trained under a z-score plan would
be a different experiment, and is not this one.

## Prediction, written before the run

A per-volume z-score maps each MRI onto zero mean and unit variance without a fixed window, so it
preserves the distribution's shape and its tails, which the percentile match into `[-38, 174]` does
not. Against that, the network's learned filters expect the *specific* intensity statistics of the
CT fingerprint, and a z-score puts MR soft tissue at a different place in that space than CT soft
tissue sits.

**Predicted: rung 3c lands close to rung 3b, plausibly a little above it. A range of 0.20 to 0.50,
and around 0.35 if pressed for one number. I do not expect it to approach the CT arm's 0.8932.**

Interpretation fixed in advance:

| Outcome | What it establishes |
|---|---|
| 3c ≈ 3b | The intensity **domain** is the whole of the preprocessing story; the form of the transform does not matter. |
| 3c clearly > 3b | The form matters too — discarding the tails into a fixed window costs real performance beyond the domain mismatch. |
| 3c clearly < 3b | A z-score is *worse* than matching the CT window, i.e. the network depends on the absolute CT intensity scale and not merely on having usable dynamic range. |
| 3c ≈ 0.015 | The whole preprocessing account is wrong and rung 3b's recovery came from something the plan did not name. This would be the most damaging outcome and is why the arm is worth running. |

## What neither counterfactual can establish

Both keep a CT-trained representation fixed. Neither says what a model trained on MR would do, and
neither makes this single worked example generalisable.

---

## Outcome, rung 3c (2026-08-01, appended after the run — the prediction above is unedited)

**Median Dice 0.2870 (95% CI 0.1348–0.3546)**, against rung 3b's 0.3016 and rung 3's 0.0152. Empty
predictions 15 of 60, the same as 3b (the arm as shipped had 20).

| contrast | difference [95% CI] |
|---|---|
| 3c − 3 (z-score − as shipped) | **+0.2718** [+0.0947, +0.3546] |
| **3c − 3b** (z-score − rescaled input) | **−0.0146** [−0.2136, **+0.1575**] — **includes zero** |
| 3c − 2 (z-score − external CT) | −0.6062 [−0.7613, −0.5168] |

**This is the first row of the interpretation table: the intensity *domain* is the whole of the
preprocessing story, and the *form* of the transform does not matter.** Three independent signals
agree: the medians differ by 0.015 with an interval that comfortably spans zero; both arms leave the
same 15 empty predictions; and the two arms' per-case Dice correlate at **r = 0.939** across 59
cases, so they succeed and fail on the same images rather than trading wins.

Two entirely different repairs — rescale the input under the wrong normaliser, or swap the
normaliser and leave the input alone — arrive at the same place. What mattered was only whether the
data reached the network in the intensity domain it was trained in.

**The prediction was inside its stated range and wrong in direction.** It said "0.20 to 0.50, around
0.35, plausibly a little above 3b", reasoning that a per-volume z-score preserves distribution tails
that a percentile match into a fixed window discards. The measured difference is −0.0146 and its
interval spans zero: that reasoning is not supported. Recorded here rather than quietly dropped —
and it lowers the weight the previous arm's on-the-nose prediction should carry.

**What this settles about `dataset.json`.** AMOS declares `"modality": {"0": "CT"}` for a collection
containing 100 MRI volumes, and nnU-Net would have selected `ZScoreNormalization` had that field
been right. Rung 3c is that world, and it reaches **0.2870** — far short of the CT arm's 0.8932.
**Correcting the metadata field would not have been enough.**

## Verifying that the arm did what it claims

The sbatch log echoes a hardcoded results path and is therefore not evidence that the patched plan
was used. nnU-Net writes its plan into its own output directory; that file is the evidence, and it
is committed at `qc/rung3c_plans_used.json`:

- rung 3c output plan → `["ZScoreNormalization"]`
- rung 3b output plan → `["CTNormalization"]`

Only `normalization_schemes` differs from the trained plan; every other configuration field is
byte-identical and the five fold checkpoints are the same files.
