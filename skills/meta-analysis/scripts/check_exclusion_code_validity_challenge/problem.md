# Challenge — exclusion-code validity vs registered eligibility

## The defect this gate catches

A screening sheet can be internally perfect — two reviewers agree, Cohen's kappa
is high, every PRISMA count reconciles — and still delete eligible studies in
bulk, because the *exclusion code itself* is wrong. The code excludes a study
design the registered protocol explicitly **includes**. No consistency,
arithmetic, or inter-rater gate can see this: they all operate on the cells, and
the defect is in the legend, above the cells.

Real instance: a protocol admitted single-arm case series, but three studies were
removed under a "not comparative" code. The code was applied consistently and the
sheet was coherent; the code should not have existed.

## Fixtures

**Positive** (`protocol_positive.md` + `screening_positive.tsv`): the protocol
admits single-arm / non-comparative designs, yet the screening applies

  - `F2` "single-arm / no comparator" — excludes an **eligible** design
    → `CODE_CONTRADICTS_ELIGIBILITY` (Major, the study-loss defect);
  - `F9` — a code **absent from the registered legend**
    → `CODE_NOT_REGISTERED` (Major);
  - `F3` — registered as "Full-text unavailable" but applied as "Overlapping
    cohort", the same number meaning two things
    → `CODE_RENUMBERED` (Minor, a documentation defect at a lower severity).

  Valid codes (`F1` = duplicate) fire nothing. Exit 1 under `--strict`.

**Negative** (`protocol_negative.md` + `screening_negative.tsv`): the protocol
**requires** a comparator and excludes single-arm studies. The very same "no
comparative data" code (`F2`) is now correct — it excludes a design the protocol
excludes — and every code is registered and consistent. Zero verdicts, exit 0.

The discrimination between the two fixtures is the whole point: an exclusion
reason contradicts eligibility only when the protocol's own **non-negated**
eligibility text names the excluded design as eligible.

## Verify

`bash verify.sh` — deterministic, network-free. Runs the detector on both
fixtures and asserts the three positive verdicts (exit 1) and a clean negative
(exit 0).
