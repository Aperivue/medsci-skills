# Phase 7 — Polish: step detail

Load-on-demand companion to `/write-paper` Phase 7. SKILL.md keeps the strict step
sequence (7.1 → 7.7), the command that runs at each step, and every HALT condition;
this file carries the detail behind them — the AI-disclosure four-token grep, the
Step 7.4a recovery routing table, the DOCX/citeproc build options and bundled CSL
list, and the Step 7.6a cross-reference status matrix with its per-symptom fix routes.

Read it when you reach the build steps (7.5 → 7.6a), when a HALT fires, or when the
manuscript carries an AI/LLM-use disclosure paragraph.

Two deeper references are cited from here and from SKILL.md:
`references/phase7_integrity_audits.md` (Steps 7.3a/7.3b/7.3c) and
`references/section_guides/step7_4a_audit_recovery.md` (the full recovery procedure).

Final quality pass before submission.

**Actions (strict sequential execution — each step MUST complete before the next begins):**

#### Step 7.1: AI Pattern Scan

Scan for and remove AI writing patterns (see AI Pattern Avoidance below). Edit `manuscript/manuscript.md` in place.

**Classical-style QC (for senior MA reviewers) — load on demand:**

| Trigger | Action |
|---------|--------|
| Manuscript type = MA, systematic review, or a senior co-author review is expected | Load `references/section_guides/step7_1_classical_qc.md` → run the 7 grep checks together (§ symbol, AI Disclosure paragraph, heading style, eligibility numbered list, Funding placeholder, PROSPERO chronology, em-dash overuse) |
| Verify all at once with a deterministic lint | `python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/self-review/scripts/check_classical_style.py" --manuscript manuscript/manuscript.md --strict` — `SECTION_SYMBOL`/`INBODY_AI_DISCLOSURE` (Major) + `ELIGIBILITY_PROSE`/`DECIMAL_INCONSISTENCY`/`EM_DASH_OVERUSE` (Minor). The machine-checkable subset of the same conventions as the 7-grep checklist. |
| Global-rule cross-reference | `~/.claude/rules/manuscript-style-classical.md` (motivation for the 11 items) |
| Pattern 19–21 body rewrite | `/humanize` (§, self-reference, AI Disclosure boilerplate) |

**AI-disclosure meta-applicability (manuscript-style-classical §15):** if the manuscript
contains an AI/LLM-use disclosure, that paragraph must itself satisfy the reporting items the
manuscript critiques (FLAIR F1.6, TRIPOD-LLM, MI-CLEAR-LLM all require the tool **version**, the
**access channel**, the **date range**, and the **responsible party**). Enforce all four tokens
and zero unresolved placeholders:

```bash
DISC=$(grep -niE 'generative ai|large language model|\bLLM\b|assisted (the|with) (writing|drafting)|ChatGPT|Claude|Copilot|Gemini' manuscript/manuscript.md)
# the disclosure paragraph must carry: version + channel + date + responsible party
grep -iE 'version|[0-9]+\.[0-9x]+|GPT-[0-9]'   <<<"$DISC"   # version present
grep -iE 'API|chat|web|Bedrock|Azure|interface' <<<"$DISC"   # access channel present
grep -E '20[0-9]{2}'                            <<<"$DISC"   # date / date range present
grep -iE 'by [A-Z]\.[A-Z]\.|reviewed by|deployed by|the authors' <<<"$DISC" # responsible party
# zero placeholders
grep -nE '\[(version|date|tool|model|channel)\]|TODO|XXXX|TBD' manuscript/manuscript.md  # must be empty
```

Any missing token (or a surviving `[version]`/`TODO`/`XXXX` placeholder) is a HALT: the paper
cannot critique a framework's AI-disclosure item while failing it itself. For a classical /
senior-MA target the disclosure paragraph is not placed in the body at all — branch it to the
title page (manuscript-style-classical §7 forbids the in-body AI-disclosure paragraph).

#### Step 7.2: Reporting Guideline Check

