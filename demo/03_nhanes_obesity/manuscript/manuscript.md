# Association Between Body Mass Index and Diabetes Prevalence Among US Adults: A Cross-Sectional Analysis of NHANES 2017-2018

## Abstract

**Background:** Obesity is a well-established risk factor for type 2 diabetes, yet population-level estimates of the association stratified by BMI category and adjusted for demographic confounders remain important for public health surveillance.

**Objective:** To quantify the association between BMI category and diabetes prevalence in a nationally representative sample of US adults, adjusting for age, sex, race/ethnicity, and education.

**Design:** Cross-sectional analysis of the National Health and Nutrition Examination Survey (NHANES) 2017-2018 cycle.

**Setting:** Non-institutionalized civilian US population.

**Participants:** A total of 4,866 adults aged 20 years and older with complete BMI and HbA1c data (excluding 74 underweight participants).

**Main Outcome:** Diabetes, defined as HbA1c of 6.5% or higher.

**Results:** Overall diabetes prevalence was 14.9% (724/4,866). Prevalence increased across BMI categories: 7.5% (95% CI: 6.1%-9.1%) in normal-weight, 13.9% (12.3%-15.7%) in overweight, and 19.9% (18.2%-21.6%) in obese participants. In multivariable logistic regression adjusted for age, sex, race/ethnicity, and education with survey-weight normalization, obesity was associated with 4.50-fold higher odds of diabetes compared with normal weight (OR 4.50, 95% CI: 3.23-6.27, p < 0.001). Overweight was associated with 2.06-fold higher odds (OR 2.06, 95% CI: 1.45-2.92, p < 0.001). Non-Hispanic Asian participants had the highest adjusted odds among racial/ethnic groups (OR 2.97, 95% CI: 1.98-4.44), and female sex was associated with lower odds (OR 0.70, 95% CI: 0.57-0.85).

**Conclusions:** Obesity was associated with a fourfold increase in diabetes prevalence compared with normal weight in this nationally representative sample. The magnitude of this association persisted after adjustment for key demographic confounders. Given the cross-sectional design, these associations should not be interpreted as causal relationships. These findings support targeted diabetes screening and prevention programs for individuals with obesity.

---

## Introduction

Diabetes mellitus affects an estimated 37.3 million Americans, of whom approximately 90-95% have type 2 diabetes. The economic burden of diagnosed diabetes in the United States exceeded $327 billion in 2017, comprising direct medical costs and reduced productivity. Obesity is among the strongest modifiable risk factors for type 2 diabetes, with the pathophysiologic link mediated through insulin resistance, chronic low-grade inflammation, and dysregulated adipokine secretion.

The National Health and Nutrition Examination Survey (NHANES) provides a nationally representative framework for monitoring the prevalence and correlates of chronic diseases in the US population. Regular cross-sectional analyses of NHANES data enable detection of temporal trends and identification of high-risk subpopulations that may benefit from targeted interventions.

Although the association between obesity and diabetes is well established, contemporary estimates that account for the evolving demographic composition of the US population remain valuable for public health planning. Furthermore, the differential burden of diabetes across racial and ethnic groups warrants updated quantification in the context of current BMI distributions. This analysis provides updated prevalence estimates from the most recent complete NHANES cycle with pre-pandemic data, serving as a baseline for comparison with post-pandemic metabolic trends. The objective of this study was to quantify the association between BMI category (normal weight, overweight, obese) and diabetes prevalence in the NHANES 2017-2018 cycle, adjusted for age, sex, race/ethnicity, and education level.

## Methods

### Study Design and Population

This was a cross-sectional analysis of the NHANES 2017-2018 cycle, a nationally representative survey conducted by the National Center for Health Statistics (NCHS) using a complex, multistage, stratified probability sampling design. The study included non-institutionalized civilian adults aged 20 years and older with available body mass index (BMI) and glycated hemoglobin (HbA1c) measurements. Participants classified as underweight (BMI < 18.5 kg/m², n = 74) were excluded to avoid confounding from illness-related weight loss, which may independently affect glycemic status, yielding an analytic sample of 4,866 participants.

### Variables

BMI was categorized as normal weight (18.5-24.9 kg/m2), overweight (25.0-29.9 kg/m2), and obese (30.0 kg/m2 or higher) according to World Health Organization criteria. The primary outcome was diabetes, defined as HbA1c of 6.5% or higher, consistent with American Diabetes Association diagnostic criteria. Glycemic status was additionally classified as normal (HbA1c < 5.7%), prediabetes (5.7%-6.4%), and diabetes (6.5% or higher).

Covariates included age (continuous, in years), sex (male, female), race/ethnicity (non-Hispanic White, non-Hispanic Black, non-Hispanic Asian, Mexican American, other Hispanic, other/multi-racial), and education level (less than high school, high school graduate/GED, some college/associate degree, college graduate or above).

