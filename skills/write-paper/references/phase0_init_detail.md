# Phase 0 — Init: paper-type modes and gate detail

Load-on-demand companion to `/write-paper` Phase 0. SKILL.md keeps the required
inputs, the flags, the reporting-guideline selection, the backbone full-text gate, and
the five citekey hard rules — everything the agent needs *before* it knows the ask.

This file carries what only becomes relevant *after* the paper type is known:
**Case Report Mode** and **Case Series Mode** (their word/reference-limit overrides,
outline rewrites, and default figure sets), the backbone-article ranking and proposal
behaviour, and the rationale behind the citekey gate.

Read the mode block that matches the declared paper type. Do not read the others —
a manuscript has one paper type.

Gather essential information from the user before any writing begins.

**Required inputs:**
1. **Title** (working title is fine)
2. **Paper type**: original article, AI validation, case report, case series, meta-analysis, technical note, animal study, NHIS cohort, cross-national
3. **Target journal**: load profile from `${CLAUDE_SKILL_DIR}/references/journal_profiles/`
4. **Research question / hypothesis**
5. **Available data**: what datasets, tables, analyses already exist

**Optional flags:**
- `--no-llm-disclosure`: Skip LLM writing assistance disclosure. Default is ON (disclosure included). See [LLM Disclosure](#llm-writing-disclosure) section below.
- `--autonomous`: Run the full pipeline without user gates. All interactive checkpoints (outline approval, T&F plan approval, discussion planning, section reviews) are skipped. The pipeline executes Phases 0-7 sequentially without pausing. Default is OFF (all gates active). Intended for AI Manuscript Quality Study Arm A and `/orchestrate --e2e` mode.

**Actions:**
1. Load the journal profile. If no profile exists, ask the user for: word limits, abstract format, citation style, figure/table limits, special requirements.
2. Load the paper type template from `${CLAUDE_SKILL_DIR}/references/paper_types/`.
3. Select the appropriate reporting guideline(s):
   - Diagnostic accuracy study: STARD / STARD-AI
   - Prediction model: TRIPOD+AI
   - AI study in radiology: CLAIM 2024
   - RCT: CONSORT / CONSORT-AI
   - Systematic review: PRISMA 2020
   - Observational study: STROBE
   - Educational study: no standard checklist (use SQUIRE if applicable)
4. **AI/LLM design-stage reporting map**: for AI validation, LLM/MLLM, NLP extraction, or report-generation papers, map each required AI-reporting item to a manuscript section before drafting. At minimum record model/version/access date, input fields, prompt or fine-tuning protocol, same-backbone zero-shot/few-shot baseline if an adaptation claim is made, test-data independence/contamination assessment, repeatability/stochasticity handling, and the Methods subsection where each will appear. If any item cannot be placed, halt for design clarification rather than burying it as a Phase 7 limitation.
5. Create or confirm the project scaffold directory.
6. Check for `--no-llm-disclosure` flag. If absent, LLM disclosure is ON by default.
   Check for `--autonomous` flag. If present, record autonomous mode as ON.
   Record both flag states for use in Phase 1-7 gate logic.

#### Case Report Mode

When paper type is "case report":
1. Load `${CLAUDE_SKILL_DIR}/references/paper_types/case_report.md` (CARE structure).
2. Load `${CLAUDE_SKILL_DIR}/references/exemplar_case_report.md` for the narrative flow,
   150-word structured abstract anatomy, and case-report failure modes.
2b. If the case is **imaging-led** (diagnostic radiology, nuclear medicine, or interventional
    radiology — the contribution is the image or an image-guided procedure), also load
    `${CLAUDE_SKILL_DIR}/references/exemplar_case_report_radiology.md` for per-modality
    technique→findings→impression discipline, structured-reporting lexicons (BI-RADS/LI-RADS/
    PI-RADS/TI-RADS/Lung-RADS/O-RADS), quantitative anchors with method/threshold honesty,
    multimodality discordance, the IR procedure/complication subtype, incidental-finding reporting,
    and DICOM de-identification / real alt text / device-vendor COI.
3. Override word limits: total 1000-1500 words (excl. abstract, references, legends).
4. Override abstract limit: 150 words, structured (Introduction, Case Presentation, Conclusion).
5. Override reference limit: 15 references maximum.
6. Apply CARE 2013 reporting guideline (mandatory; see `/check-reporting` `CARE.md`).
7. Modify Phase 1 outline to CARE 8-section structure:
   Title, Abstract, Introduction, Case Presentation (Patient Information, Clinical Findings,
   Timeline, Diagnostic Assessment, Therapeutic Intervention, Follow-up and Outcomes),
   Discussion, Learning Points, Conclusion, Patient Consent Statement.
8. In Phase 2, default figures:
   - Figure 1: Key imaging findings (annotated, typically 3-6 panels)
   - Figure 2: Clinical timeline (if complex course)
   - Table 1: Laboratory and clinical data at presentation
9. In Phase 5 (Discussion), call `/search-lit` with query: `"[condition]" AND "case report"[Publication Type]`.
   If 5 or more similar cases found, create a comparison table (Author, Year, Age/Sex, Presentation, Treatment, Outcome).
   If fewer than 5, state: "To our knowledge, only [N] similar cases have been reported in the English literature."
10. Skip Phase 5a Discussion Planning Gate — case reports are shorter; proceed directly to drafting.
11. For extended case reports with literature review, user can specify `--extended` to raise
    the word limit to 2000-3000 words and add a structured review section.

#### Case Series Mode

When paper type is "case series" (n≥2 patients reported together):
1. Load `${CLAUDE_SKILL_DIR}/references/paper_types/case_series.md` — a case series is a
   **methods-light mini-cohort**, not a stack of single case reports.
2. Also load `${CLAUDE_SKILL_DIR}/references/exemplar_case_report.md` for per-case narrative
   discipline (each vignette still follows the CARE moves).
3. Typical word count: 1500–3000 words (scales with patient count).
4. Apply CARE adapted for multiple patients; for ≥5 surgical cases consider PROCESS/SCARE.
5. Modify Phase 1 outline to: Title → Abstract (structured) → Introduction → **Methods**
   (design, setting, case identification, eligibility as a numbered list, protocol, assessment
   process) → **Results** (mandatory all-cases summary table + consistent per-case vignettes,
   grouped by subtype where a taxonomy exists) → Discussion (cross-case synthesis +
   cohort-level limitations) → Conclusions → Ethics/Consent.
6. In Phase 2, default a **summary Table 1 enumerating every case** (one row per patient) plus
   representative figures labeled to each case number.
7. In Discussion, enforce the case-series discipline: state selection/ascertainment and the
   screened pool size; **report counts, not rates** (a referral/database series is not a
   denominator of all disease); cohort-level limitations are mandatory and specific.

7. **Identify a backbone article (auto-proposal first, ask only as fallback)**:
   a. **Scan first** — if `manuscript/_src/refs.bib` exists, scan it for entries matching the current paper's study design (Phase 0 paper_type), imaging modality, and target journal (or comparable tier). Prefer entries whose Zotero record has a PDF attachment (full text locally available).
   b. **Rank candidates** by: PDF available locally (+2), recency within 5 years (+1), same target journal (+2), same study design + modality (+2).
   c. **Behavior**:
      - **One strong candidate (score ≥ 5)** — propose it proactively: *"I found a likely backbone article: [citation]. Full text appears available. I will use it as the structural backbone unless you prefer another."* Proceed once user confirms or stays silent for one turn.
      - **Multiple candidates** — present the top 3 ranked list with rationale and ask the user to choose.
      - **No refs.bib, or no candidates** — ask the user to provide a published study (legacy behavior).
   d. Record the chosen citekey in `project.yaml::backbone_article` so Methods, Tables, and Figures phases reuse it without re-asking.
   e. **Full-text readiness gate (MANDATORY before any drafting).** A backbone whose full text is not extracted is a backbone in name only — the draft would follow an abstract. After recording the citekey, confirm its full text is retrieved and converted to Markdown, then gate on it:
      ```bash
      python3 ${CLAUDE_SKILL_DIR}/scripts/gate_backbone_fulltext.py \
        --project project.yaml --refs manuscript/_src/refs.bib \
        --fulltext-dir pdfs/ --strict
      ```
      `BACKBONE_FULLTEXT_MISSING` / `BACKBONE_FULLTEXT_THIN` means stop and retrieve it first — `/lit-sync` Phase 2.7 (open-access + Zotero "Find Available PDF") then `/fulltext-retrieval` `pdf_to_md.py` to convert the PDF to Markdown. Do **not** begin Methods drafting until this gate passes (addresses issues #4 and #8: the backbone is *used*, not merely *detected*). If the article is genuinely unavailable in full text, record that limitation explicitly and get user confirmation before proceeding on the abstract.
8. Summarize the setup to the user and confirm before proceeding.

**Output:** Setup summary with journal constraints, paper type, reporting guideline, backbone article, directory path, and LLM disclosure status (ON/OFF).

#### Phase 0 Gate: Citekey-only references

Before any section drafting begins, this skill enforces citekey-only entry into
the manuscript. LLM-generated reference strings in prose are a primary source of
citation fabrication.

**Hard rules (v1.1.1 Phase 1A.4)**:

1. **Every in-text citation MUST be `[@citekey]`**, where `citekey` exists in `manuscript/_src/refs.bib`. Pandoc/Quarto-style only. No "(Smith et al., 2024)" free text.
2. **For a citation the user intends to add but has not yet imported to Zotero**, use the placeholder form `[@NEW:short-topic]` (e.g., `[@NEW:chest-xray-llm]`, `[@NEW:radbench-1]`). The topic slug is kebab-case, ≤30 characters, and must be unique within the manuscript.
3. **Never** fabricate a citekey that "looks real" (e.g., `[@Smith_2024_AI]`) when the entry is not in `refs.bib`. The `[@NEW:...]` form is the only allowed placeholder.
4. Before Phase 7 (Polish), ALL `[@NEW:...]` placeholders must be resolved:
   - Owner runs `/search-lit` → `/lit-sync` to import verified entries into Zotero; Better BibTeX auto-export refreshes `refs.bib`; owner replaces `[@NEW:topic]` with the real citekey.
   - Collaborators notify the owner (per `docs/zotero_policy.md`).
5. Phase 7 pre-submission check: `grep -E '\[@NEW:[^]]+\]|\[N\]|\[N–N\]' manuscript/index.qmd` must return zero matches before `/sync-submission` is allowed to freeze a journal package. The bare numeric markers `[N]` / `[N–N]` are the failure mode where a manuscript is drafted outside this pipeline (no `refs.bib`) and method-load-bearing citations are left as unresolved placeholders; block them the same way as `[@NEW:...]`.

**Why this matters**: PRISMA citation fabrication in MA projects and reference hallucination in solo manuscripts both traced back to LLM-generated citation strings inlined during drafting. Forcing the citekey discipline at Phase 0 redirects that failure mode into a visible placeholder the submission gate can block.

**If refs.bib is absent (new project)**:
- Create an empty `manuscript/_src/refs.bib` placeholder with a comment: `% refs.bib managed by /lit-sync via Zotero Better BibTeX. Do not hand-edit.`
- Record in `SSOT.yaml` `reference_manager.required_for: project_owner` per Zotero policy.
- Proceed; all early citations will be `[@NEW:...]` placeholders until the first `/lit-sync` run.

---
