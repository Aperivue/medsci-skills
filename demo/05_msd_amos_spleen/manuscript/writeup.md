---
title: "Where an unaided clinician's deep-learning study breaks: a three-rung external-validation ladder for spleen segmentation, and a preprocessing contract that fails in silence"
author: "Demonstration Author"
date: "2026-07-31"
---

## Abstract

**Background and objective.** Agentic toolkits can now scaffold a medical-imaging model, and a
clinician-researcher without an engineer can plausibly reach a trained network. What is not known is
where that path breaks. We ran one such study end to end on public data and recorded both the result
and every point that required engineering knowledge. This is a **tooling demonstration, not a
clinical claim.**

**Methods.** We trained nnU-Net v2 (`3d_fullres`, five folds, 100 epochs) for 3-D spleen segmentation
on 32 cases of MSD Task09 (patient-level split, seed 42, 9 held out) and evaluated it on three
labelled rungs: the internal held-out set, AMOS22 CT (n = 300) as a genuinely external cohort, and
AMOS22 MRI (n = 60) as a modality shift. The evaluation plan, including metric choice, the handling
of cases containing no spleen, the subgroup cut-points, and a written prediction for the MRI rung,
was fixed before any prediction existed. Two deterministic gates ran before training: a
split-disjointness proof and a preprocessing-leakage check. Dice and HD95 are reported as medians
with bootstrap 95% confidence intervals (10,000 resamples, seed 20260725). Every number comes from an
executed run.

**Results.** Internal median Dice was 0.9595 (95% CI 0.9367 to 0.9734). On genuinely external CT it
fell to 0.8932 (0.8639 to 0.9108), a drop of 0.0662, with 28 of 300 predictions empty and both
spleen-free cases receiving a false positive. Performance was lowest in the subgroup that motivates
the task: enlarged spleens above 250 mL scored 0.7694 (n = 67) against 0.9114 for normal 100 to
250 mL volumes (n = 194). On MRI, median Dice was 0.0152 (0.0000 to 0.0626). Replaying the trained
plan's normalisation over both external arms located the cause. The plan applies `CTNormalization`,
clipping to the training foreground's [-38, 174] HU and z-scoring by mean 89.8 and SD 39.8. Every one
of the 300 CT cases contains negative voxels and a median of 2.7% of voxels exceed the clip ceiling;
none of the 60 MRI cases contains a single negative voxel and a median of 23.2% (up to 68.6%) exceed
it, leaving as few as two distinct intensity levels in the extreme case. The pipeline reported no
error and produced 60 plausible segmentations.

**Conclusion.** The unaided path failed neither at model choice nor at study design, both of which the
clinician completed correctly, but at a preprocessing contract recorded in a configuration file that
no step in the workflow asks anyone to read. The failure is invisible without ground truth. We argue
that the useful target for tooling is the class of defect that produces a number instead of an error.

## Introduction

The practical question behind agentic research tooling is not whether a clinician can obtain a
trained model. They can. It is whether the study that results is defensible, and where it stops being
so. Answering that requires running the whole path, including the parts that are tedious, and
recording the failures rather than the finished artifact.

We chose 3-D spleen segmentation because it admits a clean ladder of increasing distributional
distance with ground truth at every step, and because both datasets download without registration.
Access, not narrative quality, decided the choice. ACDC to M&Ms is the better domain-shift pair and
sits behind registration walls; a demonstration about reproducibility cannot open with a step the
reader is unable to take.

Two properties of the setup have to be stated before any result is read. First, nnU-Net won the 2018
Medical Segmentation Decathlon and its self-configuring heuristics were developed against that
benchmark family, so the internal rung on MSD Task09 demonstrates that the pipeline runs and does not
independently evidence the method. AMOS22 postdates nnU-Net, so the external rungs carry the
evidence. Second, a clinician sourcing a model from a public repository checks its licence and its
citation count, and neither of those surfaces the first point.

## Methods

**Data.** MSD Task09 Spleen (Medical Segmentation Decathlon; Antonelli et al., *Nature
Communications* 2022; doi:10.1038/s41467-022-30695-9), CC-BY-SA 4.0, 41 labelled cases. AMOS22
(Zenodo record 7262581, CC BY 4.0), 300 labelled CT and 60 labelled MRI. Dataset facts were read from
the shipped files rather than from the accompanying prose: the spleen index is 1 in both label sets,
the CT label set runs 0 to 15 and the MRI set 0 to 13, and the readme's modality rule is off by one
against a contiguous identifier space.

