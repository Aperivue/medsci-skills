# Efficacy of BCG Vaccination for the Prevention of Tuberculosis: A Systematic Review and Meta-Analysis of Randomized Controlled Trials

## Abstract

**Background:** BCG (Bacillus Calmette-Guérin) vaccine remains the only licensed vaccine against tuberculosis, yet its protective efficacy has varied substantially across trials conducted in different geographic settings.

**Objective:** To quantify the overall efficacy of BCG vaccination in preventing tuberculosis and to explore sources of heterogeneity through subgroup analysis and meta-regression.

**Data Sources:** PubMed, Embase, and Cochrane CENTRAL were searched from inception through December 2023 without language restrictions.

**Study Selection:** Randomized or quasi-randomized controlled trials that compared BCG-vaccinated participants with unvaccinated controls and reported tuberculosis incidence were eligible.

**Data Extraction and Synthesis:** Two reviewers independently extracted data. Risk ratios (RR) with 95% confidence intervals (CI) were pooled using a random-effects model (restricted maximum likelihood estimator). Heterogeneity was assessed with I², Q statistic, and prediction intervals. Meta-regression was performed to evaluate the moderating effect of absolute latitude.

**Results:** Thirteen trials (357,347 participants; 191,064 vaccinated, 166,283 controls; published 1948-1980) were included. The pooled RR was 0.489 (95% CI: 0.344-0.696), corresponding to a 51.1% risk reduction (95% CI: 30.4%-65.6%). Substantial heterogeneity was observed (I² = 92.2%, Q = 152.23, p < 0.001; tau² = 0.3132; prediction interval: 0.155-1.549). Meta-regression identified absolute latitude as a significant moderator (coefficient = -0.0291, p < 0.001), explaining 75.6% of between-study variance. No significant publication bias was detected (Egger's test p = 0.189; Begg's test p = 0.952).

**Conclusions:** BCG vaccination reduced tuberculosis risk by approximately half, with considerably greater efficacy at higher latitudes. The pronounced geographic gradient suggests that environmental mycobacterial exposure may attenuate vaccine-induced protection in tropical regions.

**Registration:** [UNVERIFIED - DEMO] PROSPERO CRD42024000000

---

## Introduction

Tuberculosis remains a leading infectious cause of death worldwide, responsible for an estimated 1.3 million deaths annually among HIV-negative individuals. BCG vaccine, derived from an attenuated strain of Mycobacterium bovis and first administered to humans in 1921, continues to serve as the sole licensed vaccine for tuberculosis prevention. Although BCG vaccination has been incorporated into the immunization programs of over 150 countries, individual trials have reported widely divergent estimates of its protective efficacy, ranging from no detectable benefit to greater than 80% protection.

Several hypotheses have been advanced to explain this heterogeneity. The most prominent is the latitude hypothesis, which posits that exposure to environmental non-tuberculous mycobacteria (NTM) in tropical regions confers partial immunity that masks the incremental benefit of BCG vaccination. Other proposed explanations include differences in vaccine strains, variations in the virulence of prevailing Mycobacterium tuberculosis strains, differences in study methodology and participant selection, and the use of diverse allocation methods across trials.

The original meta-analysis by Colditz et al. (1994) synthesized evidence from 13 prospective trials and demonstrated a pooled relative risk of approximately 0.49, with latitude emerging as a significant moderator. However, the original analysis employed a DerSimonian-Laird estimator without prediction intervals, did not report meta-regression R² statistics, and predated the PRISMA reporting framework. The present re-analysis addresses these gaps by applying restricted maximum likelihood (REML) estimation, computing prediction intervals to characterize the distribution of true effects, conducting meta-regression with R² quantification, performing a complete publication bias assessment (Egger, Begg, and trim-and-fill), and reporting in accordance with PRISMA 2020 guidelines. The objective was to quantify the overall efficacy of BCG vaccination in preventing tuberculosis and to explore sources of between-study heterogeneity through subgroup analysis and meta-regression.

## Methods

### Protocol and Registration

This systematic review followed the Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 guidelines. The protocol was registered prospectively [UNVERIFIED - DEMO].

### Eligibility Criteria

Eligible studies were randomized or quasi-randomized controlled trials that (a) compared BCG-vaccinated participants with unvaccinated controls and (b) reported tuberculosis incidence as an outcome. No restrictions were imposed on language, publication date, or geographic setting. Observational studies, case reports, and studies evaluating BCG revaccination were excluded.

### Information Sources and Search Strategy

