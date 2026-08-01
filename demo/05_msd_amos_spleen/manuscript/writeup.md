---
title: "Where an unaided clinician's deep-learning study breaks: a three-rung external-validation ladder for spleen segmentation, and a preprocessing contract that fails in silence"
author: "Demonstration Author"
date: "2026-07-31"
bibliography: _src/refs.bib
---

## Abstract

**Background and objective.** Agentic toolkits can now scaffold a medical-imaging model, and a
clinician-researcher without an engineer can plausibly reach a trained network. Where that path
breaks is not known.

**Methods.** We trained nnU-Net v2 [@isensee2021nnunet] for 3-D spleen segmentation on 32 cases of
the Medical Segmentation Decathlon Task09 [@antonelli2022msd] under a patient-level split, and
evaluated it on three labelled rungs: the internal held-out set, AMOS22 CT (n = 300) as a genuinely
external cohort, and AMOS22 MRI (n = 60) as a modality shift [@ji2022amos]. Metrics, the handling of
cases containing no spleen, the subgroup cut-points and a written prediction for the MRI rung were
fixed before any prediction existed; Dice is reported with a boundary metric and never accuracy
[@maierhein2024metrics].

**Results.** Internal median Dice was 0.9595 (95% CI 0.9367 to 0.9734) and fell to 0.8932 (0.8633 to
0.9108) on external CT, a difference of −0.0662 (−0.0996 to −0.0416). Performance was lowest where
the task matters most: enlarged spleens scored 0.7694 against 0.9114 for normal volumes. On MRI,
median Dice was 0.0152 (0.0000 to 0.0626). Replaying the trained plan's normalisation over both
external arms documents an incompatibility present in every MRI case and no CT case: all 300 CT
cases contain negative voxels and 2.7% of voxels exceed the clip ceiling, while **no** MRI case
contains a negative voxel and a median 23.2% exceed it. The pipeline reported no error and returned
a file for all 60 cases — 20 of them empty.

**Conclusion.** The third rung is a **constructed** test: the plan named the normalisation contract
and predicted the collapse before inference ran. It demonstrates that the pipeline stays silent
about a known incompatibility, not that the failure was discovered in unaided work. Within that
limit it shows a defect class worth tooling against — one that produces a number rather than an
error, and that the toolkit's own profiler had already flagged at Minor severity in a directory no
later step reads. Generalisation beyond this example is a hypothesis, not a result.

## Introduction

The practical question behind agentic research tooling is not whether a clinician can obtain a
trained model. They can. It is whether the study that results is defensible, and where it stops
being so. Answering that requires running the whole path, including the tedious parts, and
recording the failures rather than the finished artifact.

**What kind of evidence this is.** Rungs 1 and 2 are ordinary internal and external validation and
are reported as such. Rung 3 is different and should be read differently: while writing the
evaluation plan we inspected the trained configuration, found that it carries a CT intensity
transform, and **predicted in writing that MRI performance would collapse for that reason**. We then
ran the arm anyway. That makes rung 3 a **constructed** demonstration — a stress test of whether the
pipeline says anything when handed an input it cannot process — and not a discovery made in the
course of unaided work. Read as a discovery it would overclaim; read as a constructed test it
answers a narrow question cleanly, which is: given a known incompatibility, does anything in the
workflow surface it? The answer is no, and the run exits 0.

The failure modes this literature documents most often are about *what the model learned*: a
pneumonia classifier that encoded the scanner rather than the disease [@zech2018generalization],
a hip-fracture model driven by healthcare process variables [@badgeley2019confounding]. The
methodological guidance that follows from them concerns cohort design and external testing
[@park2018methodologic]. The failure recorded here is a different species. It is not about what the
model learned; it is about what the pipeline silently did to the images before the model ever saw
them.

We chose 3-D spleen segmentation because it admits a clean ladder of increasing distributional
distance with ground truth at every step, and because both datasets download without registration.
Access, not narrative quality, decided the choice. ACDC to M&Ms is the better domain-shift pair and
sits behind registration walls; a demonstration about reproducibility cannot open with a step the
reader is unable to take.

