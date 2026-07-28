---
name: write-paper
description: Full-pipeline medical/scientific paper writing. 8-phase IMRAD workflow from outline to submission-ready manuscript. Supports original articles, case reports, case series, meta-analyses, AI validation studies, animal studies, and technical notes. Do NOT trigger for self-checking (use self-review instead).
triggers: write paper, manuscript, draft paper, start writing, write methods, write results, write discussion, write introduction
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Write-Paper Skill

You are helping a medical researcher write scientific manuscripts for journal submission.
You orchestrate the full writing pipeline from initial outline through submission-ready
polish, producing publication-quality prose that reads as if written by an experienced
academic physician.

## Key Directories

- **Journal profiles (built-in)**: `${CLAUDE_SKILL_DIR}/references/journal_profiles/`
- **Paper type templates**: `${CLAUDE_SKILL_DIR}/references/paper_types/`
- **Section templates**: `${CLAUDE_SKILL_DIR}/references/section_templates/`
- **Section guides**: `${CLAUDE_SKILL_DIR}/references/section_guides/` (on-demand per phase)
- **Manuscript workspace**: determined at Phase 0 (typically `7_Manuscript/{PaperN}/`)

---

## 8-Phase Pipeline

### Phase 0: Init

Gather essential information from the user before any writing begins.

**Required inputs:**
1. **Title** (working title is fine)
2. **Paper type**: original article, AI validation, case report, case series, meta-analysis, technical note, animal study, NHIS cohort, cross-national
3. **Target journal**: load profile from `${CLAUDE_SKILL_DIR}/references/journal_profiles/`
4. **Research question / hypothesis**
5. **Available data**: what datasets, tables, analyses already exist

**Optional flags:**
- `--no-llm-disclosure`: skip the LLM writing-assistance disclosure. Default is ON.
- `--autonomous`: run Phases 0–7 without user gates (outline approval, T&F plan, discussion planning, section reviews all skipped). Default OFF.

**Actions:**
1. Load the journal profile. If none exists, ask for word limits, abstract format, citation style, figure/table limits, and special requirements.
2. Load the paper-type template from `${CLAUDE_SKILL_DIR}/references/paper_types/`.
3. Select the reporting guideline: diagnostic accuracy → STARD / STARD-AI · prediction model → TRIPOD+AI · radiology AI → CLAIM 2024 · RCT → CONSORT / CONSORT-AI · systematic review → PRISMA 2020 · observational → STROBE · educational → SQUIRE if applicable.
4. **AI/LLM design-stage reporting map** (AI validation, LLM/MLLM, NLP extraction, report generation): map every required AI-reporting item to a manuscript section *before* drafting — model/version/access date, input fields, prompt or fine-tuning protocol, same-backbone zero-shot/few-shot baseline if an adaptation claim is made, test-data independence/contamination, repeatability, and the Methods subsection each will land in. **If any item cannot be placed, halt for design clarification** rather than burying it as a Phase 7 limitation.
5. Create or confirm the project scaffold directory.
6. Record the `--no-llm-disclosure` and `--autonomous` flag states for Phase 1–7 gate logic.
7. **Identify a backbone article** — scan `manuscript/_src/refs.bib` first and propose proactively; ask only as a fallback. Record the chosen citekey in `project.yaml::backbone_article`. The ranking and proposal behaviour are in the reference file. Then gate on its full text — **a backbone whose full text is not extracted is a backbone in name only; the draft would follow an abstract:**

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/gate_backbone_fulltext.py \
     --project project.yaml --refs manuscript/_src/refs.bib \
     --fulltext-dir pdfs/ --strict
   ```

   `BACKBONE_FULLTEXT_MISSING` / `BACKBONE_FULLTEXT_THIN` → **stop and retrieve it** (`/lit-sync` Phase 2.7, then `/fulltext-retrieval` `pdf_to_md.py`). Do not begin Methods drafting until this passes. If the article is genuinely unavailable in full text, record that limitation and get user confirmation before proceeding on the abstract alone.
8. Summarize the setup to the user and confirm before proceeding.

**Output:** setup summary with journal constraints, paper type, reporting guideline, backbone article, directory path, and LLM disclosure status.

#### Phase 0 Gate: Citekey-only references

LLM-generated reference strings inlined during drafting are a primary source of citation
fabrication — in MA projects and solo manuscripts alike. Forcing citekey discipline at Phase 0
redirects that failure mode into a **visible placeholder the submission gate can block**.

1. **Every in-text citation MUST be `[@citekey]`**, with `citekey` present in
   `manuscript/_src/refs.bib`. Pandoc/Quarto style only — no "(Smith et al., 2024)" free text.
2. For a citation intended but not yet imported, use `[@NEW:short-topic]` (kebab-case, ≤30 chars,
   unique in the manuscript).
3. **Never** fabricate a citekey that "looks real" (`[@Smith_2024_AI]`) when the entry is not in
   `refs.bib`. `[@NEW:...]` is the *only* allowed placeholder.
4. All `[@NEW:...]` placeholders must be resolved before Phase 7 (`/search-lit` → `/lit-sync`
   imports verified entries; Better BibTeX refreshes `refs.bib`).
5. Pre-submission check — must return zero matches before `/sync-submission` may freeze a package:

   ```bash
   grep -E '\[@NEW:[^]]+\]|\[N\]|\[N–N\]' manuscript/index.qmd
   ```

   The bare `[N]` / `[N–N]` markers are the failure mode of a manuscript drafted outside this
   pipeline (no `refs.bib`), with method-load-bearing citations left unresolved. Block them
   exactly like `[@NEW:...]`.

If `refs.bib` is absent, create it empty with the comment
`% refs.bib managed by /lit-sync via Zotero Better BibTeX. Do not hand-edit.`, record
`reference_manager.required_for: project_owner` in `SSOT.yaml`, and proceed — early citations
will all be `[@NEW:...]` until the first `/lit-sync` run.

**Read on demand — once the paper type is known (step 2), and only the row that matches:**

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phase0_init_detail.md` → **Case Report Mode** | paper type is `case report` — word/abstract/reference-limit overrides, the CARE 8-section outline, default figures | ~1,500 tokens; a manuscript has one paper type |
| `references/phase0_init_detail.md` → **Case Series Mode** | paper type is `case series` — the methods-light mini-cohort outline, all-cases summary table, counts-not-rates discipline | ~900 tokens |
| `references/phase0_init_detail.md` → **Backbone ranking** | `refs.bib` exists and you are proposing a backbone | ~700 tokens |

