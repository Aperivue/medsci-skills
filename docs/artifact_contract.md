# MedSci Artifact Contract

**Revision**: v1.1.1 (2026-04-24, Phase 0.5.7)
**Supersedes**: v1.0 (initial project.yaml-only contract)

This document defines the durable handoff layer for `medsci-skills`.
Skills may still use narrative instructions, but cross-skill automation must pass
through typed artifacts rather than relying on prose memory.

## Design Rules

1. **Canonical first.** Every project has one canonical manuscript source (`SSOT.truth.manuscript`) and a small project registry (`SSOT.yaml`). Journal submission folders are derived artifacts.
2. **Scripts own repeatability.** Reference checks, submission drift checks, numerical reconciliation, and manifest validation are deterministic scripts. LLMs may triage, summarize, and draft prose, but they must not silently invent or reconcile source-of-truth data.
3. **Artifacts are append-friendly.** Repair and revision steps write new audit files or update machine-readable manifests. They do not overwrite frozen submissions without recording provenance.
4. **Orchestrators validate, workers produce.** `/orchestrate` reads contract files and routes work. It does not substitute for worker skills or scripts.
5. **Sole writer is enforceable.** Each artifact lists exactly one writer skill (below). Pre-save hooks and validators enforce this.

## Project Registry

See `docs/ssot_schema_v1.md` for the canonical schema. Projects in the 6-month transition window (until 2026-10-24) may still use `project.yaml`; validator warns.

Validate a project with:

```bash
python3 scripts/validate_project_contract.py --project-root path/to/project
```

Dual-path behavior: `SSOT.yaml` preferred, `project.yaml` warns, neither fails.

## Artifact Roster (v1.1.1 §2.5)

| Artifact | Sole Writer | Readers | Lock | Notes |
|---|---|---|---|---|
| `manuscript/_src/refs.bib` | `/lit-sync` (Zotero Better BibTeX export) | `/write-paper`, `/verify-refs`, `/render`, `/self-review` | advisory | LLM direct write forbidden. See `zotero_policy.md`. |
| `manuscript/_src/numbers.yaml` | `/analyze-stats` | `/write-paper`, `/make-figures`, `/render` | strict | Concurrent writes forbidden. |
| `manuscript/index.qmd` or `manuscript.md` | `/write-paper` (draft→revise→humanize sequence) | `/self-review`, `/verify-refs`, `/render` | sequential strict | Order enforced by harness. |
| `manuscript/working_latest.docx` | `/render` only | human reviewers | strict | Hand edits forbidden; backport via `/backport-to-ssot`. |
| `submission/{journal}/*` | `/render` only | `/check-reporting` (final), human reviewers | strict | Frozen after build. |
| `submission/{journal}/.journal_meta.json` | `/render` / `/sync-submission` | `/orchestrate`, `/check-reporting` | read-only (consumers) | Machine metadata; see below. |
| `manuscript/_metadata.yml` | user (manual) | all | read-only | Authors/affiliations. Skills cannot write. |
| `manuscript/figures/*` | `/make-figures` | `/render` | none | Read-only; copied into submission at build. |
| `manuscript/_src/tables.yaml` | `/analyze-stats` (data rows) + `/write-paper` (captions) | `/render` | dual-write OK (different fields) | Separate concerns by key. |
| `decisions/*.md` | any skill | all | append-only | Layer D intent log. |
| `artifact_manifest.json` | `/render`, `/sync-submission` (auto) | all | advisory | Derived inventory. |
| `qc/status.json` | pipeline runner | all | advisory | Runtime pipeline state. |
| `qc/reference_audit.json` | `/verify-refs` | `/render`, pre-save hooks | read-only (consumers) | Citation audit output. |
| `references/library.bib` | `/search-lit` (produces verified candidates) | `/lit-sync` (imports to Zotero), `/verify-refs` | advisory | Not the SSOT bibliography; that is `manuscript/_src/refs.bib`. |
| `references/fulltext_retrieval.json` | `/lit-sync` (Phase 2.7) | `/meta-analysis`, human reviewers | advisory | Opt-in fulltext-retrieval report: retrieved (OA-disk / Zotero-native, user-reported) vs not-retrieved + institutional-fallback list + title-match flags. |
| `pdfs/` + `pdfs/retrieval_report.json` | `/fulltext-retrieval` (engine) | `/lit-sync`, `/meta-analysis`, `/obsidian-paper-vault` | none | OA PDFs + per-DOI `status` (arxiv/oa/pmc/skip/fail), `source`, and `title_match` (match / mismatch / unavailable). Engine report; `/lit-sync` merges it into `references/fulltext_retrieval.json`. |

