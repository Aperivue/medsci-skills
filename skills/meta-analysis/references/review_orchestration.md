# Peer Review Orchestration (3-tier)

**Extends**: the existing `phase9_circulation.md` (circulation email template). This document covers the full internal → external → journal three-round orchestration.

## 3-tier structure

| Tier | Reviewer | Output | Blocking point |
|---|---|---|---|
| 1. Internal | Clinical PI (second dual rater) + methodology lead | dual-rating consensus, QUADAS-2 domain table | PI availability |
| 2. External | Adversarial GPT review + independent peer (optional) | critique memo, defensive-tone audit | — |
| 3. Journal | Editorial + peer reviewers | reject/revise/accept, Response matrix | — |

## Core rules

### RO-1. Dual-rating work ships as a trio: "figure + per-study table + supplementary", together
- **Problem pattern**: A QUADAS-2 traffic-light figure ships without an accompanying per-study domain table → PRISMA-DTA Item 19 remains PARTIAL. The supplementary table must be planned alongside the figure, not added one revision later.
- **Rule**: Plan dual-rating outputs such as QUADAS-2 / RoB2 / GRADE as a three-part set at the design stage. A figure alone does not complete PRISMA-DTA Item 19.

### RO-2. Secure the "second-reviewer lead time" before sending the circulation package
- **Problem pattern**: Manuscript circulated after only first-reviewer screening → the second-reviewer dual rating then blocks the entire revision cycle for weeks, leaving PRISMA Item 9 PARTIAL.
- **Rule**: Confirm the clinical PI's second-rating availability window before writing the circulation email. Put blocking items as a bullet at the very top of the email body. Add a "PI availability window" field to the circulation template.

### RO-3. External review specializes in "defensive tone / bias-inflation / upper-bound framing"
- **Problem pattern**: External adversarial review surfaces over-defensive Methods prose (multi-paragraph justifications for pre-specified protocol deviations) and flags that a homogeneity statistic (e.g., Sp I²=0%) is driven by universalized bias rather than true between-study agreement.
- **Rule**: Include in the external adversarial-review prompt: (a) a defensive-tone audit (check that protocol-deviation explanations in Methods are ≤3 sentences), (b) a bias-driven homogeneity interpretation check, and (c) an upper-bound/lower-bound framing check. Offload detailed rationale to the Supplement.

### RO-4. The Response matrix tracks reviewer reply + manuscript edit + supplement together
- **Problem pattern**: During revision, a numeric value (e.g., a subgroup p-value) changes between versions with no before/after diff recorded in the Response matrix → the reviewer's re-review cannot verify the update.
- **Rule**: For each comment row in the Response matrix, record (a) the reviewer's original text, (b) a response summary, (c) the manuscript edit locator (section/line), and (d) whether a number changed, tagged `[VERIFY-CSV]`. Remove all tags on submission day.

### RO-5. Consolidate protocol deviations into a single PROSPERO amendment
- **Problem pattern**: Analysis-framework deviation, subgroup deviation, and search-amendment notes split across three manuscript sections and three separate tracker files → the PROSPERO amendment loses provenance.
- **Rule**: One file at the project root, `protocol_deviations_tracker.md`. Bundle them under one ID when submitting the PROSPERO amendment. Use a single citation in the manuscript too.

## Templates

- Circulation email: see the existing `phase9_circulation.md`. Per RO-2 of this document, propose adding a "PI availability window" field.
- Internal peer review memo: `internal_peer_review_MA{n}_v{N}_{date}.md`
- External GPT review memo: `external_review_gpt_MA{n}_{date}.md`
- Response matrix: the existing `/revise` skill template. Per RO-4, add a `[VERIFY-CSV]` field.
