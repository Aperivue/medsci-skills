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
- Gate 4: docx audits must use a recursive walk (paragraphs + tables + nested-table cells); a flat `document.paragraphs` scan is insufficient.
- Gate 5: before freeze, confirm portal free-text fields (cover letter, data availability, acknowledgements, abstract, author contributions) match the manuscript body.

## Verification Blind Spots

Post-submission learnings (npj Digital Medicine R1, 2026-05): a clean docx-level audit still missed several stale artifacts that surfaced only at the portal review stage. Apply these whenever auditing a submission package.

### B1. docx scanning must be recursive

`python-docx` `paragraph.runs` does not expose runs inside `<w:hyperlink>`; `document.paragraphs` skips table cells; `document.tables` does not recurse into nested tables. Figures, captions, and reporting checklists are routinely wrapped in 1×1 or nested tables, so flat scans silently miss them.

- Walk `paragraphs + tables + nested-table cells` recursively for every stale-string scan.
- For run-level edits near hyperlinks or fields, inspect the paragraph XML, not just `.runs` — a missing inline element can be misread as an empty `()` artifact and "fixed" into a real defect.

### B2. Portal input fields are a separate SSOT

Cover letter, Data Availability, Acknowledgements, Abstract, and Author Contributions are often typed directly into the journal portal, outside any docx this skill audits. A clean docx audit does not imply a clean portal.

- Before final submission, diff the portal's final review page against the manuscript body 1:1.
- Treat each portal free-text field as its own drift target.

### B3. Verify change propagation across the whole SSOT tree

A tone, wording, or number change applied to one file (e.g. the abstract) must propagate to every file that repeats it — discussion, response-to-reviewers quotes, reporting checklists, supplementary captions, title page.

- grep the OLD string across the entire SSOT tree, never a subset of files.
- Watch for substring near-misses (`expertise-dependent patterns` vs `expertise-dependent evaluation patterns`) — an exact-match grep on the short form passes while the long form remains stale.

## What This Skill Does NOT Do

- Does not invent journal formatting rules.
- Does not silently merge submission edits back into the SSOT.
- Does not replace `/write-paper`; it packages already canonical content.

## Anti-Hallucination

- Never claim a submission package is current without matching source hashes.
- Never mark a package as submitted without writing `.journal_meta.json`.
- Never hide journal-only differences; record them as drift or explicit exceptions.
