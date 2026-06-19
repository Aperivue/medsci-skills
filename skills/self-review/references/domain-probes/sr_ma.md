<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Systematic Review / Meta-Analysis probes (P0–P11)

Internal-consistency-first gate (P0) plus an 11-probe checklist (P1–P11). These probes complement (do not replace) the generic Phase 2 issue checklist.

**P0 — Internal-consistency-first gate (run before P1; gates any fabrication claim)**:
- Before alleging fabrication on a manuscript that "feels AI-generated", reproduce the headline pooled statistics, paired study counts (k), and subgroup counts directly from the extracted data table (or supplement included-studies table).
- If paired k, pooled medians, and subgroup counts reproduce, fabrication is unlikely — **pivot the review to table-vs-source fidelity (P1), comparator definition (P1), and eligibility**, not to a fabrication framing.
- Only if the table cannot be reproduced, or is internally inconsistent, escalate to a transparency/integrity MAJOR.
- Rationale: an "AI-smelling" surface is not evidence of fabrication. Real references can be present and the arithmetic coherent while the substantive flaws are extraction, comparator, eligibility, and overclaiming.

**P1 — Performance-MA value + comparator-existence probe**:
- For method-comparison MAs reporting accuracy / DSC / AUC / F1 (model-vs-model, AI-vs-reader, two training paradigms) and for DTA MAs reporting sensitivity / specificity, select ≥2 outlier or headline-driving studies.
- (a) Verify each sampled arm value against the source paper (PubMed abstract or full text). For DTA cells, check for **sens/spec swap** (source sens=A% / spec=B% appearing in the forest as sens=B% / spec=A%).
- (b) **Comparator-existence check**: verify the comparator arm is consistently defined and actually exists in each source. A baseline mislabeled as the comparator inflates the headline (e.g., a limited single-source baseline reported as a "centralised" comparator when the source paper has no centralised arm).
- (c) Per-study schema: `Exists | Correct citation | Eligible (domain-specific) | Same comparator (same task/dataset) | Value matches source | Author-derived/averaged | Verdict`.
- (d) Severity ladder: `<1pp rounding or author-derived average = minor`; `wrong dataset/task/comparator or not domain-specific = major`; `unfindable or wrong-citation = integrity concern (verify against source); potentially major`.
- If a confirmed error drives a reported subgroup p-value or a headline claim, register as a primary major finding.

**P2 — Cohort / benchmark non-independence probe**:
- Identify clusters in included studies sharing: (a) institution name, (b) author surname + year proximity, (c) public ICU/EHR database (MIMIC-IV, eICU, MIMIC-III, KNHIS, UK Biobank, Optum, MarketScan, IBM), (d) **public imaging-challenge benchmark** (BraTS, FeTS, TCIA, Kaggle) reused across multiple included studies.
- For each cluster, fetch PubMed efetch affiliation + abstract Methods database/benchmark source.
- Flag pairs sharing the same data source + overlapping enrollment period (or the same public benchmark) as "high-confidence non-independence".
- Manuscript should acknowledge in Limitations + perform a leave-one-dataset-out sensitivity analysis and add a data-provenance column to Table 1. If absent → MAJOR.
- **Nuance**: map provenance and *request* the provenance column + sensitivity analysis; do NOT assert that a specific study used a given benchmark from coarse supplement labels alone (e.g., a supplement labeling a study only as "Hospital" or "Public" does not confirm BraTS/FeTS use). Confirm against the source before stating it.

**P3 — Diagnostic subset N transparency (mixed DTA + prognostic MA)**:
- Compute bivariate pool denominator (TP+FP+TN+FN) from Table 2 or forest plot.
- Compare to total N reported in Abstract.
- If diagnostic subset is <50% of total without explicit "diagnostic subset N = X / Y" in Results → MAJOR transparency gap.

**P4 — k=1 subgroup flag**:
- Inspect subgroup analyses for strata with k=1 (single included study).
- If a reported subgroup p-value is driven by k=1 stratum → flag MAJOR.
- Recommend reframing as exploratory or removing from formal subgroup test.