## `.journal_meta.json` Standard (v1.1.1)

Every `submission/{journal}/` folder MUST contain `.journal_meta.json` with this schema:

```json
{
  "schema_version": 1,
  "journal_id": "radiology_ai",
  "profile_path": "submission/_profiles/_quarto-radiology_ai.yml",
  "source_hash": "sha256:<hex>",
  "source_files": [
    "manuscript/index.qmd",
    "manuscript/_src/refs.bib",
    "manuscript/_src/numbers.yaml"
  ],
  "build_time": "2026-04-24T12:34:56Z",
  "builder": "render@1.0.0",
  "status": "frozen | submitted | rejected | accepted | withdrawn",
  "status_updated": "2026-04-24T12:34:56Z",
  "blind": true,
  "strip_metadata": ["funding", "acknowledgments"],
  "notes": null
}
```

**Required**: `schema_version`, `journal_id`, `source_hash`, `build_time`, `status`.

**Rules**:
- `source_hash` is a SHA-256 over concatenated SHA-256s of `source_files` (order-stable).
- `status` transitions: `frozen` → `submitted` → (`rejected` | `accepted` | `withdrawn`). No backward transitions without a new build (new `source_hash`).
- `/sync-submission` compares `source_hash` to current `source_files` content; mismatch = drift → alert.
- Consumers (e.g., `/check-reporting`, `/orchestrate`) read this file; they MUST NOT write it.

## `artifact_manifest.json` Standard

```json
{
  "schema_version": 1,
  "project_id": "example",
  "canonical": {
    "manuscript": "manuscript/index.qmd",
    "refs_bib": "manuscript/_src/refs.bib",
    "numbers_yaml": "manuscript/_src/numbers.yaml"
  },
  "analysis": {
    "outputs": "analysis/_analysis_outputs.md",
    "tables": ["analysis/tables/table1.csv"],
    "figures_manifest": "analysis/figures/_figure_manifest.md"
  },
  "qc": {
    "status": "qc/status.json",
    "reference_audit": "qc/reference_audit.json",
    "reporting_checklist": "qc/reporting_checklist.md",
    "self_review": "qc/self_review.md"
  },
  "submissions": {
    "radiology_ai": {
      "path": "submission/radiology_ai",
      "journal_meta": "submission/radiology_ai/.journal_meta.json",
      "status": "frozen"
    }
  }
}
```

## Status File

`qc/status.json` is the lightweight pipeline state consumed by the orchestrator.

```json
{
  "schema_version": 1,
  "stage": "drafting | qc | submitted | revision | rejected | retargeting",
  "blocking_issues": [],
  "last_reference_audit": null,
  "last_submission_sync": null,
  "last_numerical_audit": null
}
```

## Skill Contract

Each skill includes `skill.yml`. See `docs/skill_yml_schema_v2.md` for v2 schema. Validator treats missing contracts as warnings during migration and validates contracts that exist.

## Submission Rule

`submission/{journal}/` is derived and frozen after build. If a journal portal or a manual editor changes a submission manuscript, the change MUST be represented as one of:

- a patch back to the canonical manuscript via `/backport-to-ssot`,
- a documented journal-only formatting transform recorded in `.journal_meta.json` notes, or
- a frozen rejected/submitted package with no reuse in later journals.

`/sync-submission` detects this drift via `source_hash` comparison and produces the audit record.

## Reference Rule

Reference output is valid only when `qc/reference_audit.json` exists and contains no `FABRICATED` rows. Entries without DOI or PMID may be `UNVERIFIED`, but they must be explicitly visible in `qc/reference_audit.json` and `manuscript/_src/refs.bib` with `verified: false`.

## Meta-analysis Rule

Screening totals used in PRISMA flow diagrams, manuscript prose, and submission packages MUST come from a machine-readable reconciliation artifact:

```text
2_Screening/screening_consensus_final.json
```

The prose summary can explain the decisions, but downstream stages consume the JSON totals and explicit ID sets.

## Change log

- **2026-06-29** Roster: added `references/fulltext_retrieval.json` (sole writer `/lit-sync`, opt-in Phase 2.7) and `pdfs/` + `pdfs/retrieval_report.json` (writer `/fulltext-retrieval`). OA cascade consolidated to the `/fulltext-retrieval` engine; `/search-lit` Phase 5 delegates to it.
- **2026-04-24 v1.1.1** `.journal_meta.json` standardized; roster updated for `refs.bib` sole writer = `/lit-sync`; `qc/reference_audit.json` sole writer = `/verify-refs` (write logic to be removed from `/verify-refs` in Phase 1A).
- **v1.0** Initial contract (project.yaml era).
