# Orchestrate Dialogue Nodes — RPG-style CLI UX (prototype v0.1)

**Status:** Load-on-demand. The orchestrator reads this file only when entering interactive mode (default). `--autonomous` mode skips this file entirely and uses each node's `default` branch.

## Design Principles

1. **Present choice, commit downstream.** Each node makes explicit what the decision locks in (format, journal scope, analysis plan) so the user sees the cost of a wrong choice now vs. later.
2. **Default = safest reversible path.** If the user cannot decide, the default is the lowest-commitment option (e.g., "draft first, journal later"), never the highest.
3. **Recovery cost is visible.** When an option is hard to reverse ("locks journal format, 90-day revision clock"), the node shows this before the user picks.
4. **One question at a time.** Never render two decision nodes in the same turn.
5. **Interrupt-safe.** The user can always type `back`, `skip`, or `pause` to re-enter the previous node or stop the pipeline.

## Node Structure

```yaml
id: unique-slug
phase: which orchestrate phase this fires in
context: one-line summary of what orchestrator has observed
question: the user-facing prompt (<=120 chars)
options:
  - id: 1
    label: short description
    unlocks: [downstream-skill-or-phase]
    locks: [commitments this creates]
    recovery_cost: low | medium | high
default: option id chosen in --autonomous mode
autonomous_rationale: why this default is safe for unattended runs
```

## Primary Decision Nodes

### N1. Entry Classification
- **phase:** activation
- **context:** user request received, context-detection scan complete
- **question:** "Is this a single-skill task, a multi-step pipeline, or unclear?"
- **options:**
  1. Single skill — route now (low cost; always reversible)
  2. Pipeline — plan then confirm (medium cost; announce plan)
  3. Unclear — ask one clarifying question (no cost)
- **default:** inferred from classification table in SKILL.md; falls back to 3 only when truly ambiguous
- **rationale:** matches existing classification logic

### N2. Paper Type
- **phase:** before /write-paper or /write-protocol
- **context:** user wants manuscript-style output
- **question:** "What kind of manuscript? This locks the IMRAD template and reporting guideline."
- **options:**
  1. Original article (STROBE / CONSORT / STARD per design) — high recovery cost
  2. Case report (CARE) — medium cost; easy to escalate to original if series grows
  3. Systematic review / meta-analysis (PRISMA / PRISMA-DTA) — high cost; triggers /meta-analysis
  4. Protocol (SPIRIT / PRISMA-P) — medium cost
  5. Grant proposal (/grant-builder) — low cost; output is internal
- **default:** 1
- **locks:** reporting guideline choice, abstract structure, figure count expectations

### N3. Study Design (only for N2 option 1)
- **phase:** before /analyze-stats
- **context:** original article path chosen
- **question:** "What study design? This locks the analysis template and reporting guideline."
- **options:**
  1. Diagnostic accuracy (STARD, QUADAS-2) — forces 2x2 + DeLong CI
  2. Intervention / RCT (CONSORT) — arm-specific ITT/PP
  3. Cohort (STROBE) — Kaplan-Meier / Cox
  4. Case-control (STROBE) — conditional logistic
  5. Cross-sectional (STROBE) — prevalence + association
  6. AI prediction model (TRIPOD+AI) — held-out validation mandatory
- **default:** inferred from CLAIMS.md / PROJECT.md if present; otherwise ask
- **locks:** analysis code template, table skeleton, figure roster

### N4. Target Journal Timing
- **phase:** after /analyze-stats, before /write-paper Phase 2 (outline)
- **context:** analysis complete, manuscript drafting begins
- **question:** "Commit to a target journal now, or draft journal-neutral and pick later?"
- **options:**
  1. Commit now (/find-journal → pick one) — locks word limit, abstract structure, AI policy, figure format. High recovery cost if rejected.
  2. Draft neutral, pick at Phase 8 — medium cost; slightly longer total time but more flexibility after self-review.
- **default:** 2
- **rationale:** late commitment preserves option value; Phase 8+ cover letter is cheap to regenerate per journal.

### N5. Analysis Scope (MA only)
- **phase:** /meta-analysis Phase 4–5
- **context:** extraction complete, synthesis about to begin
- **question:** "Synthesis depth? Wider scope = longer pipeline but stronger discussion."
- **options:**
  1. Primary outcome only — fastest; default if K small (<6 studies)
  2. Primary + predefined subgroups — medium; requires protocol-registered subgroups
  3. Primary + subgroups + sensitivity (leave-one-out, risk-of-bias strata) — full depth
  4. Primary + meta-regression (requires K ≥ 10 per covariate) — heavy; only if protocol specifies
- **default:** 2 when protocol specifies subgroups; else 1
- **locks:** forest plot count, funnel plot requirement, discussion outline

### N6. PHI Safety Gate
- **phase:** before any data-handling skill
- **context:** CSV/Excel detected, no `*_deidentified.*` marker
- **question:** "Does this data contain PHI (names, RRN, DOB, contact)?"
- **options:**
  1. Yes — route to /deidentify first (blocking, interactive script)
  2. No — proceed
  3. Already de-identified — proceed (user attests)
- **default:** in `--autonomous` mode, HALT if unknown. PHI gate overrides autonomy.
- **lock:** audit trail — once user picks 3, their attestation is logged

