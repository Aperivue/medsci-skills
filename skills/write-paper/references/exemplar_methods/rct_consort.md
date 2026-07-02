# Methods structure — randomized controlled trial (CONSORT 2010)

A structure model for a parallel-group RCT. Each heading is a paragraph; each bullet is *what it
must establish*. Fill the `[brackets]`; do not copy this text. Anchors to CONSORT 2010; pairs the
`peer-review/references/domain-probes/rct_trial.md` probes (and CONSORT-AI/SPIRIT-AI for an AI
intervention).

## Trial design and registration
- Design (parallel-group / crossover / cluster), allocation ratio (e.g. 1:1), and framework
  (superiority / non-inferiority / equivalence) — with the **margin** stated up front for the
  latter two.
- **Prospective trial registration** (ClinicalTrials.gov / a WHO ICTRP registry) with the number,
  and the protocol reference; ethics approval and informed consent.

## Participants, setting, interventions
- Eligibility as a numbered inclusion / exclusion list; the settings and the recruitment and
  follow-up dates.
- The experimental and comparator interventions in enough detail to replicate (dose, schedule,
  who delivered them); the comparator is a real, defined control (placebo / standard-of-care),
  not a strawman.

## Outcomes
- The **single pre-specified primary outcome** with its metric and time point (do not re-designate
  the primary after seeing data); secondary outcomes listed; any changes to outcomes after trial
  commencement disclosed with dates.

## Sample size
- The power calculation: assumed effect (the MCID, not the hoped-for effect), α, power, and the
  resulting N with attrition inflation; for non-inferiority, the margin and its justification.

## Randomization, allocation concealment, blinding
- **Sequence generation** (how the random sequence was produced), **allocation concealment**
  (the mechanism that hid the next assignment — central/pharmacy/sealed opaque envelopes), and
  **implementation** (who enrolled, who assigned) — three distinct items, all required.
- **Blinding**: who was blinded (participants, clinicians, outcome assessors, analysts) and how;
  if open-label, state it and how assessor blinding was preserved.

## Statistical methods
- The primary analysis and estimand: the contrast, the population (**intention-to-treat** as
  primary — everyone as randomized; per-protocol as a secondary, and the primary population for a
  non-inferiority trial stated), and how missing data were handled (not naive complete-case for a
  dropout-prone endpoint).
- Pre-specified subgroups and interim analyses / stopping rules; multiplicity handling; software.

## Reporting-guideline fit
- CONSORT 2010 (+ CONSORT-AI for an AI intervention). Critical items: registration, sequence
  generation + allocation concealment + blinding, the pre-specified primary, ITT, and a
  participant flow diagram that reconciles (randomized → received → analyzed).

## Common omission
- **Allocation concealment described as blinding** (they are different — concealment protects
  *assignment*, blinding protects *ascertainment*), and an unstated **ITT vs per-protocol**
  primary population — the Methods elements RCT drafts most often conflate or skip, and the first
  a trials reviewer checks. Cross-reference `section_guides/methods.md` and the
  `peer-review/references/domain-probes/rct_trial.md` probes.
