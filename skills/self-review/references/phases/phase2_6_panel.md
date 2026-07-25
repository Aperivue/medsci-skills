# Phase 2.6 — Multi-Agent Panel Review (`--panel`)

Read this only when `--panel` was passed. A default single-pass review never reaches any of it.

The panel simulates independent peer reviewers who do not see each other's comments, then an editor who consolidates them — the same structure a journal uses. It reuses the vendored domain-probe modules so every reviewer applies the same criteria.

**Precondition (blocking): the SSOT must be singular.** Before spawning any reviewer, enforce the Phase 1 step 4 SSOT gate: if more than one manuscript-like `.md` exists and none is pinned (no `SSOT.yaml` `truth.manuscript_md`, no explicit `--ssot`), **halt and ask the user which file is the SSOT** — a panel is too expensive to spend on a stale copy. Clear any `STALE_COPY` from `detect_copy_divergence.py` first.

## Step 1 — Compose the reviewer set by research type

Auto-detect the manuscript type (Phase 1 input + the Research-Type Adaptation table). Each reviewer loads the matching domain-probe module so the panel's criteria are single-sourced.

| Research type | Reviewer set (each is one reviewer) | Domain-probe module each loads |
|---|---|---|
| Survival / prognostic cohort | R1 Biostatistics & Study Design · R2 Clinical (domain) · R3 Imaging/Radiology (if an imaging exposure) | `references/domain-probes/survival_prognostic.md` |
| Systematic review / meta-analysis | R1 Methodology (search/screening/PRISMA) · R2 Clinical · R3 Statistics (pooling/heterogeneity) | `references/domain-probes/sr_ma.md` |
| Radiomics / feature reproducibility | R1 Imaging physics & acquisition · R2 ML / Statistics · R3 Clinical translation | `references/domain-probes/radiomics.md` |
| Diagnostic-accuracy / AI model | R1 Study design & leakage · R2 Statistics (DeLong, calibration) · R3 Clinical / reference standard | `references/domain-probes/sr_ma.md` (P1 DTA cells) + `references/domain-probes/ai_overclaiming.md` (AO0–AO7, for AI clinical claims) + categories A–C |
| Observational (STROBE) | R1 Epidemiology / confounding · R2 Clinical · R3 Statistics | `references/domain-probes/observational_confounding.md` (O1/O8 run as the Phase 2.5e / `check_cohort_arithmetic.py --id-col` deterministic gates; O7 over-adjustment) + `references/domain-probes/clinical_prediction_model.md` (CP1–CP4, when it is a prediction-model paper) + categories A–J + the effect-size / added-value axes |
| Narrative / review article | R1 Domain-content expert · R2 Methodology / SANRA · R3 Technical accuracy · R4 Adversarial reject-hunter (structural: RV9 curated-base circularity, RV6 single-anchor overload, RV8 self-citation architecture) | `references/domain-probes/narrative_review.md` |
| Perspective / opinion / viewpoint | R1 Domain-content expert · R2 Argument architecture (thesis clarity, section-as-argument-move, single spine device) · R3 Technical accuracy · R4 Adversarial reject-hunter | `references/domain-probes/narrative_review.md` |
| Case report | R1 Clinical case-report reviewer · R2 Ethics / de-identification · R3 Literature-context reviewer | `references/domain-probes/case_report.md` + CARE items + categories D/F/G |

If the type is ambiguous, ask the user before composing the set.

Append the **handling-editor desk-impression** persona (the ceiling lens) to every reviewer set: it loads no domain probe, reads only for narrative confidence vs over-defensiveness, and returns Minor REMOVE / MOVE / TIGHTEN findings (category L) that the editor routes to the separate Editorial-Impression Risks block. Its focus checklist is in `references/panel_review_template.md`. It does not count toward the Step 3.5 lens-diversity axes.

## Step 2 — Run the reviewers (portable execution)

When the host provides a parallel subagent / Task capability (Claude Code, or any harness exposing an Agent tool), spawn the reviewer set as independent parallel subagents, each blinded to the others, then run the editor as a final synthesis agent. **Fallback (no subagent capability — e.g. a minimal Codex/Cursor harness):** a single agent role-plays each reviewer sequentially and in isolation — it completes and writes out reviewer R1's full structured review before reading the manuscript "fresh" as R2, so a later reviewer never sees an earlier reviewer's comments. The panel is defined by these instructions; it does **not** depend on the `Workflow` tool or any Claude-Code-only orchestration.

**Before spawning, write a roster manifest** — `panel_roster.json`. At minimum the list of `reviewer_id`s you are about to spawn (so a reviewer that returned nothing is distinguishable from one that was never expected — the Step 3.5 `--roster` completeness check). **When the manuscript was AI-drafted, the roster must also declare substrates** — a top-level `generator_substrate` and a `substrate` per reviewer, each a coarse lane label (`"claude"` | `"codex"` | `"gpt"` | `"human"`) — because a panel that shares the drafter's substrate inherits its blind spots and is not an independent check. Routing at least one lens to a **different substrate** (the Codex adversarial path) or a human co-author is the **default, not an option**: the Step 3.5 gate fires `SUBSTRATE_MONOCULTURE` (Major) when every declared reviewer shares `generator_substrate`. Example: `{"generator_substrate": "claude", "reviewers": [{"reviewer_id": "R1", "substrate": "claude"}, {"reviewer_id": "R2", "substrate": "codex"}, {"reviewer_id": "R3", "substrate": "human"}]}`.

