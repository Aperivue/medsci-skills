# `/orchestrate --e2e` REPORT Template

This is the canonical end-of-run report written to `manuscript/<id>/REPORT.md` at the
termination of every `--e2e` invocation (whether the pipeline completed, halted at
pre-flight, or halted on validation failure). It is the single artifact the user
reviews — every other QC output is referenced from here.

The Worker fills every section. Missing or non-applicable information is recorded
explicitly as `(none)`, `(unknown)`, or `N/A` — never omitted.

This is the English default template. For a Korean-language report, use `report_template_ko.md`.

---

```markdown
# {project_id} Phase {N} Completion Report

## One-line summary
{what was done and how it turned out, in one sentence}

## Frozen / Version status
- Source artifact: {manuscript/<id>/v_N_package/draft.md, mtime, sha256}
- Frozen version: v_{N} (freeze date YYYY-MM-DD, at the time of circulation)
- This run wrote to: v_{N+1}_package/ (branch OK) | OR v_{N} directly (**violation — halt**)
- `manuscript-versioning.md` rule compliance: ✅ / ❌

## Source artifacts checked
- {path1} — read at {timestamp}, sha256 {hash}
- {path2} — ...
- Missing expected input: {list, or "(none)"}
- Pre-flight result: PASS | HALT (reason: STATUS_MISSING / FROZEN_VIOLATION / REQUIRED_INPUT_MISSING / DEPENDENCY_MISS)

## Changed files (in priority order)
- {path} — {1-line change summary}
- ...
- (if none, "(none)")

## Changed claims
- {in Methods, sample size N=68 → N=70 (re-counted from CSV rows)}
- {in Discussion, "primary outcome" → "co-primary outcome"}
- (if none, "no claim-level changes")

## Review points (in the user's priority order)
1. {most important — usually number / citation / logic verification points}
2. {next}
3. {then}

## Hallucination-gate results
- citation_safety: PASS / FAIL ({n} refs verified, first-author cross-check applied)
- numerical_safety: PASS / FAIL ({n} [VERIFY-CSV] tags remaining)
- dictionary_first: PASS / N/A (applies only in observational/cohort contexts)
- reporting_compliance: PASS / PARTIAL / FAIL ({guideline})

## QC artifact links
- `qc/reference_audit.json` — verify-refs result
- `qc/self_review.md` — self-review JSON block
- `qc/reporting_checklist.md` — check-reporting result
- `qc/xref_audit.json` — manage-refs cross-reference QC
- `qc/_pipeline_log.md` — Dialogue node defaults + halt reasons

## Human-only missing fields
The user must fill these in directly (autonomous authoring permanently forbidden):
- Funding grant IDs: ___
- Senior mentor circulation replies incorporated: ___
- Recommended reviewers (or "none"): ___
- Cover letter greeting / corresponding-author signature: ___
- (if not applicable, "(none)")

## Tier-3 Blocked Items
These actions are permanently forbidden in `--e2e` autonomous flow. On any attempt, halt + record below.

**Hook-confirmed blocks (`~/.claude/hooks/tier3-confirm.sh`)**:
- `gws gmail +send/+reply`
- YouTube upload

**Prompt / skill guard only (no hook — the Worker prompt blocks)**:
- `git push`, `gh pr create`
- MCP Gmail send, MCP Calendar send
- MCP GitHub create-pr
- `/sync-submission build` external-publish path
- Phase 8 (auto-building / submitting the submission docx)
- automatic senior-mentor replies

Attempts detected this run: `tier3_pending: <command or "(none)">`

## Next actions
- [ ] APPROVE → proceed to the next phase
- [ ] REJECT (reason: ___)
- [ ] PARTIAL (fixes: ___)

## Next safe command
The next-phase delegation command (the user can copy it verbatim):
`/orchestrate "<id> Phase {N+1} to completion" --e2e`

## Pipeline log
{5-line summary of qc/_pipeline_log.md — Dialogue node defaults, skill invocations, halt reasons}
```

---

## Notes for the Worker

- The fenced block above is the literal template. Copy it verbatim into
  `manuscript/<id>/REPORT.md` and replace `{...}` placeholders.
- Never delete a section. If empty, write `(none)`.
- The "Tier-3 Blocked Items" hook vs prompt-guard split is mandatory — collapsing them
  hides which blocks survive prompt regression. See SKILL.md §"Tier-3 Worker Guard".
- "Pipeline log" is a 5-line summary, not a paste of the full
  `qc/_pipeline_log.md`.
