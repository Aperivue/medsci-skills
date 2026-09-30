# `/manage-project init` — the scaffold it emits

What `scripts/init_project.py` writes: the directory tree and the `project_state.json` shape.
The script builds all of it; this file only answers "where does X land" and "what does field Y mean".

```
{name}/
├── SSOT.yaml                  <- Contract (with --ssot; otherwise legacy project.yaml)
├── project_state.json         <- Progress tracking
├── artifact_manifest.json     <- Contract stub
├── PROJECT.md                 <- Project identity and scope
├── STATUS.md                  <- Current phase, blockers, next actions
├── CLAIMS.md                  <- Claim-to-result map
├── DATA_DICTIONARY.md         <- Variable and outcome definitions
├── ANALYSIS_PLAN.md           <- Primary/secondary analyses
├── REVIEW_LOG.md              <- Reviewer comments and responses
├── README.md                  <- Project overview
├── manuscript/
│   ├── index.qmd              <- Canonical manuscript stub
│   ├── _src/
│   │   └── refs.bib
│   └── figures/
├── qc/
│   └── status.json
├── paper/
│   ├── sections/
│   ├── figures/
│   ├── tables/
│   └── supplementary/
├── analysis/
│   ├── scripts/
│   └── outputs/
├── references/
│   ├── library.bib
│   └── checklist_{GUIDELINE}.md  <- Copied from /check-reporting after the script runs
├── revision/
└── submission/
```

Every directory the script creates gets a `.gitkeep`.

`project_state.json`:

```json
{
  "name": "{name}",
  "type": "{type}",
  "journal": "{journal}",
  "created": "YYYY-MM-DD",
  "target_submission": null,
  "current_phase": 0,
  "phases": {
    "0_init": "complete",
    "1_outline": "pending",
    "2_tables_figures": "pending",
    "3_methods": "pending",
    "4_results": "pending",
    "5_discussion": "pending",
    "6_intro_abstract": "pending",
    "7_polish": "pending"
  },
  "word_counts": {
    "abstract": 0,
    "introduction": 0,
    "methods": 0,
    "results": 0,
    "discussion": 0,
    "total": 0
  },
  "checklist_status": "pending",
  "citation_status": "unverified",
  "revision_round": null,
  "memory_files": {
    "PROJECT.md": true,
    "STATUS.md": true,
    "CLAIMS.md": true,
    "DATA_DICTIONARY.md": true,
    "ANALYSIS_PLAN.md": true,
    "REVIEW_LOG.md": true
  }
}
```