---
### Phase 1: Outline

Create a structured IMRAD outline with section-level word budgets that respect journal limits.

**Outline structure:**
```
Title: {working title}
Target: {journal} | Type: {paper type}
Total word limit: {N} (excl. abstract, references, legends)

1. Abstract ({N} words, structured: {format per journal})
2. Introduction ({N} words, {M} paragraphs)
   - P1: Clinical context / background
   - P2: Knowledge gap
   - P3: Study objective / hypothesis
3. Materials and Methods ({N} words)
   - 3.1 Study Design and Setting
   - 3.2 Participants / Dataset
   - 3.3 Procedures / Intervention / Model
   - 3.4 Outcome Measures
   - 3.5 Statistical Analysis
   - 3.6 Ethics
4. Results ({N} words)
   - 4.1 Study population (Table 1)
   - 4.2 Primary endpoint
   - 4.3 Secondary endpoints
   - 4.4 Subgroup / sensitivity analyses
5. Discussion ({N} words, {M} paragraphs)
   - P1: Key findings summary
   - P2-3: Comparison with prior literature
   - P4: Clinical implications
   - P5: Limitations
   - P6: Conclusion
6. Tables: {list with descriptions}
7. Figures: {list with descriptions}
8. Supplemental materials: {if applicable}
```

**Gate:** Present outline to user. Do NOT proceed until user approves or requests changes.
**Autonomous mode:** If `--autonomous` is ON, skip this gate. Log the outline to `qc/_pipeline_log.md` and proceed to Phase 2.

---

### Phase 2: Tables & Figures

Design all tables and figures BEFORE writing prose. This ensures the narrative serves the data, not the reverse.

**Actions:**
1. Review available data with the user.
2. Design each table:
   - Table 1: Demographics / baseline characteristics (always)
   - Table 2+: Primary and secondary outcomes
   - Supplemental tables as needed
3. Design each figure:
   - Figure 1: Study flow diagram (CONSORT/STARD/PRISMA as applicable)
   - Additional figures: performance curves, forest plots, calibration plots, etc.
4. Call `/analyze-stats` if statistical analysis is needed.
5. Call `/make-figures` if figure generation is needed. **Pass `--study-type`** mapped from the paper type / reporting guideline selected in Phase 0: diagnostic accuracy → `diagnostic-accuracy`, prediction model → `ai-validation`, systematic review → `meta-analysis`, DTA systematic review → `dta-meta-analysis`, observational → `observational-cohort`, RCT → `rct`, case report → `case-report`.
6. **Auto-detect required figures.** Based on the reporting guideline selected in Phase 0, consult the `/make-figures` study-type figure set table. Call `/make-figures` with the full figure set for the study type. Do not ask the user to name each figure individually.
7. **Visual abstract check.** If the target journal requires or encourages a visual abstract (check the journal profile for a "Visual Abstract" section), call `/make-figures` with visual abstract request. Provide: title, Key Points 1 and 3, methodology summary, and the best study figure as the visual element.
8. **Figure discovery and embedding.** After figure generation completes, scan the `analysis/figures/` directory for all PNG and PDF files. For each figure:
   - Generate a markdown image reference: `![Figure N. Caption](analysis/figures/filename.png){width=80%}`
   - Draft a figure legend based on the figure type and analysis context
   - Insert the reference at the appropriate location in the Results section
9. **Manifest verification (HALT gate).** After `/make-figures` completes, verify that `analysis/figures/_figure_manifest.md` exists and contains at least one figure entry. If the manifest is missing or empty: in **autonomous mode**, HALT with error code `MANIFEST_MISSING`, log to `qc/_pipeline_log.md`, and write a recovery note to `manuscript/<id>/REPORT.md` Tier-3 section ("rerun /make-figures or manually create _figure_manifest.md"). In **interactive mode**, report the error and ask the user how to proceed. **Rationale**: Phase 7 DOCX build (line 567) parses the manifest to embed figures; a missing manifest silently drops all figures from the final docx, which surfaces only at submission. HALT-on-missing is cheaper than discovering the absence in submission QC.

**Gate:** Present T&F plan to user. Do NOT proceed until user approves.
**Autonomous mode:** If `--autonomous` is ON, skip this gate. Log the T&F plan to `qc/_pipeline_log.md` and proceed to Phase 3.

---

### Phase 3: Methods

