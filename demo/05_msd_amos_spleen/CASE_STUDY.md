# Demo 5 — case study

The long version. [`README.md`](README.md) is the 60-second one; everything below is what was
actually done, in the order it was done, including the parts that were wrong.

---

Demos 1–3 run the classical-stats / manuscript pipeline; Demo 4 runs the model-engineering lane on a
28×28 benchmark that trains in minutes. **Demo 5 is the one that leaves the laptop.** It asks a
narrower question than "does the toolkit work":

> Given a dataset, its labels and a task, can a clinician carry a deep-learning study to a
> defensible result **without an engineer** — and where exactly does that break?

The answer is a three-rung external-validation ladder for 3-D spleen segmentation, every rung
labelled, run on a real GPU cluster over nine days. **Tooling demonstration, not a clinical claim.**

> **Read rungs 1–2 and rung 3 differently.** Rungs 1 and 2 are ordinary internal and external
> validation. Rung 3 is a **constructed** test: while writing the evaluation plan we inspected the
> trained configuration, found it carries a CT intensity transform, and predicted in writing that
> MRI would collapse for that reason — then ran it anyway. So rung 3 does not show that this failure
> was *discovered* by an unaided clinician. It shows that when a pipeline is handed an input it
> cannot process, **nothing in the command, the logs or the output says so**. That is the claim, and
> it is narrower than "we found where the path breaks".

## Datasets

Both chosen on **access, not on story quality** — a demo about reproducibility cannot ship a first
step the reader cannot take.

| Dataset | Licence | How it downloads |
|---|---|---|
| MSD Task09 Spleen (MSKCC) | CC-BY-SA 4.0 | `s3://msd-for-monai/` with `--no-sign-request` |
| AMOS22 | CC BY 4.0 | Zenodo 7262581 |

ACDC → M&Ms is the better domain-shift pair and was rejected: it sits behind registration walls.
Third-party Hugging Face / Kaggle mirrors were rejected for provenance. **No data is vendored here.**

## The ladder

| Rung | Cohort | n scored | Dice median [95% CI] | HD95 mm (n) | ΔDice vs internal |
|---|---|---:|---|---|---|
| 1 internal | MSD held-out | 9 | **0.9595** [0.9367–0.9734] | 1.78 (9) | — |
| 2 genuine external | AMOS **CT** | 298 / 300 | **0.8932** [0.8633–0.9108] | 5.68 (270) | **−0.0662** [−0.0996, −0.0416] |
| 3 modality shift | AMOS **MRI** | 59 / 60 | **0.0152** [0.0000–0.0626] | 70.05 (40) | **−0.9443** [−0.9715, −0.8813] |
| 3b counterfactual | AMOS MRI, **input rescaled** | 59 / 60 | **0.3016** [0.1744–0.4048] | 39.98 (45) | **−0.6579** [−0.7924, −0.5392] |
| 3c counterfactual | AMOS MRI, **z-score normaliser** | 59 / 60 | **0.2870** [0.1348–0.3546] | 52.45 (45) | **−0.6724** [−0.8302, −0.5927] |

**HD95 carries its own n, and it is smaller than the Dice n.** A case whose prediction is empty has
a Dice of 0 but no predicted surface, so no boundary distance exists for it — and those are exactly
the cases that failed hardest. An HD95 median quoted against the Dice denominator is optimistic by
the worst cases in the arm, and the gap grows with the failure rate: 9/9, then 270/298, then
**40/59**. The review panel caught this; the author had reported one HD95 per arm with no n.

Bootstrap 10,000 resamples, seed 20260725, **seeded per (arm, metric)** so an arm's interval does
not depend on how many other arms were bootstrapped before it. Full table with subgroups: [`results/summary_across_cohorts.md`](results/summary_across_cohorts.md).
Figure: [`figures/across_cohorts_dice.png`](figures/across_cohorts_dice.png).

Three things the headline Dice hides, all pre-specified in [`EVALUATION_PLAN.md`](EVALUATION_PLAN.md)
before any prediction existed:

- **Target-free cases are never a silent zero.** Three of the 360 labelled AMOS cases contain no
  spleen voxel at all. Dice is undefined on them (0/0), so they are excluded from the distributions
  (hence 298/300 and 59/60) and reported on their own line. Two of the three were CT, and on **both**
  the model predicted a spleen that is not there.
- **28 of 300 external CT predictions were empty**, and 20 of 60 on MRI.
- **The model is worst where a radiologist would care.** Enlarged spleens (>250 mL) score **0.7694**
  (n=67) against 0.9114 for normal 100–250 mL (n=194). Splenomegaly is what a spleen segmentation is
  *for*, and 0.8932 conceals it.

## Rung 3 is the finding: a silent normaliser, not "MRI is hard"

A Dice of 0.015 is extreme enough that the first duty is to try to disprove it. Two rival
explanations were checked and both failed:

- **Wrong label index?** No. MRI ground truth carries labels 0–13 (the CT subset runs 0–15 — the MRI
  subset genuinely has fewer organs), spleen is `1` in both, and the reference volumes are
  physiological (median 187.6 mL over the 59 scored cases).
