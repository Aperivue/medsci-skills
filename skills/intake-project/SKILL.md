---
name: intake-project
description: >
  Intake and normalize a new radiology research project. Classifies project type, summarizes current state,
  identifies missing inputs, recommends next steps, and scaffolds lightweight project memory files.
  Triggers: new project, intake project, project intake, 프로젝트 시작, 프로젝트 정리, 새 연구 정리
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
