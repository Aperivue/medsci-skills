---
name: write-paper
description: Use when drafting a medical research manuscript or any IMRAD section. Runs an 8-phase pipeline from outline to submission-ready draft for original articles, AI validation studies, case reports, meta-analyses, technical notes and more. Checking a draft is /self-review.
metadata:
  triggers: "write paper, manuscript, draft paper, start writing, write methods, write results, write discussion, write introduction"
---

# Write-Paper Skill

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
7. **Identify a backbone article** — scan `manuscript/_src/refs.bib` first and propose proactively (ranking: Backbone ranking below); ask only as a fallback. Record the chosen citekey in `project.yaml::backbone_article`. Then gate on its full text — **a backbone whose full text is not extracted is a backbone in name only; the draft would follow an abstract:**

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/gate_backbone_fulltext.py \
     --project project.yaml --refs manuscript/_src/refs.bib \
     --fulltext-dir pdfs/ --strict
   ```

   A file in `--fulltext-dir` counts as the backbone when it is named `<citekey>.md` or names the backbone DOI/citekey *before* its References heading; a paper that only cites the backbone in its reference list does not count. Known limit: another paper that names the DOI in its own body still resolves — name the file `<citekey>.md` or pass `--fulltext` to remove the doubt.

   `BACKBONE_FULLTEXT_MISSING` / `BACKBONE_FULLTEXT_THIN` → **stop and retrieve it** (`/lit-sync` Phase 2.7, then `/fulltext-retrieval` `pdf_to_md.py`). Do not begin Methods drafting until this passes. If the article is genuinely unavailable in full text, record that limitation and get user confirmation before proceeding on the abstract alone.
8. Summarize the setup — journal constraints, paper type, reporting guideline, backbone article, directory path, LLM-disclosure status — and confirm before proceeding.

#### Phase 0 Gate: Citekey-only references

Citekey discipline turns citation fabrication into a **visible placeholder the submission gate can block**.

1. **Every in-text citation MUST be `[@citekey]`**, with `citekey` present in
   `manuscript/_src/refs.bib`. Pandoc/Quarto style only — no "(Smith et al., 2024)" free text.
2. For a citation intended but not yet imported, use `[@NEW:short-topic]` (kebab-case, ≤30 chars,
   unique in the manuscript).
3. **Never** fabricate a citekey that "looks real" (`[@Smith_2024_AI]`) when the entry is not in
   `refs.bib`. `[@NEW:...]` is the *only* allowed placeholder.
4. All `[@NEW:...]` placeholders must be resolved before Phase 7 (`/search-lit` → `/lit-sync`
   imports verified entries; Better BibTeX refreshes `refs.bib`). Cite only references whose DOI or
   PMID `/search-lit` has confirmed; mark any other as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
5. Pre-submission check — must return zero matches before `/sync-submission` may freeze a package:

   ```bash
   grep -E '\[@NEW:[^]]+\]|\[N\]|\[N–N\]' manuscript/index.qmd
   ```

   Bare `[N]` / `[N–N]` markers mean a manuscript drafted outside this pipeline (no `refs.bib`)
   with method-load-bearing citations left unresolved. Block them exactly like `[@NEW:...]`.

If `refs.bib` is absent, create it empty with the comment
`% refs.bib managed by /lit-sync via Zotero Better BibTeX. Do not hand-edit.`, record
`reference_manager.required_for: project_owner` in `SSOT.yaml`, and proceed — early citations
will all be `[@NEW:...]` until the first `/lit-sync` run.

**Read on demand — once the paper type is known (step 2), and only the row that matches:**

| File | Read it when |
|---|---|
| `references/phase0_init_detail.md` → **Case Report Mode** | paper type is `case report` — word/abstract/reference-limit overrides, the CARE 8-section outline, default figures |
| `references/phase0_init_detail.md` → **Case Series Mode** | paper type is `case series` — the methods-light mini-cohort outline, all-cases summary table, counts-not-rates discipline |
| `references/phase0_init_detail.md` → **Backbone ranking** | `refs.bib` exists and you are proposing a backbone |

---
### Phase 1: Outline

Build the outline on the paper-type template's section structure. Start with a header — working
title, target journal, paper type, total word limit (excluding abstract, references and legends) —
then give every section a word budget and a paragraph- or subsection-level plan, with the budgets
summing within the journal limits. End with the planned tables, figures and supplemental
materials, one line each.

**Gate:** Present the outline to the user. Do NOT proceed until the user approves or requests changes.
**Autonomous mode:** skip this gate; log the outline to `qc/_pipeline_log.md` and proceed to Phase 2.

---

### Phase 2: Tables & Figures

Design all tables and figures BEFORE writing prose, so the narrative serves the data.

1. Review available data with the user. Plan Table 1 (demographics / baseline characteristics — always), Table 2+ (primary and secondary outcomes) and supplemental tables; Figure 1 is the study flow diagram (CONSORT/STARD/PRISMA as applicable), followed by performance curves, forest plots, calibration plots, etc.
2. Call `/analyze-stats` if statistical analysis is needed.
3. Call `/make-figures` with the full figure set the study type requires — do not ask the user to name each figure. **Pass `--study-type`** mapped from the Phase 0 paper type / reporting guideline: diagnostic accuracy → `diagnostic-accuracy`, prediction model → `ai-validation`, systematic review → `meta-analysis`, DTA systematic review → `dta-meta-analysis`, observational → `observational-cohort`, RCT → `rct`, case report → `case-report`.
4. **Visual abstract.** If the journal profile's "Visual Abstract" section requires or encourages one, call `/make-figures` with a visual abstract request: title, Key Points 1 and 3, methodology summary, and the best study figure as the visual element.
5. **Figure embedding.** Scan `analysis/figures/` for every PNG and PDF. For each, insert `![Figure N. Caption](analysis/figures/filename.png){width=80%}` at the appropriate place in Results and draft its legend from the figure type and analysis context.
6. **Manifest verification (HALT gate).** `analysis/figures/_figure_manifest.md` must exist with at least one figure entry — the Phase 7 DOCX build embeds figures from it, and a missing manifest silently drops every figure. If it is missing or empty: in **autonomous mode**, HALT with error code `MANIFEST_MISSING`, log to `qc/_pipeline_log.md`, and write a recovery note to `manuscript/<id>/REPORT.md` Tier-3 section ("rerun /make-figures or manually create _figure_manifest.md"); in **interactive mode**, report the error and ask the user how to proceed.

**Gate:** Present T&F plan to user. Do NOT proceed until user approves.
**Autonomous mode:** skip this gate; log the T&F plan to `qc/_pipeline_log.md` and proceed to Phase 3.

---

### Phase 3: Methods

Write Methods first — it is the most objective section and anchors the rest of the paper.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/methods.md` and skim the matching study type in `${CLAUDE_SKILL_DIR}/references/exemplar_methods/` (diagnostic-accuracy/STARD, AI-validation/TRIPOD+AI·CLAIM, observational-cohort/STROBE, meta-analysis/PRISMA 2020, RCT/CONSORT 2010): what each paragraph must establish, plus the element that type most often omits. Every exemplar used in Phases 3–6 is synthetic, with placeholder specifics — model its structure; it is not prose to copy.

