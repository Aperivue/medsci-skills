<!-- Loaded on demand by write-paper Phase 7 (Polish). The SKILL.md keeps a short
     trigger/blocker pointer for Steps 7.3a / 7.3b / 7.3c; the full audit procedures
     live here so they cost context only when Phase 7 actually runs. -->

# Phase 7 integrity audits — Steps 7.3a / 7.3b / 7.3c (full detail)

Read this when the Phase 7 pointer routes you here. These three steps run after
Step 7.3 (Citation Verification) and before Step 7.4 (Self-Review); each can HALT
the pipeline and route to **Step 7.4a (Audit Recovery Branch)**.

#### Step 7.3a: Numerical Claim Audit (MANDATORY for MA / pooled estimates / comparative arms)

Citation verification protects against fabricated references; this step protects against
fabricated numbers. They are different failure modes and Step 7.3 does not catch the latter.

**Precedent failure pattern:**
> A revision-era comparative meta-analysis reached Step 7.3 with 0 citation errors (all
> PMIDs verified against PubMed) yet carried a silent numerical reversal on a safety
> outcome — the reported arm-level events were direction-flipped relative to the primary
> source Table. The error originated in a hand-typed Fisher-exact matrix in a revision-era
> analysis script, and internal consistency checks (Phase 2.5 of `/self-review`) passed
> cleanly because every downstream artifact echoed the same wrong number.

**Trigger conditions:** any of the following makes this step mandatory before Step 7.4.
- The manuscript contains pooled estimates, forest plots, or a meta-analysis Table.
- The manuscript contains comparative-arm specific values extracted from a larger study.
- The manuscript contains any `[VERIFY-CSV]` tag (from `/revise` Step 2.5 or `/meta-analysis`
  Phase 6b).
- The current draft is a revision (post-v1).
- The manuscript synthesizes completion of an items × studies reporting-quality checklist
  (TRIPOD+AI, PROBAST+AI, CLAIM, PRISMA, STARD, CHARMS, ARRIVE, or similar) and reports
  corpus-level, study-level, or item-level PRESENT / PARTIAL / ABSENT / compliance counts
  and percentages. The matrix cells are the authoritative source; headline numbers are
  derivations and must be recomputed from cells via code before prose drafting.

**Precedent failure pattern for the reporting-quality trigger:**
> A reporting-quality systematic review reported corpus PRESENT at ~61% in v1.0; cell-level
> recomputation on v1.1 produced ~51% (delta ~10 percentage points). The error survived
> internal consistency because every downstream table, figure caption, and abstract
> sentence echoed the hand-tallied v1.0 total. Recomputation from matrix cells — not from
> hand-tallied per-study totals — is the only reliable source for headline numbers.

**Procedure:**

1. **3-way matching.** For every pooled estimate, subgroup result, and Table value, establish
   that the text ↔ Table (`analysis/tables/*.csv`) ↔ extraction CSV (`data_extraction_*.csv`)
   triplet agrees. Random-sample 5 claims if the full set is large.

2. **Primary-source back-check.** For each sampled claim, locate the original paper's Table
   or Figure coordinate and confirm the value. Record page number.

3. **Analysis-script audit.** Grep all `.R` / `.py` scripts for `matrix(`, `c(`, `data.frame(`,
   and `fisher.test(`. Any numerical literal without a CSV-coordinate comment is flagged —
   even if the value happens to be right. Hand-typed numerical literals are a structural risk,
   not a cosmetic issue.

4. **Tag removal.** Every `[VERIFY-CSV]` tag may be removed only after that specific value
   has been confirmed in steps 1–3. Record the removal in `qc/_pipeline_log.md`:
   ```
   ## Numerical Claim Audit (Phase 7.3a)
   - [VERIFY-CSV] tags cleared: {N}/{N}
   - 3-way mismatches found: {count}
   - Hand-typed script literals without CSV comment: {count}
   - Primary-source disagreements: {count}  ← P0 blocker if >0
   ```