Call `/check-reporting` on `manuscript/manuscript.md`. Parse the output:
- If the report includes a JSON summary block (Part D), extract MISSING items.
- For each MISSING item where `fixable_by_ai` is true (e.g., missing ethics statement, missing data availability statement, missing sample size justification), insert the suggested text at the indicated location in `manuscript/manuscript.md`.
- Do NOT attempt to fix items requiring external information (IRB numbers, registration numbers, protocol details only the author knows).
- Log all auto-inserted text to `qc/_pipeline_log.md`.

#### Step 7.3: Citation Verification

**7.3.1 — Placeholder gate (v1.1.1 Phase 1A.4).** Before running `/verify-refs`,
confirm that no `[@NEW:topic]` placeholders remain:

```bash
grep -nE '\[@NEW:[^]]+\]' manuscript/index.qmd manuscript/manuscript.md 2>/dev/null
```

If any match is returned, HARD STOP. Report the unresolved placeholders to the
user and loop back: owner runs `/search-lit` → `/lit-sync` to import entries,
collaborators flag via owner. Do NOT proceed to 7.3.2 until the grep is clean.

**7.3.2 — Audit.** Call `/verify-refs` on the current manuscript. Per v1.2.0
contract, its sole output is `qc/reference_audit.json` (no longer writes
`references/*`). Parse that file: if `submission_safe: false`, stop the pipeline
and surface the `FABRICATED` / `MISMATCH` records AND any `duplicate_findings[]`
entries (duplicate PMID/DOI; cite renumbering required) to the user. If
`/verify-refs` is unavailable, fall back to `/search-lit --verify-only` and flag
any unverified references with `[UNVERIFIED]` markers.

#### Steps 7.3a / 7.3b / 7.3c: Integrity audits (numerical / estimand / reference-adequacy)

After Step 7.3 and before Step 7.4, run three integrity audits. Each can HALT and route to **Step 7.4a (Audit Recovery Branch)**. **Full procedures (triggers, blocker policy, the delegated checker commands, and the `qc/_pipeline_log.md` log formats) are in `${CLAUDE_SKILL_DIR}/references/phase7_integrity_audits.md` — load it when this step runs.**

- **7.3a Numerical Claim Audit** (mandatory for MA / pooled estimates / comparative arms / revisions / reporting-quality-checklist synthesis): 3-way match text ↔ Table ↔ extraction CSV, primary-source back-check, analysis-script literal audit, and recompute reporting-quality headline numbers from matrix cells (denominator = Σ non-NA). A direction reversal or a p<0.05↔p≥0.05 crossing is a **P0 blocker**; composes with `/self-review` Phase 2.5a.
- **7.3b Estimand Provenance & Promised-Analysis Audit** (any pre-registered/protocol primary, E-value, or named analyses): delegate to `/self-review` Phase 2.5f — `PRIMARY_REASSIGNED` / `ESTIMAND_DRIFT` / `EVALUE_ARITHMETIC` / `EVALUE_NON_PRIMARY` are **P0 blockers**; grep that Methods-promised analyses appear in Results; run `check_artifact_coverage.py --strict` for the disk-present-but-unreported reverse scan.
- **7.3c Reference Adequacy Gate** (every named statistical method / reporting guideline must carry a citation): run `check_reference_adequacy.py` (no `--strict`; write-paper decides from the JSON); a `methods_zero_citations` / `methods_named_method_uncited` finding is a reference-acquisition blocker resolved only via `/search-lit` → `/lit-sync` → `/verify-refs --strict` (never fabricate); composes with `/self-review` Phase 2.5c-2.

#### Step 7.4: Self-Review + Fix Loop

Call `/self-review --json --fix` on the current `manuscript/manuscript.md`.

This delegates the entire fix loop to the self-review skill, which:
1. Runs systematic review (Phase 2) and generates a JSON report (Phase 3c).
2. If `verdict` is `"REVISE"`: filters `fixable_by_ai` issues, applies text edits to `manuscript.md`, and re-reviews — up to 2 fix-and-re-review iterations.
3. If `verdict` is `"PASS"` after any iteration: stops early.
4. Returns the final JSON report with updated scores.