**Split and preprocessing.** A patient-level split with seed 42 assigned 32 cases to training and 9
to the held-out set. Disjointness was proved by set arithmetic rather than asserted. nnU-Net fits its
resampling target and its intensity statistics from whatever occupies its raw-data directory, so the
fit scope is decided by which files are copied there and not by any flag. Held-out cases were
therefore physically excluded from that directory, and the dataset builder aborts if one appears. The
counterfactual, in which every case is present and the split is applied afterwards, is retained as a
declared manifest and fires three major preprocessing-leakage findings under the same gate that
passes the real one.

**Training and inference.** nnU-Net v2 (Isensee et al., *Nature Methods* 2021, 18:203-211;
doi:10.1038/s41592-020-01008-z), configuration `3d_fullres`, five folds, 100 epochs per fold. Measured
epoch time of 360 to 417 s makes nnU-Net's default 1000 epochs approximately 21 days for five folds
on the available hardware, so the reduced schedule follows from arithmetic and is disclosed wherever
a number from this model appears. Five folds were retained so that the deviation from default remains
a single change. Inference used the five-fold ensemble at nnU-Net's default settings with mirroring
test-time augmentation enabled, on all three arms.

**Evaluation.** Metrics were fixed before any prediction existed. Dice is reported with HD95, since a
boundary metric is required alongside an overlap metric, and accuracy is never reported because the
target occupies 0.2 to 0.4% of the volume. HD95 was computed with the supplied voxel spacing, which
matters here because the volumes are anisotropic. Three of the 360 labelled AMOS cases contain no
spleen voxel. Dice is undefined on an empty reference, so those cases were excluded from the metric
distributions, which fixes the denominators at 298 of 300 and 59 of 60, and were reported separately
with their predicted volume so that a hallucinated organ appears on its own line. Subgroup
cut-points, at 100 and 250 mL of spleen volume and 2 and 5 mm of slice thickness, were fixed in
advance and are identical across arms.

**Normalisation evidence.** To test whether the MRI result reflects the network or the preprocessing
contract, the normalisation recorded in the trained `plans.json` was replayed over every image of
both external arms, measuring per case the presence of negative voxels, the fraction of voxels above
the clip ceiling, and the number of intensity levels surviving the clip.

## Results

**The ladder.** Internal median Dice was 0.9595 (95% CI 0.9367 to 0.9734) with HD95 1.78 mm on 9
cases. On external CT, 298 of 300 cases were scored, with median Dice 0.8932 (0.8639 to 0.9108) and
HD95 5.68 mm, a drop of 0.0662 from internal. On MRI, 59 of 60 cases were scored, with median Dice
0.0152 (0.0000 to 0.0626) and HD95 70.05 mm, a drop of 0.9443. For context, nnU-Net's own
cross-validation over the 32 training cases gave fold Dice values of 0.8437, 0.9304, 0.9659, 0.9696
and 0.9507.

**What the headline hides.** Twenty-eight of the 300 external CT predictions were empty, as were 20
of the 60 MRI predictions. Both spleen-free CT cases received a non-empty prediction. In the
pre-specified subgroups, external CT performance was lowest on enlarged spleens above 250 mL, at
0.7694 (n = 67), against 0.9114 for the normal 100 to 250 mL range (n = 194) and 0.8157 for volumes
below 100 mL (n = 37). Thick slices of 5 mm or more scored 0.8752 (n = 219) against 0.9292 for the
2 to 5 mm range (n = 74).

**The MRI collapse is a preprocessing failure.** Two rival explanations were tested and rejected
before the result was accepted. The label index is correct: spleen is 1 in the MRI label set, and the
resulting reference volumes are physiological, with a median of 186.8 mL across 60 cases. The images
are genuinely MRI, with a minimum of 0 and no air floor.

The trained plan applies `CTNormalization` with the training fingerprint's parameters, clipping to
[-38, 174] HU and z-scoring by mean 89.8 and SD 39.8. Replaying it over both arms separates them
cleanly. All 300 CT cases contain negative voxels, a median of 2.7% of voxels exceed the clip ceiling
(range 1.0 to 6.9%), and 213 intensity levels survive. No MRI case contains a negative voxel, a
median of 23.2% of voxels exceed the ceiling (range 0.3 to 68.6%), and the surviving levels fall to a
median of 175 with a minimum of 2. Hounsfield units are defined by an air floor near -1000, so a
volume that never goes negative is not in that unit system, and the clip window is not a soft-tissue
window there. It is an arbitrary slice near the bottom of an arbitrary-unit range.