5. **Blocker policy.** A direction reversal or a significance-boundary crossing (p<0.05 ↔
   p≥0.05) is a P0 blocker — halt Step 7.4 and alert the user. Other mismatches are P1 and
   must be fixed before Step 7.6 DOCX build.

6. **Reporting-quality checklist SR — additional steps (only when that trigger fires).**
   When the audit target is an items × studies checklist synthesis, run these in addition
   to steps 1–5:

   a. **Per-study totals recomputation.** For each included study, recompute the
      PRESENT / PARTIAL / ABSENT / NA counts from the per-study matrix cells via code.
      Hand-tallied per-study totals in any extraction or summary file are prohibited
      as the authoritative source and must be replaced with the recomputed values.

   b. **Corpus-level denominator recomputation.** The corpus denominator is
      Σ non-NA across studies, not K × I (where K = studies, I = items). Compute
      corpus PRESENT % = Σ PRESENT / Σ non-NA and repeat for PARTIAL and ABSENT.
      An NA-unaware denominator is a P1 defect because it shifts every percentage.

   c. **Item-level roll-up.** For each item, count how many of K studies are PRESENT,
      PARTIAL, ABSENT, or NA. Flag universal-ABSENT and universal-NA items —
      these drive the Discussion paragraph and must be listed explicitly, not
      described generally.

   d. **3-way consistency.** Every headline number in the manuscript (abstract,
      Results paragraph, Tables, Figure captions) must trace back to: manuscript
      text ↔ per-study JSON or extraction file ↔ summary document (e.g.,
      `*_summary.md`). All three must agree to the last decimal place.

   e. **Source artifacts expected.** The audit expects to find a reproducible
      script (e.g., `analysis/recompute_matrix_totals.py`) that loads the per-study
      cells, recomputes every headline number from cells, emits a
      `numerical_claims_log.csv` (claim_id | description | value | source |
      computation), and exits non-zero on any 3-way mismatch. Absence of such a
      script is itself a P1 finding to flag for the user.

This step composes with — not replaces — `/self-review` Phase 2.5a. Run it here for pipeline
completeness even when `/self-review` is also invoked.

#### Step 7.3b: Estimand Provenance & Promised-Analysis Audit

Step 7.3/7.3a verify that citations and numbers are real. This step verifies that the
manuscript's **claims trace to the artifacts they should** — the pre-registration / protocol,
and the analyses Methods promised. These survive Step 7.3a because the prose is internally
consistent.

**Trigger:** any manuscript with a pre-registered or protocol-defined primary analysis, an
E-value / unmeasured-confounding statement, or a Statistical Analysis subsection that names
analyses (interaction, subgroup, sensitivity, multiple imputation). Skip for case reports.

1. **Delegate the cross-check to `/self-review` Phase 2.5f** (claim-vs-artifact). It runs the
   deterministic estimand + E-value checks and returns `PRIMARY_REASSIGNED` / `ESTIMAND_DRIFT`
   (the primary contrast was re-designated after results were known, or does not match the
   registration) and `EVALUE_ARITHMETIC` / `EVALUE_NON_PRIMARY` (a reported E-value does not
   recompute from its primary estimate, or is borrowed from a secondary one). Any of these is a
   **P0 blocker** — halt before Step 7.4 and route to **Step 7.4a (Audit Recovery Branch)**.
   The fix is to report the pre-specified and revised models coequally and disclose the change
   in the Abstract and Limitations, never to silently lead with the more favourable estimate.

2. **Methods-promised-analysis completeness (inline grep).** Every analysis named in the Methods
   Statistical Analysis subsection must appear in Results:

   ```bash
   # promised in Methods
   grep -ioE "interaction|subgroup|sensitivity analysis|multiple imputation|mediation|competing risk|landmark|E-value" \
     manuscript/index.qmd | sort -u
   ```

   Cross-check each hit against the Results section. A promised-but-absent analysis is a **HALT**:
   add it to Results, remove the promise from Methods, or file a protocol amendment. Log the
   checklist to `qc/_pipeline_log.md`.