**P5 — Supplementary completeness check**:
- SR-MA supplementary must contain at minimum:
  - PRISMA / PRISMA-DTA checklist with page refs
  - Full-text exclusion list with reasons (per PRISMA 2020 item 16b)
  - Per-study data extraction table
  - Per-study × per-domain risk-of-bias table (QUADAS-2 / QUADAS-AI / PROBAST / PROBAST-AI)
  - Full search strategy verbatim per database
- If supplementary contains only figure captions or is missing 3+ of these → MAJOR.

**P6 — PROSPERO ID format + live URL request**:
- Standard PROSPERO format: `CRD42` + 4-digit YYYY + 6-digit sequential = 13 chars total. Some pre-2020 IDs are 12 chars (5-digit sequential).
- IDs with >13 chars or non-numeric tail → FORMAT_ANOMALY (MAJOR).
- Always request authors provide live registration URL in cover letter for protocol cross-check.

**P7 — Reference duplicate detection** (extends `/verify-refs`):
- Run `/verify-refs` (PubMed + CrossRef). In addition to standard checks, detect duplicate PMID or DOI within reference list.
- Verbatim duplicates indicate LLM-assisted reference compilation error → MAJOR (cite renumbering required).

**P8 — AI Disclosure presence**:
- `grep -iE "chatgpt|gpt-|llm|generative ai|ai was used|ai-assisted|copilot|claude|gemini|chatbot|large language model"` on manuscript body.
- If 0 matches AND journal requires AI Disclosure (RYAI / Radiology / RSNA family / Lancet family / JAMA family / most BMJ family / Nature family) → flag MINOR-to-MAJOR.

**P9 — Non-significant finding promoted to Abstract (overclaim probe)**:
- Flag any exploratory or non-significant result (a crossover, a trend, a post-hoc subgroup) that appears in the Abstract or Key Points framed as a finding.
- Sub-check: does the promoted finding depend on a study flagged or mis-extracted under P1? (A headline crossover can collapse once a mis-extracted comparator is corrected.)
- Flag "non-inferiority" / "equivalence" asserted without a pre-specified margin. A margin cannot be pre-specified retrospectively — ask the authors to document any pre-existing protocol margin, otherwise drop the non-inferiority language or present it explicitly as a post hoc equivalence / sensitivity analysis.

**P10 — Citation-metadata confusion class (over-escalation guard)**:
- DOI-suffix digits that surface as an apparent article number (e.g., a DOI tail "77196" against article number 26068, or "60466-1" against 6274) are cosmetic metadata confusion, **not** fabrication — do not escalate them as fabricated references.
- Reference-list duplicates are handled by `/verify-refs` (`duplicate_findings[]`); AI-disclosure presence is the cross-cutting P8 check. Neither is unique to SR/MA.

**P11 — Poolability / construct-validity gate (does this synthesis hold at all?)**:
- Before refining cell-level extraction (P0/P1), ask the higher-altitude question the forensic layer skips: are the pooled studies answering the *same clinical question* on *comparable populations / index tests / reference standards*, such that combining them into one estimate is meaningful?
- Check that the quality / risk-of-bias instrument is valid for the included *study/model class* (e.g., a radiomics-specific QA tool applied to deep-learning studies; METRICS vs CLAIM / PROBAST mismatch). An instrument applied outside its intended class invalidates the RoB synthesis.
- When k is small and P2 non-independence reduces the independent-cohort count further (e.g., k=6 → k≈4 after overlap), quantitative pooling itself may be inappropriate → a systematic review with **descriptive synthesis** is the correct form, not a forced meta-analytic pool (and not merely a sensitivity analysis layered on top).
- This is an **unfixable-in-current-form** defect when present: cell-level re-extraction cannot rescue a synthesis that should not have been pooled. Let it dominate the severity tier over fixable extraction/reporting defects — strong cell-level forensics must not set a lenient tier when the synthesis itself is invalid.