Two properties of the setup have to be stated before any result is read. First, nnU-Net won the 2018
Medical Segmentation Decathlon and its self-configuring heuristics were developed against that
benchmark family [@antonelli2022msd; @isensee2021nnunet], so the internal rung on MSD Task09
demonstrates that the pipeline runs and does not independently evidence the method. AMOS22 postdates
nnU-Net, so the external rungs carry the evidence. Second, a clinician sourcing a model from a
public repository checks its licence and its citation count, and neither of those surfaces the first
point. That benchmark-provenance hazard is a known one in this field: competition rankings are
sensitive to design choices that a leaderboard position does not expose [@maierhein2018rankings],
and nnU-Net's own authors have since argued for more rigorous validation practice around it
[@isensee2024nnunetrevisited].

## Methods

**Data.** MSD Task09 Spleen (CC-BY-SA 4.0) [@antonelli2022msd], 41 labelled cases of 61. AMOS22
(CC BY 4.0) [@ji2022amos], 300 labelled CT and 60 labelled MRI of 600, downloaded as the Zenodo
data record doi:10.5281/zenodo.7262581, which is what carries the licence. Dataset facts were read from the
shipped files rather than from the accompanying prose: the spleen index is 1 in both label sets, the
CT label set runs 0 to 15 and the MRI set 0 to 13, and the readme's modality rule is off by one
against a contiguous identifier space. Cohort characteristics by arm are in Table 1.

**Split and preprocessing.** A patient-level split with seed 42 assigned 32 cases to training and 9
to the held-out set. Disjointness was proved by set arithmetic rather than asserted. nnU-Net fits
its resampling target and its intensity statistics from whatever occupies its raw-data directory, so
the fit scope is decided by which files are copied there and not by any flag. Held-out cases were
therefore physically excluded from that directory, and the dataset builder aborts if one appears.
The counterfactual, in which every case is present and the split is applied afterwards, is retained
as a declared manifest and fires three major preprocessing-leakage findings under the same gate that
passes the real one.

**Training and inference.** nnU-Net v2 [@isensee2021nnunet], configuration `3d_fullres`, five folds,
100 epochs per fold. Measured epoch time of 360 to 417 s makes nnU-Net's default 1000 epochs
approximately 21 days for five folds on the available hardware, so the reduced schedule follows from
arithmetic and is disclosed wherever a number from this model appears. The epoch time, the derived
21-day figure and the approximately 50 GPU-hours were read from the training job logs on the cluster;
those logs are **not shipped** with this demo, so unlike every other number here they cannot be
re-derived from the repository. Five folds were retained so
that the deviation from default remains a single change. Inference used the five-fold ensemble at
nnU-Net's default settings with mirroring test-time augmentation enabled, on all three arms.

**Evaluation.** Metrics were fixed before any prediction existed and follow Metrics Reloaded
[@maierhein2024metrics]: Dice is reported with HD95, since a boundary metric is required alongside
an overlap metric, and accuracy is never reported because the target occupies 0.2 to 0.4% of the
volume. HD95 was computed with the supplied voxel spacing, which matters here because the volumes
are anisotropic.

**HD95 has a smaller denominator than Dice, and the difference is not random.** A non-empty
reference with an empty prediction has a Dice of 0 but no predicted surface, so no symmetric surface
distance exists for it. The case is left blank rather than imputed, because the usual imputation —
the image diagonal — is a made-up number. Those are the cases that failed hardest, so an HD95 median
quoted against the Dice denominator is optimistic by exactly the worst cases, and the gap widens
with the failure rate: HD95 exists for 9 of 9 internal cases, 270 of 298 scored external CT cases,
and 40 of 59 scored MRI cases. Every HD95 below is therefore reported with its own n (Table 2), and
the MRI value in particular is a statistic over the 40 cases that produced a surface at all. HD95
here is therefore a **success-conditioned estimand**: it describes boundary agreement among the
cases that produced a boundary, and it should be read together with the empty-prediction count for
the same arm rather than as that arm's boundary performance.