Write the Methods section first -- it is the most objective and anchors the rest of the paper.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/methods.md` for PICO structure, backbone article usage, checklist cross-reference, and terminology conventions. For the matching study type, also skim the structure model in `${CLAUDE_SKILL_DIR}/references/exemplar_methods/` (diagnostic-accuracy/STARD, AI-validation/TRIPOD+AI·CLAIM, observational-cohort/STROBE, meta-analysis/PRISMA 2020, RCT/CONSORT 2010) — it lists, paragraph by paragraph, what each Methods paragraph must establish plus the element that type most often omits. Model the structure; the exemplars are synthetic, with placeholder specifics, not prose to copy.

**Writing order within Methods:**
1. Study Design and Setting
2. Participants / Dataset (inclusion/exclusion, recruitment period)
3. Procedures / Intervention / AI Model description
4. Outcome Measures (primary and secondary endpoints)
5. Statistical Analysis (reference `${CLAUDE_SKILL_DIR}/references/section_templates/methods_statistical.md`)
6. Ethics statement
7. AI/LLM disclosure (if `--no-llm-disclosure` was NOT set): insert the Methods disclosure paragraph from the [LLM Disclosure](#llm-writing-disclosure) section

**AI/LLM extraction add-ons (when applicable):**
- In Dataset / Inputs, state exactly which text fields the model received and whether clinical history,
  indication, impression, prior diagnosis, or referral text was masked. If a supplied field can contain
  the target label, Methods must either exclude it or describe a no-leaky-field sensitivity analysis.
- In AI Model or Statistical Analysis, include a same-backbone zero-shot/few-shot comparator when the
  claim is that fine-tuning, LoRA, prompt engineering, or a multi-agent wrapper improves performance.
- In Introduction, state the decision-impact path: what clinical or research workflow step changes if the
  model works, not only that the extracted label is interesting.

**Process:**
1. **Writer pass**: Draft the full Methods section following the outline and paper type template.
2. **Critic pass**: Score using the 6-dimension rubric (see Critic Scoring below). Provide specific line-level feedback.
3. **Fixer pass**: Revise based on critic feedback.
4. Repeat critic-fixer loop up to 3 rounds. Pass threshold: overall score >= 85/100.
5. Present final Methods to user.

---

### Phase 4: Results

Write Results aligned to the approved tables and figures. **Results = "What did we find?"
— nothing more.** Every sentence must be a factual statement backed by a number.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/results.md` for mirror-symmetry rules, flowchart requirements, missing data handling, and the anti-interpretation self-check. For the matching study type, also skim the structure model in `${CLAUDE_SKILL_DIR}/references/exemplar_results/` (diagnostic-accuracy/STARD, AI-validation/TRIPOD+AI·CLAIM, observational-cohort/STROBE, meta-analysis/PRISMA 2020, RCT/CONSORT 2010) — each follows its `exemplar_methods/` sibling in Methods order, listing what each Results paragraph must establish (flow → baseline/prevalence → primary estimate with CIs → calibration/agreement → subgroups → sensitivity; for meta-analysis, PRISMA flow → characteristics+provenance → RoB → pooled estimate with I²/τ²/prediction interval → subgroup interaction → publication bias; for an RCT, CONSORT flow → baseline-by-arm with no p-values → ITT primary with CI → secondary+harms → per-protocol beside ITT) plus the element that type most often omits. Model the structure; the exemplars are synthetic, with placeholder specifics, not prose to copy.

**Rules:**
- Every number in the text must match the corresponding table cell exactly.
- Start with study population description referencing Table 1.
- Present primary endpoint results first, then secondary.
- Reference every table and figure at least once in the text.
- Report exact p-values (not "p < 0.05" unless truly < 0.001).
- All primary metrics must include 95% confidence intervals.
- **Incremental value must be earned, not asserted.** If the paper claims the model/marker adds value *beyond* / *on top of* an existing tool (a clinical score, a routine test, a baseline model), Results must report the nested-model comparison — a baseline model from the in-routine-use predictors versus the augmented model — with an incremental metric: ΔC-index / ΔAUC (paired CI, e.g. DeLong), NRI, IDI, or decision-curve net benefit. A standalone discrimination number does not support a "beyond X" claim. If the design did not include the baseline comparator (see `/design-study` Phase 3), soften the claim to standalone performance rather than implying added value.
- Do not interpret results in this section; state findings only.

**Anti-interpretation guardrails (strict):**
- NO "why" explanations — save for Discussion.
- NO comparisons with prior literature — save for Discussion.
- NO causal language ("caused," "led to," "due to") — use "was associated with."
- NO evaluative adjectives without numbers ("high," "significant," "notable,"
  "remarkable," "surprising") — always pair with the actual value.
- NO hedge words implying interpretation ("suggests," "implies," "indicates importance,"
  "consistent with," "as expected").
- **Self-check heuristic (applied to every sentence):**
  1. Does this sentence explain "why"? → Move to Discussion.
  2. Does it reference another study? → Move to Discussion.
  3. Does it use "suggests/implies/indicates importance"? → Rewrite as factual statement.
  4. Does it use an adjective without a number? → Add the number or delete the adjective.
  5. Does it contain "interestingly/notably/remarkably/surprisingly"? → Delete the word.

**Structure:**
1. Study population (enrollment, exclusions, demographics → Table 1).
2. Primary endpoint results (one paragraph per primary outcome).
3. Secondary endpoint results.
4. Subgroup / sensitivity analyses (if applicable).

**Process:** Same writer -> critic -> fixer loop as Phase 3 (max 3 rounds, threshold 85/100).

**Gate:** Present final Results to user. Confirm before proceeding to Discussion.

---

### Phase 5: Discussion

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/discussion.md` for the 4-paragraph structure, word limits, limitation writing guidelines, and Table/Figure citation rules. For the matching study type, also skim the structure model in `${CLAUDE_SKILL_DIR}/references/exemplar_discussion/` (diagnostic-accuracy/STARD, AI-validation/TRIPOD+AI·CLAIM, observational-cohort/STROBE, meta-analysis/PRISMA 2020, RCT/CONSORT 2010) — completing the exemplar trio, each lists what every Discussion paragraph must establish (key finding → interpretation/comparison → limitations → generalizability → conclusion matched to the evidence) plus the element that type most often omits (spectrum/verification bias; evidence-tier separation and optimism caveats; mandatory causal caution; for meta-analysis, GRADE certainty + heterogeneity source + non-independence/overlap caveat; for an RCT, blinding/attrition limitation + clinical-vs-statistical significance vs the MCID). For case reports, use `${CLAUDE_SKILL_DIR}/references/exemplar_case_report.md` instead: it controls literature-boundary wording, n=1 causal caution, and bedside teaching-point framing. Model the structure; the exemplars are synthetic, introduce no new results, and are not prose to copy.

**Before drafting, collect user input (Discussion Planning Gate).**

#### Step 5a: Discussion Planning (interactive)

Ask the user the following questions (in the user's preferred language). Wait for answers before drafting.

```
Q1. List the 3-5 key findings of this study in order of importance.
Q2. Name 3-5 key prior studies (anchor papers) you want to compare against in the
    Discussion — titles or DOIs.
    - Studies consistent with your results: ?
    - Studies inconsistent with your results: ?
