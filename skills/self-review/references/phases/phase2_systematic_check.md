# Phase 2 — Systematic Check: the A–L category detail

Load-on-demand companion to `/self-review` Phase 2. SKILL.md keeps the category
index and the deterministic gates; this file carries the per-category check
tables — the long enumeration you only need once you have the manuscript in hand
and know its type.

Run the manuscript through each applicable category. For each item, assess whether
a reviewer would raise it as a Major or Minor comment. Use the Research-Type
Adaptation table in SKILL.md to decide which categories apply fully, partially, or
not at all for this manuscript type.


## A. Study Design & Data Integrity

| Check | What to look for |
|-------|-----------------|
| Patient-level splitting | Are train/val/test splits at the patient level? Is this explicitly stated? |
| Leakage risk | Any postoperative variable used in a preoperative model? Cohort-wide preprocessing before split? |
| Input-text contamination | For NLP/LLM extraction tasks, does any supplied report text (clinical history, indication, impression, prior diagnosis, referral text) already contain the target label? If yes, mark as Major unless the input was masked or a no-leaky-field sensitivity analysis is reported. |
| Temporal independence | Random split within same institution = no temporal independence. Acknowledged? |
| Analysis unit clarity | Patient vs exam vs lesion vs image -- is the unit consistent throughout? |
| Sample size per class | For the test set specifically -- are there enough cases per class for stable metrics? |

## B. Reference Standard & Ground Truth

| Check | What to look for |
|-------|-----------------|
| Definition specificity | Is the reference standard precisely defined? (e.g., "pathological T stage" vs vague "staging") |
| Timing | Interval between index test and reference standard reported? |
| Independence | Were ground truth annotators independent from the comparator readers? |
| Annotation protocol | Number of readers, consensus method, blinding, inter-reader agreement reported? |

## C. Validation & Statistical Reporting

