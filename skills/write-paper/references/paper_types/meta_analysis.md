# Paper Type: Systematic Review and Meta-Analysis

## Overview

- **Reporting guideline:** PRISMA 2020 (mandatory)
- **Quality assessment:** QUADAS-2 (diagnostic), RoB 2 (RCTs), MINORS (non-randomized surgical studies)
- **Registration:** PROSPERO required before data extraction (cite protocol)
- **Typical word count:** 4500–6000 words
- **Structure:** Abstract → Introduction → Methods → Results → Discussion → Conclusions

**Worked structure models** (paragraph order + what each paragraph must establish, synthetic):
`exemplar_methods/meta_analysis_prisma.md`, `exemplar_results/meta_analysis_prisma.md`,
`exemplar_discussion/meta_analysis_prisma.md`. This file carries the fuller prose templates;
the exemplars are the compact skeletons for confirming every load-bearing paragraph is present.

---

## Required at Phase 0 (Init)

Before writing, confirm:
1. PROSPERO registration number (or justify non-registration)
2. Search databases (PubMed, Embase, Cochrane, Web of Science minimum)
3. Search date and date of last update
4. Effect measure (OR, RR, HR, MD, SMD, AUC, sensitivity/specificity)
5. Planned subgroup analyses (pre-specified in protocol)

---

## Structured Abstract (250 words)

```
Background: [One sentence: why this systematic review is needed]
Purpose: [PICO: Population, Intervention/Index test, Comparator, Outcome]
Methods: [Databases searched, dates, study design, quality tool]
Results: [N studies, N patients, pooled estimate with 95% CI, 95% PI when I² > 50%, I²]
Conclusion: [Main finding, certainty of evidence]
```

---

## Introduction (400–600 words)

1. **Background:** Why is this question clinically important? What is the burden of disease or diagnostic challenge?
2. **Knowledge gap:** What do existing studies show, and why is a synthesis needed? (Reference 2–4 key studies or previous meta-analyses)
3. **Objective:** State the PICO question explicitly.
   - "The purpose of this systematic review and meta-analysis was to evaluate the diagnostic accuracy of [index test] for [condition] in [population]."
4. **PROSPERO registration:** "This review was prospectively registered with PROSPERO (CRD[number])."

---

## Methods (1200–1800 words)

### 2.1 Protocol and Registration
State PROSPERO number. Confirm adherence to PRISMA 2020.

### 2.2 Search Strategy
List all databases with dates. Provide full search string for at least one database (or supplementary). Include grey literature (ClinicalTrials.gov, conference abstracts if applicable).

**Example:**
"MEDLINE (via PubMed) was searched from inception to [date] using the following strategy: ([MeSH term 1] OR [free text term]) AND ([MeSH term 2] OR [free text term]) AND ([MeSH term 3]). The complete search strategies for all databases are provided in Supplementary Table 1."

### 2.3 Eligibility Criteria

**Inclusion criteria table:**

| Criterion | Specification |
|-----------|---------------|
| Study design | [Prospective/retrospective, cross-sectional, RCT, etc.] |
| Population | [Patient characteristics, age, clinical setting] |
| Index test | [Specific test/intervention] |
| Reference standard | [Gold standard or comparator] |
| Outcomes | [Primary and secondary] |
| Language | English (and specify others if included) |
| Time period | [If applicable] |

**Exclusion criteria:** [List explicitly, not just "did not meet inclusion criteria"]

### 2.4 Study Selection
"Two reviewers (initials) independently screened titles/abstracts, then full texts. Inter-reviewer agreement was [% agreement / Cohen's kappa = X.XX] at the title/abstract stage and [% agreement / Cohen's kappa = X.XX] at the full-text stage. [N] discrepancies were resolved by consensus or a third reviewer (initials). The screening process is summarized in the PRISMA 2020 flow diagram (Figure 1)."

### 2.5 Data Extraction
"Two reviewers independently extracted data using a standardized form. The following variables were extracted: [list 8–15 variables]. Disagreements were resolved by discussion."

**Data extraction table template (Supplementary Table):**

| Study | Year | Country | Design | N | Age (mean±SD) | [Variable 1] | [Variable 2] | Outcome measure | Follow-up |
|-------|------|---------|--------|---|--------------|-------------|-------------|-----------------|-----------|

### 2.6 Quality Assessment
Specify which tool and how it was applied:
- **QUADAS-2** (4 domains: patient selection, index test, reference standard, flow and timing) → 2 reviewers, signaling questions → low/high/unclear risk
- **RoB 2** (5 domains for RCTs) → randomization, deviations, missing data, outcomes, reporting
- **MINORS** (12 items for non-randomized surgical studies) → score 0–24

### 2.7 Statistical Analysis

**Pooling:**
"We pooled effect estimates using a random-effects model with the DerSimonian-Laird estimator. We chose a random-effects model a priori given the expected clinical heterogeneity across studies."

**Heterogeneity:**
"Statistical heterogeneity was assessed using the I² statistic (threshold: I² > 50% indicates substantial heterogeneity) and Cochran's Q test (P < 0.10). The τ² (between-study variance) and 95% prediction interval were reported."

