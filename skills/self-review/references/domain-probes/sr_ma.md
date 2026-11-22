<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Systematic Review / Meta-Analysis probes (P0–P21)

Internal-consistency-first gate (P0) plus a 21-probe checklist (P1–P21). These probes complement (do not replace) the generic Phase 2 issue checklist.

**P0 — Internal-consistency-first gate (run before P1; gates any fabrication claim)**:
- Before alleging fabrication on a manuscript that "feels AI-generated", reproduce the headline pooled statistics, paired study counts (k), and subgroup counts directly from the extracted data table (or supplement included-studies table).
- If paired k, pooled medians, and subgroup counts reproduce, that shows internal consistency, not that the data are genuine — **pivot the review to table-vs-source fidelity (P1), comparator definition (P1), and eligibility**, not to a fabrication framing; assess any integrity concern separately, on source-level or provenance evidence.
- If the table cannot be reproduced, or is internally inconsistent, ask the authors to explain the discrepancy first (a different analysis set or estimator can explain it; see Estimator conventions below), and grade an unexplained discrepancy by its effect on the conclusions.
- Rationale: an "AI-smelling" surface is not evidence of fabrication. Real references can be present and the arithmetic coherent while the substantive flaws are extraction, comparator, eligibility, and overclaiming.
- **Estimator conventions.** When k and the P values reproduce but a non-parametric estimate (for example a paired Hodges–Lehmann estimate) does not, ask the authors which estimator, analysis set, handling of zero differences and software they used before alleging an error, because implementations differ. A value that matches only a convention other than the stated one is a methods–result discrepancy; whether it is a reporting or an analysis error is for the authors to establish, and a changed conclusion sets the severity.

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
- **Reading a leave-one-out (or influence) table.** Note what each deletion removes (a study or an independent dataset), compare each deletion's estimate and interval, and say what changes: the size of the estimate, or, where the paper tests a specific null contrast, its direction or significance verdict. A comment that "robustness is not supported" is easily answered when the paper's conclusion held in every deletion, so name the property that changed, and judge interval changes against a stated clinically meaningful range where one exists. Author side: "robustness was confirmed" should say what was robust.

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
- Standard PROSPERO format: `CRD42` + 9 digits = 14 chars total (e.g. `CRD42024500001`).
- IDs that are not 14 chars or have a non-numeric tail → FORMAT_ANOMALY (MAJOR).
- Always request authors provide live registration URL in cover letter for protocol cross-check.

**P7 — Reference duplicate detection** (extends `/verify-refs`):
- Run `/verify-refs` (PubMed + CrossRef). In addition to standard checks, detect duplicate PMID or DOI within reference list.
- Verbatim duplicates indicate LLM-assisted reference compilation error → MAJOR (cite renumbering required).

**P8 — AI Disclosure presence**:
- `grep -iE "chatgpt|gpt-|llm|generative ai|ai was used|ai-assisted|copilot|claude|gemini|chatbot|large language model"` on manuscript body.
- If 0 matches AND journal requires AI Disclosure (RYAI / Radiology / RSNA family / Lancet family / JAMA family / most BMJ family / Nature family) → flag MINOR-to-MAJOR.