Q3. Are there methodological or population differences that could explain any disagreement?
Q4. State up to 3 limitations of this study.
    (For each, include how it was mitigated and the direction in which it could affect the results.)
Q5. Are there clinical implications you want to emphasize?
```

If the user provides partial answers, proceed with what is available and note gaps.
If the user says "skip" (or the equivalent in their language), use `/search-lit` to identify
anchor papers from the reference list and proceed with best-effort defaults.

**Gate:** Do NOT start writing Discussion until user responds (or explicitly skips).
**Autonomous mode:** If `--autonomous` is ON, skip the interactive planning. Use `/search-lit` to identify anchor papers from the reference list and proceed with best-effort defaults (same as the "skip" path).

#### Step 5b: Discussion Drafting

Write the Discussion using the inverted funnel structure:

**Paragraph structure:**
1. **Summary** (1 paragraph): Restate key findings without repeating numbers verbatim.
   Bridge from Results — the reader should feel continuity.
2. **Context — anchor paper comparisons** (2-3 paragraphs): Each paragraph organized around
   one theme or finding. For each anchor paper:
   - State the prior finding with citation.
   - Compare: agreement or disagreement with our result.
   - Explain the discrepancy (if any) citing methodological or population differences.
3. **Clinical implications** (1 paragraph): What does this mean for practice or future research?
4. **Limitations** (1 paragraph): Honest, specific, ordered by severity. For each limitation:
   (a) what it is, (b) how it was mitigated, (c) direction of residual bias.
   Do NOT use "our study has several limitations" as an opener.
5. **Strengths** (optional, 1-2 sentences): Only if genuinely novel contribution.
6. **Conclusion** (1-2 sentences): Single most important finding + implication.
   Must be a citable statement. No "further studies are needed" as final sentence.

**Rules:**
- Do not introduce new data not presented in Results.
- Avoid overclaiming: language must match evidence level.
- **Endpoint↔conclusion scope.** The Clinical-implications and Conclusion sentences must not exceed what the design and endpoint support. A cross-sectional / single-visit / prevalence study cannot license a prognostic or surveillance claim (a rescreen interval, disease progression, predicting future risk) — that requires longitudinal follow-up. A binary surrogate endpoint (present/absent, >0, dichotomized) is risk stratification, not a patient-care directive (defer/withhold/initiate therapy). `/self-review` §D (`check_scope_coherence.py`) flags `CROSS_SECTIONAL_PROGNOSTIC` / `SURROGATE_CARE_DIRECTIVE`; keep the conclusion verb inside the design's reach.
- Acknowledge alternative explanations for key findings.
- Each comparison with prior work must cite the specific study.
- NO "interestingly," "notably," "it is worth noting" — state the point directly.

**Process:** Same writer -> critic -> fixer loop (max 3 rounds, threshold 85/100).

After the first draft, present to the user with (ask in the user's preferred language):
```
Here is the Discussion draft. Please review:
- Any missing anchor papers or additional comparisons needed?
- Anything you want to change in the interpretation?
- Any clinical implications to emphasize more or soften?
```
Incorporate user feedback before running the critic-fixer loop.

---

### Phase 6: Introduction + Abstract

Write these LAST because they frame the paper and depend on knowing what was actually found.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/introduction.md` for the Gap Storytelling 5-step structure, word/paragraph/reference targets, and common mistakes, and skim the paragraph-by-paragraph structure model in `${CLAUDE_SKILL_DIR}/references/exemplar_introduction.md` (¶1 significance → ¶2 landscape → ¶3 the gap → ¶4 objective, plus the vague-gap and gap↔objective-mismatch failure modes). Also load `${CLAUDE_SKILL_DIR}/references/section_guides/title_abstract.md` for Title 3-type selection, 4-component checklist, Abstract Conclusion-first priority, and Visual Abstract guidance, and skim the structured-abstract structure model in `${CLAUDE_SKILL_DIR}/references/exemplar_abstract.md` (Background/Objective → Methods → Results-with-primary-estimate-+-CI-+-denominator → Conclusion-matched-to-design, plus the estimate-free-Results, over-reaching-Conclusion, and body↔abstract number-mismatch failure modes). For case reports, use `${CLAUDE_SKILL_DIR}/references/exemplar_case_report.md` for the 150-word Introduction / Case Presentation / Conclusion abstract anatomy rather than the IMRAD abstract model. Model the structure; the exemplars are synthetic, with placeholder specifics, not prose to copy.

**Introduction structure (3-4 paragraphs):**
1. Clinical context establishing importance (cite prevalence, burden, current practice).
2. Knowledge gap that this study addresses.
3. Study objective, stated precisely. Include hypothesis if applicable.

**Abstract:**
- Follow the journal's structured format exactly.
- Must be self-contained: a reader should understand the study from abstract alone.
- All numbers must match the main text and tables.
- Final sentence: clinical implication, not "further studies are needed."
- **Lead with the pre-specified primary estimand, not the largest effect.** It is tempting (and a critic/peer-sim pass may even suggest it) to foreground the strongest number to make the Abstract "land harder." Do not let that reframe which result is *primary*: tightening effect-size language is fine, but promoting a secondary, exploratory, or post-hoc estimate to the headline is estimand shopping. The Abstract's primary result must be the registered/protocol primary contrast — the same one Step 7.3b checks. If the primary is null or underpowered, report it as such (see `/self-review` category C, power-aware null) rather than substituting a more favourable secondary estimate.

