---
name: intake-project
description: >
  Intake and normalize a new radiology research project. Classifies project type, summarizes current state,
  identifies missing inputs, recommends next steps, and scaffolds lightweight project memory files.
triggers: new project, intake project, project intake, classify project, organize project, what is this project
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Intake-Project Skill

## Purpose

This skill is the front door for a new or messy project. It converts a folder, document bundle, or mixed set of notes into a structured project state that other skills can use safely.

Use this skill when:
- a new paper or proposal folder has been created
- an older folder exists but is poorly organized
- the user asks "what is this project and what should I do next?"
- another skill needs a reliable project summary before proceeding

---

## Communication Rules

- Communicate with the user in their preferred language.
- Keep project labels and file names in the language already used by the workspace.
- Use English for manuscript section names, study design names, and medical/statistical terminology.

---

## Inputs

Accept any of the following:
- a project folder
- a manuscript draft
- an abstract or proposal
- tables/figures plus notes
- a mixed folder with PDFs, drafts, and analyses

If information is incomplete, infer cautiously from file names and contents, then label uncertain items clearly.

---

## Core Tasks

### 1. Project classification

Determine:
- project type: `original | review | meta-analysis | case report | technical note | grant | peer review | challenge | career-doc`
- primary domain: `radiology | medical AI | multimodal LLM | intervention | survival/prognostic | diagnostic accuracy | workflow`
- target output: `paper | abstract | grant | review | rebuttal | CV`
- likely target journal or venue, if recoverable

### 2. State reconstruction

Identify:
- what already exists
- what is missing
- current phase
- blocking dependencies

### 3. Project memory scaffold

If missing, propose or create lightweight anchor files:
- `PROJECT.md`
- `STATUS.md`
- `CLAIMS.md`
- `DATA_DICTIONARY.md`
- `ANALYSIS_PLAN.md`
- `REVIEW_LOG.md`

Create only files that are justified by the project type.

### 4. Action plan

Produce the next 3-5 actions in dependency order.

---

## Canonical Manuscript Folder Structure

For any manuscript project (cohort, MA, RCT, case series), enforce this structure when scaffolding or reorganizing. Map every new artifact into one of these slots — do not invent ad-hoc folders.

```
{project_root}/
├── HANDOFF.md                         # session handoff entry point
├── README.md                          # project overview
├── data/                              # raw data (NEVER edit; read-only)
├── analysis/                          # reproducible scripts (00_* → 04_*)
├── output/                            # analysis outputs: CSVs, PNGs, intermediates
├── irb/                               # IRB/ethics docs
├── proposal/                          # original protocol / approved proposal
├── reviews/                           # external correspondence
├── manuscript/                        # SOURCE manuscript + drafting
│   ├── manuscript_v{N}.{md,docx,pdf}  # current canonical working version (top level)
│   ├── build_unified_docx.py          # or pandoc wrapper
│   ├── archive/                       # ALL prior versions v1 .. v{N-1}
│   ├── reviews/                       # QC: self_review, peer_review, STROBE/PRISMA, critic
│   ├── figures/                       # figure scripts + rendered PNG/PDF
│   └── tables/                        # table scripts + rendered docx
└── submission/                        # per-journal packages
    └── {journal-slug}/                # e.g., chest/, kjr/
        ├── CHECKLIST.md
        ├── cover_letter.{md,docx,pdf}
        ├── title_page.docx            # separated for double-anonymized
        ├── manuscript_anonymized.{docx,pdf}
        ├── supplement.{docx,pdf}
        ├── strobe_checklist.md        # or PRISMA / CONSORT
        ├── circulation_email.md
        └── figures/                   # submission-ready DPI copies
```

### Rules

- **`manuscript/` = source; `submission/{journal}/` = derived artifacts.** Regenerate submission files from `manuscript/manuscript_v{N}.md`; never edit anonymized/title-page directly.
- **One canonical working version** at `manuscript/manuscript_v{N}.{md,docx,pdf}`. Older versions move to `manuscript/archive/` immediately on version bump.
- **No loose files at project root.** Only `HANDOFF.md`, `README.md`, folder entries.
- **QC artifacts** (self_review, peer_review, STROBE, critic reports) live in `manuscript/reviews/`, not at manuscript top level.
- **On rejection/retarget:** `cp -r submission/{old} submission/{new}`, then rewrite cover letter and reformat.
- **Double-anonymized journals** (Chest, AJRCCM): title page and anonymized manuscript MUST be separate files under `submission/{journal}/`.

### When to apply

- At project intake: scaffold empty structure.
- At first submission prep: create `submission/{journal}/` and populate.
- Mid-project cleanup: when `manuscript/` has >3 versioned files or QC docs at top level, reorganize.
- Before session handoff: reorganize if structure is drifting.

**Precedent:** an STROBE cohort with a mortality endpoint reorganized v1–v6 plus QC docs from the manuscript/ top level so that a reject-retarget path to a different journal requires only `cp -r submission/chest submission/<new_journal>`.

---

## Workflow

### Phase 1: Discover context

1. Read top-level folder names and key files.
2. Detect manuscript-like files, tables, figures, protocols, and analysis outputs.
3. Extract:
   - project title or working title
   - study question
   - dataset or cohort hints
   - collaborators or institutions
   - venue/journal hints

### Phase 2: Classify project stage

Assign one current stage:
- `idea`
- `data assembly`
- `analysis planning`
- `analysis in progress`
- `drafting`
- `revision`
- `submission prep`
- `archived/unclear`

**Gate:** Present the classification (project type, stage, target output) to the user.
Confirm before creating any files — misclassification leads to wrong scaffold and
wrong skill routing.

### Phase 3: Surface missing inputs

Check for common gaps:
- no explicit study question
- no target journal
- no analysis plan
- no variable dictionary
- no claims-to-results map
- no review log for revised manuscripts

### Phase 4: Produce normalized summary

Output this structure:

```text
## Project Intake Summary
Project: ...
Type: ...
Current stage: ...
Likely target: ...

### What exists
- ...

### What is missing
- ...

### Risks / ambiguities
- ...

### Recommended next actions
1. ...
2. ...
3. ...
```

---

## Optional File Templates

### `PROJECT.md`

```md
# PROJECT

- Title:
- Type:
- Primary question:
- Target journal/venue:
- Lead folder:
- Collaborators:
- Last updated:
```

### `STATUS.md`

```md
# STATUS

- Current stage:
- Current blocker:
- Next actions:
  1.
  2.
  3.
- Last updated:
```

---

## Guardrails

- Do not invent data values, outcomes, or collaborator roles.
- Do not assume a target journal unless evidence exists in the files.
- Do not create a large folder scaffold when the user only wants a quick assessment.
- If a project appears to mix multiple studies, say so explicitly rather than collapsing them into one.

---

## Handoff Rules

After intake:
- route to `search-lit` if the literature basis is weak
- route to `design-study` if the research question exists but design logic is unclear
- route to `manage-project` if the folder should be scaffolded
- route to `write-paper` only after the project phase is clearly `drafting`

---

## What This Skill Does NOT Do

- It does not write full manuscript sections
- It does not perform statistical analysis
- It does not verify citations deeply
- It does not replace study design review

## Anti-Hallucination

- **Never fabricate file paths, URLs, DOIs, or package names.** Verify existence before recommending.
- **Never invent journal metadata, impact factors, or submission policies** without verification at the journal's website.
- If a tool, package, or resource does not exist or you are unsure, say so explicitly rather than guessing.