A reusable reviewer schema, a generic harsh-but-fair reviewer prompt skeleton with per-domain focus checklists, and the editor synthesis prompt skeleton live in `${CLAUDE_SKILL_DIR}/references/panel_review_template.md`.

Each reviewer returns: `reviewer_id`, `expertise_area`, an `overall_assessment` (name the single biggest threat to the conclusions), `strengths` (2–3), `major[]` (each with `heading`, `comment`, `location`, `severity`, `suggested_fix`), and `minor[]`. Map `severity` onto this skill's own scale — a conclusion-threatening / design-level finding is **Fatal**, a reporting-level finding is **Fixable** — rather than introducing a separate vocabulary.

## Step 3 — Editor synthesis

One editor pass (a final agent, or the main agent in the fallback) consolidates the reviews:

1. **Dedupe** findings by theme across reviewers.
2. **Flag CONSENSUS** for any theme raised by ≥2 reviewers, with R1/R2/R3 attribution (e.g., `[CONSENSUS: R1+R3]`); single-reviewer findings are attributed to the one reviewer.
3. **Decide** an internal readiness verdict (this sets the Phase 3c `verdict` / `overall_score`; it is not printed as a journal recommendation).
4. **Rank** the concrete pre-submission actions the author should complete first.
5. State a one-line **readiness verdict** (ready for the target tier now / fix specific items first / consider a different tier).

## Step 3.5 — Lens-diversity gate (deterministic)

A panel only earns its cost if its reviewers span *distinct* axes rather than echo one theme louder. Before the editor finalizes, serialize the reviewers' structured outputs (the schema above) to a JSON file — either a top-level list or `{"reviewers": [...], "research_type": "..."}` — and run the gate:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_panel_diversity.py \
    --panel panel_reviews.json --roster panel_roster.json \
    --research-type {survival|sr_ma|radiomics|dta|observational|narrative} --strict
```

With `--roster` it first checks **completeness** — **`PANEL_UNDERRETURN`** (Major) fires when fewer reviewers returned a parseable review than were spawned, or when fewer than 2 returned at all. A panel with <2 returned reviews is a **failed run, not a thin one**: do not synthesize it or report it as a review — re-spawn (or route to a different substrate / human co-author). This is the case that otherwise passes silently, because a thin or empty `panel_reviews.json` errors nowhere. It then checks **independence** — **`SUBSTRATE_MONOCULTURE`** (Major) fires when the roster declares a `generator_substrate` and every declared reviewer shares it: a same-model panel inherits the drafter's blind spots and is not an independent check, so route at least one lens to a different substrate (Codex) or a human co-author (skipped when the roster declares no substrates — backward compatible). It then reports three diversity failures, each mapped onto a concern family aligned to the focus checklists:

- **`UNCOVERED_AXIS`** (Major) — an axis the research type is expected to probe (e.g. heterogeneity/pooling for an SR/MA) drew **zero** major findings. The editor re-probes it with the owning reviewer before finalizing, or records in the synthesis why the gap is acceptable.
- **`FAMILY_MONOCULTURE`** (Major) — the majority of majors fall in one concern family; the lenses converged rather than spanned the manuscript.
- **`LENS_COLLAPSE`** (Flag) — a reviewer raised only families another reviewer already covered, adding no independent axis.

Healthy CONSENSUS is preserved — agreement on *some* themes is a strength (Step 3 flags it), and the gate fires `LENS_COLLAPSE` only on a *fully* redundant reviewer and the Major checks on panel-level coverage, never on agreement per se. Do not silently ship a monoculture: resolve every Major before the synthesis verdict.

## Step 4 — Feed Phase 3

The consolidated panel output flows into the Phase 3 report, Phase 3b R0 numbering (**preserved**, so `/revise` still consumes it), and Phase 3c JSON. CONSENSUS flags and reviewer attribution are additive annotations on the existing `M`/`m` comments (and the optional `consensus` JSON field); they do not change the report or JSON structure.

## Re-run the panel after a large revision

A panel is high-yield not only before the first submission but **again after any large edit** — a word-count compression, a primary-model or adjustment-set change, or resolving a batch of majors. Such edits introduce *new* drift (a compression drops a caveat; a re-fit leaves a derived CSV stale; a relocation orphans a cross-reference), and the second panel's findings shift character accordingly (method → compression-drift → residual). If the author has just compressed or re-modelled, recommend one more `--panel` pass rather than assuming the prior panel still holds; in practice each post-revision round surfaces real, distinct errors.
