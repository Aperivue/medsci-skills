---
name: review-paper
description: >
  Scaffold and draft medical/AI literature reviews (narrative, scoping PRISMA-ScR, or systematic). Asks for
  the spine axis, builds a 7-part skeleton with a required Intro scope/non-overlap block, a summary-table stub,
  an evaluation-metrics critique subsection, and reporting-guideline wiring. Reuses the self-review RV1-RV9
  narrative-review probes for QC. Does not invent citations.
triggers: review article, scoping review, narrative review, literature review, PRISMA-ScR, write a review
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Review-Paper Skill

Scaffold and draft a **literature review** — narrative, scoping (PRISMA-ScR), or systematic
(PRISMA 2020) — for medical / medical-AI research. This skill builds the structure, the
required scope/non-overlap framing, the summary-table stubs, and the reporting-guideline
wiring, then hands off to the existing QC skills. It is the review-article counterpart to
`write-paper` (which targets original research); for *reviewing* someone else's review
article, use `/peer-review` or `/self-review` (the RV1-RV9 probes). The structure follows
established review-writing conventions; it is not derived from, and does not reproduce, any
specific published review.

## Anti-Hallucination

- **Never invent citations.** Every citekey must resolve to the project's verified
  `_src/refs.bib` (produced by `/search-lit` → `/lit-sync` → `/verify-refs`). If a claim
  needs a reference that is not yet in the library, leave a `[NEEDS-REF: claim]` marker and
  route it to `/search-lit`; do not fabricate a DOI, author, year, or citekey.
- **Never invent data.** Summary-table cells (study, year, metric, finding) are filled only
  from sources the user supplies or that are verified; an unknown cell stays a placeholder.
- **No recommendation-grade language without standing.** For a scoping review especially,
  the output maps the evidence — it does not issue clinical recommendations.
- **Quality gate before hand-off:** the draft is not "done" until `/self-review` reports 0
  fatal findings and `/verify-refs` reports 0 FABRICATED / MISMATCH and no placeholder
  citations remain.

## Step 0 — Format + spine axis (the structure-determining choice)

1. Confirm **format** with the user: narrative (SANRA) | scoping (PRISMA-ScR + JBI) |
   systematic (PRISMA 2020). This decides the reporting guideline and the registration path.
2. Choose the **spine axis** — the single most consequential decision: organize the body by
   **modality** (e.g. 2D → 3D), by **task** (generation / QA / deployment), or by
   **lifecycle stage**. Every body section then follows this one axis; mixing axes is the
   most common structural failure.
3. Require a **scope statement + non-overlap boundary** against prior/adjacent reviews — this
   pre-empts the reviewer's first question, "why another review on this?" (user-approval
   checkpoint: confirm the boundary with the user before scaffolding).

## Step 1 — Scaffold the 7-part macro skeleton

Load `${CLAUDE_SKILL_DIR}/references/macro_skeleton.md` and instantiate:

1. **Abstract** — structured for scoping/systematic; a 4-5 move version for narrative.
2. **Introduction** — clinical motivation → technology → **scope + non-overlap block
   (required field)** → "this review…".
3. **Background / technical principles** — tight; cite once, do not re-survey the field.
4. **Thematic body by spine axis** — each section ends with a **summary table** (stub
   generated to match the type, Step 2).
5. **Frontiers / what is advancing.**
6. **Challenges / discussion** — include an **evaluation-metrics critique subsection** (a
   required quality signal: how the field measures itself, and where those metrics mislead).
7. **Conclusion** — measured; no recommendation-grade language for a scoping review.

## Step 2 — Summary-table stub (matched to type)

- Narrative / scoping: `study | year | [spine-axis value] | method | key finding`.
- Systematic: PRISMA flow + a study-characteristics table + an extraction table.

The stub ships with column headers and one placeholder row; rows are filled only from
verified sources (see Anti-Hallucination).

## Step 3 — Reporting + registration wiring

- **Scoping** → PRISMA-ScR (+ JBI charting) + OSF registration.
- **Narrative** → SANRA (a 6-item appraisal aid, not a reporting checklist — do not
  over-enforce it).
- **Systematic** → PRISMA 2020 (+ PROSPERO registration).
- If `/check-reporting` does not yet carry the chosen checklist (e.g. PRISMA-ScR), track a
  manual gap table and flag it for the user rather than silently skipping the item.

## Step 4 — QC hand-off

Run the standard manuscript QC chain, which this skill is designed to feed:

1. `/self-review` — the RV1-RV9 narrative-review probes auto-activate for a review article.
2. `/check-reporting` — the chosen guideline (SANRA / PRISMA-ScR / PRISMA 2020).
3. `/verify-refs` — every citation resolves; 0 FABRICATED / MISMATCH.
4. `/humanize` — AI-pattern density below threshold.
5. `/academic-aio` — discoverability pass (optional).

**Convergence gate:** self-review fatal = 0; verify-refs FABRICATED/MISMATCH = 0; no
`[NEEDS-REF]` / `[@NEW:]`-style placeholder citations remain; humanize density < 2.0.

## Guards

- Citations resolve to `_src/refs.bib` only; never invent citekeys (see Anti-Hallucination).
- Proportionate self-citation; declare an intellectual conflict of interest when an author
  has contributed to the area being reviewed (per `intellectual-coi`).
- Write only inside the manuscript directory.

## references/

- `macro_skeleton.md` — the 7-part template and the table/figure plan per review type.
