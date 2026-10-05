# Title & Abstract Writing Guide

Reference for write-paper Phase 6 (Introduction + Abstract) and Phase 1 (Outline).
Loaded on-demand when drafting Title or Abstract.

---

## Title

### Three Title Types

| Type | Characteristics | When to Use |
|------|----------------|-------------|
| **Interrogative** | Poses a question ("Is X better than Y?") | Lower-impact journals; weaker evidence |
| **Descriptive** | States what was studied, includes design | Default choice for most submissions |
| **Declarative** | States the conclusion directly | Only with strong evidence (RCT-level) |

**Default to Descriptive** unless the study has RCT-level evidence (then Declarative is acceptable).

### Required Components (4 elements)

Every title should contain:

1. **Modality**: CT, MRI, ultrasound, radiograph, etc.
2. **Disease/Condition**: HCC, Crohn's disease, lung nodule, etc.
3. **What was evaluated**: Scoring system, revised criteria, AI model, etc.
4. **Purpose/Outcome**: Prediction, identification, comparison, validation, etc.

### Title Rules

- Include the study design (retrospective, prospective, multicenter, etc.)
- Remove filler words ruthlessly — every word must earn its place
- Word limit varies by journal (e.g., Radiology: 15 words)
- Do not use abbreviations in the title unless universally understood (CT, MRI, AI)
- **General-purpose method validated on one task**: lead with the method and its general purpose,
  and put the disease or task in a validation clause — e.g. *"Self-Supervised Motion Correction
  Improves Meniscal Tear Detection on Knee MRI"* → *"Self-Supervised Motion Correction for
  Accelerated MRI: Validation with Meniscal Tear Detection"*. The abstract then opens with the
  general problem the method addresses and states the aim actually performed (develop and validate,
  or validate an existing method). The four components
  still apply (the disease sits in the validation clause); claim no more generality than was
  validated, and keep a disease-first title when the disease, not the method, is the contribution.

### Self-Check

Before finalizing, verify:
- [ ] All 4 components present (modality, disease, what, purpose)?
- [ ] Study design stated?
- [ ] Within journal word limit?
- [ ] No unnecessary filler words?

---

## Title Page — Author & Affiliation Order

Journals — and **every Nature Portfolio / npj technical check** — require the
title-page affiliations to be **numbered in the order the authors first introduce
them**, not grouped by institution. Do **not** hand-number them (an LLM groups by
institution or lets a late author keep a low number, which the technical check
bounces). The rule, stated once:

- **Affiliation 1 belongs to the first author's first affiliation.** Walk the author
  list left to right; each new affiliation gets the next integer the **first** time
  it appears; a repeat of an earlier affiliation reuses its number.
- The affiliation block is then listed in **ascending numeric order** (= first
  appearance), contiguous (1..N, no gaps), every number cited by ≥1 author.
- **Each affiliation ends with its city and country** (e.g. "…, Seoul, Republic of
  Korea").
- Corresponding authors get a `*` (and equal-contribution a `†`) appended to their
  superscript; the footnotes follow the block.

**Generate and verify this deterministically** rather than by hand:

```bash
# build the byline + affiliation block from an ordered authors file
python3 "${CLAUDE_SKILL_DIR}/scripts/build_title_page_affiliations.py" \
  --authors authors.yaml --out manuscript/title_page_affiliations.md

# verify an existing title page before submission (catches out-of-order numbering,
# gaps, undefined/orphan affiliations, and a missing city/country)
python3 "${CLAUDE_SKILL_DIR}/scripts/build_title_page_affiliations.py" \
  --check manuscript/title_page.md --strict
```

`authors.yaml` is an ordered `authors:` list (each with `name`, an ordered
`affiliations:` list of keys, optional `corresponding`/`equal_contribution`) plus an
`affiliations:` dict mapping each key to its full "Department, Institution, City,
Country" text. The script assigns the numbers; you never type a superscript.

---

## Abstract

### Structure

Most journals require a structured abstract: Background, Methods, Results, Conclusion.
Check the journal profile for the exact format (some use Purpose instead of Background,
or combine Background and Purpose).

### Word Limits (common)

| Journal | Limit |
|---------|-------|
| Radiology / KJR | 300 words |
| European Radiology | 250 words |
| European Journal of Radiology | 350 words |

Always check the loaded journal profile for the exact limit. Words left under the limit are not a
target — do not pad toward the cap. Do not state a word count or limit inside the manuscript text
(it belongs in the submission form) unless the journal asks for it there.

### Section-by-Section Rules

#### Background / Purpose

- Start with the specific gap — not a general disease overview
- No "Disease X is a major health concern" openers
- Go directly to what is unknown or insufficient about current methods
- 2-3 sentences maximum

#### Methods

- State: retrospective or prospective, single or multicenter
- Population: who, when (date range)
- Modality and key technical parameters
- Primary outcome and representative statistical method
- 3-5 sentences

#### Results

- Start with final included patient count (must match flowchart)
- Mean age and sex distribution
- Primary outcome with exact value, 95% CI, and p-value
- Key secondary outcomes (1-2 maximum)
- 3-5 sentences

#### Conclusion

- **This is where to invest the most effort** — reviewers and readers read this first
- 1-2 sentences only: state the core finding and its clinical implication
- Do not include limitations or "further studies are needed" (add only if reviewer requests)
- Must be a directly citable statement

### Abstract Self-Check

- [ ] All numbers match main text and tables?
- [ ] Conclusion does not overclaim beyond the evidence?
- [ ] Within word limit?
- [ ] Format matches journal requirements exactly?

---

## Visual Abstract

Many journals now require or encourage visual abstracts. European Radiology mandates them for
all Original Articles from first revision (Jan 2025). Submitting one voluntarily signals effort.

**Generation workflow:**
1. Check the target journal profile for visual abstract requirements and template availability.
2. Extract content: title, Key Point 1 → hypothesis, Key Point 3 → main finding, methodology
   bullets (<6 words each), patient cohort/modality/center badges.
3. Select a visual element: prefer the study's own figures (ROC, flow diagram) over illustrations.
4. Call `/make-figures` with visual abstract request, or run `generate_visual_abstract.py` directly.
5. The script fills a journal-specific PPTX template. If none exists, `medsci_default.pptx` is used.

**Design rules:**
- One page, landscape (16:9), per journal template
- Study question → Key method → Main result structure
- Use study's actual figures, not generic clip-art
- Every visual element must serve a purpose
- See `make-figures/references/medical_illustration_sources.md` for free illustration resources