**The primary summary is the median, and that is a choice with consequences.** On the external CT
arm the mean Dice is 0.7116 against a median of 0.8932, so which one leads changes the apparent
result. The estimand here is *typical-case* performance — what the model does on a case drawn from
the cohort — for which the median is the appropriate summary and is resistant to the 28 empty
predictions. The mean is the *expected per-case* performance and absorbs those failures; it is the
better summary for anyone budgeting total error. Both are reported side by side in Table 2 for
exactly that reason, and the empty-prediction count is reported with them so the median is never
read as if the failures had not happened.

**Uncertainty.** Every median is reported with a percentile bootstrap 95% interval over cases —
**10,000 resamples, seed 20260725**, seeded per (arm, metric) so that an arm's interval does not
depend on how many other arms were bootstrapped before it. Between-arm differences carry their own
interval: a difference of two separately estimated medians is not an inferential quantity on its
own, and the internal arm's n = 9 contributes most of the uncertainty, so each Δ-Dice is a bootstrap
interval for the difference in population medians with both arms resampled independently at the case
level.

Three of the 360 labelled AMOS cases contain no spleen voxel. Dice is undefined on
an empty reference, so those cases were excluded from the metric distributions, which fixes the
denominators at 298 of 300 and 59 of 60, and were reported separately with their predicted volume so
that a hallucinated organ appears on its own line. Subgroup cut-points, at 100 and 250 mL of spleen
volume and 2 and 5 mm of slice thickness, were fixed in advance and are identical across arms; a
per-arm quantile would have made the arms non-comparable. Reporting follows CLAIM 2024
[@tejani2024claim; @mongan2020claim], with TRIPOD+AI [@collins2024tripodai] consulted for the
prediction-model items.

**Provenance of the plan, stated precisely.** `EVALUATION_PLAN.md` was written before inference was
run and is shipped unedited, but **this repository cannot prove that ordering**: the plan and the
rung-3 per-case results first appear in the same commit, because the demo was committed in one
piece. A reader should treat the chronology as documented by the authors rather than as
independently verified. What the repository *does* carry independently is the profiler's own output
(`qc/amos22_dataset_profile_spleen.json`), which contains the `INTENSITY_SCALE_INCONSISTENT` claim
and its Minor severity as machine-readable fields.

**Normalisation evidence.** To test whether the MRI result reflects the network or the preprocessing
contract, the normalisation recorded in the trained `plans.json` was replayed over every image of
both external arms, measuring per case the presence of negative voxels, the fraction of voxels above
the clip ceiling, and the number of intensity levels surviving the clip.

## Results

**The ladder.** Internal median Dice was 0.9595 (95% CI 0.9367 to 0.9734), with HD95 1.78 mm over
all 9 cases. On external CT, 298 of 300 cases were scored, with median Dice 0.8932 (0.8633 to
0.9108) and HD95 5.68 mm over the 270 cases that produced a predicted surface; the difference in
population medians against the internal arm is −0.0662 (95% CI −0.0996 to −0.0416). On MRI, 59 of 60
cases were scored, with median Dice 0.0152 (0.0000 to 0.0626), HD95 70.05 mm over 40 of those 59,
and a difference of −0.9443 (−0.9715 to −0.8813) (Table 2). Figure 1 shows the per-case distributions behind those medians and
Figure 2 the across-cohort comparison with its intervals. For context,
nnU-Net's own cross-validation over the 32 training cases gave fold Dice values of 0.8437, 0.9304,
0.9659, 0.9696 and 0.9507.

**What the headline hides.** Twenty-eight of the 300 external CT predictions were empty, as were 20
of the 60 MRI predictions. Both spleen-free CT cases received a non-empty prediction. Figure 1 makes the reason plain: the external CT arm carries a long tail to zero, and the MRI arm
has most of its mass at the floor with a handful of cases reaching 0.91. In the pre-specified
subgroups (Table 3, Figure 3), external CT performance was lowest on enlarged spleens above 250 mL,
at 0.7694 (n = 67), against 0.9114 for the normal 100 to 250 mL range (n = 194) and 0.8157 for
volumes below 100 mL (n = 37). Thick slices of 5 mm or more scored 0.8752 (n = 219) against 0.9292
for the 2 to 5 mm range (n = 74). The thin-slice stratum has n = 5 and the thick MRI stratum is
empty; both are descriptive and cannot support a stable contrast. These are stratum estimates with their own intervals, not a tested
interaction; no interaction test is reported and none is implied.

