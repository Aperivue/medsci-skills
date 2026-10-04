---
name: intake-project
description: Use when starting or inheriting a radiology research project and need to know what it is. Classifies the project type, summarizes its current state, lists missing inputs, recommends next steps and scaffolds lightweight project memory files.
metadata:
  triggers: "new project, intake project, project intake, classify project, organize project, what is this project"
---

# Intake-Project Skill

## Canonical Manuscript Folder Structure

`/manage-project init` scaffolds new projects; its script is the source of truth for that tree, including the `qc/` folder the QC skills write to. Use the layout below to reorganize an existing project that was never scaffolded, mapping each artifact into one of these slots or into a folder the init scaffold or another skill already writes to.

```
{project_root}/
├── HANDOFF.md                         # session handoff entry point
├── README.md                          # project overview
├── data/                              # raw data (NEVER edit; read-only)
├── analysis/                          # reproducible scripts (00_* → 04_*)
├── output/                            # analysis outputs: CSVs, PNGs, intermediates
├── qc/                                # QC reports the skills write (self-review, checklists, audits)
├── irb/                               # IRB/ethics docs
├── proposal/                          # original protocol / approved proposal
├── reviews/                           # external correspondence
├── manuscript/                        # SOURCE manuscript + drafting
│   ├── manuscript_v{N}.{md,docx,pdf}  # current canonical working version (top level)
│   ├── build_unified_docx.py          # or pandoc wrapper
│   ├── archive/                       # ALL prior versions v1 .. v{N-1}
│   ├── reviews/                       # review notes (QC reports go in qc/ at the root)
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
- **No loose files at project root.** Only `HANDOFF.md`, `README.md`, the project memory files (Phase 3), the contract files `/manage-project init` writes (`SSOT.yaml` or `project.yaml`, `project_state.json`, `artifact_manifest.json`), and folder entries.
- **QC artifacts** (self-review, reporting checklists, cross-reference and reference audits) live in `qc/` at the project root, where the skills that produce them write them, not at manuscript top level.
- **On rejection/retarget:** `cp -r submission/{old} submission/{new}`, then rewrite cover letter and reformat.
- **Double-anonymized journals** (Chest, AJRCCM): title page and anonymized manuscript MUST be separate files under `submission/{journal}/`.
- Keep existing project labels and file names in the language the workspace already uses.

### When to apply

- At project intake: scaffold through `/manage-project init` — unless the user only wants a quick assessment.
- At first submission prep: create `submission/{journal}/` and populate.
- Mid-project cleanup: when `manuscript/` has >3 versioned files or QC docs at top level, reorganize.
- Before session handoff: reorganize if structure is drifting.

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

### Phase 2: Classify project and stage

Determine:
- project type: `original | review | meta-analysis | case report | technical note | grant | peer review | challenge | career-doc`
- primary domain: `radiology | medical AI | multimodal LLM | intervention | survival/prognostic | diagnostic accuracy | workflow`
- target output: `paper | abstract | grant | review | rebuttal | CV`
- likely target journal or venue — only if the files name one
- one current stage: `idea | data assembly | analysis planning | analysis in progress | drafting | revision | submission prep | archived/unclear`

If the folder mixes several studies, say so rather than collapsing them into one.

**Gate:** Present the classification (project type, stage, target output) to the user.
Confirm before creating any files — misclassification leads to wrong scaffold and
wrong skill routing.

### Phase 3: Surface missing inputs

Check for blocking dependencies and common gaps:
- no explicit study question
- no target journal
- no analysis plan
- no variable dictionary
- no claims-to-results map
- no review log for revised manuscripts

If missing, propose or create lightweight anchor files — `PROJECT.md`, `STATUS.md`, `CLAIMS.md`,
`DATA_DICTIONARY.md`, `ANALYSIS_PLAN.md`, `REVIEW_LOG.md` — only those the project type justifies.
Read `${CLAUDE_SKILL_DIR}/references/memory_templates.md` when creating `PROJECT.md` or `STATUS.md`.

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

### Recommended next actions (3-5, in dependency order)
1. ...
2. ...
3. ...
```

---

## Handoff Rules

After intake:
- route to `search-lit` if the literature basis is weak
- route to `design-study` if the research question exists but design logic is unclear
- route to `manage-project` if the folder should be scaffolded
- route to `write-paper` only after the project phase is clearly `drafting`