**P12 — Risk-of-bias table row-sum ↔ figure-matrix reconciliation**:
- For every per-study risk-of-bias row (NOS ★/☆, JBI Y/N, QUADAS-2/PROBAST domain grid), the count of awarded items must equal the row's stated total (NOS: ★ count == "N/9"; JBI: Y count == the "Yes" column). A row whose cells do not sum to its printed total is a visible internal contradiction — especially in a traffic-light **figure**, where a reader sees, e.g., seven filled cells next to a "6/9" label.
- Cross-check the **figure-generating data matrix** (the R/Python script that draws the traffic-light) against the **supplementary RoB table** cell-by-cell. A transcription drift between the two surfaces as a figure-vs-table mismatch even when each row's printed total looks fine.
- The single source of truth is the **primary reviewer assessment form** (the filled extraction/appraisal sheet), not a value hardcoded in a plotting script. When they disagree, regenerate the figure from the assessment form and re-derive the table; then re-sync the table, caption, and any prose sentence that names per-item losses.
- Severity: a row-sum vs total mismatch (or figure vs table mismatch) in a submitted artifact is MAJOR (it reads as a data-handling error). Motivating case: an NOS figure drew one study with seven stars but labeled it 6/9 because the plotting script's comparability cell contradicted the primary appraisal form.

**P13 — Included-study ↔ reference-list completeness**:
- In an SR/MA, **every study in the characteristics table (Table 1) must be cited as a numbered reference.** A manuscript that lists included studies only as "First-author Year" labels in Table 1, while the reference list holds only methodology/guideline citations, will draw an "included studies not cited" reviewer flag.
- Deterministic check: the set of Table-1 included-study labels (First-author + Year) must be a subset of the reference-list first-authors. Flag any included study with no matching reference.
- Place the citations as a cluster at the point the pool is first introduced ("N studies were included [c1; c2; … cN]") so a numeric CSL renumbers them in order of appearance; citations placed only inside a separately-built table file are not processed by the manuscript's citeproc pass.
- Do not source included-study citations from hand-kept extraction notes / appraisal sheets — those carry journal and page errors. Resolve each via PubMed `efetch` (authoritative), disambiguating same-author/year papers by **technique + sample size** (e.g., a study reporting "249 tumors, 110 adjacent to the diaphragm" is identified by the n that matches the synthesis, not by a remembered journal name). Take the article DOI only from `PubmedData/ArticleIdList`, not from an ArticleId inside the article's own reference list.

**Output template (P1 cell-swap example)**:
> "I spot-checked [Author Year] (PMID [...]) against the source paper and found that the values in Figure X are swapped. The source paper reports external-test sensitivity A% / specificity B% (n=N); the manuscript forest entries place [num1/denom1] in the sensitivity slot (which is the source's specificity numerator/denominator) and [num2/denom2] in the specificity slot (which is the source's sensitivity)."

**Output template (P1 comparator-existence example)**:
> "I spot-checked [Author Year] (PMID [...]) against the source. The manuscript lists this study's comparator ('[label]', [value]) in [comparison], but the source paper does not report that arm; the [value] appears to be the study's [limited single-source baseline]. Because this entry contributes to [the pooled comparison / a headline claim], I'd suggest re-extracting the comparator definition per study and adding a comparator-definition column to Table 1 so readers can confirm each arm is the same task on the same data."

**Output template (P2 example)**:
> "[Author1 Year1] uses [Database] (N=...). [Author2 Year2] uses [Database] (N=...). These are nearly certainly overlapping patient pools, and the statistical independence assumption for MA pooling is violated. I'd suggest a sensitivity analysis excluding one of the two studies, plus an explicit cohort-source column in Table 1."

**Discipline — leads vs findings (applies to every P0–P10 probe)**:
- Output from a forensic sub-agent or automated scan is a **lead, never a finding, until confirmed against the source.** Concrete failure modes to discard on inspection: treating recent (in-press / current-year) publication dates as "impossible", inventing journal article-number rules, and inflated all-or-nothing fabrication-risk scores.
- Before finalizing, run an **overclaim sweep of your own draft** (mandatory external-QC pass — independent model or colleague). Two worked examples: a strong claim that "the references are real, not fabricated" should be narrowed to "the sampled references / DOIs resolved"; a benchmark example list should be trimmed to studies whose benchmark use was source-confirmed.
- **Do not compute chance-probabilities** for suspicious or identical values. Record the observation neutrally: "exact match to ≥2 decimals; source verification pending."
