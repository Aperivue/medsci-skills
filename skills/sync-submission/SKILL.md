---
name: sync-submission
description: Audit SSOT-to-submission drift and create journal submission manifests from canonical manuscript artifacts.
triggers: sync submission, build submission, submission drift, SSOT sync, journal package, retarget journal, freeze submission
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Sync Submission

You help keep the canonical manuscript and journal-specific submission packages
from drifting apart. The skill treats `submission/{journal}/` as derived output
and records whether it is current, stale, or frozen.

## When to Use

- Before submitting a journal package.
- After a journal portal or Word editor changed a submission manuscript.
- After rejection, before retargeting to another journal.
- Before `/orchestrate --e2e` marks a project as submission-ready.

## Inputs

1. Project root containing `project.yaml`, or a direct canonical manuscript path.
2. Journal short name, e.g. `chest`, `ryai`, `academic_radiology`.
3. Optional mode:
   - `audit`: compare existing submission against canonical source.
   - `build`: copy canonical source into `submission/{journal}/manuscript/` and write metadata.
   - `freeze`: mark a package as submitted/frozen.

## Deterministic Script

```bash
python "${CLAUDE_SKILL_DIR}/scripts/sync_submission.py" audit --project-root . --journal chest
python "${CLAUDE_SKILL_DIR}/scripts/sync_submission.py" build --project-root . --journal chest
python "${CLAUDE_SKILL_DIR}/scripts/sync_submission.py" freeze --project-root . --journal chest --status submitted
```

## Output Contract

| Artifact | Path | Purpose |
|---|---|---|
| Submission metadata | `submission/{journal}/.journal_meta.json` | Source hash, status, canonical path |
| Sync audit | `qc/submission_sync_{journal}.json` | Drift result consumed by orchestrator |
| Manifest update | `artifact_manifest.json` | Submission package registry |

## Workflow

1. Resolve canonical manuscript from `project.yaml` or explicit input.
2. Run the script in the requested mode.
3. If `audit` reports `DRIFT`, do not retarget or freeze until the user either
   patches the canonical manuscript or records the difference as journal-only.
4. If `build` succeeds, run `/verify-refs` before final submission.

## Quality Gates

- Gate 1: block freezing when canonical manuscript is missing.
- Gate 2: block retargeting when the previous submission has unresolved drift.
- Gate 3: require `/verify-refs` audit before marking a package submission-safe.

## What This Skill Does NOT Do

- Does not invent journal formatting rules.
- Does not silently merge submission edits back into the SSOT.
- Does not replace `/write-paper`; it packages already canonical content.

## Anti-Hallucination

- Never claim a submission package is current without matching source hashes.
- Never mark a package as submitted without writing `.journal_meta.json`.
- Never hide journal-only differences; record them as drift or explicit exceptions.
