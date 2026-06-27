<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; an
         instrument-validity / pleiotropy / sample-overlap design flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Mendelian randomization probes (MR1–MR8)

An 8-probe checklist for **Mendelian randomization (MR)** studies — causal-inference designs that use germline genetic variants as **instrumental variables (IVs)** for an exposure: two-sample summary-data MR, one-sample MR, multivariable MR (MVMR), drug-target / cis-MR, and non-linear MR (NLMR). These probes complement (do not replace) the generic Phase 2 checklist and the **STROBE-MR** reporting items; they target the gap between MR's "genetic randomization mimics a trial" framing and whether the three IV assumptions and their sensitivity analyses actually hold. The two-sample summary-data approach is cheap and public, which has produced an explosion of low-quality MR — so the burden is on the manuscript to *evidence* validity, not assert it. MR2 (instrument validity) and MR4 (pleiotropy-robust sensitivity) are the highest-yield; run them first.

**MR1 — Research question, estimand, and engagement with prior evidence**:
- Is the exposure a **well-defined, modifiable, heritable** trait with a credible genetic instrument, or an ill-defined / non-modifiable / composite construct for which a genetic proxy is not interpretable? A genetic instrument for a vague exposure estimates the effect of *whatever the variants actually act on*, not the named exposure.
- MR estimates a **lifelong average effect of a genetically-proxied shift** in the exposure, not the effect of a time-limited clinical intervention; interpreting a per-SD genetic estimate as the expected effect of a drug/behaviour change started in adulthood is an estimand mismatch (see MR8).
- Is the finding **triangulated** with prior observational/RCT evidence and discrepancies discussed, or presented in isolation? A hypothesis-free "everything-on-everything" phenome-wide MR scan additionally inherits the many-comparison multiplicity problem (cross-link O17 in `observational_confounding.md`).
- An MR on an ill-defined/non-modifiable exposure, an estimand over-translated to a clinical-intervention magnitude, or a result with no engagement with the existing literature → MAJOR.

**MR2 — The three IV assumptions, evidenced not asserted**:
- **(IV1) Relevance** — the variant(s) are strongly associated with the exposure. Is instrument strength quantified (**F-statistic**, variance explained R²; a mean/conditional F well above ~10)? **Weak instruments** bias two-sample MR toward the null and one-sample MR toward the confounded observational estimate, and inflate type-1 error under sample overlap (MR6).
- **(IV2) Independence / exchangeability** — the instrument is independent of confounders of the exposure–outcome relationship. Is this supported (e.g. a PhenoScanner-style scan showing the variants are not associated with obvious confounders; population-stratification control via ancestry-matched GWAS + principal components)?
- **(IV3) Exclusion restriction** — the instrument affects the outcome **only through the exposure**. This is the un-testable assumption; **horizontal pleiotropy** is the central threat and must be interrogated indirectly (MR4).
- **Winner's curse** — were instruments selected in a GWAS **independent** of the one used to estimate the variant–exposure association? Selecting and estimating in the same sample inflates the instrument–exposure effect and biases the MR estimate.
- A genome-wide-significant instrument list with **no F-statistic / strength reporting**, no confounder/pleiotropy screen, or instruments discovered and weighted in the same sample → MAJOR.

**MR3 — Instrument construction, LD, and harmonization**:
- Are instruments selected at a justified threshold (genome-wide significance P < 5 × 10⁻⁸, or a pre-stated alternative) and **LD-clumped** (r² and window stated; a sensitivity at a stricter r² is reassuring)? Were **palindromic / ambiguous** SNPs handled and effect alleles **harmonized** across the exposure and outcome GWAS (a harmonization error silently flips the sign)?
- For **cis / drug-target MR** with multiple correlated variants in a single locus, naive IVW (which assumes independent instruments) is wrong — a correlation-aware estimator (e.g. **GLS-corrected IVW** with the LD matrix) is required, and the LD reference must match the GWAS ancestry.
- Were variants directly associated with the **outcome or known confounders** removed (or a reason given to keep them)?
- Undisclosed clumping/harmonization, palindromic mishandling, or naive IVW on correlated cis variants → MAJOR (sign/precision can be driven by the artefact).

