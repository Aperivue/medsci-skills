<!-- Model Card template (model-card skill). Structure follows Mitchell et al.,
     "Model Cards for Model Reporting," ACM FAccT 2019 (arXiv:1810.03993), adapted for a
     clinical medical-imaging model. Fill every [NEEDS INPUT] from user-supplied facts —
     never fabricate a number, a dataset detail, or a performance result. Keep the section
     headings (check_model_card_complete.py verifies they are present and non-empty). -->

# Model Card: [NEEDS INPUT: model name + version]

## Model Details
- **Developed by**: [NEEDS INPUT: people / organisation]
- **Model date / version**: [NEEDS INPUT]
- **Model type / architecture**: [NEEDS INPUT: e.g. 3-D U-Net (nnU-Net v2)]
- **Task**: [NEEDS INPUT: segmentation / classification / detection]
- **Provenance**: [NEEDS INPUT: in-house / vendor / open-weights + version]
- **License**: [NEEDS INPUT — state the licence the user confirmed; do not assume]
- **Citation / contact**: [NEEDS INPUT]

## Intended Use
- **Primary intended use**: [NEEDS INPUT: the clinical task + decision the model supports]
- **Intended users**: [NEEDS INPUT: e.g. radiologists as a second reader]
- **Deployment horizon**: [NEEDS INPUT: screening / triage / pre-procedure / post-hoc]

## Out-of-Scope Use
- [NEEDS INPUT: uses the model must NOT be put to; populations / modalities / scanners it
  was not validated on; autonomous use if not validated for it]

## Factors
- **Relevant factors / subgroups**: [NEEDS INPUT: age, sex, scanner/vendor, site, disease
  severity — the axes performance is expected to vary along]

## Training Data
- **Source / cohort**: [NEEDS INPUT]
- **Size**: [NEEDS INPUT: patients and images/structures]
- **Label / reference standard**: [NEEDS INPUT: who labelled, annotator count, adjudication,
  inter-reader agreement; flag any model-derived "silver" labels]
- **Preprocessing**: [NEEDS INPUT — note whether fit on the training fold only]

## Evaluation Data
- **Source / cohort**: [NEEDS INPUT]
- **Validation tier**: [NEEDS INPUT: internal split / cross-validation / temporal / external
  (site/scanner/vendor) — be honest; CV is not external validation]
- **Split**: [NEEDS INPUT: patient-level, seed-locked? reference splits/split_assignment.csv]
- **Test-set size**: [NEEDS INPUT: events / structures per class, not just patients]

## Metrics
- **Metrics reported**: [NEEDS INPUT: segmentation → Dice + HD95/NSD per structure;
  classification → AUROC + AUPRC + sensitivity/specificity, with 95% CIs; detection → FROC/mAP]
- **Operating point / threshold**: [NEEDS INPUT — fixed on train/tuning folds only]
- **Run variance**: [NEEDS INPUT: mean ± SD over >= 3 seeds, or fixed seed + determinism caveat]

## Quantitative Analyses
- **Overall performance**: [NEEDS INPUT — numbers from executed evaluation only]
- **Disaggregated / subgroup performance**: [NEEDS INPUT: performance by the Factors above —
  the fairness-relevant breakdown]

## Ethical Considerations
- [NEEDS INPUT: risks of error in this clinical context, automation bias, equity concerns,
  consent / governance of the data]

## Caveats and Recommendations
- [NEEDS INPUT: known limitations, conditions for safe use, what further validation is needed
  before deployment]