PubMed, Embase, and the Cochrane Central Register of Controlled Trials (CENTRAL) were searched from inception through December 2023. The search strategy combined MeSH terms and free-text keywords for BCG vaccination and tuberculosis (PubMed example: ("BCG Vaccine"[MeSH] OR "BCG" OR "Bacillus Calmette-Guerin") AND ("Tuberculosis"[MeSH] OR "tuberculosis") AND ("randomized controlled trial"[pt] OR "controlled clinical trial"[pt])), supplemented by manual review of reference lists from identified systematic reviews. The complete Boolean search syntax for all three databases is provided in the Supplementary Appendix.

### Study Selection and Data Extraction

Two reviewers independently screened titles and abstracts, followed by full-text assessment of potentially eligible records. Discrepancies were resolved by consensus. A standardized extraction form captured trial identifier, first author, publication year, number of events and participants in each arm, absolute latitude of the study site, and allocation method (random, alternate, or systematic).

### Risk of Bias Assessment

Risk of bias was assessed using the Cochrane Risk of Bias tool. Allocation concealment, blinding, and completeness of follow-up were evaluated for each trial. Individual study risk of bias assessments using the Cochrane Risk of Bias tool were planned but not completed for this demonstration analysis. In a full systematic review, a traffic-light summary and risk of bias table would be mandatory.

### Statistical Analysis

Risk ratios with 95% CIs were calculated for each trial using the Mantel-Haenszel method. Effect sizes were log-transformed for pooling. A random-effects model with the restricted maximum likelihood (REML) estimator was used to compute the pooled effect. Heterogeneity was quantified using the Q statistic, I² statistic, tau², and 95% prediction intervals. Subgroup analysis was performed by allocation method (random, alternate, systematic). Meta-regression was conducted with absolute latitude as a continuous moderator, reporting the regression coefficient, its standard error, p-value, and R² (proportion of heterogeneity explained).

Sensitivity analysis included leave-one-out analysis to assess the influence of individual studies and externally studentized residuals to identify influential observations. Publication bias was evaluated using funnel plot inspection, Egger's regression test, Begg's rank correlation test, and trim-and-fill analysis. All analyses were performed in R version 4.5.3 using the metafor (version 4.8.0) and meta (version 8.2.1) packages. Statistical significance was set at a two-sided alpha of 0.05.

## Results

### Study Selection

The database search identified 847 records, supplemented by 42 records from other sources (note: screening numbers in this PRISMA flow are constructed for demonstration purposes and do not reflect an actual systematic search). After removal of 277 duplicates, 612 records were screened at the title and abstract level, of which 71 proceeded to full-text assessment. Fifty-eight articles were excluded for the following reasons: not a randomized or quasi-randomized trial (n = 23), no tuberculosis outcome (n = 14), duplicate population (n = 11), or insufficient data (n = 10). Thirteen trials met all eligibility criteria and were included in the quantitative synthesis (Figure 1).

### Study Characteristics

The 13 included trials were published between 1948 and 1980 and enrolled a total of 357,347 participants (191,064 in the vaccination arm; 166,283 in the control arm). Seven trials used random allocation, two used alternate allocation, and four used systematic allocation. Study sites spanned latitudes from 13° to 55° absolute.

### Overall Efficacy

The pooled risk ratio from the random-effects model was 0.489 (95% CI: 0.344-0.696; p < 0.001), indicating that BCG vaccination reduced the risk of tuberculosis by 51.1% (95% CI: 30.4%-65.6%) (Figure 2). Substantial heterogeneity was observed (I² = 92.2%; Q = 152.23, df = 12, p < 0.001; tau² = 0.3132). The 95% prediction interval ranged from 0.155 to 1.549, indicating that the true effect in a new study setting could range from substantial protection to a modest increase in risk.

### Subgroup Analysis

Subgroup analysis by allocation method revealed the following pooled estimates: random allocation (k = 7), RR = 0.379 (95% CI: 0.221-0.650, I² = 89.9%); alternate allocation (k = 2), RR = 0.582 (95% CI: 0.335-1.011, I² = 82.0%); and systematic allocation (k = 4), RR = 0.654 (95% CI: 0.323-1.324, I² = 86.4%). The test for subgroup differences was not statistically significant (QM = 1.77, df = 2, p = 0.413), and the moderator explained none of the between-study variance (R² = 0%).

### Meta-Regression

Meta-regression with absolute latitude as a continuous moderator was statistically significant (coefficient = -0.0291, SE = 0.0072, p < 0.001), explaining 75.6% of the between-study heterogeneity (R² = 75.6%). The residual I² decreased from 92.2% to 68.4% after accounting for latitude. Trials conducted at higher latitudes demonstrated greater vaccine efficacy (Figure 3).

### Sensitivity Analysis

Leave-one-out analysis demonstrated that no single study altered the pooled estimate to a degree that would change the direction or statistical significance of the overall finding. Pooled RR values ranged from 0.452 (omitting TPT Madras 1980) to 0.533 (omitting Hart & Sutherland 1977). No study was identified as influential based on externally studentized residuals (all |rstudent| < 2).

