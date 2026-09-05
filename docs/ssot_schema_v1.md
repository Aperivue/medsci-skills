# SSOT.yaml — Schema v1

**Status**: Frozen (Phase 0.5.1, 2026-04-24)
**Supersedes**: `project.yaml` schema v1 (6-month transition, sunset 2026-10-24)
**Validator**: `scripts/validate_project_contract.py` (dual-path: SSOT.yaml enforce, project.yaml warn)

Single Source of Truth (SSOT) configuration for a medsci research project. One file per project root. Canonical for all downstream skills (`/write-paper`, `/analyze-stats`, `/render`, `/verify-refs`, `/sync-submission`, etc.).

## Design principles

1. **Truth vs derived**: `truth.*` paths are authored (manuscript body, refs, numbers, figures). `derived.*` paths are regenerated (artifact manifest, status). Never edit `derived` by hand.
2. **Policy is explicit**: Editable surface, render blocking conditions, and citation strictness live in `policy:`. Skills MUST read policy before writing.
3. **Render outputs are read-only**: `renders.*.path` describes artifacts that `/render` produces from `truth`. Journal submission folders (`submission/{journal}/`) are frozen after build.
4. **Reference manager is project-level**: Owner (project lead) runs Better BibTeX auto-export; collaborators consume `refs.bib` snapshot. See D-2 decision (2026-04-24).
5. **Markdown-first body**: `truth.manuscript` is Pandoc markdown (`.qmd` preferred for Quarto, `.md` fallback). Never docx. See D-1.

## Top-level fields