**A preprocessing incompatibility is present in every MRI case, and no CT case.** Two rival explanations were tested and rejected
before the result was accepted. The label index is correct: spleen is 1 in the MRI label set, and
the resulting reference volumes are physiological, with a median of 187.6 mL across the 59 scored
cases (Table 1; 186.8 mL if the target-free case is included). The images are genuinely MRI, with a minimum of 0 and no air floor.

The trained plan applies `CTNormalization` with the training fingerprint's parameters, clipping to
[-38, 174] HU and z-scoring by mean 89.8 and SD 39.8. Replaying it over both arms separates them
cleanly (Table 4, Figure 4). All 300 CT cases contain negative voxels, a median of 2.7% of voxels
exceed the clip ceiling (range 1.0 to 6.9%), and 213 intensity levels survive. No MRI case contains
a negative voxel, a median of 23.2% of voxels exceed the ceiling (range 0.3 to 68.6%), and the
surviving levels fall to a median of 175 with a minimum of 2. Hounsfield units are defined by an air
floor near -1000, so a volume that never goes negative is not in that unit system, and the clip
window is not a soft-tissue window there. It is an arbitrary slice near the bottom of an
arbitrary-unit range. Case accounting for both source datasets, including every exclusion and the
three target-free cases, is in Figure 5.

**What this does and does not establish.** It establishes that the trained plan applies a
Hounsfield-unit transform to images that are not in Hounsfield units, in 60 of 60 MRI cases, and
that the transform destroys most of the usable range. It does **not** isolate that transform as the
sole cause of the collapse: a CT-trained representation might fail on MRI even under a correct
normaliser, and no correctly-normalised MRI arm was run, so preprocessing failure and
representation failure are not separated here. The defensible claim is that the incompatibility is
present, is sufficient to account for the magnitude observed, and is invisible at run time — not
that it is the only thing wrong.

No part of the run signals this. The inference command has no argument that declares the modality of
the incoming images, and the normaliser travels with the checkpoint. The dataset's own
`dataset.json` declares a single CT modality for a collection that contains 100 MRI volumes, so a
pipeline that consults that field reaches the same wrong answer.

## Discussion

The clinician in this study did the things the methodological literature asks for
[@park2018methodologic]. The licence was checked, the model's provenance conflict with the internal
benchmark was identified and disclosed, the split was patient-level and seed-locked, disjointness
was proved rather than assumed, the external cohort was genuinely external, the metrics were
appropriate to the task [@maierhein2024metrics], the cases without a target were handled by a rule
fixed in advance, and the subgroups were pre-specified. The third rung still produced a meaningless
number, and a reader without ground truth would have had nothing to tell them so.

That last clause is the whole claim, and it is narrower than it first looks. We are **not** claiming
to have discovered this failure by walking the unaided path: the evaluation plan named the
normalisation contract and predicted the collapse before inference ran (see the Introduction). What
the run demonstrates is the *silence* — that a pipeline handed an input it cannot process completes,
exits 0, and reports a number, with nothing in the command, the logs or the output signalling the
problem. That is a defect class worth tooling against, and it is one this study constructed rather
than encountered.

The toolkit's own record complicates that account, and in a way worth stating precisely. Before any
training, the dataset profiler returned `INTENSITY_SCALE_INCONSISTENT` on AMOS22: "500/600 cases
bottom out near air (<= -500) and the rest do not, mixed modality, or a rescale not applied to part
of the cohort". That is a true positive, it names the exact property that later broke the MRI rung,
and it is in the shipped quality-control output, where the claim and its severity are
machine-readable fields. It was filed as **Minor**.

So detection was not the missing piece. Routing and severity were. Nothing carries a profiling-stage
observation forward to the inference stage, nothing compares the intensity domain a trained plan
assumes against the arm it is about to be applied to, and a finding whose cost turns out to be a
Dice of 0.015 was ranked below the threshold at which anyone stops. *A gate that fires correctly
into a directory no later step reads is, operationally, a gate that did not fire.* We offer that as
a hypothesis this example motivates, not as a property established by it — one organ, one
architecture, one dataset pair and one deliberately chosen mismatch cannot support a general claim
about tooling, and no independent user ever walked this path.