**High-stakes manual pass (optional):** this autonomous loop deliberately uses the single-pass review — a multi-agent panel is *not* auto-applied in the pipeline (it spawns several reviewer agents plus an editor, multiplying token cost). For a top-tier or otherwise high-stakes manuscript, run `/self-review --panel` once manually as a final pre-submission pass (it diagnoses and prioritizes but does not auto-fix, so triage its findings yourself).

After `/self-review --json --fix` completes:
- Parse the final JSON output block.
- Log the final `overall_score`, `verdict`, fix iteration count, and any remaining issues to `qc/_pipeline_log.md`.
- If any `severity: "fatal"` issue remains: **route to Step 7.4a (Audit Recovery Branch)** — do NOT proceed to Step 7.5.
- If no fatal issue remains: proceed to Step 7.5.

#### Step 7.4a: Audit Recovery Branch

**Purpose:** the linear polish flow assumes remaining issues are prose-level, but some
self-review findings are structural — underlying data, protocol application, or analysis
script is wrong, not prose. Continuing through Step 7.5 – 7.6 in that case produces a
polished manuscript built on a broken foundation. This step makes the recovery loop
explicit.

**Trigger (any one from Step 7.4 JSON):** fatal issue in category `accuracy`,
`data_fidelity`, `protocol_mismatch`, or `numerical_claim`; unresolved Step 7.3a primary-
source disagreement; `[VERIFY-CSV]` tag persisting after two fix iterations; registered
protocol ↔ delivered analysis inconsistency; reviewer-consensus ↔ locked-dataset
disagreement. Inline text fixes are forbidden — recovery requires re-extraction,
re-analysis, or re-registration.

**Routing table:**

| Symptom | Route to |
|---|---|
| MA pooled/forest/subgroup/funnel numbers disagree with source | `/meta-analysis` Phase 10 |
| MA protocol ↔ analysis mismatch (eligibility, outcome, subgroup) | `/meta-analysis` Phase 10 + registry amendment |
| Primary-study numerical claim disagrees with source Table/Figure | `/meta-analysis` Phase 6b, then return |
| Non-MA extraction error affecting Table 1 / primary endpoint | Return to Phase 2, re-enter Phase 3 – 7 for affected sections |
| Non-MA protocol amendment needed | HALT — human decision |

**Sequence**: (1) halt Steps 7.5 – 7.6; (2) log the branch decision to
`qc/_pipeline_log.md`; (3) invoke the routed skill with the specific findings; (4) on
re-entry, resume at Step 7.3 (Citation Verification) — not Step 7.1, because recovery
may have introduced new citations — and carry any change summary to Phase 8+;
(5) loop budget is one cycle — a second cycle should trigger a root-cause review of
Phase 2 / 6 / 6b rather than another recovery.

**Autonomous mode.** In `--autonomous`, the orchestrator may auto-invoke the routed
recovery skill. If the recovery requires human decision (protocol amendment, eligibility
re-scope), the run stops and flags `RECOVERY_HALT_HUMAN_DECISION` in the log.

**Load-on-demand procedural detail** (full trigger list, log-block template, per-route
re-entry checklist, autonomous-mode edge cases):
`${CLAUDE_SKILL_DIR}/references/section_guides/step7_4a_audit_recovery.md`.

#### Step 7.5: Generate Deliverables

Log the self-review fix loop results to `qc/_pipeline_log.md`:
```
## Self-Review Fix Loop (Phase 7.4)
- Initial score: {score_before} → Final score: {score_after}
- Fix iterations: {N}/2
- Fixed issues: {count}
- Remaining issues (human review needed): {count}
- Final verdict: {PASS|REVISE}
```