### Publication Bias

Egger's regression test (t = -1.40, p = 0.189) and Begg's rank correlation test (tau = 0.026, p = 0.952) detected no statistically significant funnel plot asymmetry (Figure 4). Trim-and-fill analysis identified one potentially missing study on the right side of the funnel, yielding an adjusted pooled RR of 0.518 (95% CI: 0.365-0.736), which remained statistically significant.

## Discussion

This meta-analysis of 13 randomized controlled trials demonstrated that BCG vaccination reduced tuberculosis risk by approximately 51%, with a pooled risk ratio of 0.489 (95% CI: 0.344-0.696). The protective effect was stable across sensitivity analyses, and no individual study exerted undue influence on the summary estimate. Publication bias was not detected by formal statistical tests.

The most notable finding was the pronounced geographic gradient in vaccine efficacy. Meta-regression identified absolute latitude as a potent moderator, explaining 75.6% of between-study heterogeneity. Trials conducted closer to the equator consistently reported lower protective efficacy, consistent with the hypothesis that environmental NTM exposure in tropical regions provides cross-reactive immunity that attenuates the incremental benefit of BCG vaccination. This finding aligns with the landmark analysis by Colditz et al. and has been corroborated by ecological studies demonstrating higher NTM prevalence at lower latitudes.

Subgroup analysis by allocation method did not reveal statistically significant differences, suggesting that variations in randomization procedures did not systematically bias the findings. The prediction interval (0.155-1.549) warrants particular attention because its upper bound exceeds unity, meaning that a new trial conducted in a different setting could plausibly observe no protective benefit or even a slight increase in tuberculosis risk among vaccinated individuals. This has direct policy implications: national immunization programs in low-latitude regions cannot rely on the pooled estimate alone to justify BCG vaccination for tuberculosis prevention, and the expected benefit in any individual setting remains uncertain despite the favorable overall average.

A formal GRADE certainty-of-evidence assessment was not performed, which limits the strength of recommendations that can be drawn from this analysis. The overall certainty of evidence is likely low given the high between-study heterogeneity and observational nature of most included studies.

The most consequential limitation is the age of the evidence base: the included trials were conducted between 1948 and 1980, and the epidemiology of tuberculosis has evolved considerably in the intervening decades. Second, the dataset does not capture information on BCG strain, which may contribute to between-study variability. Third, the prediction interval crossing unity indicates persistent uncertainty regarding the expected effect in any individual new setting. Fourth, assessment of additional moderators was limited by the small number of included studies (k = 13).

In conclusion, BCG vaccination reduced tuberculosis risk by approximately half across 13 randomized trials encompassing over 350,000 participants. The geographic latitude of the study site was the dominant source of heterogeneity, consistent with the environmental mycobacteria hypothesis. These findings support the continued use of BCG vaccination, particularly in higher-latitude settings, while highlighting the need for next-generation tuberculosis vaccines with more consistent efficacy across geographic regions.

## References

1. Colditz GA, Brewer TF, Berkey CS, et al. Efficacy of BCG vaccine in the prevention of tuberculosis: meta-analysis of the published literature. JAMA. 1994;271(9):698-702. [UNVERIFIED - DEMO]
2. World Health Organization. Global Tuberculosis Report 2023. Geneva: WHO; 2023. [UNVERIFIED - DEMO]
3. Mangtani P, Abubakar I, Ariti C, et al. Protection by BCG vaccine against tuberculosis: a systematic review of randomised controlled trials. Clin Infect Dis. 2014;58(4):470-480. [UNVERIFIED - DEMO]
4. Fine PEM. Variation in protection by BCG: implications of and for heterologous immunity. Lancet. 1995;346(8986):1339-1345. [UNVERIFIED - DEMO]
5. Roy A, Eisenhut M, Harris RJ, et al. Effect of BCG vaccination against Mycobacterium tuberculosis infection in children: systematic review and meta-analysis. BMJ. 2014;349:g4643. [UNVERIFIED - DEMO]

## Figure Legends

**Figure 1.** PRISMA 2020 flow diagram of study selection. Thirteen randomized controlled trials met all eligibility criteria.

**Figure 2.** Forest plot of BCG vaccine efficacy. Risk ratios with 95% confidence intervals are shown for each trial, with the pooled estimate from the random-effects model (diamond). I² = 92.2%.

**Figure 3.** Meta-regression bubble plot of absolute latitude versus log risk ratio. Each circle represents a study, sized proportionally to the inverse of its variance. The regression line and 95% prediction band are shown. R² = 75.6%.

**Figure 4.** Funnel plot of standard error versus log risk ratio. Open circles represent observed studies; the filled circle represents the single study imputed by trim-and-fill analysis.