**Process:** Same writer -> critic -> fixer loop (max 3 rounds, threshold 85/100).

---

### Phase 7: Polish

Final quality pass. **Strict sequential execution — each step MUST complete before the next
begins.** Every HALT stops the pipeline; none is advisory. Rationale, tables and greps:
`${CLAUDE_SKILL_DIR}/references/phase7_polish_detail.md`.

**7.1 — AI Pattern Scan.** Remove AI writing patterns (see AI Pattern Avoidance below), editing
`manuscript/manuscript.md` in place. Then run the deterministic lint — the machine-checkable
subset of the classical-style conventions a senior reviewer flags on sight:
`python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/self-review/scripts/check_classical_style.py" --manuscript manuscript/manuscript.md --strict`.
For an MA / systematic review, or when a senior co-author review is expected, also work the
7-grep checklist in `references/section_guides/step7_1_classical_qc.md`. Pattern 19–21 body
rewrites (§, self-reference, AI-disclosure boilerplate) go to `/humanize`.

> **HALT — AI-disclosure meta-applicability.** An AI/LLM-use disclosure must itself satisfy the
> items the manuscript critiques (FLAIR F1.6, TRIPOD-LLM, MI-CLEAR-LLM): **version**, **access
> channel**, **date range**, **responsible party**, zero `[version]`/`TODO` placeholders. A paper
> cannot fail a framework item it critiques. (Classical target: title page, not the body.)

**7.2 — Reporting Guideline Check.** Call `/check-reporting`. Auto-insert only MISSING items whose
`fixable_by_ai` is true; never invent items needing external facts (IRB / registration numbers).
Log every insertion to `qc/_pipeline_log.md`.

**7.3 — Citation Verification.** The placeholder gate first — **HARD STOP** on any hit of
`grep -nE '\[@NEW:[^]]+\]' manuscript/index.qmd manuscript/manuscript.md`, looping back to
`/search-lit` → `/lit-sync`. Then `/verify-refs`: parse `qc/reference_audit.json` and **stop the
pipeline** if `submission_safe: false`, surfacing every `FABRICATED` / `MISMATCH` and any
`duplicate_findings[]`.

**7.3a / 7.3b / 7.3c — Integrity audits.** Run all three between 7.3 and 7.4; each can HALT and
route to 7.4a. **7.3a** numerical claims (text ↔ Table ↔ extraction CSV + primary-source check; a
direction reversal or a p<0.05↔p≥0.05 crossing is a **P0 blocker**). **7.3b** estimand provenance
(delegates to `/self-review` 2.5f; `PRIMARY_REASSIGNED`, `EVALUE_ARITHMETIC`, `EVALUE_NON_PRIMARY`
= **P0**). **7.3c** reference adequacy (every named method cited — resolve via `/search-lit` →
`/lit-sync` → `/verify-refs --strict`, **never fabricate**). See `phase7_integrity_audits.md`.

**7.4 — Self-Review + Fix Loop.** Call `/self-review --json --fix`: it reviews, applies
`fixable_by_ai` edits, and re-reviews (≤2 iterations), stopping early on `PASS`. Log the score,
verdict, iteration count, and residual issues. **Any surviving `severity: "fatal"` issue routes to
7.4a — do not proceed to 7.5.**

**7.4a — Audit Recovery Branch.** Some findings are structural, not prose: the data, protocol, or
analysis script is wrong, and polishing on top yields a clean manuscript on a broken foundation.
**Inline text fixes are forbidden** — recovery means re-extraction, re-analysis, or
re-registration. Halt 7.5–7.6, log the branch, invoke the routed skill, re-enter at **7.3**.
Loop budget: one cycle. Routing: `references/section_guides/step7_4a_audit_recovery.md`.

**7.5 — Generate Deliverables.** `manuscript/manuscript.md`, `manuscript/title_page.md`,
`qc/reporting_checklist.md`, `qc/self_review.md`, `qc/_pipeline_log.md`. **Do not hand-number
author affiliations** — build and verify with `scripts/build_title_page_affiliations.py --check
title_page.md --strict` (a Nature Portfolio / npj technical-check item).

**7.6 — DOCX Build.** Embed figures from `analysis/figures/_figure_manifest.md`, then render.
Prefer `/manage-refs` (pandoc + citeproc + journal CSL) for any submission with >5 references, and
**never hand-type a References list**.

**7.6a — Cross-Reference QC.** After the build, before the final gate:

```bash
python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/check_xref.py" \
  --md manuscript/manuscript.md --docx manuscript/manuscript_final.docx \
  --out qc/xref_audit.json --strict
```

Catches in-text citations resolving to the **wrong rendered caption** — body prose and build
script each echo their own divergent SSOT, so no internal-consistency check sees it. Any
`MISSING_DOCX`/`MISSING_BODY`/`MISMATCH` → `submission_safe: false`, exit 1, **HALT**. The body
caption is the SSOT — fix the build pipeline, never the reverse.

**7.7 — Final Gate.** Autonomous: log completion; report word count, figure count, self-review
score, reporting-compliance %, FATAL flags. Interactive: present summary, await confirmation.

| File | Read it when | Cost if read blindly |
|---|---|---|
| `references/phase7_polish_detail.md` | you reach the build steps (7.5–7.6a), a HALT fires, or the manuscript has an AI-disclosure paragraph | ~7,300 tokens — a run that stops at a 7.3 blocker never builds a DOCX |
| `references/phase7_integrity_audits.md` | running 7.3a / 7.3b / 7.3c | ~3,000 tokens |
| `references/section_guides/step7_4a_audit_recovery.md` | 7.4 left a fatal finding | ~1,700 tokens; most runs never branch |

---
### Phase 8+ (Optional): Cover Letter Generation

Triggered when the user requests "generate cover letter" or after `/find-journal` recommendation.

This is an optional post-pipeline step. Do NOT generate automatically — only when explicitly requested.