Generate the following files:
- `manuscript/manuscript.md`: Complete manuscript (with LLM disclosure in Methods and Acknowledgments if enabled)
- `manuscript/title_page.md`: Title page with author info, word count, key points if required. **Number the author affiliations by first appearance** (affiliation 1 = the first author's first affiliation; each new affiliation gets the next integer as the author list is read left to right; each ends with city + country) — required by Nature Portfolio / npj technical checks. Do not hand-number; generate and verify with `scripts/build_title_page_affiliations.py` (`--authors authors.yaml` to build, `--check title_page.md --strict` to verify). See `references/section_guides/title_abstract.md` § "Title Page — Author & Affiliation Order".
- `qc/reporting_checklist.md`: Filled reporting guideline checklist from Step 7.2
- `qc/self_review.md`: Final self-review report from Step 7.4
- `qc/_pipeline_log.md`: Pipeline execution log

#### Step 7.6: DOCX Build

Build the final submission-ready documents from the assembled components:

1. **Input files**: `manuscript/manuscript.md`, `analysis/figures/_figure_manifest.md`, `analysis/tables/*.csv`
2. **Figure embedding**: Parse `analysis/figures/_figure_manifest.md`. For each figure entry, verify the file exists at the specified path. Replace markdown image references `![Figure N. ...](path)` with the actual image path.
3. **Table embedding**: For each `analysis/tables/*.csv` file referenced in the manuscript, the pandoc conversion will handle table formatting.
4. **Pandoc conversion** (primary):
   ```bash
   pandoc manuscript/manuscript.md -o manuscript/manuscript_final.docx -V mainfont="Times New Roman" -V fontsize=12pt
   pandoc manuscript/manuscript.md -o manuscript/manuscript_final.pdf --pdf-engine=xelatex -V geometry:margin=1in -V fontsize=11pt -V mainfont="Times New Roman"
   ```
   Ensure all figure image references use relative paths so figures render in both formats.

   **With pandoc citeproc + journal CSL** (when manuscript uses `[@bibkey]` citations and a `.bib` is available — preferred for any submission with > 5 references; mandatory when reviewers have asked for "automatically generated reference list"):

   The validation + render scripts live in `/manage-refs` (split out 2026-05-01). Either invoke `/manage-refs` directly (recommended), or call the scripts manually:
   ```bash
   MR="${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs"

   # 1. Validate keys vs .bib first (fail fast on UNDEFINED keys; [@NEW:topic] placeholders pass through)
   python "$MR/scripts/check_citation_keys.py" \
     manuscript/manuscript.md manuscript/_src/refs.bib

   # 2. Render with journal CSL (see manage-refs/citation_styles/ for bundled CSLs)
   "$MR/scripts/render_pandoc.sh" \
     -j european-radiology \
     -i manuscript/manuscript.md \
     -b manuscript/_src/refs.bib \
     -o manuscript/manuscript_final.docx
   ```
   Bundled CSLs: `european-radiology`, `radiology`, `american-journal-of-roentgenology`,
   `cardiovascular-and-interventional-radiology`, `korean-journal-of-radiology`,
   `vancouver`, `vancouver-superscript`. Use `radiology` for RYAI; use `vancouver` for JVIR
   (no dedicated CSL). On rejection cascade (e.g., ER → JVIR → CVIR), re-render with
   different `-j` — references reformat in seconds. Never hand-type the References list.

   **Decision: pandoc vs Zotero Word plugin (CWYW)** — `/manage-refs` documents the hybrid 3-phase strategy (Phase 1 pandoc draft → Phase 2 transition → Phase 3 Zotero CWYW for circulation/revision/submission). Use Workflow B (CWYW) once co-authors collaborate live in Word; use Workflow A (pandoc) for single-author lockdown, journal-cascade rejection re-formatting, or when the plugin is unavailable. See
   `~/.claude/rules/manuscript-references.md` and `skills/manage-refs/SKILL.md`.
5. **Fallback** (if pandoc is unavailable): Generate the DOCX using python-docx:
   - Parse `manuscript/manuscript.md` sections (`##` → Heading 2, `###` → Heading 3, `**bold**` → bold runs)
   - Insert figures as inline images at their markdown reference locations
   - Insert tables as formatted Word tables from CSV sources
   - Apply Times New Roman 12pt, double spacing, 1-inch margins, page numbers
   - Save as `manuscript/manuscript_final.docx`
6. **Verify output**: Confirm `manuscript/manuscript_final.docx` exists and is non-empty. Report file size.

#### Step 7.6a: Cross-Reference QC (Manuscript ↔ rendered DOCX)

Catches the failure mode where in-text Table/Figure citations resolve to the
wrong rendered caption. Internal consistency (Phase 2.5 of `/self-review`)
does NOT catch this because both the body prose and the build script can echo
their own divergent SSOTs cleanly. Precedent: an STROBE cohort manuscript revision —
body cited "Supplementary Table S4 (a sensitivity-analysis)" but the rendered DOCX S4
was a diagnostics table; S1, S6, S7 mismatched and S8, S9 were cited but absent from
the DOCX entirely.

**Run after Step 7.6 DOCX build and before Step 7.7 final gate:**

```bash
MR="${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs"
python3 "$MR/scripts/check_xref.py" \
  --md manuscript/manuscript.md \
  --docx manuscript/manuscript_final.docx \
  --out qc/xref_audit.json \
  --strict
```

The script extracts (a) every `(Supplementary )?(Table|Figure)\s+(S?\d+[A-Z]?)`
in-text citation, (b) caption definitions from `## Tables` / `## Figures` /
`## Figure Legends` / `## Supplementary {Tables,Figures}` sections in the body,
and (c) caption paragraphs in the rendered DOCX (via python-docx). It then
emits a 3-way matrix to `qc/xref_audit.json`:

| Status | Meaning | Severity |
|---|---|---|
| `OK` | cited + body caption + DOCX caption all present and caption text agrees (Jaccard ≥ 0.40) | — |
| `MISSING_DOCX` | cited but no caption with that label in the rendered DOCX | **P0 blocker** |
| `MISSING_BODY` | cited but no caption definition in the markdown body sections (build SSOT drift) | **P0 blocker** |
| `MISMATCH` | label exists in both body and DOCX but caption text disagrees | **P0 blocker** |
| `UNCITED` | caption defined or rendered but never cited in main text | warn |
| `NOT_CITED_NO_BODY` | label appears only in DOCX (rare; legacy artifact) | warn |

**Submission gate:** if any `MISSING_DOCX` / `MISSING_BODY` / `MISMATCH` row is
present, `submission_safe: false` and the script exits 1 under `--strict`.
HALT pipeline. Do NOT proceed to Step 7.7. Route fixes by symptom:

- `MISSING_BODY` → add caption definition under `## Tables` / `## Figures` in
  `manuscript.md`, then re-run Step 7.6 + 7.6a. If the build script
  (`build_manuscript_docx.py` or equivalent) carries its own hardcoded caption
  list, that is the IMPROVEMENT_QUEUE #2 SSOT-unification issue — flag it.
- `MISSING_DOCX` → either drop the citation (the table/figure was retired) or
  re-add the table/figure to the build pipeline, then rebuild DOCX.
- `MISMATCH` → reconcile body vs build script. Body caption is the SSOT;
  update the build pipeline to match, never the reverse.

Log the run to `qc/_pipeline_log.md`:
```
## Cross-Reference QC (Phase 7.6a)
- in-text citations: {N}
- unique labels: {N}
- OK: {N} | MISSING_DOCX: {N} | MISSING_BODY: {N} | MISMATCH: {N} | UNCITED: {N}
- submission_safe: {true|false}
- audit: qc/xref_audit.json
```

If `python-docx` is unavailable, the script falls back to a body-only audit
(citations vs body captions) with a warning. Install with `pip install python-docx`.

#### Step 7.7: Final Gate

- **Autonomous mode**: Log completion to `qc/_pipeline_log.md`. Report summary: word count, figure count, self-review score, reporting compliance percentage, any FATAL flags.
- **Interactive mode**: Present the full summary to the user and await confirmation.

---
