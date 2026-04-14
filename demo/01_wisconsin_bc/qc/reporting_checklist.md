# Reporting Guideline Compliance Report

**Manuscript:** Machine Learning Classification of Breast Cancer Using Fine-Needle Aspiration Cytology Features: A Diagnostic Accuracy Study
**Guideline:** STARD 2015
**Date:** 2026-04-14
**Assessed by:** Claude (automated pre-screening)

## Summary (Post-Fix)

| Status | Count | Percentage |
|--------|-------|------------|
| PRESENT | 23 | 76.7% |
| PARTIAL | 2 | 6.7% |
| MISSING | 3 | 10.0% |
| N/A | 2 | 6.7% |
| **Total** | **30** | **100%** |

Overall compliance: 23/28 (82.1%)

## Auto-Fixed Items

| Item | Status Change | Fix Applied |
|------|--------------|-------------|
| 13 (Sample size) | MISSING → PRESENT | Added sample size justification paragraph |
| 28 (Funding) | MISSING → PRESENT | Added "no specific funding" statement |
| 6 (Eligibility) | PARTIAL → PRESENT | Added explicit inclusion criteria and sampling method |
| 7 (Sampling) | PARTIAL → PRESENT | Added convenience sample description |
| 10a (Cut-offs) | PARTIAL → PRESENT | Added pre-specified 0.5 threshold statement |

## Remaining Action Items

1. **[MISSING] Item 17: Time interval** — Time between FNA and histology not available in dataset (fixable_by_ai: true, but information not in dataset)
2. **[MISSING] Item 26: Registration** — No study registration (fixable_by_ai: false)
3. **[MISSING] Item 23: Subgroup analyses** — None performed (acceptable for demo)
4. **[PARTIAL] Item 14: Dates** — Recruitment dates not available in dataset
5. **[PARTIAL] Item 18: Severity** — Tumor grade/stage not available in dataset

```json
{
  "check_reporting_version": "1.0",
  "manuscript_title": "Machine Learning Classification of Breast Cancer Using Fine-Needle Aspiration Cytology Features: A Diagnostic Accuracy Study",
  "guideline": "STARD",
  "guideline_version": "2015",
  "date": "2026-04-14",
  "total_items": 30,
  "present": 23,
  "partial": 2,
  "missing": 3,
  "na": 2,
  "compliance_pct": 82.1,
  "action_items": [
    {
      "item_number": 17,
      "section": "Results",
      "item_name": "Time interval between index test and reference standard",
      "status": "MISSING",
      "suggested_location": "Results, after study population paragraph",
      "suggested_fix": "The time interval between FNA cytology and histological diagnosis was not recorded in the dataset.",
      "fixable_by_ai": true
    },
    {
      "item_number": 26,
      "section": "Other",
      "item_name": "Registration number",
      "status": "MISSING",
      "suggested_location": "Other Information section",
      "suggested_fix": "This study was not registered in a study registry.",
      "fixable_by_ai": false
    },
    {
      "item_number": 23,
      "section": "Results",
      "item_name": "Subgroup analyses",
      "status": "MISSING",
      "suggested_location": "Results, after diagnostic performance",
      "suggested_fix": "Subgroup analyses were not performed due to the homogeneous study population (all female, single imaging modality).",
      "fixable_by_ai": true
    },
    {
      "item_number": 14,
      "section": "Results",
      "item_name": "Dates and setting",
      "status": "PARTIAL",
      "current_text": "University of Wisconsin Hospitals",
      "needed": "Recruitment dates",
      "suggested_fix": "Data were collected at the University of Wisconsin Hospitals; exact recruitment dates were not available from the public dataset.",
      "fixable_by_ai": true
    },
    {
      "item_number": 18,
      "section": "Results",
      "item_name": "Distribution of severity",
      "status": "PARTIAL",
      "current_text": "212 malignant, 357 benign",
      "needed": "Severity spectrum (tumor grade/stage) or alternative diagnoses",
      "suggested_fix": "Detailed tumor grade and staging information was not available in the dataset. The distribution of specific benign diagnoses was not recorded.",
      "fixable_by_ai": true
    }
  ]
}
```
