---
name: present-paper
description: >
  Academic paper presentation preparation. Analyzes a research paper, finds supporting references,
  drafts audience-adapted speaker scripts, injects speaker notes into slides, and prepares Q&A.
  Supports journal clubs, grand rounds, seminar presentations, and coursework presentations.
  Triggers: present paper, paper presentation, journal club, seminar presentation, grand rounds,
  academic presentation, presentation prep
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Present-Paper Skill

## Purpose

Prepare a polished academic presentation from a research paper. The skill walks through a 5-phase
pipeline: paper analysis, supporting research, script writing, slide note injection, and Q&A
preparation.

Use it when:

- preparing a journal club or seminar presentation
- presenting a paper for a graduate course
- preparing grand rounds or conference talks based on a published paper
- building speaker notes for an existing slide deck

---

## Communication Rules

- Communicate with the user in their preferred language.
- Use English for medical, statistical, and methodological terminology.
- Add pronunciation guides for drug names and technical abbreviations in the user's language.
- Be direct about paper limitations, but frame them constructively.

---

## Phase 0: Init & Outline

### Required Inputs

Before starting, collect these from the user:

| Input | Why |
|-------|-----|
| **Paper** | PDF path, DOI, or PMID |
| **Presentation time** | Determines depth and slide count |
| **Target audience** | Specialty mix, knowledge level — controls terminology depth |
| **Context** | Course name, conference, journal club format, prior session topics |
| **Extension section** | Optional topic to include (e.g., AI directions, clinical implications). Default: none |

### Paper Analysis

Read the paper and produce a structured analysis:

```text
## Paper Analysis

### Citation
[Full citation with DOI]

### Background
- What gap does this paper address?
- What was known vs. unknown before this study?

### Study Design
- Type: [RCT / cohort / case series / meta-analysis / etc.]
- Subjects: [n, inclusion/exclusion]
- Methods: [key methodological choices]
- Primary outcome: [what was measured]

### Key Results
1. [Finding 1 with effect size and CI/p-value]
2. [Finding 2]
3. [Finding 3]

### Patient/Case Summary Table
[If applicable — structured table of individual cases or subgroups]

### Limitations
1. [Limitation 1]
2. [Limitation 2]

### Significance
- Why does this matter?
- What changes because of this paper?
```

### Slide Outline

Create a slide-by-slide outline with time allocation:

```text
## Slide Outline ([N] slides, [M] minutes)

| # | Title | Time | Key Content |
|---|-------|------|-------------|
| 1 | Title slide | 0:30 | Paper citation, presenter |
| 2 | Context / Prior sessions | 1:00 | How this connects to prior knowledge |
| 3 | Background | 1:30 | The gap this paper fills |
| ... | ... | ... | ... |
| N | Take-home messages | 0:30 | 3-5 key points |
```

**Gate: User approves outline before proceeding.**

---

## Phase 1: Supporting Research

### Search Strategy

Find references that strengthen the presentation:

1. **Follow-up studies** — Has the main finding been replicated or extended?
2. **Clinical trial data** — Large-scale data that contextualizes the findings
3. **Review articles** — Authoritative summaries that frame the topic
4. **Contradicting evidence** — Important for balanced Q&A preparation

### Selection Criteria

Do NOT summarize every paper found. Extract only:

- Specific data points needed for slides (incidence rates, OR/HR, AUC values)
- Findings that directly support or challenge the main paper
- Context that helps the audience understand significance

### Output

```text
## Verified References

### Main Paper
1. [Citation] — PMID: XXXXX, DOI: XX.XXXX/XXXXX

### Supporting References
2. [Citation] — PMID: XXXXX
   → Used for: [specific data point or context]
3. [Citation] — PMID: XXXXX
   → Used for: [specific data point or context]

### Key Data for Slides
- [Statistic 1]: [value] — Source: [Ref #]
- [Statistic 2]: [value] — Source: [Ref #]
```

**Every reference must have a verified DOI or PMID. Mark unverified references with [UNVERIFIED].**

---

## Phase 2: Script & Content

### Speaker Script

Draft a complete speaker script with these requirements:

1. **Language**: User's preferred language for narration; English for technical terms
2. **Audience adaptation**: Adjust explanation depth based on Phase 0 audience profile
   - For mixed audiences: add one-line plain-language explanations for specialty-specific terms
   - Example: "FLAIR sequence — an MRI technique that suppresses fluid signal to highlight edema"
3. **Pronunciation guide**: Include native-language pronunciation for drug names, abbreviations
   - Example: "lecanemab (leh-KAN-eh-mab)" or local equivalent
4. **Timing markers**: Note approximate time per slide
5. **Transition phrases**: Connect each slide to the narrative arc

### Structure

