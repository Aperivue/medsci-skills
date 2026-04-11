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

### Self-Check

Before finalizing, verify:
- [ ] All 4 components present (modality, disease, what, purpose)?
- [ ] Study design stated?
- [ ] Within journal word limit?
- [ ] No unnecessary filler words?

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

Always check the loaded journal profile for the exact limit.

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
