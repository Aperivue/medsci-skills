<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a
         code-list / linkage-quality / selection-flow / RWD-bias design flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Routinely-collected-data study probes (RD1–RD8)

An 8-probe checklist for observational studies conducted using **routinely-collected health data** — administrative claims, electronic health records (EHR), disease/population registries, health-administrative and health-checkup databases, and linked versions of these (data **not collected for the study's purpose**). These probes complement (do not replace) the generic Phase 2 checklist, the **STROBE** + **RECORD** reporting items (and **RECORD-PE** for drug studies), and the observational-confounding probes (`observational_confounding.md`, which cover adjustment/collider/analysis-unit issues). They target what secondary-use data add: whether the database can even observe the question, whether the phenotype code-lists and linkage are evidenced rather than asserted, and whether the limitations endemic to data collected for another purpose are confronted. RD2 (phenotype code-lists & validation), RD3 (linkage quality), and RD4 (participant-selection flow) are the highest-yield; run them first.

**RD1 — Database identity, provenance, and fitness-for-purpose**:
- Is the **database named** and its **type** (claims / EHR / registry / health-checkup), provenance, coverage population, and capture window described — and can it **structurally observe** the exposure and outcome? A claims database cannot see out-of-network or cash-pay care; an EHR cannot see care at other systems; neither reliably sees OTC drugs, over-the-counter outcomes, or death out of hospital.
- Is the **timeframe and geographic setting** stated (title/abstract per RECORD 1.1–1.2)?
- An unnamed/undescribed database, or one whose structure cannot capture the named exposure/outcome (so the measure is systematically incomplete), → MAJOR.

**RD2 — Phenotype definitions: code-lists and algorithms, evidenced not asserted**:
- Are the **codes / algorithms** (ICD-9/10, CPT/HCPCS, ATC/NDC drug codes, Read/SNOMED, lab thresholds) used to define the **population, exposure, outcome, confounders, and effect modifiers** provided in full (text or supplement), per RECORD 6.1 / 7.1? "Diabetes/MI/the cohort was identified from the database" with **no code list** is the single most common RECORD failure.
- Are those definitions **validated** — a referenced validation study, or a PPV/sensitivity estimate — or at least is the lack of validation acknowledged (RECORD 6.2)? An unvalidated outcome algorithm presented as if it were a gold-standard diagnosis is a misclassification risk (RD5).
- Missing code-lists, or validated-sounding phenotypes with no validation reference/acknowledgement → MAJOR.

**RD3 — Data linkage and linkage-quality evaluation**:
- If two or more databases were **linked**, is the **linkage method** (deterministic on a unique identifier vs **probabilistic**, and on which fields) and the **linkage-quality evaluation** (match/linkage rate, handling of non-matches and false matches, any bias in who links) reported (RECORD 12.3)? Is a **person-flow at each linkage stage** shown (RECORD 6.3)?
- Are individuals who **failed to link** characterised (linkage is often differential by age/region/insurance), and is the impact on selection considered?
- Undisclosed linkage method or quality, no linkage-stage flow, or treating the linked subset as representative without examining non-linkage → MAJOR.

**RD4 — Participant-selection flow including data-quality filtering**:
- Is there a **selection/flow** from the source database to the analytic cohort that includes filtering on **data quality, data availability, and linkage** — not only clinical eligibility — with the **N at each step** (RECORD 13.1)? A jump from "the database contains N million records" straight to an analytic N, with the exclusions opaque, hides selection bias.
- Is the **analysis unit** (persons vs records/encounters/claims) explicit and consistent (cross-link `observational_confounding.md` O8)?
- No data-driven selection flow, or an unexplained gap between source and analytic N → MAJOR.

**RD5 — Misclassification of exposure and outcome**:
- Are **exposure and outcome misclassification** (from coding/recording, not clinical adjudication) acknowledged and, where possible, **quantified** (validation PPV/sensitivity, quantitative bias analysis, or a sensitivity analysis under alternative definitions)? Are **proxy/surrogate** measures (a prescription ≠ ingestion; a code ≠ the disease) flagged as such?
- Coded variables treated as gold-standard with no misclassification discussion, or a single rigid definition with no sensitivity to a broader/narrower one → MAJOR (or MINOR if non-differential and acknowledged).

**RD6 — Missing data and informative missingness**:
- Secondary data are frequently **missing-not-at-random** — a lab not ordered is not a normal lab, an unrecorded covariate is not absence of the condition. Is missingness **characterised** (extent, pattern) and handled appropriately (not a naive complete-case that assumes MCAR when missingness is informative; multiple imputation or a sensitivity analysis where justified)?
- Naive complete-case analysis on informatively-missing EHR fields, or treating "no record of X" as "X absent" without justification → MAJOR.

**RD7 — Unmeasured confounding and RWD-specific design bias**:
- Is **unmeasured/residual confounding** confronted — secondary data often lack lifestyle, disease severity, frailty, or over-the-counter exposures — with a negative-control, E-value, or sensitivity analysis, rather than asserting "adjusted for available confounders" (cross-link `observational_confounding.md`)?
- For an exposure/drug study, are the biases endemic to RWD addressed by **design**: **immortal-time bias** (time-fixed exposure misclassified person-time), **prevalent-user bias** (new-user / active-comparator design), **protopathic/reverse-causation bias** (a lag/induction window), and confounding by indication? (These are the core of **RECORD-PE**.)
- An effect estimate with no engagement with unmeasured confounding, or a drug-effect design exposed to immortal-time / prevalent-user bias with no mitigation → MAJOR.

**RD8 — Eligibility drift, data access, and reproducibility**:
- Over the study window, did **coding systems or eligibility/enrolment rules change** (ICD-9→10 transition, formulary or coverage changes), and is that acknowledged (RECORD 19.1)? 
- Are the **extent of data access**, the **data-cleaning methods**, and the **availability of the protocol, derived-variable definitions / code-lists, and analysis code** stated (RECORD 12.1 / 12.2 / 22.1)? Reproducibility in RWD studies rests on the published phenotype definitions and code.
- Unacknowledged coding/eligibility drift over a multi-year window, or no availability of protocol/code-lists/code for a non-public database, → MAJOR (drift) / MINOR (availability), per centrality.