**Required user inputs (MUST ask, never fabricate):**
1. Editor name (if known; otherwise use "Dear Editor")
2. Suggested reviewers (2-3 names with affiliations and email addresses)
3. Excluded reviewers (if any, with brief reason)
4. Any specific points to emphasize for the target journal

**Cover letter structure:**

1. **Salutation**: "Dear [Editor name / Editor],"
2. **Submission statement**: "We submit our manuscript entitled '[Title]' for consideration as [article type] in [Journal Name]."
3. **Novelty statement** (2-3 sentences): What is new and why it matters. Extract from abstract key findings.
4. **Scope fit** (1-2 sentences): Why this journal is appropriate. Reference journal scope from profile if loaded.
5. **Brief methods** (1 sentence): Study design and key numbers.
6. **Ethical compliance**: IRB approval number, author agreement, COI statement, no dual submission.
7. **AI disclosure** (if applicable): Specific AI tools used and human oversight statement.
8. **Suggested reviewers**: Name, affiliation, email, expertise area (2-3 minimum).
9. **Excluded reviewers** (if any): Name and reason.

**Reviewer COI cross-check (mandatory for meta-analyses):**
Cross-check all suggested and excluded reviewers against the included-study author list and their co-authors. Same-institution authors of included studies constitute automatic COI and must be excluded from reviewer suggestions.
10. **Closing**: Corresponding author name and credentials.

**Anti-overclaiming guard:**
Automatically flag and rewrite any of these words in cover letters: "first," "novel," "unprecedented," "groundbreaking," "paradigm-shifting," "revolutionary." Replace with specific factual statements about what the study contributes.

**Word limit:** 300-500 words. Cover letters exceeding 500 words should be trimmed.

---

## LLM-Assisted Writing Principles

When using this skill (or any LLM) for manuscript drafting, follow this 3-step process:

1. **Structure first**: The user (or the skill) outlines the logical flow, key arguments, and paragraph-level plan *before* generating prose. An LLM cannot evaluate its own output without a pre-defined target.
2. **LLM drafts**: Generate prose based on the structured plan.
3. **Critical evaluation**: Review LLM output against the plan. Check for logical gaps, unsupported claims, AI pattern phrases, and deviation from the intended argument. Revise or reject sections that do not meet the standard.

This principle applies at every phase: the outline (Phase 1) is the structure; the writer pass is the LLM draft; the critic-fixer loop is the critical evaluation. The user remains the final arbiter of scientific accuracy and narrative direction.

---

## Critic Scoring Rubric

Each section goes through a critic-fixer loop. The critic scores 6 dimensions (0-20 each, total 0-120 scaled to 0-100).

### Dimensions

| # | Dimension | What the critic checks |
|---|-----------|----------------------|
| 1 | **Accuracy** | Every claim matches data/tables. No fabricated numbers. Effect directions correct. |
| 2 | **Completeness** | All required elements per reporting guideline present. No missing subsections. |
| 3 | **Clarity** | Each sentence parseable on first read. No ambiguous referents. Logical paragraph flow. |
| 4 | **Conciseness** | No filler phrases, redundant sentences, or unnecessary hedging. Within word budget. |
| 5 | **Reporting** | Specific guideline items (STARD/TRIPOD/CLAIM/etc.) addressed in this section. |
| 6 | **Humanness** | No AI writing patterns detected (see list below). Reads like an experienced physician wrote it. |
| 7 | **Section Boundaries** | **Results only:** No interpretation, no "why," no prior literature references, no evaluative adjectives without numbers. **Discussion only:** No new data not in Results, no overclaiming beyond evidence level. Flag any sentence that belongs in the other section. |

> **Note:** Dimensions 1-6 are scored 0-20 each (total 0-120 scaled to 0-100). Dimension 7
> is a **pass/fail gate** applied during Phase 4 (Results) and Phase 5 (Discussion): if any
> sentence violates section boundaries, the critic MUST flag it regardless of overall score.
> The fixer must move or rewrite the flagged sentence before the section can pass.

### Scoring Guide

- **18-20**: Publication-ready. No changes needed.
- **14-17**: Minor revisions. Specific sentences flagged.
- **10-13**: Moderate revisions. Structural or content gaps.
- **0-9**: Major rewrite. Fundamental issues.

### Pass Threshold

- Overall score >= 85/100 to pass.
- No single dimension below 12/20.
- If either condition fails, trigger fixer round.

### Critic Output Format

```
## Critic Report: {Section Name} -- Round {N}

Overall: {score}/100
Accuracy: {}/20 | Completeness: {}/20 | Clarity: {}/20
Conciseness: {}/20 | Reporting: {}/20 | Humanness: {}/20

### Issues (by priority)
1. [Dimension] Line/paragraph reference: {specific issue} -> {suggested fix}
2. ...

### Verdict: {PASS | REVISE}
```

---

## Manuscript Writing Rules

### Prose Quality

- **Full prose only.** NEVER use bullet points or numbered lists in manuscript sections (Methods, Results, Discussion, Introduction). Bullet points are acceptable only in structured abstracts if the journal format requires them.
- **Active voice preferred.** "We analyzed" not "Analysis was performed." Use passive only when the agent is truly irrelevant.
- **Tense conventions:**
  - Methods and Results: past tense ("We enrolled," "The AUC was")
  - Discussion and Introduction: present tense for established facts ("Lung cancer is"), past tense for study-specific findings ("Our results showed")
  - Abstract: matches the section it describes
- **Paragraph structure:** Each paragraph has one main idea. First sentence states the point; subsequent sentences provide evidence or elaboration.
- **Transitions:** Every paragraph connects logically to the next. Use explicit transition phrases sparingly but effectively.

### Data Integrity

- All numbers in text must match the corresponding table cells exactly.
- Report effect sizes with 95% confidence intervals for all primary endpoints.
- Use exact p-values (p = 0.032) rather than thresholds (p < 0.05), except when p < 0.001.
- Percentages must match: if 23 of 150, write "23 (15.3%)" -- verify the math.
- Never round numbers differently between text and tables.

