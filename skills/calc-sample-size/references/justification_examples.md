# Sample-size justification — worked prose exemplars (IRB / Methods)

Reviewer-safe **justification paragraphs** for the prospective designs this skill computes,
complementing `formulas.md` (the math); the retrospective/experience-based templates (SKILL.md
Phase 2b) are at the end of this file. Each exemplar shows the same five elements a methods
reviewer or IRB looks for; fill the `[brackets]` from the actual calculation — never invent the
inputs. These are synthetic
teaching models of *standard* justification structure, not copied text.

## The five elements (every justification states all five)
1. The **primary outcome** and its effect/precision target (with the **source** of the assumed
   value — prior study, pilot, or a minimal clinically important difference, cited).
2. **α** (and one- vs two-sided) and **power** (or the target CI half-width for a precision aim).
3. The **test/method** the calculation matches (it must match the planned primary analysis).
4. The resulting **n**, including any **inflation** for attrition/clustering/multiplicity.
5. The **software/approach** used (named, so it is reproducible).

## Exemplars by design

**Two proportions (superiority).** "Assuming an event rate of `[p1]` in the control arm
(from `[cited source]`) and a clinically meaningful absolute reduction to `[p2]`, a two-sided
α = 0.05 and 80% power require `[n/arm]` per arm (two-proportion test). Allowing for `[d]%`
attrition, we will enrol `[N]`."

**Two means (superiority).** "To detect a between-group difference of `[Δ]` in `[outcome]`
(SD `[s]`, from `[source]`; standardised effect `[d]`) with two-sided α = 0.05 and 90% power
requires `[n/arm]` per arm (two-sample t-test)."

**Diagnostic accuracy (precision aim).** "To estimate sensitivity with a 95% CI half-width of
`[w]`, assuming sensitivity `[Se]` and disease prevalence `[π]`, `[N_total]` participants
(`[N_diseased]` with the target condition) are needed; the **specificity** target is checked
separately from the non-diseased count `[N_nondiseased]` and is satisfied at this n. The aim is
**precision, not power** — no comparison hypothesis is tested." (Cite Hajian-Tilaki / Buderer.)

**Survival (log-rank).** "To detect a hazard ratio of `[HR]` (median `[m1]` vs `[m2]`) with
two-sided α = 0.05 and 80% power and `[1:1]` allocation, `[E]` events are required (Schoenfeld,
1983); with uniform accrual over `[a]`, a minimum follow-up of `[f]` and `[d]%` loss to follow-up per
year, this needs `[N]` participants. The **event count**, not N, drives power."

**Agreement / reliability (ICC).** "Assuming a true ICC of `[ρ]` with `[k]` raters per subject,
`[n]` subjects give a 95% CI width of `[w]` (a **precision** aim, Bonett 2002) —
*or*, framed as a **test**, `[n]` subjects give `[power]`% power to show the ICC exceeds the minimally
acceptable `[ρ0]` at one-sided α `[α]` (Walter, Eliasziw & Donner 1998). State which of the two aims
you used; the two give different n."

**Non-inferiority.** "With a non-inferiority margin of `[m]` (justified clinically and by
`[regulatory/prior]` precedent), assuming no true difference (or a true difference of `[Δ]` in
favour of the new method) and a control rate `[p]`, one-sided α = 0.025 and 90% power require
`[n/arm]` per arm. The margin and its rationale are pre-specified."

## Discipline
- The calculation must match the **planned primary analysis** (do not power for a t-test and
  analyse with a mixed model); state any clustering (design effect) or multiplicity adjustment.
- For a **precision** aim (DTA, agreement, single-arm), report the **CI half-width**, not power —
  do not invent a comparison hypothesis to manufacture a power statement.
- Never reverse-engineer the effect size from an achievable n (post-hoc justification); the
  assumed effect comes from a cited source or an MCID. Post-hoc/observed power is uninformative.

## Retrospective / experience-based (SKILL.md Phase 2b)

**Institution volume-based** (`exams in period × prevalence × (1 − exclusion rate) = expected N`):
> Based on approximately [X] [modality] examinations performed annually at [institution],
> and an estimated prevalence of [condition] of [Y]%, we anticipate identifying approximately
> [N] eligible patients over the [Z]-year study period. After accounting for an estimated
> [W]% exclusion rate (due to [reasons]), we expect a final sample of approximately [N_adj]
> patients for analysis.

**Prior study-based** (3–5 comparable published studies, cited):
> Previous studies evaluating [similar topic] with [similar design] enrolled [N1] (Author1
> et al., Year), [N2] (Author2 et al., Year), and [N3] (Author3 et al., Year) patients.
> Our anticipated sample of [N] patients is [comparable to / larger than] these prior studies.
