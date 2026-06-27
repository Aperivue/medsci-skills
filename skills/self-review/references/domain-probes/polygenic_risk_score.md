<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; an
         ancestry-portability / incremental-value / overfitting design flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Polygenic risk score probes (PG1–PG8)

An 8-probe checklist for **polygenic risk score / polygenic score (PRS / PGS)** studies — a genome-wide weighted sum of trait-associated alleles used as a predictor or risk-stratifier. These probes complement (do not replace) the generic Phase 2 checklist, the **TRIPOD+AI / TRIPOD** prediction-model items, the **PGS Reporting Standards (PGS-RS)**, and the clinical-prediction-model probes (CP1–CP4 in `clinical_prediction_model.md`); they target the failure modes a PRS adds on top of a generic prediction model — **ancestry transferability, base/target leakage, incremental value over established clinical risk, and the gap between discrimination and clinical/screening utility**. PG1 (ancestry portability) and PG4 (incremental value) are the highest-yield; run them first. This is distinct from the instrumental-variable use of genetics in `mendelian_randomization.md` (PRS is *prediction*, MR is *causal inference*).

**PG1 — Ancestry transferability / portability**:
- Is the **ancestry of the discovery (base) GWAS** stated, and is PRS performance **reported separately for each target ancestry** rather than pooled or assumed? A PRS trained in European-ancestry GWAS systematically **underperforms in non-European ancestries** (lower R²/accuracy) because of **LD differences, allele-frequency differences (drift/selection), and gene–environment interactions on causal effect sizes** — and the loss can be large.
- Differences **within** broad ancestry groups (e.g. across African regional ancestries) can be **as large as across continental groups**, so a single "African" performance figure can itself mislead.
- Was multi-ancestry / ancestry-matched discovery used, or is a single-ancestry score generalized? A deployment / clinical-utility claim extended to ancestries in which the score was not validated → MAJOR (portability failure **and** an equity harm; cross-link the fairness/equity probes EQ in `equity_fairness.md`). The fix is per-ancestry validation (and ancestry-matched or multi-ancestry training), not a generalizability caveat alone.

**PG2 — Base/target independence, tuning, and overfitting**:
- Are the **discovery (base) GWAS** and the **target/validation** samples **independent**? Overlap (e.g. the same biobank in both) inflates the apparent performance. Was any **tuning** (P-value threshold / clumping, LDpred or PRS-CS shrinkage / proportion-of-causal-variants, the chosen quantile cut) done on a **separate tuning set** and the final score evaluated **out-of-sample**?
- Reporting the **best-tuned** configuration's performance **in the same data** used to pick it is overfitting; **winner's curse** similarly inflates if instruments/weights and evaluation share a sample.
- Undisclosed base/target overlap, tuning-and-evaluating in the same data, or no independent/out-of-cohort validation → MAJOR.

**PG3 — Score construction & effect-size reporting**:
- Is the PRS **construction reproducible** — variant set / GWAS source (a **PGS Catalog ID** where available), weights, build, allele alignment/strand handling, and how missing genotypes/imputation were treated?
- Is the score **standardized** and the effect reported as **OR/HR per SD** with a CI, plus **quantile stratification** (decile/percentile, with the **reference group** stated) and, for a clinical claim, **absolute risk** by stratum — not relative risk alone?
- A black-box score with no construction detail, or relative-risk-only reporting with no per-SD CI / absolute risk → MAJOR (reporting), MINOR if only the PGS Catalog ID is missing.

**PG4 — Incremental value over established clinical risk (the clinical crux)**:
- A PRS clinical claim is **not** supported by **PRS-alone AUC**. Does the study report the PRS **on top of the guideline-recommended clinical model** (SCORE2 / QRISK3 / Pooled Cohort Equations / Tyrer-Cuzick / FRAX as appropriate) — the **change in discrimination (ΔC-statistic with a CI)**, **NRI/IDI**, and ideally net benefit — versus the clinical model alone?
- A large **HR/OR per SD** or a high **PRS-alone** AUC presented as "improves prediction" without the incremental-over-clinical comparison overstates utility; the right question is what the PRS adds to what a clinician already has.
- An "improves risk prediction / clinically useful" claim resting on PRS-alone discrimination, or on a ΔC with no CI, → MAJOR (downgrade to "associated with" or add the incremental-value analysis against the clinical model).

