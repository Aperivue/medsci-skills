# `/manage-project init` — the scaffold it emits

Load-on-demand companion to `/manage-project init`. SKILL.md keeps the parameters, the
SSOT substitutions, and the invocation; this file records **what `scripts/init_project.py`
writes** — the full directory tree and the `project_state.json` shape.

Read it when you need to know where a scaffolded file lands, or what a field in
`project_state.json` means. You do not need it to *run* init: the script builds all of
this. Never hand-build the tree — a hand-built scaffold drifts from what
`scripts/validate_project_contract.py` expects.

Create a complete project scaffold for a new research paper.

**Parameters:**
- `{name}` -- Project identifier (e.g., `nnunet-skull-fracture`, `rfa-meta-analysis`)
- `--type` -- Paper type: `original | meta | case | animal | technical | ai_validation | letter`
- `--journal` -- Target journal: `RYAI | AJR | Radiology | European_Radiology | KJR | INSI | AJNR | generic`
- `--ssot` -- Emit `SSOT.yaml` (schema v1) from `templates/SSOT.yaml.template` instead of legacy `project.yaml`. Required for Phase 1C auto-enforce (PostToolUse verify-refs hook blocks instead of warns). New projects on or after 2026-04-24 should pass `--ssot`. Legacy in-flight projects stay on `project.yaml` until `/manage-project migrate-ssot` is run.
- `--zotero-collection NAME` -- Optional. Create a new Zotero collection with `NAME` via pyzotero and populate `library_id` + `collection_key` in the contract. Requires env vars `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID` (and optionally `ZOTERO_LIBRARY_TYPE`, default `user`). Graceful degrade: if pyzotero is not installed or credentials are missing, the contract is scaffolded with `library_id: null` / `collection_key: null` and a WARN is printed.

**SSOT template substitutions:** `{{PROJECT_ID}}` → `{name}`, `{{PROJECT_TYPE}}` → SSOT `project_type` enum mapped from `--type` (`original → original_research`, `meta → meta_analysis`, `case → case_report`, `ai_validation → ai_validation`, else `other`). Without `--zotero-collection`, `library_id` / `collection_key` stay `null` — populated manually when the owner links an existing Zotero collection.

**Implementation:** `/manage-project init` is backed by `scripts/init_project.py`. Invoke directly when running outside the skill harness:

```bash
python3 scripts/init_project.py \
    --name {name} --type {type} --journal {journal} [--ssot] \
    --project-root {target_dir}
```

(Run from the `medsci-skills` repo root.)

The helper writes the contract file (`SSOT.yaml` with `--ssot`, otherwise legacy `project.yaml`), the directory scaffold, minimal stubs required by `scripts/validate_project_contract.py` (`manuscript/index.qmd`, `artifact_manifest.json`, `qc/status.json`), the memory-file templates, and `project_state.json`. `qc/migration_complete` is **not** written by init — the migrate pipeline is responsible for that marker.

**What it creates:**

```
{name}/
├── paper/
│   ├── main.qmd               <- Main manuscript (Quarto)
│   ├── sections/
│   │   ├── abstract.qmd
│   │   ├── introduction.qmd
│   │   ├── methods.qmd
│   │   ├── results.qmd
│   │   ├── discussion.qmd
│   │   └── conclusion.qmd
│   ├── figures/
│   │   └── .gitkeep
│   ├── tables/
│   │   └── table_shells.md    <- Table structure designed before prose
│   └── supplementary/
│       └── .gitkeep
├── analysis/
│   ├── scripts/
│   │   └── .gitkeep
│   └── outputs/
│       └── .gitkeep
├── references/
│   ├── library.bib
│   └── checklist_{GUIDELINE}.md  <- Loaded from /check-reporting
├── revision/
│   └── .gitkeep
├── submission/
│   └── .gitkeep
├── PROJECT.md                <- Project identity and scope
├── STATUS.md                 <- Current phase, blockers, next actions
├── CLAIMS.md                 <- Claim-to-result map
├── DATA_DICTIONARY.md        <- Variable and outcome definitions
├── ANALYSIS_PLAN.md          <- Primary/secondary analyses
├── REVIEW_LOG.md             <- Reviewer comments and responses
├── project_state.json         <- Progress tracking
└── README.md                  <- Project overview
```

**Also creates** `project_state.json`:

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

---