| Field | Required | Type | Notes |
|---|---|---|---|
| `schema_version` | yes | int | Must be `1`. |
| `project_id` | yes | str | Short snake_case id. Stable across lifecycle. |
| `project_type` | yes | enum | `original_research` \| `meta_analysis` \| `case_report` \| `ai_validation` \| `protocol` \| `other`. |
| `truth` | yes | map | See [truth block](#truth-block). |
| `reference_manager` | yes | map | See [reference_manager block](#reference_manager-block). |
| `renders` | no | map | See [renders block](#renders-block). Populated as build targets are defined. |
| `derived` | yes | map | See [derived block](#derived-block). |
| `policy` | yes | map | See [policy block](#policy-block). |
| `legacy` | no | map | Only present during project.yaml → SSOT.yaml migration window. |

## truth block

```yaml
truth:
  manuscript: manuscript/index.qmd         # REQUIRED, Pandoc markdown (.qmd or .md)
  refs_bib: manuscript/_src/refs.bib       # REQUIRED, Zotero Better BibTeX snapshot
  numbers_yaml: manuscript/_src/numbers.yaml  # REQUIRED for projects with statistics
  tables_yaml: manuscript/_src/tables.yaml    # optional; data rows + captions split
  figures_dir: manuscript/figures/         # REQUIRED; master figures live here
  metadata: manuscript/_metadata.yml       # REQUIRED; authors + affiliations
```

- Paths are relative to project root.
- `manuscript` file must exist; validator fails otherwise.
- `refs_bib` is written only by `/lit-sync` (owner) or by explicit snapshot drop-in (collaborator). See artifact_contract.md.

## reference_manager block

```yaml
reference_manager:
  type: zotero                             # only supported type in v1
  required_for: project_owner              # project_owner | all_contributors | none
  library_type: user                       # user | group
  library_id: null                         # Zotero userID/groupID (required if required_for=project_owner and this is owner's checkout)
  collection_key: null                     # Zotero collection key (e.g., "ABCD1234")
  sync_method: better_bibtex_auto_export   # owner path
  fallback_for_collaborator: snapshot_only # collaborators without Zotero consume refs_bib snapshot
  citekey_policy: pinned_or_stable         # Better BibTeX pinned keys required
  refs_bib_snapshot: manuscript/_src/refs.bib  # must equal truth.refs_bib
```

**required_for semantics (D-2, F4)**:
- `project_owner`: only project lead (유진) must have Zotero+BetterBibTeX. Collaborators work from the committed `refs.bib` snapshot.
- `all_contributors`: every contributor mirrors the Zotero collection. Rare; used for multi-institution SR/MA with shared screening.
- `none`: `refs.bib` is hand-maintained (discouraged; fallback only for legacy projects).

Validator rules:
- If `required_for=project_owner`, `library_id` and `collection_key` MAY be null in collaborator checkouts, but MUST be populated in the owner's environment for `/lit-sync` to run.
- `refs_bib_snapshot` MUST equal `truth.refs_bib` (single canonical path).

## renders block

```yaml
renders:
  working_docx:
    path: manuscript/working_latest.docx
    style: journal_generic
    from: truth
  circulation:
    path: revision/R1/circulation_latest.docx
    style: circulation
    from: truth
  submission_ryai:
    path: submission/radiology_ai/manuscript.docx
    style: ryai
    blind: true
    strip_metadata: [funding, acknowledgments]
    from: truth
```

- Each entry names a build target. `/render <key>` consumes `truth.*` and writes `path`.
- `from: truth` is the only supported source in v1 (no derived-of-derived).
- `blind: true` triggers author/affiliation stripping during render.
- `strip_metadata` is a list of top-level metadata keys to omit in the rendered artifact.

## derived block

```yaml
derived:
  artifact_manifest: artifact_manifest.json   # auto-written by /render, /sync-submission
  status_file: qc/status.json                 # auto-written by pipeline runner
```

- Both paths are project-root-relative.
- These files MUST NOT be hand-edited. Validators flag human-authored changes.

## policy block

```yaml
policy:
  ssot_only_editable: true                    # edits go to truth.*, not to renders.*
  submission_readonly: true                   # submission/{journal}/ is frozen post-build
  back_merge_required_before: render          # any external edit must backport before next render
  manuscript_citations: citekey_only          # [@citekey] form only; no free-text citations
  allow_new_reference_from_llm: false         # LLMs cannot invent bibtex entries
  missing_citekey: block                      # /render fails on unresolved [@key]
  unverified_reference: block_before_submission  # verify-refs must pass before render submission_*
```

All keys REQUIRED. Downstream skills MUST read and honor each before writing.

## legacy block

Present only during the 6-month migration window (2026-04-24 → 2026-10-24):

```yaml
legacy:
  project_yaml_alias: project.yaml            # if both files exist, SSOT.yaml wins
  sunset_date: "2026-10-24"                   # after this date, validator FAILs on project.yaml
```

After the sunset date, remove this block and delete `project.yaml`.

## project.yaml → SSOT.yaml field mapping

| `project.yaml` field | `SSOT.yaml` location | Notes |
|---|---|---|
| `schema_version` | `schema_version` | Both schemas use `1`; meaning differs. |
| `project_id` | `project_id` | Verbatim. |
| `project_type` | `project_type` | Verbatim. |
| `canonical_manuscript` | `truth.manuscript` | Path unchanged. |
| `references_bib` | `truth.refs_bib` | Path unchanged; also copied to `reference_manager.refs_bib_snapshot`. |
| `artifact_manifest` | `derived.artifact_manifest` | Path unchanged. |
| `status_file` | `derived.status_file` | Path unchanged. |
| `submission_root` | (implicit, always `submission/`) | Hard-coded convention in v1. |
| `target_journal` | (implicit via `submission/_profiles/`) | Not a top-level field in SSOT. |
| `reporting_guideline` | (skill.yml `qc` inference, or `policy.reporting_guideline` future) | Not yet first-class in v1; Phase 2 candidate. |
| `zotero_collection` | `reference_manager.collection_key` | Verbatim. |

Any fields not in this table are dropped with a migration warning (`migrate_project_to_ssot.py --verbose`).

## Validator behavior (Phase 0.5.4)

`scripts/validate_project_contract.py` dual-path logic:

1. `SSOT.yaml` exists → enforce SSOT schema. `project.yaml` presence → WARN with sunset date.
2. Only `project.yaml` exists → WARN "SSOT.yaml missing — migrate with `scripts/migrate_project_to_ssot.py`" and enforce legacy schema.
3. Neither exists → FAIL.
4. After `legacy.sunset_date`, case 2 escalates to FAIL.

## Minimal example

```yaml
schema_version: 1
project_id: example_study
project_type: original_research

truth:
  manuscript: manuscript/index.qmd
  refs_bib: manuscript/_src/refs.bib
  numbers_yaml: manuscript/_src/numbers.yaml
  tables_yaml: manuscript/_src/tables.yaml
  figures_dir: manuscript/figures/
  metadata: manuscript/_metadata.yml

reference_manager:
  type: zotero
  required_for: project_owner
  library_type: user
  library_id: "12345678"
  collection_key: "ABCD1234"
  sync_method: better_bibtex_auto_export
  fallback_for_collaborator: snapshot_only
  citekey_policy: pinned_or_stable
  refs_bib_snapshot: manuscript/_src/refs.bib

renders:
  working_docx:
    path: manuscript/working_latest.docx
    style: journal_generic
    from: truth
  submission_ryai:
    path: submission/radiology_ai/manuscript.docx
    style: ryai
    blind: true
    strip_metadata: [funding, acknowledgments]
    from: truth

derived:
  artifact_manifest: artifact_manifest.json
  status_file: qc/status.json

policy:
  ssot_only_editable: true
  submission_readonly: true
  back_merge_required_before: render
  manuscript_citations: citekey_only
  allow_new_reference_from_llm: false
  missing_citekey: block
  unverified_reference: block_before_submission
```

## Change log

- **2026-04-24** Schema v1 frozen (Phase 0.5.1). Decisions: D-1 Pandoc markdown body, D-2 owner/collaborator split for Zotero.