- **Not actually MRI?** No — see below; it is the *plan* that thinks it is CT.

`plans.json`, written at fingerprint time and carried into inference with the checkpoint, records
`normalization_schemes: ['CTNormalization']`: clip every voxel to the training foreground's
`[−38, 174]` HU, then z-score by mean 89.8 / sd 39.8. Replaying that contract over both external arms
([`pipeline/normalizer_modality_evidence.py`](pipeline/normalizer_modality_evidence.py) → `results/normalizer_evidence_*.json`)
measures what it does:

| | rung 2 AMOS CT (n=300) | rung 3 AMOS MRI (n=60) |
|---|---|---|
| cases with **any** negative voxel | **300 / 300** | **0 / 60** |
| voxels flattened at the clip ceiling | median **2.7 %** (1.0–6.9) | median **23.2 %** (0.3–68.6) |
| intensity levels surviving the clip | 213 (213–213) | 175 (**2**–175) |

Hounsfield units are defined by an air floor near −1000. The CT arm has one in every case; the MRI
arm has none in any, so `[−38, 174]` is not a soft-tissue window there — it is an arbitrary slice near
the bottom of an arbitrary-unit range, and it flattens up to two thirds of the volume. In the extreme
case the whole image survives as **two** distinct values.

Nothing in the run says so. `nnUNetv2_predict` has **no flag that means "this is MRI"** — the
normaliser comes from the training plan, not from the incoming image. AMOS's own `dataset.json`
declares `"modality": {"0": "CT"}` for a dataset that contains 100 MRI volumes, so a pipeline reading
*that* field to choose a normaliser gets it wrong too. The job exits 0 and returns an output file for
all 60 cases — **20 of them empty**, and five more under 1 mL against reference spleens of 100–600 mL.
**Only ground truth made this loud.** On an unlabelled clinical MRI series the same run produces 60
files and no signal at all that anything is wrong.

### The counterfactual: both mechanisms are real, and they are not the same size

The obvious objection is that a CT-trained model might fail on MRI anyway, normaliser or not. That
objection was correct, and it needed an arm rather than an argument.

**Rung 3b changes exactly one thing: the input intensity scale.** Each MRI is affinely mapped so its
in-body percentile range lands on the CT fingerprint's window, read from the trained `plans.json` —
the normaliser is *handed input in the domain it assumes*, not bypassed. Clipping at the ceiling
falls from a median of 23.2 % to **0.4 %**. Same checkpoint, same folds, same TTA, **no retraining**.
The arm and a **written prediction** were fixed in [`COUNTERFACTUAL_PLAN.md`](COUNTERFACTUAL_PLAN.md)
before it ran.

| contrast | difference in medians [95% CI] |
|---|---|
| 3b − 3 (rescaled − as shipped) | **+0.2864** [+0.1204, +0.4048] |
| 3b − 2 (rescaled − external CT) | **−0.5916** [−0.7259, −0.4674] |

Neither interval crosses zero. **Of the −0.944 collapse, roughly 0.29 Dice is the preprocessing
contract and roughly 0.59 is a representation that does not transfer.** An input rescaling alone
multiplied median Dice by twenty and cut empty predictions from 20 to 15 — for much of the original
failure the network was not misreading MRI so much as never receiving it. The residual is equally
real: an affine map restores dynamic range and cannot make an MR sequence's tissue contrast agree
with the ordering a Hounsfield window encodes.

**A second arm, by a different route, lands in the same place.** Rung 3b keeps the wrong normaliser
and repairs the input. Rung 3c does the opposite: it keeps the original images and patches the
trained plan's `normalization_schemes` to `ZScoreNormalization` — the normaliser nnU-Net *would*
have chosen had `dataset.json` not declared a collection of 100 MRI volumes to be CT. Only that one
field differs from the trained plan; the five checkpoints are the same files, and the plan nnU-Net
wrote into its own output directory is committed as evidence
([`qc/rung3c_plans_used.json`](qc/rung3c_plans_used.json)) because a run's log echoes a path rather
than proving what it loaded.

**3c − 3b = −0.0146 [−0.2136, +0.1575] — the interval spans zero.** Both arms leave the same 15 empty
predictions, and their per-case Dice correlate at **r = 0.939**: they succeed and fail on the same
images. Two unrelated repairs reaching the same place means the **intensity domain is the whole of
the preprocessing story** and the form of the transform is not. It also answers the metadata
question — fixing the mislabelled modality field alone would have reached 0.2870, not 0.8932.

Both predictions were written before their runs. The first ("around 0.3") landed on the nose; the
second ("around 0.35, plausibly above 3b") was inside its range but **wrong in direction**. Recorded
together, because the second lowers the weight the first deserves.

### The toolkit saw half of it, and filed it as Minor

Before any training, `/profile-imaging` returned `INTENSITY_SCALE_INCONSISTENT` on AMOS22:
*"500/600 cases bottom out near air (<= -500) and the rest do not — mixed modality, or a rescale not
applied to part of the cohort"* ([`qc/amos22_dataset_profile_spleen.json`](qc/amos22_dataset_profile_spleen.json)).
A true positive. It names the exact property that later broke rung 3, and it sat in `qc/` for the
whole nine days at **Minor** severity.