### AI Pattern Avoidance

The manuscript must NOT contain these patterns commonly flagged as AI-generated:

**Forbidden phrases:**
- "In conclusion" (use "In summary" or rephrase)
- "It is worth noting that"
- "It is important to note that"
- "Notably,"
- "Interestingly,"
- "Importantly,"
- "Furthermore," at sentence start (use "In addition," or restructure)
- "Moreover," at sentence start
- "plays a crucial role"
- "a comprehensive analysis"
- "delve into"
- "leverage" (use "use" or "apply")
- "utilize" (use "use")
- "in the realm of"
- "underscores the importance of"
- "sheds light on"
- "paves the way for"
- "a nuanced understanding"
- "the landscape of"
- "a paradigm shift"
- "robust" (unless describing a statistical method)

**Forbidden structural patterns:**
- Three-part list sentences ("X, Y, and Z" repeated across paragraphs)
- Excessive hedging chains ("may potentially be associated with possible")
- Mirror-structure paragraphs (same template repeated with different content)
- Grandstanding opening sentences ("In the rapidly evolving landscape of...")

**Preferred alternatives:**
- Vary sentence structure and length within paragraphs.
- Use specific, concrete language over abstract generalizations.
- Let data speak: "The AUC was 0.92" rather than "The model demonstrated remarkable performance."

### Journal Compliance

- Respect all word limits from the loaded journal profile.
- Follow the journal's structured abstract format exactly.
- Use the journal's citation style (Vancouver numbered for most radiology journals).
- Include all journal-specific required elements (e.g., "Key Points" for AJR, CLAIM checklist for RYAI AI studies).

---

## Skill Interactions

This skill orchestrates other skills at specific phases:

| Phase | Skill called | Purpose |
|-------|-------------|---------|
| 2 | `/analyze-stats` | Statistical analysis for tables |
| 2 | `/make-figures --study-type` | Figure generation with study-type auto-detection |
| 7.1 | (built-in) | AI pattern removal |
| 7.2 | `/check-reporting` | Reporting guideline compliance + auto-fix MISSING items |
| 7.3 | `/verify-refs` | Citation verification and reference artifact audit |
| 7.4 | `/self-review --json` | Self-review with auto-fix loop (max 2 iterations) |
| 7.4a | `/meta-analysis` Phase 10 (MA manuscripts) | Audit recovery branch — rebuild extraction/analysis/figures/body when self-review surfaces structural data or protocol issues |
| 7.5 | `/humanize` | AI-pattern density sweep (<2.0 / 1000 words) |
| 7.5a | `/academic-aio` (optional, off by default) | AI-search-engine and RAG visibility checklist — run after humanize so QC-confirmed claims and human-readable text anchor the PASS/PARTIAL/FAIL report. Opt-in via `--aio` or when preparing preprint / GitHub README / CITATION.cff / HF card alongside submission. Silent pipeline execution is explicitly prohibited by the skill's Communication Rules. |
| 7.6 | `/manage-refs` (pandoc citeproc / Zotero CWYW) | DOCX build from manuscript/manuscript.md + analysis/figures + analysis/tables. Bibliography rendering delegated to `/manage-refs scripts/render_pandoc.sh` since 2026-05-01. |
| 7.6a | `/manage-refs scripts/check_xref.py --strict` | Cross-reference QC: in-text Table/Figure citations ↔ body captions ↔ rendered DOCX captions (3-way matrix). Submission gate. |
| 8+ | `/find-journal` | Journal scope for cover letter (optional) |

If a called skill is not available, perform that step inline using the relevant section of this skill document as guidance.

---

## LLM Writing Disclosure

When LLM disclosure is enabled (default), the skill generates transparency statements
compliant with ICMJE 2025 and COPE guidelines. The user can disable this with `--no-llm-disclosure`.

### Why Default ON

Major journals (Nature, Lancet, Radiology, JAMA) and the ICMJE (2025 update) require
disclosure of AI writing assistance. Omitting disclosure risks rejection or retraction.
The default-on design protects the user; they can opt out for journals with no such policy
or when LLM assistance was minimal.

### Disclosure Locations (3 places)

#### 1. Methods Section — Last Paragraph

Insert at the end of the Methods section, after the ethics statement:

**Template (adapt to specifics):**
```
[AI-Assisted Writing Disclosure]
An artificial intelligence language model (Claude, Anthropic) was used to assist with
manuscript drafting, including structuring sections, refining prose, and verifying
internal consistency of reported statistics. All content was critically reviewed,
verified against source data, and approved by all authors. The AI tool was not involved
in study design, data collection, data analysis, or interpretation of results.
```

**Customization rules:**
- Replace "Claude, Anthropic" with the actual tool(s) used.
- List specific tasks the LLM performed (drafting, editing, literature search, statistical code).
- If the LLM was also used for data analysis (e.g., statistical code generation via
  `/analyze-stats`), state this explicitly: "was also used to generate statistical
  analysis code, which was reviewed and validated by [statistician/author]."
- Keep to 2-3 sentences. Do not over-explain.

#### 2. Acknowledgments Section

**Template:**
```
The authors acknowledge the use of [Claude/tool name] ([Anthropic/developer]) for
writing assistance in preparing this manuscript. The authors retain full responsibility
for the content.
```

#### 3. Cover Letter — AI Disclosure Paragraph (Phase 8+)

**Template:**
```
In accordance with [Journal Name]'s policy on AI-assisted writing, we disclose that
[Claude/tool name] was used to assist with manuscript preparation, specifically
[list tasks: drafting, language editing, statistical code review]. All authors have
reviewed and take responsibility for the final content. The AI tool was not listed
as an author and did not contribute to study conception, design, or data interpretation.
```

### What NOT to Disclose