```text
## Speaker Script

### Slide 1: Title (0:30)
"[Opening — introduce yourself and the paper]"

### Slide 2: Context (1:00)
"[Connect to prior knowledge or clinical relevance]"

...

### Slide N: Take-home Messages (0:30)
"[Summarize 3-5 key points. Thank audience. Invite questions.]"
```

### Extension Section (Optional)

Only include if user requested in Phase 0. Examples:

- AI/computational research directions stemming from the paper
- Clinical practice implications
- Policy or guideline implications
- Connections to the user's own research

**Gate: User reviews script before proceeding.**

---

## Phase 3: Slides & Notes

### Two Modes

**Mode A: Generate new slides**
- Create slide content (text, tables, diagrams) as Markdown or PPTX
- Follow presentation design principles: one idea per slide, visual elements on every slide

**Mode B: Add notes to existing slides** (more common)
- Read existing PPTX to understand slide structure and count
- Map speaker script sections to corresponding slides
- Generate `inject_notes.py` script tailored to the specific presentation

### Note Injection Script

Generate a Python script using `python-pptx` that:

```python
#!/usr/bin/env python3
"""Inject speaker notes into presentation slides."""

import argparse
from pptx import Presentation

notes = {
    1: """[Speaker note for slide 1]""",
    2: """[Speaker note for slide 2]""",
    # ...
}

def main():
    parser = argparse.ArgumentParser(description='Inject speaker notes into PPTX')
    parser.add_argument('input', help='Input PPTX file')
    parser.add_argument('-o', '--output', help='Output PPTX file (default: input with _notes suffix)')
    parser.add_argument('--append', action='store_true', help='Append to existing notes instead of replacing')
    args = parser.parse_args()

    output = args.output or args.input.replace('.pptx', '_notes.pptx')
    prs = Presentation(args.input)

    for i, slide in enumerate(prs.slides, 1):
        if i in notes and notes[i]:
            if not slide.has_notes_slide:
                slide.notes_slide
            tf = slide.notes_slide.notes_text_frame
            if args.append and tf.text.strip():
                tf.text = tf.text + '\n\n---\n\n' + notes[i]
            else:
                tf.text = notes[i]

    prs.save(output)
    print(f'Done: {output} ({len(prs.slides)} slides)')

if __name__ == '__main__':
    main()
```

### Critical Rule

**Speaker notes are injected without modifying slide design, layout, text, or images.**
The script only touches the notes pane. Verify by comparing slide content before and after.

---

## Phase 4: Q&A Preparation

### Question Generation

Generate questions from multiple perspectives:

1. **Methodology critics**: "Why this design? Why not...?"
2. **Domain experts**: Deep technical questions about the specific field
3. **Generalists**: "What does this mean for clinical practice?"
4. **Students/trainees**: Clarification questions about unfamiliar concepts

### Answer Structure

Every answer should follow the pattern:

```
Acknowledge → Evidence → Conclude

"That's an important limitation. [Acknowledge the concern honestly.]
However, [cite specific supporting evidence — author, year, finding].
So while [restate limitation], [conclude with the paper's contribution despite it]."
```

### Quick Review Sheet

A single-page reference for last-minute review:

```text
## Quick Review

### Must-Know Numbers
| Metric | Value | Source |
|--------|-------|--------|
| [Key stat 1] | [value] | [Ref] |
| [Key stat 2] | [value] | [Ref] |

### Common Pitfalls
- Don't confuse [X] with [Y]
- [Classification A] and [Classification B] are independent frameworks
- Slide says [rounded value], precise value is [exact value]

### Key Takeaways (memorize these)
1. [Point 1]
2. [Point 2]
3. [Point 3]
```

---

## Output File Structure

All outputs go in the user's presentation directory:

```
{presentation_dir}/
├── _analysis.md              # Phase 0: Paper analysis + outline
├── _references.md            # Phase 1: Verified references + key data
├── _script.md                # Phase 2: Speaker script
├── _qa_prep.md               # Phase 4: Expected Q&A
├── _quick_review.md          # Phase 4: Pre-presentation review sheet
├── inject_notes.py           # Phase 3: Tailored note injection script
├── figures/                  # Extracted paper figures (if needed)
└── reference/                # Supporting paper PDFs (if downloaded)
```

---

## Constraints

- **Never fabricate references.** Every citation must be verified against PubMed, DOI, or the PDF itself.
- **Never modify slide design** when injecting notes. Notes and slides are separate concerns.
- **Always ask audience first.** Do not start drafting until the target audience is defined.
- **Extension sections are opt-in.** Do not add AI/clinical/policy sections unless explicitly requested.
- **Respect presentation time.** Script length must match allocated time (roughly 130-150 words per minute for academic presentations).