**MR4 — Pleiotropy-robust sensitivity suite (not IVW alone)**:
- IVW is efficient but assumes **no horizontal pleiotropy**; a credible MR reports a **pre-specified suite of estimators with different bias assumptions** and shows the estimate is **concordant** across them: **MR-Egger** (its intercept tests directional pleiotropy), **weighted median** (valid if ≤50% of weight is invalid), **weighted mode**, and **MR-PRESSO** (detects/corrects outliers). Concordance across methods — not the IVW point estimate — is the actual robustness claim.
- Is **heterogeneity** across instruments reported (**Cochran's Q**, I²_GX), and are outliers investigated rather than silently dropped?
- A headline causal claim resting on **IVW only**, with no pleiotropy-robust estimators and no heterogeneity assessment → MAJOR (downgrade to exploratory or add the sensitivity suite). MR-Egger alone, with low precision, is not a substitute for the full suite.

**MR5 — Direction of causation / reverse causation**:
- Could the genetic association run **outcome → exposure** (or to a shared upstream trait)? Is the **direction** addressed — **Steiger filtering** (the instrument should explain more variance in the exposure than in the outcome) and/or **bidirectional MR**?
- When exposure and outcome are biologically intertwined (e.g. a biomarker and a disease that alters it), absence of a direction check is a real threat, not a formality.
- A plausibly-reversible exposure–outcome pair analysed in one direction only, with no Steiger/bidirectional check → MAJOR (or a prominent limitation when direction is otherwise constrained).

**MR6 — Sample overlap, ancestry, and two-sample assumptions**:
- Two-sample MR assumes the exposure-GWAS and outcome-GWAS samples are **independent**. Is the **degree of overlap** reported (e.g. UK Biobank contributing to both)? Overlap biases the estimate toward the **confounded observational** association and, combined with weak instruments (MR2), inflates type-1 error; it must be disclosed and, where material, addressed (independent samples, an overlap-corrected method, or a stated bias direction).
- Are the GWASs **ancestry-matched**, with population stratification controlled? Cross-ancestry instruments carry different LD and allele frequencies and can bias the estimate.
- Undisclosed substantial sample overlap, or cross-ancestry instrument transport with no LD/stratification handling → MAJOR.

**MR7 — Non-linear MR caution**:
- A reported **non-linear / threshold / J- or U-shaped** MR effect from the **residual** or **doubly-ranked** stratification methods must be treated with caution: both can produce **artefactual shapes** (documented failures for Vitamin D, BMI, and a failure to recover the trial-established LDL-C → myocardial-infarction shape). A quoted inflection point/threshold from NLMR is not a validated cutoff.
- Are the NLMR-specific safety checks present — **negative-control outcomes**, **positive controls** (a relationship of known shape), **sensitivity excluding extreme exposure strata**, **biological plausibility**, and **triangulation**? Is the stratification on the **non-genetic (residual) exposure** acknowledged as the assumption it is?
- An NLMR "threshold/saturation" claim with no negative/positive controls and no extreme-stratum sensitivity → MAJOR (this is the MR analogue of the data-driven threshold mining in O12; cross-link it).

**MR8 — Interpretation, drug-target specifics, and STROBE-MR reporting**:
- Is the conclusion scaled to what MR supports — a **lifelong genetic-proxy effect direction**, not a precise **clinical-intervention magnitude**? "A drug lowering X will reduce risk by the per-SD MR estimate" over-reads the design (MR1 estimand).
- **Drug-target / cis-MR** specifics: is **colocalization** reported to distinguish a shared causal variant from LD confounding between the exposure-pQTL/eQTL and the outcome signal; is a **positive control** (a known on-target effect) shown; and is an **adverse-effect / phenome-wide** scan reported for safety claims? A drug-target MR with no colocalization is open to LD-driven confounding.
- Is the study reported against **STROBE-MR** (data sources, instrument selection, assumptions, sensitivity, overlap), and — for a registered analysis — was the primary analysis pre-specified?
- A causal claim translated into a clinical-effect size, a drug-target MR without colocalization, or reporting that omits STROBE-MR-level instrument/assumption detail → MAJOR for the interpretation/headline, MINOR for a reporting-only gap.

**Output template (MR4 example)**:
> "The causal claim rests on the inverse-variance-weighted estimate alone. Because IVW assumes no horizontal pleiotropy — the un-testable exclusion-restriction assumption — a single IVW estimate cannot support a causal conclusion on its own. I'd suggest reporting a pre-specified pleiotropy-robust suite (MR-Egger with its intercept test for directional pleiotropy, weighted median, weighted mode, and MR-PRESSO for outliers) and showing the estimate is concordant across them, together with a heterogeneity assessment (Cochran's Q) and an F-statistic for instrument strength. If the estimate is not stable across methods, or the MR-Egger intercept indicates directional pleiotropy, the causal interpretation should be downgraded accordingly and the Abstract/Conclusions revised to match."

**Output template (MR6 example)**:
> "The exposure and outcome GWAS both include UK Biobank, so the two-sample independence assumption is violated by partial sample overlap. Overlap biases the estimate toward the confounded observational association and, with any weak instruments, inflates the type-1 error rate. I'd suggest quantifying the overlap, reporting the mean F-statistic, and either using non-overlapping samples, applying an overlap-aware correction, or at minimum stating the expected direction and magnitude of the resulting bias so the causal claim can be read against it."
