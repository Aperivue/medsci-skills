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

**This is the second row of the interpretation table: both mechanisms are real.** Of the −0.944
observed against internal, roughly **0.29 is attributable to the preprocessing contract** and roughly
**0.59 to a representation that does not transfer**. Fixing the input scale — no retraining, same
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