So the gap is **not detection**. It is **routing and severity**: nothing carries a profiling-stage
claim to the inference stage, nothing compares the trained plan's assumed intensity domain against
the arm about to be predicted, and a finding that costs a Dice of 0.015 was ranked below the level at
which anyone stops. A gate that fires correctly into a directory no later step reads is,
operationally, a gate that did not fire.

*(This section is a correction. An earlier draft of this README and of the write-up asserted that no
gate in the toolkit sees this — written before the profiler's own output file was opened. The claim
was wrong and is left recorded here rather than edited away.)*

### The prediction was written in advance, and was partly wrong

[`EVALUATION_PLAN.md` §6](EVALUATION_PLAN.md) predicted the rung-3 collapse *and its cause*, reasoning
from one MRI case whose maximum is ~186,000: "clips essentially all
tissue to the 174 ceiling … a volume with only two values". The outcome was right. The mechanism was
right in kind and **wrong in degree**: two values is the extreme of the cohort (`levels` minimum = 2),
not the typical case (median 175, median 23.2 % clipped). Reasoning from a single case overstated it.
The plan said its predictions could be wrong in public; this is that entry.

**Chronology caveat.** The plan was written before inference ran and ships unedited, but *this
repository cannot prove that ordering* — the plan and the rung-3 results first appear in the same
commit, because the demo was committed in one piece. Treat the ordering as documented by the
authors, not as independently verified. What the repo does carry independently is the profiler's own
output, where the `INTENSITY_SCALE_INCONSISTENT` claim and its Minor severity are machine-readable
fields.

## Two disclosures that no licence or citation check surfaces

- **nnU-Net won the 2018 MSD challenge.** Training it on MSD Task09 means **rung 1 is not an
  independent test of nnU-Net** — it demonstrates that the pipeline runs. AMOS22 (2022) post-dates
  nnU-Net (2021), so rungs 2 and 3 carry the independent evidence.
- **nnU-Net leaks if used the obvious way.** Its resampling target *and* CT intensity statistics are
  fit from whatever sits in `nnUNet_raw/imagesTr`; the fit scope is decided by which files you copy,
  not by a flag. Dropping all cases in and splitting later fits the fingerprint on the held-out set.
  The counterfactual is shipped, not described: [`manifests/preprocessing_manifest_naive.json`](manifests/preprocessing_manifest_naive.json)
  fires **3 × `PREPROCESS_BEFORE_SPLIT`** under the same gate that passes the real one
  ([`qc/preprocessing_leakage_naive.json`](qc/preprocessing_leakage_naive.json) vs [`qc/preprocessing_leakage.json`](qc/preprocessing_leakage.json)).
  Held-out cases are therefore physically absent from that directory, and `make_nnunet_dataset.py`
  self-checks and aborts if one appears.

## Deviations, disclosed

- **100 epochs, not nnU-Net's default 1000.** Measured epoch time was 360–417 s, so the default is
  ~4.2 days per fold ≈ 21 days for five — infeasible by arithmetic, not by preference. Five folds were
  kept so the deviation stays *one* thing (schedule) rather than two (schedule + no ensemble).
- **Single configuration** (`3d_fullres`). nnU-Net's own search across 2d / 3d_lowres / cascade was not
  run, so this is nnU-Net-the-network, not nnU-Net-the-method.
- **Training cohort n = 32** after the held-out carve, single institution.
- Subgroups are estimated **on the external set only** — n=9 internally cannot support subgroup
  estimates without manufacturing numbers.

## What you can re-run

| Tier | What | Needs |
|---|---|---|
| **A** | The analysis — headline table, bootstrap CIs, subgroups, figure, from the shipped per-case CSVs | a laptop |
| **B** | Profiling, split, both leakage gates, evaluation, normalisation evidence | the two datasets on disk |
| **C** | Training + inference | ~50 GPU-hours in a CUDA container |

`bash reproduce.sh` runs **tier A** and stops, because that is the part this repository can honestly
promise. Tier B and C commands are printed rather than executed, with what each needs.

## Layout

- `pipeline/` — the demo's own scripts. The two leakage gates are **not** vendored; `reproduce.sh`
  calls them from `../../skills/` so the demo tests the shipped code, not a copy of it.
- `results/` — per-case CSVs (one row per case, the SSOT), the across-cohort summary, and the
  normalisation-evidence JSON for both external arms.
- `qc/` — deterministic gate outputs: split leakage, preprocessing leakage (real **and**
  counterfactual), dataset profiles.
- `splits/`, `manifests/` — the seed-locked split assignment and the preprocessing manifests the gates
  read.
- `manuscript/writeup.md` — the write-up. `EVALUATION_PLAN.md` — pre-specified, dated before results.
- `FRICTION.md` — **every point that needed engineering knowledge**, which is the only thing that makes
  the headline question answerable rather than self-serving.
