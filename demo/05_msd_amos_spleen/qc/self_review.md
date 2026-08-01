# Self-review — panel mode, one round, revisions applied

**Manuscript**: `manuscript/writeup.md` · **Date**: 2026-07-31 · **Mode**: `/self-review --panel`
**Roster**: `qc/_selfreview/panel_roster.json` · **Reviews**: `qc/_selfreview/panel_reviews.json`

The manuscript was drafted by Claude, so a panel of Claude reviewers would have inherited the
drafter's blind spots. The roster therefore declares `generator_substrate: "claude"` and routes a
lens to **Codex** — a different substrate. That decision is the reason this review is worth reading:
**the Codex reviewer returned a Reject and was substantially right, on points the same-substrate
reviewers and every deterministic gate had passed.**

## Deterministic gates (run first, on every pass)

| Gate | Before revision | After |
|---|---|---|
| `check_scope_coherence --strict` | 1 Minor (`GRADIENT_WITHOUT_INTERACTION`) | PASS |
| `check_classical_style --strict` | PASS | PASS |
| `check_analysis_definitions --strict` | PASS | PASS |
| `check_figure_citation` | PASS | PASS |
| `check_citation_order --strict` | **2 Major** (`CITATION_ORDER`, tables and figures both out of order) | PASS |
| `check_table_percentages --strict` | PASS | PASS |
| `check_rounded_delta` | PASS | PASS |
| `check_editorial_impression` (ceiling) | no subtraction needed | no subtraction needed |
| `verify-refs` (pre-render) | 1 MISMATCH | **13/13 OK** |

## Panel

| Reviewer | Lens | Substrate | Returned |
|---|---|---|---|
| R1 | Statistics and uncertainty | codex | yes (after two same-substrate agents died mid-run) |
| R2 | Statistics, metrics, uncertainty | claude | **partially** — recovered from an interrupted transcript |
| R3 | Adversarial reject-hunter | **codex** | yes |
| R4 | Handling-editor desk impression | claude | yes |

`check_panel_diversity --strict` fired `PANEL_UNDERRETURN` while R2's run was incomplete, which is
the correct behaviour and is recorded rather than worked around: two Claude subagents were terminated
by API errors and a resume stalled. R2's findings survive only because its transcript was recovered
and **every numeric claim in it was independently recomputed before being accepted** — an agent's
assertion is not evidence.

The `clinical` axis is uncovered and stays uncovered. This is a tooling demonstration with no patient
outcome, no clinical endpoint and an explicit no-clinical-claim stance; there is nothing for a
clinical lens to probe. Recorded here rather than papered over.

## Anticipated Major Comments

**M1. Rung 3 is a constructed stress test, not a discovered failure** [A · Fatal] — *R3*
The evaluation plan named `CTNormalization`, recorded its clip parameters, and predicted the collapse
**before inference ran**. The draft nonetheless framed the result as a clinician doing everything
right and landing on a defect "no step asked them to read" — while the investigator had read exactly
that field, in advance. **Action (applied)**: the Introduction now separates rungs 1–2 from rung 3
and states plainly that rung 3 is constructed; the claim is narrowed to *the pipeline is silent about
a known incompatibility*, which the run does establish. The Discussion, Conclusion and both READMEs
carry the same reframing.

**M2. The causal attribution exceeds the design** [C · Fatal] — *R3*
Table 4 shows the normaliser treats CT and MRI differently. It does not show that the normaliser
*caused* the collapse rather than a CT-trained representation failing on MRI, or both: no
correctly-normalised MRI arm was run. **Action (applied)**: "located the cause" and "is a
preprocessing failure" are gone. The claim is now that the incompatibility is present in 60/60 cases
and sufficient to account for the magnitude, with an explicit paragraph on what the design does not
separate, repeated in Limitations. **Closed by measurement 2026-08-01**: rung 3b changed only the
input intensity scale and recovered median Dice 0.0152 → **0.3016** (difference **+0.2864**
[+0.1204, +0.4048]) while staying **−0.5916** [−0.7259, −0.4674] below external CT. Both mechanisms
are real and their sizes differ. A **second** counterfactual (rung 3c) then swapped the normaliser
instead of the input and reached 0.2870 — indistinguishable from 3b (−0.0146 [−0.2136, +0.1575]),
same 15 empty predictions, per-case r = 0.939 — so the decomposition rests on two independent
routes: roughly **0.28 intensity domain, 0.60 representation**. The hedge is replaced by a
decomposition, which is a *stronger* claim than the hedge and a weaker one than the draft's original
"located the cause".

