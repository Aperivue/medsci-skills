# Acceptance Signals — schema & taxonomy

This reference defines the **acceptance-feasibility** layer that `/find-journal`
adds alongside scope fit. Scope fit answers *"does this journal cover my topic?"*
Acceptance feasibility answers *"can this manuscript's design + importance clear
this journal's bar?"* — the filter editors apply **first** (the #1 desk-rejection
driver is lack of novelty/importance, ahead of scope).

Three pieces live here:
1. the `## Acceptance Signals` block a journal profile may carry,
2. the **selectivity bands** vocabulary (qualitative — never a fabricated %), and
3. the **unfixable-defect taxonomy** the Phase 2.5 pre-flight scans for.

---

## 1. The `## Acceptance Signals` profile block (optional, source-traceable)

A compact or detail profile may add this block. Every line must be **generic and
traceable to the journal's own public guidance** (same bar as the rest of the
profile — see `POLICY.md`). Journal-specific editor behaviour learned from a
private review corpus is **confidential** and belongs ONLY in the user-local
private overlay (`$HOME/.claude/private-journal-profiles/find-journal/`), never in
a public profile.

```
## Acceptance Signals
- **Selectivity band:** highly-selective | selective | accessible | fast-track
- **Desk-reject triggers:** <bullet list of what this journal commonly desk-rejects on,
  from its scope/guidelines — e.g., single-center without external validation;
  case series; out-of-scope clinical specialty>
- **Design expectations:** <sample-size / multi-center / external-validation expectations
  stated or implied by the journal>
- **Study-type tolerance:** <which designs the journal values vs deprioritises>
- **Review process:** <statistical reviewer; double-blind; mandatory reporting guideline;
  presubmission inquiry accepted?>
- **Cascade / transfer:** <same-publisher transfer targets and tier-down fallbacks>
```

All fields are optional; include only what the journal's own pages support. Absence
of the block ≠ "anything goes" — it just means the feasibility axis falls back to
the LLM-applied taxonomy below plus the profile's existing Special Notes.

### Selectivity bands (qualitative — no fake percentages)
There is **no database of journal acceptance rates** (homepage/editor only), and
cached IF/acceptance numbers go stale and are paywalled. So we use bands, not %:

| Band | Meaning |
|------|---------|
| `highly-selective` | flagship/high-impact; desk-rejects most; expects definitive multi-center / external-validation designs |
| `selective` | strong specialty/society journal; expects solid single- or multi-center originals with clear contribution |
| `accessible` | sound-science or broad-scope journal; methodology/incremental work accepted if rigorous and well-reported |
| `fast-track` | rapid / continuous-publication venue; speed-oriented, scientific bar still applies |

---

## 2. Unfixable vs fixable defects (why the ceiling matters)

Across editor decisions the decisive lever is **fixable vs unfixable**:

- **Fixable** (reporting, extraction, measurement, presentation, missing analysis)
  → Major → Minor → Accept trajectory. These do **not** cap the venue tier.
- **Unfixable** (a design-level validity or importance ceiling) → an editor rejects
  even when everything fixable is addressed, and is frequently **more severe than
  the reviewers**. These **cap the venue tier** the design can support.

The pre-flight surfaces unfixable/ceiling signals so the skill stops recommending a
high-impact venue whose bar the design cannot clear, and instead routes to a
tolerant venue or recommends a design change (or a presubmission inquiry).

## 3. Pre-flight taxonomy (what `assess_acceptance_readiness.py` scans)

Four categories. The script does a deterministic lexical scan; the LLM phase
applies the same taxonomy with judgement when only an abstract is available.

- **DESIGN_CEILING** — the design cannot support the claimed altitude:
  cross-sectional vs prognostic/causal/surveillance claim; surrogate/non-invasive
  marker as the sole endpoint; single-center; no external validation for a
  prediction/diagnostic model; pilot/preliminary/proof-of-concept framing.
- **UNFIXABLE_DEFECT** — validity threats editors reject on, not revisable:
  data/information leakage (target-derived, train/test overlap); circular
  design/validation; missing field-standard comparator/baseline;
  single-vendor / single-scanner generalizability ceiling.
- **IMPORTANCE_RISK** — the novelty/importance gate (top desk-reject cause):
  null/negative framing without an importance argument; incremental/marginal gain;
  me-too positioning ("consistent with prior literature").
- **CLAIM_MISMATCH** — an action verb the endpoint may not support
  (recommend / defer / guide management / surveillance / actionable), emitted only
  when the document also carries a design-ceiling signal.

### Verdict bands (from the script + LLM judgement)
- `NO STRUCTURAL CEILING DETECTED BY LEXICAL SCAN` → feasibility does not cap tier.
- `IMPORTANCE-FRAMING REVIEW RECOMMENDED` → tighten the contribution/novelty argument.
- `SPECIALTY / TOLERANT-VENUE OR DESIGN FIX RECOMMENDED` → one ceiling/claim signal.
- `HIGH-IMPACT VENUE UNLIKELY WITHOUT A DESIGN CHANGE` → unfixable defect, or ≥2
  design-ceiling signals.

---

## 4. How the two axes combine (Phase 3 ranking)

For each candidate journal report **two independent axes**:

- **Scope fit** (existing composite: scope 40 / study-type 25 / tier 20 / OA 10 / special 5).
- **Acceptance feasibility** = the manuscript's ceiling verdict weighed against the
  journal's Acceptance Signals (selectivity band + desk-reject triggers + design
  expectations).

Rules of thumb:
- Rank primarily by **scope fit**, but **demote or annotate** any journal where
  feasibility is Low / ceiling-mismatch.
- Always **surface the mismatch explicitly** — e.g., *"scope fit High, but
  feasibility Low: this `highly-selective` venue desk-rejects single-center
  surrogate-endpoint designs; consider a `selective`/`accessible` venue or add
  external validation."* A silent demotion teaches the author nothing.
- Output is a **risk/feasibility band with reasons, never an acceptance
  probability** — ML acceptance predictors cap well below certainty and ride
  surface features, so a number here would be false precision.

## 5. Confidentiality

Public Acceptance-Signals lines must be generic and traceable to the journal's own
public guidance. Specific editor-decision patterns learned from confidential peer
review (COPE) are abstracted and kept in the **private overlay only**. The private
tier wins on filename collision, so a user's local profile can enrich any public
profile with their own corresponding-author editor-bar notes without those notes
ever entering the shared library.
