# Discussion structure — AI/ML model development + validation (TRIPOD+AI / CLAIM)

A structure model for the Discussion of a clinical AI/ML model study, completing the trio
with the `exemplar_methods/` and `exemplar_results/` siblings. Each heading is a paragraph;
each bullet is *what it must establish*. Fill the `[brackets]`; do not copy this text.
Follows `section_guides/discussion.md`. Introduces **no new results**, cites **no
tables/figures**, and the claim must not exceed the validation evidence.

## Paragraph 1 — Key finding and why it matters
- Restate the primary discrimination (and that it held on the external set), plus calibration
  in one phrase — not a single best number.
- One sentence on the decision the model could support, hedged to the evidence level.

## Paragraphs 2–3 — Interpretation and comparison
- Compare to existing models / current practice: what the model adds (e.g., extends to a
  group current criteria exclude), and frame it as **complementary, not a replacement** for
  the clinician or standard pathway.
- Biological / clinical plausibility for why the inputs carry signal (named mechanism), so
  the model is not a black box asserted to work.
- Separate the **evidence tiers** explicitly: a retrospective validation shows discrimination;
  decision-impact and outcome benefit require prospective / trial evidence — and say which is
  and is not yet available.

## Limitations
- Name **overfitting / optimistic validation** candidly (any test-set leakage, internal-only
  validation, thin subgroups), **calibration** limits, single-site/scanner data, and the
  absence of prospective or decision-curve evidence if a use claim is made.

## Generalizability and future work
- Where the model would and would not transfer (sites, scanners, demographics); the
  prospective/external validation and, ultimately, the trial needed before deployment.

## Conclusion
- Matched to the evidence — "may support / warrants prospective evaluation", never "ready for
  clinical deployment" or "outperforms clinicians" unless a same-task, difference-tested,
  prospective comparison supports it.

## Common omission
- An explicit **evidence-tier separation** (discrimination ≠ clinical benefit) and a candid
  **optimism/calibration** caveat — the Discussion elements AI drafts most often skip, and the
  gateway to deployment over-reach. Cross-reference `section_guides/discussion.md`, the AO5
  probe and `peer-review/references/exemplar_reviews/optimistic_validation_reporting.md`, and
  the TRIPOD+AI / CLAIM critical items in
  `peer-review/references/reviewer_calibration/compliance_floor.md`.