**M3. One authored example cannot support general claims about tooling** [D · Fatal] — *R3*
One organ, one architecture, one dataset pair, one deliberately chosen mismatch, no independent
users, no comparator workflow. **Action (applied)**: the routing-and-severity claim is now labelled a
hypothesis this example motivates; the Conclusion says what the study cannot settle.

**M4. HD95 was reported against the wrong denominator** [C · Fixable] — *R2 (recomputed and confirmed)*
HD95 is undefined when a prediction is empty, and empty predictions are the worst cases. HD95 existed
for 9/9, **270/298** and **40/59** cases while being quoted against the Dice denominator — a
one-directional optimism that grows with the failure rate. **Action (applied)**: `n_with_hd95` is a
column in Table 2, every HD95 in the prose carries its n, and the metric is labelled a
success-conditioned estimand.

**M5. The Abstract contradicted Table 2 in the same document** [F · Fixable] — *R3*
"produced 60 plausible segmentations" — of which **20 are empty files** and five more are under 1 mL
against 100–600 mL references. **Action (applied)**: replaced with what the artifacts support.

**M6. The bootstrap interval depended on arm processing order** [C · Fixable] — *R2 (confirmed)*
All arms drew from one RNG stream, so `seed 20260725` pinned the *run*, not the arm: adding an arm
silently moved published intervals. **Action (applied)**: seeded per (arm, metric). While fixing it
the first patch used `hash()`, which Python randomises per process — the fix would have destroyed
determinism in the act of repairing it; replaced with blake2b and verified stable across
`PYTHONHASHSEED`. External CT's interval moved 0.8639 → **0.8633**; every quotation was updated.

**M7. Δ-Dice was quoted as a "drop" with no interval** [C · Fixable] — *R1*
A difference of two separately estimated medians is not an inferential quantity, and the n=9 internal
arm carries most of the uncertainty. **Action (applied)**: both arms are resampled independently and
the difference reported with a 95% interval — −0.0662 [−0.0996, −0.0416] and −0.9443 [−0.9715,
−0.8813]. Both exclude zero, so the word "drop" is now earned.

**M8. Prospective chronology is not auditable from this repository** [E · Fixable] — *R3*
`EVALUATION_PLAN.md` and the rung-3 results first appear in the **same commit**. **Action (applied)**:
"registered" is gone; Methods states that the ordering is documented by the authors and not provable
here, and points at the profiler output, which *is* independently machine-readable.

## Anticipated Minor Comments

- **m1. Stratum labels described a different rule from the binning code** — *R2/R3*. Labels read
  `thin (<=2 mm)` while the code increments on `value >= edge`; **67 external CT cases sit at exactly
  2.00 mm** and were placed in `mid`. **Applied**: labels now state the implemented closure, in both
  scripts and the module docstring.
- **m2. Text and Table 1 disagreed on the MRI reference-volume median** (186.8 over 60 vs 187.6 over
  59 scored) — *R2*. **Applied**: one denominator, named.
- **m3. `spacing_z` is not the through-plane axis for much of the MRI arm** — 26 of 60 volumes; nine
  scored cases would change stratum under a coarsest-axis rule — *R2*. **Applied** as a Limitation;
  the CT arm is unaffected.
- **m4. A missing prediction warned and exited 0** — *R3*. **Applied**: `evaluate_segmentation.py`
  now returns 3 unless `--allow-missing` is passed.
- **m5. Runtime numbers have no shipped artifact** (epoch time, 21 days, ~50 GPU-hours come from
  cluster logs) — *R3*. **Applied**: stated as the one class of number that cannot be re-derived here.
- **m6. Sparse strata** (thin CT n=5, thick MRI n=0) — *R1*. **Applied**: labelled descriptive.
- **m7. The headline median needed an estimand justification** (external CT mean 0.7116 vs median
  0.8932) — *R1*. **Applied**: the estimand is typical-case performance, stated with why the mean and
  the empty-prediction count are reported beside it.