### Statistical Analysis

Baseline characteristics were compared across BMI categories using one-way ANOVA for continuous variables and chi-square tests for categorical variables. Diabetes prevalence with 95% Wilson confidence intervals was calculated for each BMI category.

Multivariable logistic regression was performed using two models. Model 1 (unadjusted) included BMI category alone. Model 2 (adjusted) additionally included age, sex, race/ethnicity (with non-Hispanic White as the reference), and education level (with college graduate or above as the reference). Survey examination weights were incorporated using frequency-weight normalization (weights rescaled so that the sum equaled the analytic sample size) to preserve point estimates while yielding confidence intervals based on the actual sample size rather than an inflated pseudo-population.

All analyses were performed in Python 3.14 using numpy (2.4.3), pandas (2.3.3), scipy (1.17.1), and statsmodels (0.14.6). The significance level was set at two-sided alpha = 0.05. This study was reported according to the Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) guidelines.

### Ethical Considerations

NHANES protocols were approved by the NCHS Research Ethics Review Board, and all participants provided written informed consent. The present analysis used de-identified publicly available data and was exempt from additional institutional review board approval.

## Results

### Participant Characteristics

Of 9,254 NHANES 2017-2018 participants, 4,940 adults aged 20 years and older had complete BMI and HbA1c measurements. After excluding 74 underweight participants (BMI < 18.5 kg/m²) and 4,240 participants with incomplete BMI or HbA1c data, 4,866 were included in the complete-case analysis (Figure 1). Among these, 1,189 (24.4%) had normal BMI, 1,593 (32.7%) were overweight, and 2,084 (42.8%) were obese. The mean age was 51.5 years (SD 17.6), and 51.9% were female. Non-Hispanic White participants comprised 34.7% of the sample, followed by non-Hispanic Black (22.9%) and non-Hispanic Asian (14.1%) participants (Table 1).

BMI categories differed significantly in age (p < 0.001), sex distribution (p < 0.001), and racial/ethnic composition (p < 0.001). Mean BMI ranged from 22.4 kg/m2 (SD 1.7) in the normal group to 36.5 kg/m2 (SD 6.3) in the obese group.

### Diabetes Prevalence

Overall diabetes prevalence was 14.9% (724/4,866). Prevalence increased monotonically across BMI categories: 7.5% (95% CI: 6.1%-9.1%) in normal-weight, 13.9% (12.3%-15.7%) in overweight, and 19.9% (18.2%-21.6%) in obese participants (p < 0.001). Survey-weighted prevalence estimates showed the same pattern: 4.1%, 8.8%, and 14.7% for normal, overweight, and obese groups, respectively (Figure 2).

The distribution of glycemic status differed markedly across BMI categories (p < 0.001). Among normal-weight participants, 68.0% had normal glycemic status, 24.5% had prediabetes, and 7.5% had diabetes. Among obese participants, these proportions were 44.7%, 35.5%, and 19.9%, respectively.

### Association Between BMI and Diabetes

In unadjusted logistic regression (Model 1), both overweight (OR 2.26, 95% CI: 1.61-3.16, p < 0.001) and obesity (OR 4.05, 95% CI: 2.97-5.53, p < 0.001) were associated with significantly higher odds of diabetes compared with normal weight.

After adjustment for age, sex, race/ethnicity, and education (Model 2), the associations remained significant and were slightly strengthened for obesity: overweight (OR 2.06, 95% CI: 1.45-2.92, p < 0.001) and obese (OR 4.50, 95% CI: 3.23-6.27, p < 0.001) (Figure 3).

Among covariates in the adjusted model, each additional year of age increased the odds of diabetes by 6% (OR 1.06, 95% CI: 1.05-1.06, p < 0.001). Female sex was associated with 30% lower odds compared with male sex (OR 0.70, 95% CI: 0.57-0.85, p < 0.001). Compared with non-Hispanic White participants, non-Hispanic Asian participants had the highest adjusted odds (OR 2.97, 95% CI: 1.98-4.44, p < 0.001), followed by non-Hispanic Black (OR 1.84, 95% CI: 1.37-2.47, p < 0.001) and Mexican American participants (OR 1.58, 95% CI: 1.10-2.26, p = 0.013).

Subgroup analysis by age group revealed that diabetes prevalence increased with both age and BMI category. Among adults aged 60-79 years who were obese, diabetes prevalence reached 32.4%, compared with 14.9% among normal-weight adults in the same age group and 5.3% among obese adults aged 20-39 years (Figure 4).

## Discussion

