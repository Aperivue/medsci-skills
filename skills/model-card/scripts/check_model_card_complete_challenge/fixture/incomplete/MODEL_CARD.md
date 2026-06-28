# Model Card: HepaSeg-UNet v1.2 (synthetic, incomplete)

## Model Details
- **Model type / architecture**: 3-D residual U-Net
- **Task**: liver-lesion segmentation on multiphase CT

## Intended Use
- **Primary intended use**: second-reader assistance for delineating liver lesions

<!-- NOTE: the "Out-of-Scope Use" section is missing entirely -> MISSING_SECTION -->

## Training Data
- **Source / cohort**: 480 patients from a single tertiary centre.

## Evaluation Data
- **Validation tier**: temporal internal validation, single centre.

## Metrics
- **Metrics reported**: Dice and HD95 with 95% CIs.

## Quantitative Analyses
- **Overall performance**: mean Dice 0.81 (95% CI 0.78-0.84).

## Ethical Considerations
- Errors could lead to missed lesions; automation bias is a risk.

## Caveats and Recommendations
- [NEEDS INPUT: known limitations and conditions for safe use]