No part of the run signals this. The inference command has no argument that declares the modality of
the incoming images, and the normaliser travels with the checkpoint. The dataset's own `dataset.json`
declares a single CT modality for a collection that contains 100 MRI volumes, so a pipeline that
consults that field reaches the same wrong answer.

## Discussion

The clinician in this study did the things the methodological literature asks for. The licence was
checked, the model's provenance conflict with the internal benchmark was identified and disclosed,
the split was patient-level and seed-locked, disjointness was proved rather than assumed, the
external cohort was genuinely external, the metrics were appropriate to the task, the cases without a
target were handled by a rule fixed in advance, and the subgroups were pre-specified. The study still
produced a meaningless number on its third rung, and would have reported it as a modality-transfer
finding if ground truth had not been available.

This is the shape of defect worth building tooling against. It is not an error, it is a result. It
survives every check that inspects the study's design, because it lives in the configuration a
training run wrote about itself.

The toolkit's own record complicates that account, and in a way worth stating precisely. Before any
training, the dataset profiler returned `INTENSITY_SCALE_INCONSISTENT` on AMOS22: "500/600 cases
bottom out near air (<= -500) and the rest do not, mixed modality, or a rescale not applied to part
of the cohort". That is a true positive, it names the exact property that later broke the MRI rung,
and it sat in the study's quality-control directory for the whole nine days. It was filed as
**Minor**.

So the failure is not one of detection. It is one of routing and of severity. Nothing carries a
profiling-stage observation forward to the inference stage, nothing compares the intensity domain a
trained plan assumes against the arm it is about to be applied to, and a finding whose cost turns out
to be a Dice of 0.015 was ranked below the threshold at which anyone stops. A gate that fires
correctly into a directory no later step reads is, operationally, a gate that did not fire.

**The registered prediction was right in kind and wrong in degree.** The evaluation plan predicted
the MRI collapse and attributed it to the normalisation contract before any prediction existed, which
is the outcome. It also predicted that the clipped volume would retain "only two values", reasoning
from a single MRI case with an unusually large intensity range. Measured across the cohort, two
levels is the extreme rather than the norm: the median is 175 levels and 23.2% of voxels clipped.
Generalising a mechanism from one case overstated it, and the plan is left uncorrected in the
repository with this note beside it.

**Limitations.** The training cohort is 32 cases from a single institution, and the schedule is a
tenth of nnU-Net's default. Only one configuration was trained, so this is nnU-Net the network rather
than nnU-Net the method. Subgroup estimates are external-only because 9 internal cases cannot support
them. Whether the spleen-free cases reflect splenectomy or annotation omission was not determined.
The internal rung is not independent evidence about nnU-Net, for the reason given above. No claim is
made about clinical utility, and none of these numbers should be read as a statement about
nnU-Net's quality: a correctly configured MRI pipeline was never attempted here.

## Conclusion

A clinician-researcher without an engineer reached a defensible external-validation result on CT and
a silently meaningless one on MRI. Deterministic gates already prevent the leakage failures this
field documents most often, and one of them had already observed the property that broke the MRI
rung. What was missing was the step that carries such an observation to the point of use: a check
that the intensity domain a trained plan assumes is the domain of the data it is being handed,
evaluated per evaluation arm and enforced before an inference run is allowed to report a number. The
lesson we take from this study is less about writing a new detector than about where an existing
finding is allowed to stop.

## References

1. Isensee F, Jaeger PF, Kohl SAA, Petersen J, Maier-Hein KH. nnU-Net: a self-configuring method for
   deep learning-based biomedical image segmentation. Nat Methods. 2021;18:203-211.
   doi:10.1038/s41592-020-01008-z
2. Antonelli M, Reinke A, Bakas S, et al. The Medical Segmentation Decathlon. Nat Commun. 2022;13.
   doi:10.1038/s41467-022-30695-9. PMID 35840566
3. Ji Y. AMOS: a large-scale abdominal multi-organ benchmark for versatile medical image
   segmentation. Dataset, Zenodo, 28 Nov 2022. doi:10.5281/zenodo.7262581 (CC BY 4.0). Creator list
   as recorded by the deposit, which names one creator; the accompanying conference paper carries a
   longer author list and is not the artifact used here.
4. Maier-Hein L, Reinke A, Godau P, et al. Metrics reloaded: recommendations for image analysis
   validation. Nat Methods. 2024;21:195-212. doi:10.1038/s41592-023-02151-z

Reference metadata was resolved by DOI against CrossRef and PubMed rather than written from memory;
see `../qc/reference_audit.json`. Entry 3 cites the **data record**, which is what this study used and
what carries the licence, not the conference paper.
