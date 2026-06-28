# Model Card: HepaSeg-UNet v1.2 (synthetic example)

## Model Details
- **Developed by**: the imaging-AI group at a tertiary-care hospital
- **Model date / version**: 2026-03, v1.2
- **Model type / architecture**: 3-D residual U-Net (MONAI SegResNet backbone)
- **Task**: liver-lesion segmentation on multiphase CT
- **Provenance**: in-house, trained from scratch
- **License**: CC BY-NC 4.0 (confirmed by the developing group)
- **Citation / contact**: imaging-ai@example.org

## Intended Use
- **Primary intended use**: second-reader assistance for delineating liver lesions on portal-venous CT
- **Intended users**: board-certified radiologists reviewing abdominal CT
- **Deployment horizon**: post-acquisition decision support, not autonomous reporting

## Out-of-Scope Use
- Not validated for non-contrast CT, for paediatric patients, or for scanners outside the two vendors in the training set; must not be used autonomously without a radiologist in the loop.

## Factors
- **Relevant factors / subgroups**: scanner vendor (two vendors), lesion size (under vs over 2 cm), and presence of cirrhosis.

## Training Data
- **Source / cohort**: 480 patients with multiphase abdominal CT from a single tertiary centre, 2018-2023.
- **Size**: 480 patients, 612 annotated lesions.
- **Label / reference standard**: manual segmentation by two abdominal radiologists with disagreements adjudicated by a third; inter-reader Dice 0.86.
- **Preprocessing**: HU windowing and z-score normalisation fit on the training fold only.

## Evaluation Data
- **Source / cohort**: a temporally held-out cohort of 120 patients from the same centre, 2024.
- **Validation tier**: temporal internal validation (single centre); no external-site test.
- **Split**: patient-level, seed-locked (see splits/split_assignment.csv, seed 42).
- **Test-set size**: 120 patients, 158 lesions.

## Metrics
- **Metrics reported**: Dice and HD95 per lesion, plus per-patient mean Dice, with 95% CIs.
- **Operating point / threshold**: probability threshold 0.5, fixed on the training fold.
- **Run variance**: mean +/- SD over 3 seeds.

## Quantitative Analyses
- **Overall performance**: mean Dice 0.81 (95% CI 0.78-0.84), HD95 7.2 mm, on the held-out cohort.
- **Disaggregated / subgroup performance**: Dice 0.74 for lesions under 2 cm vs 0.85 over 2 cm; comparable across the two scanner vendors.

## Ethical Considerations
- Errors could lead to missed lesions; automation bias is a risk if used without independent review. The training cohort is single-centre and may not represent other populations.

## Caveats and Recommendations
- Single-centre, temporally validated only; external multi-site validation is required before deployment. Performance on small lesions is weaker and should be communicated to users.