**Subgroup analyses (pre-specified):**
List subgroup variables. Example: scanner type, field strength, patient age group, reference standard type.

**Sensitivity analyses:**
- Leave-one-out analysis
- Restricting to prospective studies only
- Restricting to studies with low QUADAS-2 risk of bias

**Publication bias:**
"Publication bias was assessed using Egger's test (for continuous outcomes) or Deeks' funnel plot asymmetry test (for diagnostic accuracy) when ≥10 studies were available. Trim-and-fill analysis was performed if asymmetry was detected."

**Software:** R (version X.X.X), packages: `meta`, `metafor`. Seed: set.seed(42).

---

## Results (1200–1500 words)

### 3.1 Study Selection
"Database searches identified [N] records. After removing [N] duplicates, [N] records were screened, of which [N] were excluded at the title/abstract stage. A total of [N] full-text articles were assessed for eligibility; [N] were excluded [with reasons]. Finally, [N] studies (N = [total patients]) were included in the systematic review, of which [N] were included in the meta-analysis. The PRISMA 2020 flow diagram is shown in Figure 1."

### 3.2 Study Characteristics
"Included studies were published between [year] and [year]. Sample sizes ranged from [N] to [N] participants (median [N], IQR [N–N]). [N] studies were prospective and [N] were retrospective. Studies were conducted in [list countries]."

Reference the characteristics table.

### 3.3 Quality Assessment
"Quality assessment results are summarized in Figure 2 (QUADAS-2 summary plot). [N] studies were rated at low risk of bias across all four domains. The most common methodological concern was [domain]: [N/N] studies had high or unclear risk."

### 3.4 Quantitative Synthesis
"[N] studies (N = [patients]) contributed to the primary meta-analysis. The pooled [effect measure] was [value] (95% CI, [lower]–[upper]; I² = [value]%, τ² = [value], P for heterogeneity = [value]). The 95% prediction interval ranged from [value] to [value], indicating that in a new study setting, the true effect could be as low as [value]."

Report each subgroup analysis with test for subgroup interaction (P for interaction).

### 3.5 Publication Bias
If ≥10 studies: "Egger's test showed [evidence/no evidence] of funnel plot asymmetry (P = [value]). Trim-and-fill analysis imputed [N] studies, resulting in an adjusted pooled estimate of [value] (95% CI, [lower]–[upper])."

---

## Discussion (800–1000 words)

1. **Summary of evidence:** Restate main finding in one sentence with the effect size and units.
2. **Context with prior meta-analyses:** Compare your estimate to the 2–3 most recent related meta-analyses.
3. **Heterogeneity explanation:** Clinical (population, technique) vs. statistical. Subgroup findings.
4. **Quality of evidence:** Comment on overall QUADAS-2/RoB2/MINORS findings. GRADE (if applicable): downgrade for risk of bias, inconsistency, indirectness, imprecision, publication bias.
5. **Limitations:** (a) cannot rule out publication bias; (b) retrospective study designs; (c) clinical heterogeneity; (d) limited number of studies for subgroup analyses.
6. **Clinical implications:** What should clinicians take from this?

---

## Conclusions (100–150 words)

"In this systematic review and meta-analysis of [N] studies including [N] patients, [index test] demonstrated a pooled [metric] of [value] (95% CI, [lower]–[upper]) for [condition/outcome]. [One sentence on heterogeneity or quality.] These findings suggest that [clinical recommendation or need for further research]."

---

## Required Figures and Tables

| Item | Content |
|------|---------|
| Figure 1 | PRISMA 2020 flow diagram |
| Figure 2 | Forest plot (primary outcome) |
| Figure 3 | Funnel plot (if ≥10 studies) |
| Figure 4 | QUADAS-2 / RoB 2 summary plot |
| Table 1 | Study characteristics |
| Table 2 | Quality assessment results |
| Suppl. Table 1 | Full search strategy (all databases) |
| Table 3 (or next) | GRADE Summary of Findings table |
| Table 4 (or next) | Per-study risk of bias table (NOS domain scores for comparative; JBI item scores for single-arm) |
| Suppl. Table 2 | Excluded studies with reasons |

---

## Common Meta-Analysis Pitfalls

1. **Not registering on PROSPERO** before data extraction — reviewers will ask.
2. **Fixed-effects model without justification** — use random-effects unless strong homogeneity and similar populations.
3. **Reporting I² without prediction interval** — I² tells proportion, not magnitude; prediction interval shows the range of true effects.
4. **Subgroup analyses not pre-specified** — post-hoc subgroups must be labeled as exploratory.
5. **Including studies where the same dataset was used multiple times** — check for overlapping populations.
6. **Misinterpreting non-significant Egger's test** — power is often low; state the limitation.
7. **Confusing statistical significance with clinical significance** — a statistically significant pooled OR = 1.05 may be clinically trivial.
8. **Missing duplicate publications** — check corresponding author + institution + dates.
9. **Not reporting absolute numbers** — always provide N patients per group, not just proportions.
10. **Ignoring GRADE** — many high-impact journals now expect GRADE certainty of evidence ratings.