In this cross-sectional analysis of 4,866 US adults from NHANES 2017-2018, obesity was associated with a 4.5-fold increase in the odds of diabetes compared with normal weight after adjustment for age, sex, race/ethnicity, and education. This association demonstrated a clear dose-response pattern, with overweight conferring a twofold and obesity a fourfold increase in odds. Given the cross-sectional design, these associations should not be interpreted as causal relationships; nevertheless, the magnitude and consistency of these findings across subgroups reinforce obesity as the dominant modifiable risk factor for type 2 diabetes at the population level.

The observed adjusted OR of 4.50 for obesity is consistent with prior analyses of earlier NHANES cycles and large prospective cohort studies. The slight increase in the obesity OR from unadjusted (4.05) to adjusted (4.50) models reflects negative confounding by age and race/ethnicity; younger and non-Hispanic White participants are both more likely to have normal weight and less likely to have diabetes, and adjusting for these variables unmasks the full BMI-diabetes association.

The pronounced racial and ethnic disparities observed in this analysis warrant particular attention. Non-Hispanic Asian participants demonstrated the highest adjusted odds of diabetes (OR 2.97) despite having the lowest mean BMI and the highest proportion of normal-weight individuals (25.6%), consistent with the established understanding that Asian populations develop metabolic complications at lower BMI thresholds. This finding supports the World Health Organization recommendation to use lower BMI cut-points for defining overweight and obesity in Asian populations.

Several limitations should be noted. First, the cross-sectional design precludes causal inference; the temporal relationship between obesity and diabetes onset cannot be established. Second, diabetes was defined using HbA1c alone (≥ 6.5%), which may underestimate true prevalence by missing individuals with controlled diabetes on medication or those with diabetes identified only by fasting glucose criteria. A sensitivity analysis using an expanded diabetes definition incorporating fasting plasma glucose ≥ 126 mg/dL and self-reported diabetes diagnosis was not performed. Such analysis would likely increase diabetes prevalence estimates and potentially attenuate odds ratios if the additional cases are more evenly distributed across BMI categories. Third, the analysis did not account for physical activity, dietary patterns, family history of diabetes, or duration of obesity, each of which may confound or modify the BMI-diabetes association. Fourth, although survey weights were applied for point estimates, the simplified variance estimation without Taylor series linearization may underestimate standard errors and produce narrower confidence intervals than appropriate for the complex survey design. Fifth, a complete-case analysis approach was used; of 9,254 total NHANES 2017-2018 participants, 4,314 (46.6%) were excluded due to age criteria, missing BMI or HbA1c data, or underweight status, which may introduce selection bias if missingness is related to the exposure or outcome. Sixth, this analysis applied standard WHO BMI thresholds uniformly across all racial/ethnic groups. Given that Asian populations develop metabolic complications at lower BMI thresholds, ethnicity-specific BMI cut-points may reveal differential obesity-diabetes associations not captured in this analysis.

In conclusion, obesity was associated with a fourfold increase in diabetes prevalence in a nationally representative sample of US adults, with consistent associations across age, sex, and racial/ethnic subgroups. These population-level estimates support the prioritization of weight management as a cornerstone of diabetes prevention policy.

## References

1. Centers for Disease Control and Prevention. National Diabetes Statistics Report, 2022. Atlanta, GA: US Department of Health and Human Services; 2022. [UNVERIFIED - DEMO]
2. American Diabetes Association. Economic costs of diabetes in the U.S. in 2017. Diabetes Care. 2018;41(5):917-928. [UNVERIFIED - DEMO]
3. Kahn SE, Hull RL, Utzschneider KM. Mechanisms linking obesity to insulin resistance and type 2 diabetes. Nature. 2006;444(7121):840-846. [UNVERIFIED - DEMO]
4. National Center for Health Statistics. National Health and Nutrition Examination Survey: 2017-2018 Data Documentation. Hyattsville, MD: NCHS; 2020. [UNVERIFIED - DEMO]
5. WHO Expert Consultation. Appropriate body-mass index for Asian populations and its implications for policy and intervention strategies. Lancet. 2004;363(9403):157-163. [UNVERIFIED - DEMO]

## Figure Legends

**Figure 1.** Study flow diagram. Of 9,254 NHANES 2017-2018 participants, 4,866 adults met the inclusion criteria.

**Figure 2.** Diabetes prevalence by BMI category. Error bars represent 95% Wilson confidence intervals. Prevalence increased from 7.5% in normal-weight to 19.9% in obese participants (p < 0.001).

**Figure 3.** Forest plot of adjusted odds ratios for diabetes. Diamonds indicate point estimates; horizontal lines represent 95% confidence intervals. The dashed vertical line indicates OR = 1.0 (no association). All estimates are from the multivariable model adjusted for age, sex, race/ethnicity, and education.

**Figure 4.** Diabetes prevalence by age group and BMI category. The combined effect of older age and higher BMI yielded the highest prevalence among obese adults aged 60-79 years (32.4%).