| Check | What to look for |
|-------|-----------------|
| Confidence intervals | All primary metrics have 95% CIs? |
| Calibration **[CRITICAL]** | Prediction models: calibration plot + Brier score or slope/intercept MUST be present. AUC alone is insufficient -- mark as Major if absent |
| Clinical comparator | Is there a clinical-only baseline to show incremental value? |
| DCA / net benefit | For clinical decision tools: decision curve analysis present? |
| Fine-tuning baseline | For LLM/NLP fine-tuning, LoRA, prompt-engineering, or multi-agent claims, is there a same-backbone zero-shot or few-shot comparator on the same input, schema, and test split? |
| Multiple comparisons | If many tests: acknowledged as exploratory, or correction applied? |
| Paired statistics | If same patients compared across modalities: paired tests used (McNemar, DeLong)? |
| Effect-size meaningfulness | Scored separately from significance: is each primary effect (OR, HR, beta, Cohen's d, correlation) translated to a real-world unit shift and compared to a minimal clinically important difference? Is significance driven by magnitude rather than sample size? |
| Power-aware null interpretation | Scored separately from significance, for any **non-significant primary result** (p > 0.05, 95% CI crossing the null): is the analysis powered to *exclude* a clinically meaningful effect? An underpowered null is "not yet established," not "no effect" -- if the upper CI bound still includes a meaningful effect size, a flat "X was not associated with Y" claim overreads the data. Look for reported observed power or a minimum detectable effect that justifies a negative conclusion, and watch for **bilateral over-correction** (a prior "independently associated" overclaim swinging to an equally unsupported "not associated" claim during revision). Undocumented null = Minor; a null that drives a clinical recommendation or a headline negative conclusion without power/CI-compatibility justification = Major. |
| Equivalence-margin discipline | A claim that two groups/methods are "equivalent," "non-inferior," "indistinguishable," or show "no difference" requires a **pre-stated margin** — a TOST procedure, or the CI compared against a declared MCID. Grep `indistinguishable\|equivalent\|non-inferior\|no difference` and check for an adjacent `margin\|TOST\|MCID\|non-inferiority`; a margin-free equivalence claim is a Major (it converts a failure to reject into positive evidence of no effect). |
| Interaction-anchor discipline | When synergy / interaction / effect-modification **is** the research question, the null must be anchored to the **interaction parameter** (a likelihood-ratio test of the interaction term, or the interaction OR/HR on one consistent scale), not to a main-effect OR whose upper CI is then read as "no synergy." Grep `synergy\|interaction\|joint effect\|effect modification`; if present, confirm Results carries an `OR_int\|β_int\|LRT\|p_interaction` term. A synergy conclusion resting on a main-effect estimate is a model mis-specification (Major), even when each main effect is individually correct. |
| Difference-in-significance discipline | A between-group claim that an association is "more X / stronger / more pronounced in group A than group B" must rest on a **formal interaction test**, not on group A being significant (p < 0.05) while group B is not (p = NS). The difference between "significant" and "non-significant" is **not** itself significant. Grep `more (clearly\|strongly\|pronounced)\|stronger in\|(only\|chiefly) in (men\|women\|older\|younger\|the [A-Za-z]+ subgroup)` near two stratum-specific estimates with discordant p-values; if no interaction term (`p_interaction\|OR_int\|LRT`) is reported for that contrast, flag it (difference-in-significance fallacy). A subgroup-difference conclusion built this way is a Major; the fix is to report the interaction test or soften to "associations were observed in group A; the interaction was not formally tested." |

## D. Clinical Framing & Importance

| Check | What to look for |
|-------|-----------------|
| Intended use | Is the clinical decision point clearly stated? (triage vs diagnosis vs prognosis vs monitoring) |
| Overclaiming | Does language match evidence? ("will improve" -> "may potentially"; "superior" with overlapping CIs?) |
| Terminology precision | Key terms defined? (e.g., "perioperative" = when exactly?) |
| Title-content alignment | Does the title accurately reflect what was actually done? |
| Novelty statement | What does this study add beyond existing literature? Is this explicitly stated? |
| Substantive novelty differentiation | For AI/LLM extraction papers, does the Introduction name 2-3 close prior papers/systems and state the concrete delta (new task, dataset, workflow, method, validation, or clinical decision point), rather than merely saying the method is novel? |
| Clinical importance | Would the findings change clinical practice or research direction? Is this articulated? |
| Decision impact | Does the manuscript state what decision, workflow step, or downstream action would change if the model is correct? A text-only phenotype that does not alter triage, treatment, surveillance, enrichment, or research operations has weak clinical utility even if accuracy is high. |
| Added value / actionability | Scored separately from novelty: does the finding add value over a measure already in routine use, or is it "real but redundant" (restates a standard test)? At the typical effect size, would a clinician act on it for an individual? |
| Endpoint↔conclusion scope **[CRITICAL]** | Does the conclusion's *action* exceed what the design or endpoint supports? A cross-sectional / single-visit study cannot license a prognostic or surveillance claim (rescreen interval, disease progression); a binary surrogate endpoint (present/absent, >0) is risk stratification, not a care directive (defer/withhold/initiate therapy). Both are documented anti-patterns. |

Run the deterministic scope gate:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_scope_coherence.py" \
  --manuscript manuscript.md --out qc/scope_coherence.json --strict
```

`CROSS_SECTIONAL_PROGNOSTIC` and `SURROGATE_CARE_DIRECTIVE` are Anticipated Major Comments (category: D. Clinical Framing). `CROSS_SECTIONAL_YIELD_LANGUAGE` is an Anticipated **Minor** Comment — a cross-sectional / prevalence design using incidence-flavored screening vocabulary ("yield", "detection rate", "number-needed-to-screen/image", "rescreen interval") without defining "yield" once as cross-sectional report-positive prevalence. The gate is conservative — it fires only when a design/endpoint signal and a conclusion-region action verb (or the yield lexicon) co-occur.

## E. Reproducibility

| Check | What to look for |
|-------|-----------------|
| Preprocessing details | All steps listed in order? Normalization, augmentation, resampling specified? |
| Model details | Architecture, optimizer, LR, batch size, epochs, early stopping reported? |
| Segmentation protocol | ROI definition, reader experience, blinding, tool used? |
| Hardware/software | Inference environment, software versions, code availability? |
| Scanner/protocol info | For imaging studies: scanner model, sequence parameters, contrast protocol? |
| Data/code availability | Is a data availability statement included? Code shared or reason for not sharing stated? |

## F. Reporting Completeness

| Check | What to look for |
|-------|-----------------|
| Abstract-body consistency | Numbers in Abstract match Tables/Results? |
| Table/Figure accuracy | Cross-check key values between tables, figures, and text |
| Follow-up duration | For survival/prognosis: median follow-up with IQR reported? |
| Ethics | All participating institutions' IRB approval documented? Patient consent described? |
| Missing data | Handling of incomplete cases described? |
| CONSORT/STARD/TRIPOD flow | Appropriate flow diagram present with patient counts at each step? |
| Body word count vs journal cap | Is the body within the target journal's word limit? A revise loop monotonically adds words and silently breaches the cap. Run `/sync-submission` `scripts/check_wordcount_cap.py` (`--journal-profile` or `--limit`; the binding number is the rendered DOCX count). Over cap → Major; within 0.95× → Minor (a further pass will likely breach). |
| Funding & COI | Funding sources and competing interests disclosed? |

## G. Reporting Guideline Compliance

Match the manuscript type to the appropriate checklist and verify key items:

| Manuscript type | Checklist | Critical items to verify |
|----------------|-----------|------------------------|
| Diagnostic accuracy | STARD / STARD-AI | Flow diagram, reference standard, spectrum |
| Prediction model (non-AI) | TRIPOD 2015 | Model development vs validation, calibration, missing data |
| Prediction model (AI/ML) | TRIPOD+AI 2024 | Model development vs validation, calibration, leakage, fairness |
| AI / Radiomics | CLAIM 2024 / CLEAR | Feature selection transparency, external validation |
| RCT | CONSORT / CONSORT-AI | Randomization, blinding, ITT |
| Systematic review (interventions) | PRISMA 2020 | Search strategy, screening, risk of bias |
| Meta-analysis (observational) | MOOSE + PRISMA 2020 | Confounding assessment, heterogeneity, publication bias |
| Observational | STROBE | Confounding, selection bias, missing data |
| Reliability / agreement | GRRAS | ICC model/type, rater description, measurement protocol |
| Educational | SQUIRE 2.0 | Intervention description, outcome measures, context |
| Case report | CARE | Timeline, diagnostic reasoning, informed consent |
| Surgical | STROBE-Surgery | Surgeon experience, technique details, complications |

For a full item-by-item audit, run `/check-reporting` on this manuscript. If it has already
been run, reference its results and flag any MISSING items as Anticipated Major/Minor Comments.
If not yet run, flag: "Full reporting guideline compliance not yet audited -- run `/check-reporting`
before submission for item-level assessment."

## H. Circularity

| Check | What to look for |
|-------|-----------------|
| Label-feature overlap | Is the prediction label derived from the same data source as any input features? (e.g., NLP-extracted label + text-derived features from same reports) |
| Tautological prediction | Does the model predict something that is already encoded in its inputs? |
| Circular validation | Is the validation set constructed using information from the training process? |

## I. Protocol Heterogeneity

| Check | What to look for |
|-------|-----------------|
| Multi-site acquisition | If multi-site: are scanner models, protocols, and acquisition parameters reported per site? |
| Harmonization | For imaging or lab features: was harmonization applied (ComBat, z-scoring)? If not, acknowledged? |
| Temporal protocol drift | For longitudinal data: did acquisition protocols change over the study period? |

## J. Method Transparency

| Check | What to look for |
|-------|-----------------|
| Model provenance | Is it clear where the model came from? (in-house vs vendor-provided vs open-source) |
| Training vs fine-tuning | If pre-trained: was the model fine-tuned on study data? If vendor-provided: any access to training data composition? |
| Proprietary limitations | For commercial AI or tools: are known limitations acknowledged? Can results be independently reproduced? |
| Classical-style body conventions | Does the body carry an AI tell or a policy violation a senior reviewer flags on sight — a `§` symbol, an in-body AI-disclosure paragraph, eligibility criteria as prose, mixed OR/HR decimal places, or em-dash overuse? |

Run the deterministic classical-style lint (these are all greps, so they belong in a gate, not eyeballing):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_classical_style.py" \
  --manuscript manuscript.md --out qc/classical_style.json --strict
```

`SECTION_SYMBOL` and `INBODY_AI_DISCLOSURE` are Major (the `§` count must be 0; the AI-disclosure paragraph belongs on the title page for a classical / senior-MA target, not the body). `ELIGIBILITY_PROSE`, `DECIMAL_INCONSISTENCY`, and `EM_DASH_OVERUSE` are Minor. This is the self-review-side mirror of `/write-paper` Step 7.1's classical QC (manuscript-style-classical §5/§6/§7/§8).

## K. Reviewer-team consistency (SR/MA-only; fabrication-grade)

| Check | What to look for |
|-------|-----------------|
| DUAL vs SINGLE conjunction **[CRITICAL]** | Methods or PROSPERO claims dual independent reviewers AND Discussion/Limitations admits single primary reviewer + 20% sample (or "deferred to before submission")? Mark as **MAJOR**, fabrication-grade. |
| LLM-as-reviewer **[CRITICAL]** | A per-study extraction JSON whose `reviewer`/`screener`/`extractor` field is an LLM (Claude, GPT-4, Gemini, "LLM")? An LLM is a tool, not an independent reviewer — listing it as one misrepresents the team. **Fatal**, regardless of the prose. |
| Deferred mitigation | A future-tense mitigation promise — "a 20% sample **will be completed before submission**" — unmet at circulation? The future tense is the tell that the work is not done. **MAJOR**. |

Run the deterministic check at Phase 2 entry (pass the extraction JSON — a file or
a directory of per-study JSONs — so the prose↔JSON↔confession 3-way is covered):

```bash
python "${CLAUDE_SKILL_DIR}/scripts/check_reviewer_team_consistency.py" \
    --manuscript manuscript.md \
    --prospero prospero/record.md \
    --extraction-json extraction/ \
    --out _audit_self/reviewer_team_consistency.md
```

Exit 1 = MAJOR red flag. The JSON sidecar carries `dual_hits`, `single_hits`,
`llm_reviewer_hits`, and `deferred_mitigation_hits`. Any of the DUAL+SINGLE
conjunction, an LLM reviewer field, or a deferred mitigation trips it. Either of
the dual/single claims alone is fine; the conjunction is read by reviewers as
fabrication. Resolution path:
1. Honest Methods/PROSPERO update (single-reviewer execution disclosed), OR
2. Limitations confession rewritten if dual review was actually completed.

## L. Editorial impression & defensiveness (advisory; the counterweight)

This is the **ceiling** category (see "Two Objectives" above) and the inverse of the floor
gates: where A–K and the numerical gates ask "what is missing or wrong?" (and answer by
**adding**), L asks "does the accurate manuscript read confidently, or has it over-defended?"
(and answers by **subtracting**). Every L finding is **advisory (Minor / impression) and
non-blocking** — it never converts to a Major and never blocks submission. The fixes are
REMOVE / MOVE / TIGHTEN, not "add a caveat."

| Check | What to look for | Action |
|-------|-----------------|--------|
| Hedge density | Defensive-caveat tokens stacking up per 1,000 narrative words — the prose hedges faster than it asserts. Keep the load-bearing caveats; cut the reflexive ones. | TIGHTEN |
| Repeated caveat | The same caveat motif ("no deployable claim", "not generalizable", "hypothesis-generating") repeated across body + Abstract. Say it once, firmly. | TIGHTEN |
| Audit minutiae in body | Provenance tokens (SHA / git commit / unit-test / post-lock timeline / manifest / seed=N / audit trail) in the Introduction / Results / Discussion narrative. Reproducibility detail belongs in a Methods statement or a supplement. | MOVE |
| Limitations volume | A Limitations passage that enumerates a long list of discrete items reads as a rebuttal letter; consolidate related items. | TIGHTEN |
| Abstract caveat load | The Abstract carries several caveat clauses, burying the headline result before a reader reaches it. Lead with the result; keep one or two essential qualifiers. | TIGHTEN |
| Buried defense | A strong numeric robustness / sensitivity result sitting only in Limitations or the supplement, with no robustness mention in Results. Promote it into Results — it is *evidence for* the finding, not a caveat against it. (The inverse of the scope-coherence gate, which pushes a *weak* analysis out of Results.) | MOVE |

Run the deterministic gate (Phase 2.5g) rather than eyeballing it — these are all counts and placements:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_editorial_impression.py" \
  --manuscript manuscript.md --out qc/editorial_impression.json
```

`HEDGE_DENSITY`, `HEDGE_REPEAT`, `AUDIT_IN_BODY`, `LIMITATIONS_VOLUME`, `ABSTRACT_CAVEAT_LOAD`,
and `BURIED_DEFENSE` are Anticipated **Minor** Comments (category: L. Editorial impression),
each carrying a REMOVE / MOVE / TIGHTEN `action`. The gate never blocks (it has no Major and
exits 0 even under `--strict`); thresholds are tunable (`--hedge-per-1k`, `--repeat-threshold`,
`--limitations-max`, `--abstract-caveat-max`). It is conservative — each probe fires only on an
explicit, locatable signal.
