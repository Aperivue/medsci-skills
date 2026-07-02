# Results structure — randomized controlled trial (CONSORT 2010)

A structure model for the Results of a parallel-group RCT. It follows its Methods CONSORT
sibling in Methods order. Each heading is a paragraph; each bullet is *what it must establish*.
Fill the `[brackets]`; do not copy this text. Report findings only — no interpretation.

## Participant flow (Figure 1 — CONSORT diagram)
- The CONSORT flow: assessed → randomized → allocated (received / did not receive) → followed up
  (lost, discontinued, with reasons) → analyzed, **per arm**, with counts.
- The cascade reconciles (randomized = Σ analyzed + Σ excluded-with-reason); the number
  **analyzed for the primary outcome** matches the ITT denominator. Numbers match the Abstract,
  Methods, and Table 1.

## Recruitment and baseline (Table 1)
- Recruitment and follow-up dates and why the trial ended (target reached / stopped);
  Table 1 baseline characteristics **by arm** — **no p-values for baseline balance** (randomization
  makes them meaningless; show the descriptive comparison and, if used, the balance metric).

## Primary outcome
- The pre-specified **primary** outcome by arm: the **effect estimate with its 95% CI** and the
  absolute numbers per arm (events/N or mean±SD), on the **ITT** population — not just a p-value.
- For non-inferiority: the CI relative to the **pre-stated margin** (the conclusion follows from
  where the CI sits, not from a significance test).

## Secondary outcomes and harms
- Secondary outcomes with estimates + CIs, flagged as secondary (multiplicity in view — do not
  elevate a significant secondary to a headline).
- **Harms / adverse events** reported per arm (a trial that reports only efficacy is incomplete).

## Subgroups and sensitivity
- Pre-specified subgroup analyses with the **interaction test**, framed as exploratory; the
  per-protocol analysis beside ITT (concordance is reassuring; divergence is discussed, not hidden).

## Common omission
- **Baseline p-values** (should not appear), and the **primary reported off the per-protocol set**
  rather than ITT, or without its absolute per-arm numbers — the Results elements RCT drafts most
  often get wrong. Cross-reference `section_guides/results.md`, the
  `peer-review/references/domain-probes/rct_trial.md` probes, and the CONSORT flow requirement.