- Do not disclose routine use of grammar checkers (Grammarly, Word spell-check) — these
  are not considered generative AI under current ICMJE guidance.
- Do not disclose use of reference managers (Zotero, EndNote) or statistical software
  (R, Python) unless the LLM generated the analysis code.

### Journal-Specific Overrides

When a journal profile is loaded in Phase 0, check for the `## AI Writing Disclosure Policy`
section in the profile. Tier 1 profiles now include structured fields:
- **Requirement level** (Required / Recommended / Not specified)
- **Permitted scope** (All tasks / Language editing only / Not permitted)
- **Disclosure location** (Methods / Acknowledgments / Cover letter / Submission form)
- **AI-generated images** (Allowed / Banned / Not specified)
- **Policy URL**

Use these fields to adjust disclosure language automatically. Key known policies:
- **Radiology/RSNA**: Required; language editing only; Methods + Acknowledgments; AI images banned.
- **RYAI/RSNA**: Required; language editing only; Methods + Acknowledgments; AI images banned.
- **JAMA/AMA**: Required; language editing only; Methods + Cover letter.
- **Lancet**: Required; language editing only ("readability and language"); Acknowledgments + prompts disclosed.
- **BMJ**: Required; all tasks permitted but must disclose; Methods + Acknowledgments; applies to text, images, data, diagrams.
- **Nature/Springer Nature**: Required; language editing only; Methods; AI images banned.
- **Science/AAAS**: Most restrictive. LLM use limited; treated as potential misconduct if undisclosed.

If the loaded journal profile has no AI Writing Disclosure Policy section, fall back to
ICMJE 2025 defaults (disclose in Methods + Acknowledgments, language editing scope).

---

## Error Handling

- If the user provides incomplete data for a table, flag specific missing values rather than inventing data.
- If word count exceeds the journal limit after a section draft, report the overage and suggest specific cuts.
- If the critic-fixer loop reaches 3 rounds without passing, present the best version to the user with the remaining issues listed, and ask for guidance.
- Never fabricate references. If a citation is needed, describe the type of reference needed and ask the user to provide it, or call `/search-lit` to find a real one.

## Resumption

If the user returns to a partially completed manuscript:
1. Check the workspace directory for existing drafts.
2. Identify which phase was last completed.
3. Summarize progress and ask the user where to resume.

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.

---

## Gates

Severity levels: **ENFORCED** = pipeline halts on failure (cannot proceed to next phase). **ADVISORY** = warning logged, user may override. **OPT-IN** = runs only when explicitly invoked.

| Phase | Gate | Severity | Trigger | Action on fail |
|---|---|---|---|---|
| 0 | Backbone-article auto-proposal (Phase 0 "Identify a backbone article" action) | ADVISORY | refs.bib has methodologically similar candidate | Surface to user; user accepts/declines |
| 7.0 | Citekey resolution (delegate `/manage-refs scripts/check_citation_keys.py`) | ENFORCED | UNDEFINED keys present | Halt; resolve via `/lit-sync` then re-run |
| 7.0 | NEW_PLACEHOLDER drain (delegate `/manage-refs`) | ENFORCED at 7.6 entry | `[@NEW:topic]` markers remain | Resolve each before DOCX render |
| 7.1 | Classical-style QC (manuscript-style-classical 11 items) | ENFORCED | § symbol > 0 OR AI Disclosure paragraph in body OR em-dash > 25 | Auto-fix or HALT for senior MA reviewer prep |
| 7.2 | Reporting guideline compliance (`/check-reporting`) | ENFORCED at submission | <100% mandatory items present | Auto-fix MISSING; ADVISORY for partial |
| 7.3 | Reference audit (`/verify-refs --strict`) | ENFORCED | FABRICATED or HIGH_MISMATCH_FIRST_AUTHOR > 0 | Halt; fix in Zotero, re-render refs.bib via `/lit-sync` |
| 7.4 | Self-review fix loop (`/self-review --json --fix`) | ENFORCED | score below threshold after 2 iterations | Route to Step 7.4a Audit Recovery |
| 7.4a | Audit Recovery branch (route to `/meta-analysis` Phase 10 for MA manuscripts) | ENFORCED in `--e2e` | self-review surfaced structural data issue | HALT with `RECOVERY_HALT_HUMAN_DECISION` if recovery validation fails twice |
| 7.5 | Humanize density (`/humanize`) | ADVISORY | AI patterns > 2.0 / 1000 words | Sweep + flag remaining; user reviews |
| 7.5a | AIO checklist (`/academic-aio --aio`) | OPT-IN | user supplies `--aio` flag | PASS/PARTIAL/FAIL report; never auto-applies |
| 7.6 | DOCX build (delegate `/manage-refs scripts/render_pandoc.sh`) | ENFORCED | render exits non-zero | Halt; report stderr to user |
| 7.6a | Cross-reference QC (delegate `/manage-refs scripts/check_xref.py --strict`) | ENFORCED — submission gate | MISSING_DOCX / MISSING_BODY / MISMATCH > 0 | Halt; route fixes per `references/phase7_polish_detail.md` |
| 7.7 | Final submission gate | ENFORCED | any of 7.0–7.6a above failed | Refuse to mark `submission_safe: true` |
| 8+ | Cover letter generation | OPT-IN | user invokes `--cover-letter` | Renders against journal profile |

Cross-cutting global rules applied during 7.x QC:
- `manuscript-style-classical.md` (11 items, Phase 7.1 — ENFORCED)
- `manuscript-references.md` (hand-typed References list — ENFORCED via Phase 7.6 delegation)
- `numerical-safety.md`, `data-integrity.md`, `citation-safety.md` (Phase 7.3 + 7.6a — ENFORCED)
- `senior-mentor-circulation.md` (post-7.7, when round 1 begins — ADVISORY)
- `ai-drafted-document-policy.md` (Phase 0 if AI-draft attached — ENFORCED)