3. **Reverse direction — disk-present-but-unreported.** The forward grep only catches analyses
   the Methods promised. An analysis that was *run* but whose result is missing from the paper —
   often because it undercuts the headline — needs the opposite scan. Delegate to
   `/self-review` Phase 2.5f's coverage gate, which reads an `_analysis_outputs.md` manifest (or
   globs the analysis directory) and reconciles every output file against the manuscript body:

   ```bash
   python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/self-review/scripts/check_artifact_coverage.py" \
     --manuscript manuscript/index.qmd --analysis-dir output/analysis --strict
   ```

   A `DISK_UNREPORTED` analysis-bearing output (an added-value DeLong CSV, a calibration table)
   is a **HALT**: report it or document why it was dropped.

This step composes with `/self-review` Phase 2.5f; run it here for pipeline completeness even
when `/self-review` is also invoked.

#### Step 7.3c: Reference Adequacy Gate

Step 7.3/7.3a/7.3b verify reference **integrity** — that the cited references are real and the
numbers/estimands trace to their artifacts. This step is the complementary **reference adequacy**
check: are there *enough* relevant references, in the right sections, and does **every named
statistical method or reporting guideline carry a citation**? The dominant failure mode in an
autonomous draft is a Statistical Analysis subsection that names a competing-risk model, multiple
imputation, the E-value, and an eGFR equation with **zero citations** — internally consistent
prose that no integrity check flags.

Delegate the detection to the self-review checker (same cross-skill pattern Step 7.3b uses for
`check_artifact_coverage.py`). Resolve the manuscript path with the fallback chain
`SSOT.yaml::truth.manuscript_md` → `manuscript/manuscript.md` → `manuscript/index.qmd`; pass the
`project.yaml` paper type verbatim (the script's alias map handles repo names); pass the journal
reference cap from the chosen `references/journal_profiles/<journal>.md` when known.

```bash
python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/self-review/scripts/check_reference_adequacy.py" \
  --manuscript "$MANUSCRIPT" --bib "$BIB" \
  --article-type "$TYPE" ${CAP:+--journal-cap "$CAP"} \
  --out qc/reference_adequacy.json   # no --strict: write-paper decides the action from the JSON
```

Parse `qc/reference_adequacy.json` and act:

1. **Methods citation completeness (blocking).** Any `methods_zero_citations: true` (for an
   original/AI-validation/meta-analysis paper) **or** any `methods_named_method_uncited`
   (statistical tier) finding is a reference-acquisition blocker. **Interactive:** loop
   `/search-lit` (Manuscript Paper Reference Pool mode) → `/lit-sync` → `/verify-refs --strict`,
   then re-run this gate until the named-method gap clears. **`--autonomous` mode** (where
   `/lit-sync` needs the Zotero GUI and cannot run unattended): do **not** infinite-loop — record
   `SEARCH_LIT_REQUIRED` plus the uncited-method list in `qc/_pipeline_log.md`, surface it to the
   owner, and continue producing the draft (the same deferral Phase 0 applies to unresolved
   `[@NEW:]` placeholders).
2. **Total count (loop, then warn).** `reference_count_verdict: "BELOW_TARGET"` triggers one
   `/search-lit` acquisition round; if the field is genuinely sparse and the count stays low,
   downgrade to a logged WARN rather than blocking. **Never fabricate references to hit a target.**

All additions flow `/search-lit` → `/lit-sync` → `/verify-refs --strict` only; this skill never
writes references from memory, and the checker emits `fixable_by_ai: false` (it diagnoses gaps, it
does not write citations). Append the result to `qc/_pipeline_log.md`:

```md
## Reference Adequacy Gate (Phase 7.3c)
- Article type / Journal cap: {type} / {cap|unknown}
- Cited references: {N}   Effective target: {min}-{max}
- Section distribution: Intro {N} / Methods {N} / Results {N} / Discussion {N}
- Named methods checked: {N}   Uncited: {list}
- Action: PASS | SEARCH_LIT_REQUIRED | HALT_UNVERIFIED_REFS
```

This step composes with `/self-review` Phase 2.5c-2, which re-runs the same checker with `--strict`
and folds its findings into the review JSON; run it here so a reference-acquisition loop precedes
the prose self-review in Step 7.4.
