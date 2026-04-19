# Step 7.4a Reference — Audit Recovery Branch

Load this reference when Step 7.4 returns a fatal structural finding (category
`accuracy`, `data_fidelity`, `protocol_mismatch`, or `numerical_claim`), an unresolved
Step 7.3a primary-source disagreement, a persistent `[VERIFY-CSV]` tag, or a registry ↔
analysis inconsistency. The SKILL.md body carries only trigger table + routing table +
summary pointer; procedural detail lives here.

## Purpose

The linear polish flow (draft → review → revise → submit) assumes remaining issues are
prose-level. Some self-review findings are structural — they indicate that the
underlying data, protocol application, or analysis script is wrong, not that the prose
is wrong. Continuing through Step 7.5 – 7.6 in that case produces a polished manuscript
built on a broken foundation. This step makes the recovery loop explicit.

## Trigger Conditions (any one, from the Step 7.4 JSON report)

- A `severity: "fatal"` issue whose category is `accuracy`, `data_fidelity`,
  `protocol_mismatch`, or `numerical_claim`.
- An unresolved primary-source disagreement from Step 7.3a (P0 blocker).
- A `[VERIFY-CSV]` tag remains in the manuscript after two fix iterations.
- The self-review report flags inconsistency between the registered protocol (e.g.,
  PROSPERO record) and the delivered analysis.
- A reviewer-consensus record and the locked dataset disagree on inclusion of one or
  more studies.

**Do not attempt to fix these inline.** The `/self-review --fix` loop is text-level;
these findings require re-extraction, re-analysis, or re-registration. In-line text
patching papers over the defect and breaks downstream audit trails.

## Routing

| Symptom | Route to |
|---|---|
| MA pooled estimate / forest / subgroup / funnel numbers disagree with source | `/meta-analysis` Phase 10 (Self-Audit Recovery) |
| MA protocol vs. analysis mismatch (eligibility, outcome, subgroup) | `/meta-analysis` Phase 10 + registry amendment |
| Primary-study numerical claim disagrees with source Table/Figure | `/meta-analysis` Phase 6b (Post-Analysis Source Fidelity Audit), then return here |
| Non-MA manuscript: extraction error affecting Table 1 / primary endpoint | Return to this skill's Phase 2 (Tables & Figures) with corrected CSV, then re-enter Phase 3 – 7 for affected sections only |
| Non-MA manuscript: protocol amendment needed (e.g., IRB-registered outcome changed) | Halt and ask the user; protocol amendments are human-decision |

## Actions

1. **Halt the polish pipeline.** Do not run Step 7.5 (Generate Deliverables) or Step 7.6
   (DOCX Build). The current `manuscript/manuscript.md` is still a work-in-progress.
2. **Log the branch decision** to `qc/_pipeline_log.md`:
   ```
   ## Audit Recovery Branch (Step 7.4a)
   - Triggered by: {finding IDs from self-review JSON}
   - Routed to: {skill/phase}
   - Manuscript version frozen at: v{N}
   - Recovery workspace: {path}
   ```
3. **Invoke the routed skill** with the specific findings. For MA-type recovery, the
   `/meta-analysis` Phase 10 sprint rebuilds the extraction, analysis, figures, and
   manuscript-body numbers, and emits a `change_summary.md`.
4. **Re-entry.** When the upstream recovery completes and produces a new
   `manuscript/manuscript.md` (v{N+1}) plus a change summary:
   - Re-enter Phase 7 at Step 7.3 (Citation Verification) — not at Step 7.1, because
     recovery may have introduced new citations.
   - Carry the change summary through to Phase 8+ (cover letter) when applicable.
   - If the recovery required a registry amendment (PROSPERO or equivalent), confirm in
     Step 7.2 (Reporting Guideline Check) that the manuscript's Methods text cites the
     amendment date.
5. **Loop budget.** A single recovery cycle is expected. A second recovery cycle on the
   same manuscript is permitted but should prompt a root-cause review of Phase 2 / 6 /
   6b — repeated recoveries indicate upstream rigor gaps, not manuscript-level issues.

## Autonomous Mode

If `--autonomous` is ON and the recovery skill is also available, the orchestrator may
auto-invoke `/meta-analysis` Phase 10 and continue. If the recovery requires human
decision (protocol amendment, eligibility re-scope), the autonomous run stops and flags
`qc/_pipeline_log.md` with `RECOVERY_HALT_HUMAN_DECISION`.