**P9 — Non-significant finding promoted to Abstract (overclaim probe)**:
- Flag any exploratory or non-significant result (a crossover, a trend, a post-hoc subgroup) that appears in the Abstract or Key Points framed as a finding.
- When the Methods name a multiplicity procedure for a family of subgroup or moderator tests, check the family, the procedure and its target level, and that each result called significant survives it (from the reported adjusted P values, or from the family's raw P values when those are needed to recompute); if what the check needs is not reported, that is the request. Keep the prespecified designation: a prespecified primary result that does not meet its criterion is still the primary result, reported with its estimate and interval and described as not meeting it, and a post hoc subgroup does not become primary by being labelled "co-primary".
- When two moderators are presented as separate findings, ask how they are distributed jointly across studies (a cross-tabulation when both are categorical) and whether their effects can be separated.
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
- Beyond reconciliation, the text should say which risk-of-bias and applicability domains were most often high or unclear and what that means for the pooled estimates; a traffic-light figure alone leaves the reader to infer it. Missing interpretation alone is MINOR. Do not sum QUADAS-2 domains into a score.

**P13 — Included-study ↔ reference-list completeness**:
- In an SR/MA, **every study in the characteristics table (Table 1) must be cited in the reference list.** A manuscript that lists included studies only as "First-author Year" labels in Table 1, while the reference list holds only methodology/guideline citations, will draw an "included studies not cited" reviewer flag.
- Deterministic check: each Table-1 included-study label (First-author + Year) must match a reference-list entry for the same report (first author and year find the candidate; a year that differs only between online-first and issue publication is the same report). Flag any included study with no matching reference.
- Place the citations as a cluster at the point the pool is first introduced ("N studies were included [c1; c2; … cN]") so a numeric CSL renumbers them in order of appearance; citations placed only inside a separately-built table file are not processed by the manuscript's citeproc pass.
- Do not source included-study citations from hand-kept extraction notes / appraisal sheets — those carry journal and page errors. Resolve each against an authoritative record (PubMed `efetch` when the report is indexed there), shortlisting same-author/year candidates by **technique + sample size**, not by a remembered journal name, and confirming the match against the title, author list and the report's identifier (PMID, DOI or another persistent identifier) (the same cohort can appear in more than one report). When using PubMed XML, take the article DOI from `PubmedData/ArticleIdList`, not from an ArticleId inside the article's own reference list.
- Check the table's content as well as its citations: ask where the descriptors that bear on applicability are reported (for studies of patients, age and sex), or that the table say when the primary studies did not report them. Severity: MINOR; MAJOR only when the omission prevents assessing an applicability claim the paper makes.

**P14 — Small-k DTA/proportion MA enrollment-overlap → effective independent k**:
- Extends P2 (non-independence) for the small-k case where double-counting changes the verdict, not just the precision. Group included studies by first-author / center / source database, then pull each study's **enrollment / recruitment window** from the source and compare overlapping groups.
- When same-group studies share patients, recompute the **effective independent k** (e.g., k=8 reported → k≈5 once two same-center windows overlap). Ask explicitly whether quantitative pooling is still defensible at the reduced k, or whether a descriptive synthesis is the honest form (cross-link P11).
- A panel that flags overlap as "possible / fixable in revision" without recomputing effective k under-rates a desk-fatal flaw. Severity: MAJOR when the reduced k undermines the pooled estimate; escalate toward unfixable-in-current-form when pooling itself becomes inappropriate.

**P15 — Mixed analysis-unit denominator pooled into one proportion**:
- For a single-arm proportion MA (technical success, complication rate, pneumothorax, etc.), the contributing studies must share a denominator **unit**. Pooling per-patient, per-session, and per-lesion denominators into one proportion makes the estimand undefined.
- Deterministic lead: read the extraction denominator-unit column (or compare each study's reported N vs N_patients / N_sessions / N_lesions). Flag any outcome whose contributing studies mix units.
- Recommend denominator-coherent subset pools as the primary analysis (e.g., per-patient pool primary; per-session as a separate, labeled pool), not one blended proportion. Severity: MAJOR (estimand undefined).

**P16 — "Prospectively registered" vs registration-after-search chronology**:
- When the manuscript or cover letter calls the review "prospectively registered" (PROSPERO/OSF), cross-check the **registration date** against the **search execution / cutoff date**. A search cutoff that predates registration is not retrospective by itself (PROSPERO places the ideal point before screening), but it makes the claim depend on when screening began.
- Lead: if `prospectiv*` co-occurs with the registry name AND (search date < registration date) → find when screening began; flag when screening or extraction predates the initial submission, or when the manuscript gives no way to tell. Recommend either correcting the chronology claim or reframing as "screening and extraction followed registration" (only the steps that genuinely post-date registration may be called prospective).
- Scope: the claim is copied, so check every copy: abstract, Methods, cover letter, and any portal paste text for ethics or registration fields. A portal field rarely carries dates; compare it against the registry record. Use the registry's initial submission date, not the later date the record was published. When the review's own files are available, also compare that date against the earliest screening or extraction file (AI first-pass drafts included): registration after either has begun is retrospective, not merely late.
- **Planning, conduct and timing are separate questions.** A choice called "pre-specified" needs a dated record that documents it before the results that could have informed it were seen, such as the registry record as first submitted or a dated protocol; a choice added in a later amendment is distinguished from the first plan. A statement about how a step was done ("independently", "no automation tools were used") needs the review's own records of that step, AI first-pass screening or extraction included, and stays unverified without them; a plan shows what was intended, not what was done. Ask for the order of events to be stated (which of piloting, formal screening and extraction began before the registry's first submission), for the registration to be described accordingly (see the timing rule above), and for the AI-use disclosure to match the records of each step.
- Severity: MINOR–MAJOR depending on how load-bearing the "prospective" framing is. Every PROSPERO SR/MA cover letter is a candidate.

**P17 — Boundary-degenerate proportion pooled with spurious precision**:
- When a pooled proportion (technical success, sensitivity, specificity) has **a majority of studies at the 0% or 100% boundary**, a GLMM / random-effects pool can be near-degenerate: an I² of 0 may reflect the boundary rather than homogeneity, and a pooled point estimate with a tight CI may read as more precision than the data support.
- Lead: count studies at the 0%/100% boundary per outcome; if ≥ (k−1) are at the boundary, flag the pooled point-estimate/CI as possible spurious precision (a signal to examine, not a verdict).
- Ask for each study's events and denominator alongside the pooled estimate; when the pool cannot support the stated claim, a descriptive tally ("n of k studies reported 100%; the others reported …") may serve better. Severity: MAJOR when a pool that the study-level data cannot support is presented as a headline accuracy/success figure.
- **Very small k (k ≤ 2).** The boundary-count lead above is not informative here (at k=1 it fires on any data). For k=1, report the study's own estimate and interval. For k=2, ask for both studies' events and denominators and the pooling model, and whether the conclusion changes under another reasonable model; heterogeneity is poorly estimated at k=2. Severity: MAJOR only when a comparison or claim that the row cannot support rests on it.

**P18 — Train-vs-validation pool integrity: apparent estimate smuggled into the "validation" pool**:
- A DTA / prognostic-model MA that separates a "training" pool from a "validation" pool must build the validation pool from **held-out / external / cross-validated** estimates only. The failure mode: for studies without cross-validation, the authors drop each study's **apparent (in-sample / resubstitution)** sensitivity–specificity (or "overall estimate") INTO the validation pool — so the headline "validation" performance is partly the same in-sample numbers, and the "train ≈ validation stability" the Discussion leans on is mechanical reuse.
- Lead: grep Methods for a train/validation split co-occurring with {`overall estimate`, `non–cross-validated` / `non-cross-validated`, `apparent`, `resubstitution`, `where validation was unavailable … used the overall`}. Then check whether a **sensitivity analysis excluding non-CV studies materially moves the validation pool** (a large drop = the primary "validation" estimate is optimism-contaminated).
- Severity: MAJOR #1 when the headline rests on it (estimand incoherence — the "validation" pool is not a validation estimate); often unfixable in the current form (recompute restricted to genuinely held-out estimates, or relabel as apparent).

**P19 — Reviewer-side included-study cell audit: metric-type, self-eligibility contradiction, CI provenance**:
- As a reviewer, a **random/convenience sample of the open-access included studies** cell-checked against source is sufficient to demonstrate a systematic extraction-error class — full re-extraction is NOT the reviewer's job. A sampled error rate above ~30% ⇒ the pooled estimates are untrustworthy without author-side full cell reconciliation (P1).
- Beyond value-matches-source (P1), check three extraction pathologies: **(a) metric-type identity** — an `accuracy` or a *different task's* AUC tabulated AS the target AUC (accuracy ↔ AUC ↔ sens/spec are not interchangeable); **(b) self-eligibility contradiction** — an extracted metric/design that violates the review's OWN stated inclusion rule (e.g. an accuracy-only study the eligibility text excludes, entered anyway); **(c) CI provenance** — a CI present in the MA table that **does not exist in the source** ("derived from the point estimate and sample size" is not a valid route to an AUC CI).
- Also flag validation-type / analysis-unit mislabels (5-fold CV recorded as train/validation; N scans counted as N patients). Absence of a per-study 2×2 / sens–spec table is itself a PRISMA-DTA reporting MAJOR.
- Lead: sample K OA included studies; per study confirm metric TYPE + value + that the extracted design satisfies the paper's own eligibility + that any tabled CI appears in the source. Severity scales with the sampled error rate.

**P20 — DTA pooling model and threshold effect**:
- Sensitivity and specificity from the same studies are correlated and may trade off across thresholds. The default synthesis is a bivariate random-effects model (or the equivalent HSROC model), which also yields the summary ROC curve; separate univariate pooling of sensitivity and specificity ignores that correlation. A univariate logistic random-effects fallback is acceptable when the bivariate model is not estimable (few studies, sparse cells, non-convergence), provided the paper says so and why, as `/meta-analysis` also allows. Do not assert that univariate pooling always gives narrower intervals.
- Heterogeneity in a DTA review is not captured by I² for each margin alone. Judge a threshold effect from what the studies actually used (the explicit thresholds, and whether the study points fall along an ROC-shaped curve in SROC space), not from a significance test. A Spearman correlation between sensitivity and false-positive rate (positive under a threshold effect; equivalently, negative between sensitivity and specificity) is descriptive: its absence does not exclude a threshold effect and its presence does not prove one.
- Check that within-study choices were pre-specified: which threshold, reader or analysis unit was taken when a study reported several, and how indeterminate results were handled (cross-link P2, P11, `diagnostic_accuracy.md` D4).
- Severity: first ask for the rationale and model diagnostics. MAJOR when the chosen synthesis is inappropriate for the data or the undescribed threshold or reader selection could materially change the conclusions; MINOR when an appropriate fallback or selection rule is simply unexplained.

**P21 — Reporting-quality (checklist-adherence) reviews: agreement, denominators, and unreported analyses**:
- Applies whenever adherence to a reporting checklist (CLAIM, TRIPOD+AI, STARD, PRISMA) is an outcome, including meta-research and reporting audits submitted under other labels. Other probes apply where relevant.
- **(a) Item-level agreement.** κ is prevalence-sensitive and is undefined when both raters assign every study to one and the same category, so one κ across all items can mislead. For the items that matter, ask for the agreement counts, a measure suited to the scale and raters, and the rule used where κ is undefined.
- **(b) Denominators.** For each headline percentage, ask for the codes, which cells are eligible (not applicable versus applicable but not reported), the numerator and denominator, and whether it pools cells or averages study-level proportions; the two can differ.
- **(c) Coverage of dual scoring.** Ask how many studies were scored by two raters, how they were selected, whether ratings were independent before consensus, and what population the agreement estimate is meant to describe.
- **(d) Planned analyses not reported.** Compare the reported secondary analyses with the protocol; for each material deviation, ask what changed, when and why, and ask for the estimate and its uncertainty when the analysis was run. An analysis that was run and then left out because its result was null is selective reporting; one not run because a prespecified rule stopped the sequence is not.
- Severity: (a)–(c) are MAJOR when a headline adherence or agreement figure cannot be reproduced or interpreted without them; (d) is MINOR unless the omitted analysis was prespecified or bears on the conclusion.

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
