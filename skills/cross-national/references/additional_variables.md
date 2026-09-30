# Additional KNHANES / NHANES variables and composite-score warnings

Load-on-demand companion to `/cross-national` Phase 2. Read it when the study uses asthma, sleep,
physical-activity, diet, hypertension/lipid-treatment, or non-HDL-cholesterol variables, or a
composite score such as LE8.

## Additional KNHANES Variables (validated via LE8-Asthma replication)

| Variable | Raw Var | Coding |
|----------|---------|--------|
| Asthma | DJ4_dg | 0=No, 1=Yes (physician dx), 8=N/A, 9=Don't know → exclude |
| Asthma medication | DJ4_3 | 1=Regular treatment, 2=Only when symptomatic, 3=None, 8=N/A, 9=Don't know (check the survey year's codebook) |
| Sleep (2017-18) | BP16_11/12/13/14 | **Clock times, NOT hours!** 11=bed hour, 12=bed min, 13=wake hour, 14=wake min. Calculate: duration = wake_time - bed_time (handle midnight crossing). 99=Don't know→NA |
| Sleep (2017-18 weekend) | BP16_21/22/23/24 | Same format as weekday |
| Sleep (2019-20) | BP16_1/2 | Direct sleep hours (weekday/weekend). 99=Don't know→NA |
| PA aerobic | pa_aerobic | 0=Doesn't meet, 1=Meets guidelines. **Note: values are 0/1, NOT 1/2** |
| HTN treatment | DI1_pt | 1=Yes, 0=No, 8=N/A (not diagnosed), 9=Don't know (DI1_pr is current prevalence, not treatment) |
| Dyslipidemia tx | DI2_pt | 1=Yes, 0=No, 8=N/A (not diagnosed), 9=Don't know (DI2_* is the dyslipidemia block) |
| Non-HDL chol | HE_chol - HE_HDL_st2 | Derived: total cholesterol minus HDL |

## Additional NHANES Variables (validated via LE8-Asthma replication)

| Variable | Raw Var | Coding |
|----------|---------|--------|
| Asthma | MCQ010 | "Yes" / "No" (ever told by doctor) |
| Sleep hours | SLD012 | Numeric (hours/night on weekdays) |
| BP treatment | BPQ020 | "Yes" / "No" (told by doctor, high BP) |
| Cholesterol treatment | BPQ100D | "Yes" / "No" (taking cholesterol Rx) |
| PA vigorous work | PAQ605/PAQ610/PAD615 | Yes/No, days/week, min/day |
| PA moderate work | PAQ620/PAQ625/PAD630 | Yes/No, days/week, min/day |
| PA walk/bike | PAQ635/PAQ640/PAD645 | Yes/No, days/week, min/day |
| PA vigorous rec | PAQ650/PAQ655/PAD660 | Yes/No, days/week, min/day |
| PA moderate rec | PAQ665/PAQ670/PAD675 | Yes/No, days/week, min/day |
| Dietary fiber | DR1TFIBE (DR1TOT_J) | Numeric (grams, day 1 recall) |
| Dietary sodium | DR1TSODI (DR1TOT_J) | Numeric (mg) |
| Dietary sat fat | DR1TSFAT (DR1TOT_J) | Numeric (grams) |
| Total energy | DR1TKCAL (DR1TOT_J) | Numeric (kcal) |
| Total sugars | DR1TSUGR (DR1TOT_J) | Numeric (grams) |
| Non-HDL chol | LBXTC - LBDHDD | Derived: TCHOL_J minus HDL_J |

## Composite Score Replication Warnings (learned from LE8 replication)

1. **BMI cutoff mismatch**: LE8 uses WHO <25 which classifies most Koreans as "ideal" → Factor subscore loses BMI discriminatory power in Asian populations. Report this limitation.
2. **KNHANES sleep = clock times**: BP16_11-14 are bedtime/waketime (hour:min), NOT sleep duration. Must compute `wake_time - bed_time` with midnight crossing.
3. **pa_aerobic codes**: Values are 0/1 (not 1/2). Binary → MET-hours approximation is coarse.
4. **Diet quality scoring**: AHEI-2010 requires detailed food group data; nutrient-based proxy gives different distribution. Recommend downloading NHANES DR1TOT_J for dietary recall nutrients.
5. **LE8 sensitivity to implementation**: Small scoring differences compound across 8 components → overall score can diverge substantially, especially in the "moderate" range where most people cluster.
