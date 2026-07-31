# Where an unaided clinician's deep-learning study breaks: a three-rung external-validation ladder for spleen segmentation, and a preprocessing contract that fails in silence

## Authors

Demonstration Author¹

¹ Placeholder affiliation

## Corresponding author

Demonstration Author (placeholder)

## Article type

Demonstration / methods note (tooling). This is a worked example of the MedSci Skills
model-engineering lane carried onto a GPU cluster and out to a genuinely external cohort. **It makes
no clinical claim**, and none of its numbers should be read as a statement about the quality of
nnU-Net: a correctly configured cross-modality pipeline was never attempted here.

## Key points

- Internal held-out Dice **0.9595** (95% CI 0.9367–0.9734) fell to **0.8932** (0.8633–0.9108) on a
  genuinely external CT cohort and to **0.0152** (0.0000–0.0626) under a modality shift to MRI.
- The MRI collapse is a **preprocessing contract**, not a generalisation failure. The trained
  `plans.json` carries `CTNormalization` into inference and the inference command has no argument
  declaring the incoming modality, so a Hounsfield-unit clip was applied to arbitrary-unit images:
  **0 of 60** MRI cases contain a negative voxel against **300 of 300** on CT, and a median
  **23.2 %** of voxels are flattened at the clip ceiling against **2.7 %**.
- The run exited 0 and wrote 60 plausible segmentations. **Only ground truth made the failure
  visible**; on an unlabelled clinical series it would be silent.
- The toolkit's own dataset profiler had already flagged the underlying property before training —
  as a **Minor**, in a directory no later step reads. The gap is routing and severity, not detection.

## Data and code

MSD Task09 Spleen (CC-BY-SA 4.0) and AMOS22 (CC BY 4.0, Zenodo 7262581); neither is vendored. The
runnable pipeline, per-case results, deterministic gate outputs (including a leakage counterfactual
that must fail), the pre-specified evaluation plan and the friction log accompany this write-up in
`demo/05_msd_amos_spleen/`. The MedSci Skills toolkit is open source (archived on Zenodo, concept
DOI 10.5281/zenodo.20155321).

## Reporting guideline

CLAIM 2024 (Checklist for Artificial Intelligence in Medical Imaging), with TRIPOD+AI consulted for
the prediction-model items. The completed item-by-item assessment is in
`demo/05_msd_amos_spleen/qc/reporting_checklist.md`.

## AI-use disclosure

During preparation of this demonstration, the authors used Claude (Anthropic), accessed through the
Claude Code command-line interface (API channel), during 2026-07 to run the MedSci Skills
model-engineering lane: dataset profiling, split construction, deterministic gate execution, cluster
job orchestration, evaluation, figure and table generation, and drafting. Every quantitative claim
was verified against the committed per-case results (`results/per_case_*.csv`) and the normalisation
evidence (`results/normalizer_evidence_*.json`); two claims drafted during preparation were found
wrong on re-checking and are corrected in place with the corrections left visible. The authors take
full responsibility for the content.
