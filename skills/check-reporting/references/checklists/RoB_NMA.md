# RoB NMA Assessment Guide

Risk of Bias in Network Meta-Analysis Tool, Version 1 (March 2024).
Reference: Lunny C et al. Developed by the Knowledge Translation Foundation.
Website: https://www.riskofbias.info

Version: RoB NMA (2025) — 17 items
Source: Lunny C, Higgins JPT, White IR, Dias S, Hutton B, Pham B, et al. Risk of Bias in Network Meta-Analysis (RoB NMA) tool. *BMJ* 2025 (DOI 10.1136/bmj-2024-079839).
Licence: CC BY 4.0 — confirmed via Crossref.
Verification: **NOT VERIFIED.** The items below have not been compared against the published table. They are an in-house summary; complete the official instrument for anything you report.

## Purpose

The RoB NMA tool identifies potential limitations in the way a **network meta-analysis (NMA)** was conducted, including aspects of how the evidence was assembled that may lead to bias in the NMA's results or conclusions.

## Structure

The tool contains **18 items** organized into 3 domains:
1. Interventions and network geometry
2. Effect modifiers
3. Statistical synthesis

Within each domain, signalling statements are evaluated.

Response options: True (T) / Probably True (PT) / Probably False (PF) / False (F) / No Information (NI)

Domain-level judgments: Low risk of bias / Some concerns / High risk of bias

## Using ROBIS with the RoB NMA Tool

The final phase combines:
- RoB NMA domain judgments (for the NMA-specific aspects)
- A systematic review-level quality judgment (e.g., using ROBIS or AMSTAR-2)

This determines whether the **systematic review as a whole** is at risk of bias.

## Domain 1: Interventions and Network Geometry

Assesses whether all relevant interventions and comparators are included and whether the network structure is appropriate.

### Signalling Statements
1.1 All interventions and their comparators included in the NMA are reasonable alternatives for the whole target population
1.2 The interventions and comparators are clearly defined (e.g., dose, frequency, duration)
1.3 The network includes all important interventions that would inform clinical decision-making
1.4 Studies were not selectively included based on which comparisons they evaluated
1.5 The network geometry does not suggest that important comparisons are missing
1.6 Node definitions are clinically meaningful and not arbitrarily lumped or split

### Risk of Bias Judgment
- **Low**: All signalling statements true or probably true
- **Some concerns**: Some statements probably false but unlikely to materially affect conclusions
- **High**: One or more statements false, likely to bias results

## Domain 2: Effect Modifiers

Assesses whether the distribution of effect modifiers is balanced across comparisons (transitivity assumption).

### Signalling Statements
2.1 The distribution of potential effect modifiers is similar across treatment comparisons
2.2 Study characteristics (design, quality, sample size) are balanced across comparisons
2.3 Patient characteristics (age, severity, comorbidities) are balanced across comparisons
2.4 There is no evidence that the transitivity assumption is violated
2.5 Potential sources of intransitivity have been identified and assessed
2.6 Studies informing different comparisons are sufficiently similar to allow valid indirect comparisons

### Risk of Bias Judgment
- **Low**: Effect modifiers are balanced; transitivity assumption appears valid
- **Some concerns**: Some imbalance in effect modifiers but unlikely to materially affect results
- **High**: Clear imbalance in effect modifiers threatening the validity of indirect comparisons

## Domain 3: Statistical Synthesis

Assesses whether appropriate statistical methods were used for the NMA.

### Signalling Statements
3.1 An appropriate NMA model was used (e.g., Bayesian or frequentist, fixed or random effects)
3.2 The model adequately accounts for heterogeneity (between-study variation)
3.3 The consistency assumption was assessed (agreement between direct and indirect evidence)
3.4 Methods for assessing inconsistency were appropriate (node-splitting, design-by-treatment interaction)
3.5 Sensitivity analyses were conducted to examine the robustness of results
3.6 The ranking of treatments was based on appropriate methods (SUCRA, P-score, mean ranks with uncertainty)

### Risk of Bias Judgment
- **Low**: Appropriate statistical methods used; consistency assessed
- **Some concerns**: Minor methodological concerns unlikely to materially affect conclusions
- **High**: Inappropriate methods or unaddressed inconsistency likely to bias results

## Overall Risk of Bias

Combine domain judgments:
- **Low**: Low risk in all 3 domains
- **Some concerns**: Some concerns in at least one domain, no high risk in any
- **High**: High risk in at least one domain

## When to Use

- Assessing the quality of network meta-analyses
- Guideline development involving multiple treatment comparisons
- Overview of NMAs comparing different treatment networks
- Complements individual study RoB tools (RoB 2, ROBINS-I) which assess primary studies within the NMA
- Not for pairwise meta-analyses (use ROB-ME for missing evidence assessment)