## Editorial-impression risks (REMOVE / MOVE / TIGHTEN) — advisory, from R4

L1 **TIGHTEN** — the Abstract is ~490 words and its middle third is verification bookkeeping.
L2 **REMOVE** — the no-clinical-claim disclaimer appears four times across the package.
L3 **REMOVE** — half of Limitations restates Methods and Introduction.
L4 **MOVE** — the written prediction is introduced as a confession rather than as a strength.
L5 **MOVE** — all four table legends are repository paths.

**Round 1 — not applied.** The floor revisions above *added* material (an identification-limits
paragraph, an estimand paragraph, a chronology caveat), so the Abstract and Limitations came out of
that round longer, not shorter. Applying L1–L5 in the same pass would have mixed an accuracy
revision with a voice revision and made neither reviewable.

### Round 2 (2026-08-01) — the subtraction round, applied

All five applied. Abstract **543 → 337 words**; Limitations **~230 → 182**; body **3,972 → 3,721**.

| | Action taken |
|---|---|
| L1 | Abstract cut: seeds, resample count, gate names, normaliser constants and the "every number comes from an executed run" reassurance all left the Abstract. The contrast that does the work (300/300 vs 0/60 negative voxels, 2.7% vs 23.2% clipped, 20 empty files) stayed. |
| L2 | The clinical-claim guard now appears **once**, on the title page. |
| L3 | Limitations lost the three restatements (schedule arithmetic, internal-rung provenance, clinical-claim guard) and kept only what it alone says. |
| L4 | The prediction paragraph now opens with what the plan got right; the correction follows it. |
| L5 | Table legends describe the table instead of naming a CSV path. |

**A subtraction round can delete a fact the floor needed, and this one did.** `seed 20260725` and
`10,000 resamples` lived **only** in the Abstract, so cutting them removed the bootstrap parameters
from the manuscript entirely — a reproducibility regression that CLAIM item 29 depends on, invisible
to the ceiling lens that asked for the cut. R4's instruction was *move to Methods*, not delete.
Restored to a new **Uncertainty** paragraph in Methods, which now also states the per-(arm, metric)
seeding. Every floor gate re-run and green after the restore; the ceiling gate reports no remaining
subtraction.

## Strengths (for a cover letter)

- The counterfactual is **shipped and must fail**: the naive preprocessing manifest fires three major
  leakage findings under the same gate that passes the real one.
- Rival explanations for the headline finding were tested and rejected before it was accepted, and
  the control arm is what turned an anecdote into a measurement.
- Two of the author's own claims were found wrong during preparation and are corrected **in place**,
  with the corrections left visible.
- The reference audit records that a fuzzy bibliographic query returned the wrong paper for two of
  four citations before DOI lookup was used.

## Verdict

**Revise before circulation, not ready to submit.** The three Fatals are answered by narrowing the
claims rather than by new evidence, which is legitimate but leaves the paper smaller than the draft
pretended. **Update 2026-08-01**: M2 has since been closed by running that experiment (rung 3b, one inference
pass, no retraining). M1 and M3 stand as narrowed claims rather than new evidence, which is the
honest position for a single authored worked example.

## R0 pre-submission findings (for `/revise` cross-reference)

```
R0-1 [MAJ] Rung 3 is a constructed stress test, not a discovered failure
R0-2 [MAJ] Causal attribution exceeds the design; no correctly-normalised MRI counterfactual
R0-3 [MAJ] One authored example cannot support general claims about tooling
R0-4 [MAJ] HD95 reported against the Dice denominator
R0-5 [MAJ] Abstract contradicted Table 2 ("60 plausible segmentations")
R0-6 [MAJ] Bootstrap interval depended on arm processing order
R0-7 [MAJ] Delta-Dice quoted without an interval
R0-8 [MAJ] Prospective chronology not auditable from this repository
R0-9  [MIN] Stratum labels vs binning-code closure
R0-10 [MIN] Text/Table 1 disagreement on MRI reference-volume median
R0-11 [MIN] spacing_z is not the through-plane axis for much of the MRI arm
R0-12 [MIN] Missing prediction warned and exited 0
R0-13 [MIN] Runtime numbers have no shipped artifact
R0-14 [MIN] Sparse strata need an exploratory qualifier
R0-15 [MIN] Headline median needed an estimand justification
```