**Writing order:** (1) Study Design and Setting; (2) Participants / Dataset (inclusion/exclusion, recruitment period); (3) Procedures / Intervention / AI Model description; (4) Outcome Measures (primary and secondary endpoints); (5) Statistical Analysis (`${CLAUDE_SKILL_DIR}/references/section_templates/methods_statistical.md`); (6) Ethics statement; (7) AI/LLM disclosure (unless `--no-llm-disclosure`): when the target journal wants it in Methods, add the Methods paragraph from [LLM Writing Disclosure](#llm-writing-disclosure).

**AI/LLM extraction add-ons (when applicable):**
- In Dataset / Inputs, state exactly which text fields the model received and whether clinical history,
  indication, impression, prior diagnosis, or referral text was masked. If a supplied field can contain
  the target label, Methods must either exclude it or describe a no-leaky-field sensitivity analysis.
- In AI Model or Statistical Analysis, include a same-backbone zero-shot/few-shot comparator when the
  claim is that fine-tuning, LoRA, prompt engineering, or a multi-agent wrapper improves performance.

**Process:** Run the critic-fixer loop ([Critic Review Criteria](#critic-review-criteria)), then present the final Methods to the user.

---

### Phase 4: Results

Write Results aligned to the approved tables and figures. **Results = "What did we find?"
— nothing more.** Every sentence must be a factual statement backed by a number.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/results.md` (mirror symmetry with Methods, flowchart, missing data, the anti-interpretation self-check) and skim the matching study type in `${CLAUDE_SKILL_DIR}/references/exemplar_results/` (the same five types, each in its Methods sibling's order).

**Rules:**
- Order: study population (enrollment, exclusions, demographics → Table 1); primary endpoint results (one paragraph per primary outcome); secondary endpoints; subgroup / sensitivity analyses.
- Apply the results.md self-check to every sentence: no "why", no prior literature, no causal language ("caused," "led to," "due to" — use "was associated with"), no interpretive hedges ("suggests," "implies," "consistent with," "as expected"), no evaluative adjective without its number.
- **Incremental value must be earned, not asserted.** If the paper claims the model/marker adds value *beyond* / *on top of* an existing tool (a clinical score, a routine test, a baseline model), Results must report the nested-model comparison — a baseline model from the in-routine-use predictors versus the augmented model — with an incremental metric: ΔC-index / ΔAUC (paired CI, e.g. DeLong), NRI, IDI, or decision-curve net benefit. A standalone discrimination number does not support a "beyond X" claim. If the design did not include the baseline comparator (see `/design-study` Phase 3), soften the claim to standalone performance rather than implying added value.

**Process:** critic-fixer loop. **Gate:** Present final Results to user. Confirm before proceeding to Discussion.

---

### Phase 5: Discussion

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/discussion.md` and skim the matching study type in `${CLAUDE_SKILL_DIR}/references/exemplar_discussion/` (the same five types, each naming the element that type most often omits). For case reports, use `${CLAUDE_SKILL_DIR}/references/exemplar_case_report.md` instead (literature-boundary wording, n=1 causal caution, bedside teaching points).

#### Step 5a: Discussion Planning (interactive)

Ask the user the following questions. Wait for answers before drafting.

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
If the user says "skip", use `/search-lit` to identify anchor papers from the reference list and
proceed with best-effort defaults.

**Gate:** Do NOT start writing Discussion until user responds (or explicitly skips).
**Autonomous mode:** skip the interactive planning and take the "skip" path.

#### Step 5b: Discussion Drafting

Write an inverted funnel:
1. **Summary** (1 paragraph): restate key findings without repeating numbers verbatim, bridging from Results.
2. **Anchor-paper comparisons** (2-3 paragraphs, one theme or finding each): for each anchor paper, state the prior finding with citation, say whether our result agrees, and explain any discrepancy by methodological or population differences.
3. **Clinical implications** (1 paragraph): what this means for practice or future research.
4. **Limitations** (1 paragraph, ordered by severity): for each, (a) what it is, (b) how it was mitigated, (c) direction of residual bias. Do NOT open with "our study has several limitations".
5. **Strengths** (optional, 1-2 sentences): only for a genuinely novel contribution.
6. **Conclusion** (1-2 sentences): the single most important finding and its implication, as a citable statement. No "further studies are needed" as final sentence.

**Rules:**
- Do not introduce data not presented in Results; match language to the evidence level; acknowledge alternative explanations for key findings.
- **Endpoint↔conclusion scope.** The Clinical-implications and Conclusion sentences must not exceed what the design and endpoint support. A cross-sectional / single-visit / prevalence study cannot license a prognostic or surveillance claim (a rescreen interval, disease progression, predicting future risk) — that requires longitudinal follow-up. A binary surrogate endpoint (present/absent, >0, dichotomized) is risk stratification, not a patient-care directive (defer/withhold/initiate therapy). `/self-review` §D (`check_scope_coherence.py`) flags `CROSS_SECTIONAL_PROGNOSTIC` / `SURROGATE_CARE_DIRECTIVE`; keep the conclusion verb inside the design's reach.

After the first draft, ask the user: any missing anchor papers or comparisons, any change to the
interpretation, and which clinical implications to emphasize or soften. Incorporate the feedback,
then run the critic-fixer loop.

---

### Phase 6: Introduction + Abstract

Write these LAST because they frame the paper and depend on knowing what was actually found.

**Before writing:** Load `${CLAUDE_SKILL_DIR}/references/section_guides/introduction.md` and `${CLAUDE_SKILL_DIR}/references/section_guides/title_abstract.md`, and skim the structure models `${CLAUDE_SKILL_DIR}/references/exemplar_introduction.md` and `${CLAUDE_SKILL_DIR}/references/exemplar_abstract.md`. For case reports, use `${CLAUDE_SKILL_DIR}/references/exemplar_case_report.md` for the 150-word Introduction / Case Presentation / Conclusion abstract anatomy rather than the IMRAD abstract model.

**Introduction (3-4 paragraphs):** clinical context establishing importance (prevalence, burden, current practice) → the knowledge gap this study addresses → the study objective, stated precisely, with the hypothesis if applicable. For AI/LLM extraction studies, state the decision-impact path: what clinical or research workflow step changes if the model works, not only that the extracted label is interesting.

**Abstract:** self-contained; all numbers match the main text and tables; the final sentence is a clinical implication, not "further studies are needed."
**Lead with the pre-specified primary estimand, not the largest effect** — even when a critic or peer-sim pass suggests foregrounding the strongest number. Tightening effect-size language is fine; promoting a secondary, exploratory, or post-hoc estimate to the headline is estimand shopping. The Abstract's primary result must be the registered/protocol primary contrast — the same one Step 7.3b checks. If the primary is null or underpowered, report it as such (see `/self-review` category C, power-aware null) rather than substituting a more favourable secondary estimate.

**Process:** critic-fixer loop.

---

### Phase 7: Polish

Final quality pass. **Strict sequential execution — each step MUST complete before the next
begins.** Every HALT stops the pipeline; none is advisory.

**7.1 — AI Pattern Scan.** Remove AI writing patterns (see AI Pattern Avoidance below), editing
`manuscript/manuscript.md` in place. Then run the deterministic classical-style lint:
`python3 "${CLAUDE_SKILL_DIR}/../self-review/scripts/check_classical_style.py" --manuscript manuscript/manuscript.md --strict`.
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

**7.4a — Audit Recovery Branch.** When a finding is structural — the data, protocol, or analysis
script is wrong — polishing yields a clean manuscript on a broken foundation.
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
python3 "${CLAUDE_SKILL_DIR}/../manage-refs/scripts/check_xref.py" \
  --md manuscript/manuscript.md --docx manuscript/manuscript_final.docx \
  --out qc/xref_audit.json --strict
```

It catches in-text citations resolving to the **wrong rendered caption**. Any
`MISSING_DOCX`/`MISSING_BODY`/`MISMATCH` → `submission_safe: false`, exit 1, **HALT**. The body
caption is the SSOT — fix the build pipeline, never the reverse.

**7.7 — Final Gate.** Autonomous: log completion; report word count, figure count, self-review
score, reporting-compliance %, FATAL flags. Interactive: present summary, await confirmation.

| File | Read it when |
|---|---|
| `references/phase7_polish_detail.md` | you reach the build steps (7.5–7.6a), a HALT fires, or the manuscript has an AI-disclosure paragraph |
| `references/phase7_integrity_audits.md` | running 7.3a / 7.3b / 7.3c |
| `references/section_guides/step7_4a_audit_recovery.md` | 7.4 left a fatal finding |

---
### Phase 8+ (Optional): Cover Letter Generation

Only when the user explicitly asks for a cover letter (for example after `/find-journal` picks a
target) — never automatically. Read `${CLAUDE_SKILL_DIR}/references/phase8_cover_letter.md` for
the inputs you must ask for, the letter structure, the reviewer-COI cross-check (mandatory for
meta-analyses), and the overclaiming guard.

---

## Critic Review Criteria

Phases 3–6 each run writer → critic → fixer: draft the section, have the critic review it with
line-level feedback, revise, and repeat for up to 3 rounds. After 3 rounds without a pass, present
the best version to the user with the remaining issues listed, and ask for guidance.

The critic reviews six dimensions, with line-level feedback: **Accuracy** (every
claim matches data/tables; effect directions correct), **Completeness** (all reporting-guideline
elements and subsections present), **Clarity** (parseable on first read; no ambiguous referents),
**Conciseness** (no filler or redundant hedging; within word budget), **Reporting** (this
section's STARD/TRIPOD/CLAIM/etc. items addressed), **Humanness** (no AI Pattern Avoidance hits).
The section passes when no dimension carries an issue a journal reviewer would raise; otherwise
run a fixer round.

**Section boundaries (pass/fail, Phases 4 and 5):** in Results, no interpretation, no "why," no
prior-literature references, no evaluative adjectives without numbers; in Discussion, no data
absent from Results and no overclaiming beyond the evidence level. The critic MUST flag every
violating sentence, and the section cannot pass until the fixer moves or rewrites it.

Report each round as `## Critic Report: {Section} -- Round {N}` with the issues by priority as
`[Dimension] location: issue -> suggested fix`, and `Verdict: PASS | REVISE`.

---

## Manuscript Writing Rules

- **Full prose only.** NEVER use bullet points or numbered lists in manuscript sections (Methods, Results, Discussion, Introduction). Bullet points are acceptable only in structured abstracts if the journal format requires them.
- **Voice and tense.** Active voice preferred ("We analyzed" not "Analysis was performed"); passive only when the agent is truly irrelevant. Methods and Results: past tense. Discussion and Introduction: present tense for established facts, past tense for study-specific findings. Abstract: matches the section it describes.
- **Numbers.** All numbers in text must match the corresponding table cells exactly, never rounded differently. Percentages must match: if 23 of 150, write "23 (15.3%)" -- verify the math. Report effect sizes with 95% confidence intervals for all primary endpoints. Use exact p-values (p = 0.032) rather than thresholds (p < 0.05), except when p < 0.001.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Journal compliance.** Respect the loaded journal profile's word limits (if a section draft exceeds one, report the overage and suggest specific cuts) and structured-abstract format exactly, and include the journal-specific required elements (e.g., "Key Points" for AJR, CLAIM checklist for RYAI AI studies).

### AI Pattern Avoidance

The manuscript must NOT contain these patterns commonly flagged as AI-generated:

**Forbidden phrases:** "In conclusion" (use "In summary" or rephrase) · "It is worth noting that" ·
"It is important to note that" · "Notably," · "Interestingly," · "Importantly," · "Furthermore,"
or "Moreover," at sentence start (use "In addition," or restructure) · "plays a crucial role" ·
"a comprehensive analysis" · "delve into" · "leverage" (use "use" or "apply") · "utilize" (use
"use") · "in the realm of" · "underscores the importance of" · "sheds light on" · "paves the way
for" · "a nuanced understanding" · "the landscape of" · "a paradigm shift" · "robust" (unless
describing a statistical method).

**Forbidden structural patterns:** three-part list sentences ("X, Y, and Z" repeated across
paragraphs); excessive hedging chains ("may potentially be associated with possible");
mirror-structure paragraphs (same template repeated with different content); grandstanding
opening sentences ("In the rapidly evolving landscape of...").

**Instead:** vary sentence structure and length, prefer specific concrete language, and let data
speak: "The AUC was 0.92" rather than "The model demonstrated remarkable performance."

## Resumption

If the user returns to a partially completed manuscript, check the workspace for existing drafts,
identify the last completed phase, summarize progress, and ask the user where to resume.

---

## LLM Writing Disclosure

When enabled (default), the skill generates transparency statements that follow the ICMJE
Recommendations and COPE. It is ON by default because the ICMJE and major journals require
disclosure of AI writing assistance and omitting it risks rejection or retraction;
`--no-llm-disclosure` turns it off for journals with no such policy or when LLM assistance was minimal.

### Disclosure Locations

Where the disclosure goes is a fact about the target journal, and journals disagree: some want
it in Methods, some in Acknowledgments, some only in the cover letter, title page or submission
form. Take the location from the loaded journal profile (**Journal-Specific Overrides** below)
and use only the templates for the places that journal asks for. With no target journal
recorded, fall back to ICMJE — Acknowledgments for writing assistance, Methods for use in data
collection, analysis or figures, and the cover letter for either — and treat the placement as
unconfirmed: the Phase 7.1 check (`check_classical_style.py`, `INBODY_AI_DISCLOSURE`) reports
it as a Minor item until a target is set, and as Major if the target does not accept a body
disclosure.

The statements about what the authors did (reviewed, verified, approved; what the tool was not
used for) are the authors' to make. Draft them inside a `[TODO authors confirm: …]` marker and
leave the marker for the authors to resolve — `check_placeholders.py` blocks submission while a
`TODO`, an unfilled token from these templates (`[tool]`, `[version]`, `[developer]`,
`[Claude/tool name]`, `[Journal Name]`, `[statistician/author]`, `{version}` …), or any
`[VERIFY…]` / `[UNVERIFIED - NEEDS MANUAL CHECK]` marker remains.

#### 1. Methods Section — Last Paragraph

When the target journal wants it in Methods, place it at the end of the Methods section, after
the ethics statement:

**Template (adapt to specifics):**
```
[AI-Assisted Writing Disclosure]
An artificial intelligence language model ([tool] [version], [developer]) was used to assist
with [tasks actually performed, e.g. structuring sections, refining prose, checking the
internal consistency of reported statistics]. [TODO authors confirm: All content was
critically reviewed, verified against source data, and approved by all authors. The tool was
not involved in study design, data collection, data analysis, or interpretation of results.]
```

**Customization rules:**
- Replace `[tool] [version], [developer]` with the actual tool(s) used.
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
[tool] [version] was used to assist with manuscript preparation, specifically
[list tasks: drafting, language editing, statistical code review]. [TODO authors confirm:
All authors have reviewed and take responsibility for the final content. The AI tool was
not listed as an author and did not contribute to study conception, design, or data
interpretation.]
```

### What NOT to Disclose

- Do not disclose routine use of grammar checkers (Grammarly, Word spell-check) — these
  are not considered generative AI under current ICMJE guidance.
- Do not disclose use of reference managers (Zotero, EndNote) or statistical software
  (R, Python) unless the LLM generated the analysis code.

### Journal-Specific Overrides

When a journal profile is loaded in Phase 0, check for the `## AI Writing Disclosure Policy`
section in the profile. Its structured fields — **Requirement level** (Required / Recommended /
Not specified), **Permitted scope** (All tasks / Language editing only / Not permitted),
**Disclosure location** (Methods / Acknowledgments / Cover letter / Submission form),
**AI-generated images** (Allowed / Banned / Not specified), **Policy URL** — set the disclosure
language automatically. Key known policies:
- **Radiology/RSNA**: Required; language editing only; Methods + Acknowledgments; AI images banned.
- **RYAI/RSNA**: Required; language editing only; Methods + Acknowledgments; AI images banned.
- **JAMA/AMA**: Required; language editing only; Methods + Cover letter.
- **Lancet**: Required; language editing only ("readability and language"); Acknowledgments + prompts disclosed.
- **BMJ**: Required; all tasks permitted but must disclose; Methods + Acknowledgments; applies to text, images, data, diagrams.
- **Nature/Springer Nature**: Required; language editing only; Methods; AI images banned.
- **Science/AAAS**: Most restrictive. LLM use limited; treated as potential misconduct if undisclosed.

If the loaded journal profile has no AI Writing Disclosure Policy section, fall back to the
ICMJE placement under Disclosure Locations. ICMJE requires disclosure; it does not limit what AI
may be used for, so take any limit on scope from the journal.

---

## Gates

Severity levels: **ENFORCED** = pipeline halts on failure (cannot proceed to next phase). **ADVISORY** = warning logged, user may override. **OPT-IN** = runs only when explicitly invoked.

| Phase | Gate | Severity | Trigger | Action on fail |
|---|---|---|---|---|
| 0 | Backbone-article auto-proposal (Phase 0 "Identify a backbone article" action) | ADVISORY | refs.bib has methodologically similar candidate | Surface to user; user accepts/declines |
| 7.0 | Citekey resolution (delegate `/manage-refs scripts/check_citation_keys.py`) | ENFORCED | UNDEFINED keys present | Halt; resolve via `/lit-sync` then re-run |
| 7.0 | `[@NEW:topic]` drain (delegate `/manage-refs`; `check_citation_keys.py` reports them as UNDEFINED, exit 1) | ENFORCED at 7.6 entry | `[@NEW:topic]` markers remain | Resolve each before DOCX render |
| 7.1 | Classical-style QC (`check_classical_style.py`) | ENFORCED | a § section cross-reference OR an AI disclosure in the body of a journal that does not accept one there (per profile); more than 25 prose em-dashes is reported as Minor and does not halt | Auto-fix or HALT for senior MA reviewer prep |
| 7.2 | Reporting guideline compliance (`/check-reporting`) | ENFORCED at submission | <100% mandatory items present | Auto-fix MISSING; ADVISORY for partial |
| 7.3 | Reference audit (`/verify-refs --strict`) | ENFORCED | `submission_safe: false` (any FABRICATED or MISMATCH row, or a non-empty `duplicate_findings[]`), or any UNVERIFIED row (`--strict` exits 1 on those too) | Halt; fix in Zotero, re-render refs.bib via `/lit-sync` |
| 7.4 | Self-review fix loop (`/self-review --json --fix`) | ENFORCED | score below threshold after 2 iterations | Route to Step 7.4a Audit Recovery |
| 7.4a | Audit Recovery branch (route to `/meta-analysis` Phase 10 for MA manuscripts) | ENFORCED in `--e2e` | self-review surfaced structural data issue | HALT with `RECOVERY_HALT_HUMAN_DECISION` if recovery validation fails twice |
| 7.5 | Humanize density (`/humanize`) | ADVISORY | AI patterns > 2.0 / 1000 words | Sweep + flag remaining; user reviews |
| 7.5a | AIO checklist (`/academic-aio --aio`) — run after `/humanize`; also when preparing a preprint / GitHub README / CITATION.cff / HF card alongside submission. Never run it silently: academic-aio's Communication Rules prohibit that. | OPT-IN | user supplies `--aio` flag | PASS/PARTIAL/FAIL report; never auto-applies |
| 7.6 | DOCX build (delegate `/manage-refs scripts/render_pandoc.sh`) | ENFORCED | render exits non-zero | Halt; report stderr to user |
| 7.6a | Cross-reference QC (delegate `/manage-refs scripts/check_xref.py --strict`) | ENFORCED — submission gate | MISSING_DOCX / MISSING_BODY / MISMATCH > 0 (under `--allow-separate-attachments`: MISMATCH, or MISSING_BODY whose float is in the DOCX) | Halt; route fixes per `references/phase7_polish_detail.md` |
| 7.7 | Final submission gate | ENFORCED | any of 7.0–7.6a above failed | Refuse to mark `submission_safe: true` |
| 8+ | Cover letter generation | OPT-IN | user invokes `--cover-letter` | Renders against journal profile |