**PG5 — Prevalent vs incident, and study design**:
- Is the validation **prospective/incident** (predicting future events in a cohort) or a **cross-sectional case–control prevalent-disease** association? A PRS associates strongly with **prevalent** disease but typically predicts **incident** disease less well — and incident prediction is what a clinical-utility claim requires.
- Case–control sampling, survival/prevalence–incidence bias, and immortal-time issues (cf. the observational probes) apply. A prediction/utility claim from a prevalent case–control design with no incident-cohort validation → MAJOR.

**PG6 — Screening / stratification utility ≠ discrimination**:
- A **population-screening or risk-stratification** claim needs the **operating-characteristic** evidence, not AUC: the **detection rate at a fixed false-positive rate** (or the likelihood ratio for a given PRS quantile), and the **number needed to screen / absolute risk difference** at the proposed cut. Discrimination (AUC) and HR-per-SD routinely look favourable while the **detection rate at an acceptable FPR is poor** — the two are different questions.
- A "useful for population screening / would justify earlier screening in the top decile" claim with only AUC/HR-per-SD and no detection-rate-at-FPR / likelihood-ratio evidence → MAJOR.

**PG7 — Calibration & absolute risk in the target population**:
- Discrimination is **not** calibration. Is the PRS-based (or PRS-plus-clinical) **absolute risk calibrated in the target population** (calibration plot / slope-intercept, observed-vs-expected by stratum), especially when transported **across ancestries or cohorts** where baseline incidence and allele frequencies differ?
- A well-discriminating but **miscalibrated** score gives wrong absolute risks at the individual level. An absolute-risk / actionable-threshold claim with no calibration in the target population → MAJOR (cross-link CP1 apparent-vs-corrected calibration in `clinical_prediction_model.md`).

**PG8 — Reporting standards & clinical-actionability overclaim**:
- Is the study reported against **PGS-RS** (PGS Reporting Standards) / TRIPOD+AI — development and validation samples with ancestry composition, score-construction provenance, and the full performance set (discrimination, calibration, incremental value)?
- Is the conclusion scaled to the evidence — a **relative-risk gradient across quantiles is not, by itself, demonstrated clinical actionability**? A "once-in-a-lifetime test to guide management" / "should be added to guidelines" claim requires incremental value (PG4), calibration (PG7), screening operating characteristics (PG6), and ideally decision-analytic or trial evidence, not association alone.
- A clinical-deployment / guideline-adoption recommendation outrunning the validation, or reporting that omits PGS-RS-level ancestry/provenance/performance detail → MAJOR for the interpretation/headline, MINOR for a reporting-only gap.

**Output template (PG1 example)**:
> "The polygenic score was developed and validated in participants of European ancestry, but the Abstract and Conclusions frame it as a tool for risk stratification in the general population. Because polygenic scores transfer poorly across ancestries — owing to differences in linkage disequilibrium, allele frequencies, and gene–environment interactions — performance in non-European ancestries cannot be assumed and is often substantially lower, which also raises an equity concern. I'd suggest reporting performance (R²/discrimination and calibration) separately for each ancestry available, training on ancestry-matched or multi-ancestry GWAS where possible, and scoping the deployment claim to the validated population unless per-ancestry performance is shown."

**Output template (PG4 example)**:
> "The clinical claim rests on the polygenic score's standalone discrimination (AUC and HR per SD). Because clinicians already risk-stratify with an established model, the decision-relevant question is what the score adds *on top of* that model. I'd suggest reporting the change in the C-statistic (with a confidence interval) and the NRI/IDI when the polygenic score is added to the guideline-recommended clinical risk score (e.g. SCORE2 / Pooled Cohort Equations / Tyrer-Cuzick), and ideally a decision-curve/net-benefit analysis, rather than the score-alone AUC; if the incremental gain is small or its CI includes no improvement, the Abstract and Conclusions should be revised accordingly."