**The written prediction called the mechanism, then overstated it.** Before any prediction existed,
the evaluation plan named the normalisation contract as the thing that would break the MRI rung, and
the outcome matched. (Its chronology is documented by the authors rather than provable from this
repository; see Methods.) It also predicted that the clipped volume would retain "only two values",
reasoning from a single MRI case with an unusually large intensity range. Measured across the
cohort, two levels is the extreme rather than the norm: the median is 175 levels and 23.2% of voxels
clipped. Generalising a mechanism from one case overstated it, and the plan is left uncorrected in
the repository with this note beside it.

**Limitations.** The training cohort is 32 cases from a single institution and only one nnU-Net
configuration was trained, so this is nnU-Net the network rather than nnU-Net the method
[@isensee2024nnunetrevisited]. Subgroup estimates are external-only because 9 internal cases cannot
support them, and whether the spleen-free cases reflect splenectomy or annotation omission was not
determined. The slice-thickness axis is the third voxel dimension, which is the through-plane axis
for every CT case but **not** for 26 of the 60 MRI volumes; nine scored MRI cases would change
stratum under a coarsest-axis rule, so the MRI subgroup rows should be read with that in mind.

Most importantly, **the design does not separate preprocessing failure from representation
failure**: the correctly-normalised MRI counterfactual, the one arm that would distinguish them, was
not run. The incompatibility is documented and sufficient to account for the magnitude; it is not
isolated as the sole cause, and a correctly configured cross-modality pipeline was never attempted
here [@wasserthal2023totalsegmentator]. Finally, this is one worked example authored by the people
who built the toolkit — no independent users, no comparator workflow, no repetition.

## Conclusion

A clinician-researcher without an engineer reached a defensible external-validation result on CT.
On a third arm, constructed to carry a known incompatibility, the same pipeline returned output for
every case, exited 0, and reported a number that means nothing — and the toolkit's own profiler had
already recorded the underlying property, at Minor severity, in a directory no later step reads.

The change that example suggests is not another detector but a route: carry a profiling-stage
observation to the point of use, and compare the intensity domain a trained plan assumes against
the arm it is about to be applied to, before an inference run is allowed to report a number.
Whether that would prevent failures beyond the one constructed here is untested, and this study
cannot settle it — one organ, one architecture, one dataset pair, one author team. What it does
establish is that the failure can be complete, and completely quiet, at the same time.

## Tables

**Table 1.** Cohort characteristics by evaluation arm: case counts, target-free counts, spleen
volume and slice thickness.

**Table 2.** Performance by arm, with the target-free, empty-prediction and HD95 denominators
reported beside each estimate.

**Table 3.** Pre-specified subgroups, identical cut-points across arms.

**Table 4.** What the trained plan's normaliser does to each external arm.

## Figure legends

**Figure 1.** Per-case Dice by cohort. Box plots with jittered per-case points; the spread is what
the medians in Table 2 conceal.

**Figure 2.** Median Dice with bootstrap 95% confidence intervals across the three cohorts, with the
internal arm as the dashed reference.

**Figure 3.** Pre-specified subgroups on the external CT arm, both axes with identical cut-points.

**Figure 4.** Why rung 3 collapsed, measured on both external arms. (a) Per-case minimum intensity:
every CT case has a Hounsfield air floor near -1000; no MRI case has one. (b) The share of each
volume flattened at the trained plan's clip ceiling under the same normaliser.

**Figure 5.** Case accounting across both source datasets and the three rungs, including the three
cases excluded from the metric distributions because their reference contains no spleen.

## Data and code availability

Both datasets are public and are not vendored here: MSD Task09 Spleen (CC-BY-SA 4.0) and AMOS22
(CC BY 4.0, Zenodo 7262581). The pipeline, the per-case results behind every number, the
deterministic gate outputs including the leakage counterfactual, and the friction log are in
`demo/05_msd_amos_spleen/`. `reproduce.sh` re-runs the gates and the full across-cohort analysis on
a laptop; training requires approximately 50 GPU-hours and is documented rather than executed.

## References
