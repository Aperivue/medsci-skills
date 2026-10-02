---
name: manage-project
description: Use when managing a manuscript project over time. Scaffolds the project structure, tracks writing progress across phases, maintains project memory files, and generates submission checklists and backwards timelines (commands init, status, sync-memory, checklist, timeline).
metadata:
  triggers: "manage project, project init, project status, submission checklist, project scaffold, create project, new paper project"
---

# Manage-Project Skill -- Research Project Management

## Commands

### `/manage-project init {name} --type {type} --journal {journal} [--ssot] [--zotero-collection NAME]`

**Parameters:**
- `{name}` -- Project identifier (e.g., `nnunet-skull-fracture`, `rfa-meta-analysis`)
- `--type` -- Paper type: `original | meta | case | animal | technical | ai_validation | letter`
- `--journal` -- Target journal: `RYAI | AJR | Radiology | European_Radiology | KJR | INSI | AJNR | generic`
- `--ssot` -- Emit `SSOT.yaml` (schema v1) from `templates/SSOT.yaml.template` instead of legacy `project.yaml`. Required, but not sufficient, for Phase 1C auto-enforce (the PostToolUse verify-refs hook blocks instead of warns): enforce also needs `qc/migration_complete`, which init does not write. After init, run `migrate_project_to_ssot.py --project-root {target_dir} --mark-complete` to validate the SSOT.yaml and write the marker. New projects should pass `--ssot`; legacy in-flight projects stay on `project.yaml` until `/manage-project migrate-ssot` is run.
- `--zotero-collection NAME` -- Optional. Create a Zotero collection via pyzotero and populate `library_id` + `collection_key` in the contract. Requires `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID` (optionally `ZOTERO_LIBRARY_TYPE`, default `user`). With pyzotero or the credentials missing, the contract is scaffolded with `library_id: null` / `collection_key: null` and a WARN is printed.

**SSOT template substitutions:** `{{PROJECT_ID}}` → `{name}`; `{{PROJECT_TYPE}}` → the SSOT
`project_type` enum mapped from `--type` (`original → original_research`, `meta → meta_analysis`,
`case → case_report`, `ai_validation → ai_validation`, else `other`). Without
`--zotero-collection`, `library_id` / `collection_key` stay `null` until the owner links an
existing collection.

Run `scripts/init_project.py`:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_project.py" \
    --name {name} --type {type} --journal {journal} [--ssot] \
    --project-root {target_dir}
```

It writes the contract file (`SSOT.yaml` with `--ssot`, else legacy `project.yaml`), the
directory scaffold, the minimal stubs `scripts/validate_project_contract.py` requires
(`manuscript/index.qmd`, `artifact_manifest.json`, `qc/status.json`), the memory-file stubs,
and `project_state.json`. **`qc/migration_complete` is NOT written by init** — that marker belongs
to the migrate script. For an `--ssot` project, run it with `--mark-complete` (no project.yaml
needed): it validates the existing SSOT.yaml and writes the marker only on PASS. Until then the
reference hook stays in warn mode.

**Do not hand-build the scaffold.** The script is the source of truth for the tree and for
`project_state.json`; a hand-built one drifts from what the contract validator expects. Read
`${CLAUDE_SKILL_DIR}/references/init_scaffold.md` only when you need to know where a scaffolded
file lands or what a `project_state.json` field means.

After the script, copy the matching reporting-guideline checklist from
`${CLAUDE_SKILL_DIR}/../check-reporting/references/checklists/` into `references/checklist_{GUIDELINE}.md`.

### `/manage-project migrate-ssot [--no-mark-complete]`

Converts a legacy `project.yaml` project into SSOT.yaml form and, by default, touches `qc/migration_complete` so Phase 1C `auto` mode switches from `warn` to `enforce`.
On an SSOT-native project (SSOT.yaml present, no project.yaml — e.g. `init --ssot`) there is nothing
to convert: `--mark-complete` validates the existing SSOT.yaml and writes the marker on PASS;
SSOT.yaml is not rewritten.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/migrate_project_to_ssot.py" \
    --project-root . --write --mark-complete
```

- `--no-mark-complete`: run with `--write` only. Use it when the project still has open QC failures — enforcement is deferred until the migration is validated.
- The migrate script refuses to touch `qc/migration_complete` unless the generated SSOT.yaml passes `validate_project_contract.py` AND `contract_mode=ssot`. Do not `touch qc/migration_complete` manually.

Re-run after resolving failures; the script is idempotent.

### `/manage-project status`

Report current progress: read `project_state.json`, scan the existing files, and check whether the
project memory files are present and aligned. Take word-count limits from the target journal's
profile, `${CLAUDE_SKILL_DIR}/../write-paper/references/journal_profiles/{JOURNAL}.md`, not from
memory. Lay the report out as in `${CLAUDE_SKILL_DIR}/references/status_output_format.md`.

### `/manage-project sync-memory`

Audit and refresh the project memory files:
- check for `PROJECT.md`, `STATUS.md`, `CLAIMS.md`, `DATA_DICTIONARY.md`, `ANALYSIS_PLAN.md`, `REVIEW_LOG.md`
- identify stale or contradictory project metadata
- propose the minimum files to create or update; create them from `${CLAUDE_SKILL_DIR}/references/scaffold_templates.md`
- align `project_state.json` with the current manuscript phase

### `/manage-project checklist`

Read the pre-submission checklist from `${CLAUDE_SKILL_DIR}/references/pre_submission_checklist.md`
and write it to `submission/pre_submission_checklist.md`. Then recommend `/self-review` (manuscript
quality gate), `/verify-refs` (citation verification) and AI pattern removal (`/write-paper` Phase 7).

### `/manage-project timeline {submission_date}`

Generate a backwards timeline from the submission date, in the layout of
`${CLAUDE_SKILL_DIR}/references/timeline_example.md`.

---

## Project State Conventions

**Phase numbers:**
- 0 = Init (scaffold created)
- 1 = Outline approved
- 2 = Table/Figure shells approved
- 3 = Methods (critic >= 85)
- 4 = Results (critic >= 85)
- 5 = Discussion (critic >= 85)
- 6 = Introduction + Abstract (critic >= 85)
- 7 = Polish complete (AI pattern removal + checklist + self-review >= 80)

**Phase status values:** `pending | in_progress | complete | blocked`