### N7. Autonomous vs Interactive
- **phase:** pipeline start
- **context:** user invoked /orchestrate with or without `--e2e` flag
- **question:** inferred from flag — no prompt
- **options:**
  1. Interactive (default) — render every node, pause between skills
  2. `--e2e` / `--autonomous` — use defaults, skip confirmations, halt only on PHI or validation failure
- **default:** 1
- **lock:** affects every downstream node's behavior

### N8. Audit Recovery Branch (Step 7.4a trigger)
- **phase:** after /self-review with fatal finding
- **context:** self-review returned `accuracy` / `data_fidelity` / `protocol_mismatch` / `numerical_claim` fatal
- **question:** "Self-review flagged a fatal structural issue. Which recovery?"
- **options:**
  1. MA manuscript → /meta-analysis Phase 10 (v{N}→v{N+1} rebuild) — high cost, required for MA fidelity
  2. Non-MA extraction error → /write-paper Phase 2 re-entry — medium cost
  3. Protocol amendment needed → HALT for human decision — recovery off-pipeline
  4. Override (user asserts finding is not fatal) — requires written justification in qc/_pipeline_log.md
- **default:** 1 or 2 based on manuscript type; never 4 in autonomous mode
- **lock:** Steps 7.5–7.6 blocked until recovery returns clean

### N9. Section Entry Point (/write-paper reentry)
- **phase:** /write-paper reentry after recovery
- **context:** re-entering the pipeline post-recovery
- **question:** "Where to resume? Phase 7.3 (re-audit) or Phase 7.1 (re-draft) or Phase 2 (restructure)?"
- **options:**
  1. Phase 7.3 — recovery only touched numbers; audit is the right re-entry (default per Step 7.4a spec)
  2. Phase 7.1 — recovery changed claims; re-draft conclusions
  3. Phase 2 — recovery changed outline; re-do structure
- **default:** 1
- **lock:** later re-entry invalidates later polish; later = expensive

### N10. Reference Workflow (manage-refs entry)
- **phase:** /manage-refs entry (Phase 7.6 of write-paper, or standalone DOCX rebuild)
- **context:** manuscript ready for DOCX rendering with bibliography; need to choose Workflow A (pandoc citeproc) vs Workflow B (Zotero CWYW)
- **question:** "Bibliography rendering: pandoc citeproc (single-author / cascade reformat) or Zotero CWYW (co-author Word collaboration)?"
- **options:**
  1. Workflow A — pandoc citeproc + journal CSL (markdown SSOT, regenerable, cascade-friendly)
  2. Workflow B — Zotero CWYW field-code injection (Word-tracked-changes-friendly, co-author live edit)
  3. Hybrid 3-phase — start A (draft), transition to B (circulation/revision/submission)
- **default:** 3
- **lock:** Workflow B `.docx` becomes editable SSOT; markdown re-render requires re-extraction. Hybrid is the documented default per `~/.claude/rules/manuscript-references.md`
- **autonomous_rationale:** Hybrid 3-phase is the accumulated pattern; A→B transition only happens when circulation begins, so default is safe for solo drafting

### N11. Protocol Delivery Format (write-protocol → fill-protocol vs render-pdf-doc)
- **phase:** /write-protocol Phase final (or standalone protocol rendering)
- **context:** content drafted; need final deliverable. Institutional Word template availability differs
- **question:** "Final deliverable: institutional .docx form (use `/fill-protocol`) or markdown → PDF (use `/render-pdf-doc`)?"
- **options:**
  1. `/fill-protocol` — institutional Word template exists (IRB 연구계획서, 심사면제, 동의면제, etc.)
  2. `/render-pdf-doc` — no institutional template; markdown-driven layout (proposal cover, briefing handout, anchor doc, IRB cover letter)
- **default:** 1 (when `${institutional_template_path}` resolves; else 2)
- **lock:** option 1 inherits institutional layout (immutable styles, table cantSplit, eastAsia fonts); option 2 inherits markdown frontmatter + content-proportional pipe-table widths
- **autonomous_rationale:** Most institutional submissions require option 1; default to scanning known template paths first (`~/.claude/rules/institutional-form-fill.md` table) before falling back to option 2

## Rendering Template

When presenting a node in interactive mode, use:

```
▸ {node.id} — {one-line purpose}

  Context: {node.context}

  {node.question}

    1) {option 1 label}
       → unlocks: {...}    locks: {...}    recovery: {low|med|high}

    2) {option 2 label}
       → unlocks: {...}    locks: {...}    recovery: {low|med|high}

  Pick 1–N, or type `back` / `pause` / `skip`.
  (autonomous default: {default_option})
```

Keep the rendering under ~15 lines. If the user types the option number, the orchestrator confirms the lock-in and proceeds.

## Autonomous Mode Contract

When `--autonomous` / `--e2e` is set:

- Do NOT render any node rendering template.
- Do NOT prompt for input.
- For each node, select the `default` and log the choice to `qc/_pipeline_log.md` as: `[orchestrate] N{id}: defaulted to option {n} ({label}) — {autonomous_rationale}`.
- PHI Safety Gate (N6) is the only node that can HALT autonomous mode.
- Audit Recovery (N8) may HALT in autonomous mode if the default recovery route itself fails validation twice.

## Future Expansion

- Add recovery-cost accumulator: track how many "medium / high" locks the user has accumulated; surface a warning when cumulative lock debt is high.
- Add `replay` command to print all nodes and chosen options for post-submission review.
- Consider `what-if` simulation: show downstream path of each option without committing.
