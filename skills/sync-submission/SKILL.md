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

For double-blind journals, sweep author identifiers across all upload artifacts:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/blind_sweep.py" \
  --registry _shared/authors/author_registry.yaml \
  --files submission/{journal}/supplementary/*.md submission/{journal}/cover_letter.md \
  --backup-dir .cache/blind_sweep_backup
```

The registry is a project-local YAML mapping author identifiers (full names, native scripts, initials with/without periods, email, ORCID) to role labels (e.g., "Reviewer 1"). See `scripts/author_registry_example.yaml` for schema. Never commit a populated registry to a public repository — keep it next to the manuscript.

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
- Gate 6 (double-blind journals): before freeze, export the portal's blinded review PDF and grep for all author identifiers across the entire upload set — manuscript, supplementary, cover letter, registry record PDFs (PROSPERO/ClinicalTrials), portal Letter-field text. A clean manuscript blind does not imply a clean portal blind.
- Gate 7 (text-only docx rebuilds): never use `pandoc --reference-doc=manuscript.docx` for response/cover/supplementary text-only docx — the reference docx ships its embedded media (figure files) into the new docx, bloating size 50–100×. Use plain `pandoc input.md -o output.docx` for text-only artifacts.
- Gate 5b (Phase 4 cover-letter free-text drift): before freeze, run `scripts/cover_letter_drift_check.py` to verify the cover letter's word-count / reference-count / table-figure-count claims still match the manuscript. Cover letters routinely go stale across v_N → v_(N+1) branching and are not covered by any docx-level audit. See "Phase 4 — Cover-letter free-text drift" below.
- Gate 8 (Phase 5 cross-document N consistency): before freeze, run `scripts/cross_document_n_check.py` over the manuscript bundle (abstract, body, PROSPERO record, cover letter, supplementary, INDEX, PRISMA flow caption). Any N category with >1 distinct integer value is a P0 drift. When a `FINAL_POOL_LOCK.yaml` is present, supply `--pool-lock` to make the locked counts the authoritative baseline. See "Phase 5 — Cross-document N consistency" below.
- Gate 9 (Phase 6 intra-manuscript scope drift): run `scripts/scope_drift_check.py` against the manuscript (and optionally the PROSPERO record). Numeric anchors (AUC, OR/HR/RR, sensitivity/specificity) appearing in Limitations / Discussion but absent from Methods + Results are P0 SCOPE_DRIFT. PROSPERO ↔ Methods synthesis-method disagreement is a P0 PROSPERO_DRIFT.
- Gate 10 (Phase 7 v_(N+1) docx regeneration): when building a new submission from a frozen prior version, run `scripts/verify_package_integrity.py --assert-vN-docx-changed --vN-docx <prev>.docx --new-docx <next>.docx`. Identical MD5 = unmodified seed copy = block submission. Defense-in-depth — required even when the upstream pipeline appears to have regenerated the docx.

## Phase 4 — Cover-letter free-text drift

Cover letters live outside the submission docx files but are read by the
editor side-by-side with the manuscript. Their `## Article details`
block — body word count, abstract word count, reference count,
table/figure count — is a sidecar SSOT that routinely goes stale when a
manuscript branches v_N → v_(N+1) (word limit retarget, abstract
restructure, late reference batch).

`scripts/cover_letter_drift_check.py` measures the manuscript truth and
compares it to the cover letter's numeric claims:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/cover_letter_drift_check.py" \
    --manuscript manuscript.md \
    --cover-letter cover_letter.md \
    --refs refs.bib \
    --out qc/cover_letter_drift.json
```

Body words are matched with a 5% tolerance ("approximately N words"
phrasing). Abstract words tolerate ±5. Reference / table / figure counts
require exact match.

Output `qc/cover_letter_drift.json`:

```json
{
  "submission_safe": false,
  "truth": {"body_words": 3036, "abstract_words": 319, "references": 12,
            "tables": 3, "figures": 4},
  "claims": {"body_words": 3790, "abstract_words": 250, "references": 12},
  "drifts": [
    {"field": "body_words", "truth": 3036, "cover_letter_claim": 3790,
     "severity": "MAJOR",
     "note": "|claim - truth| = 754 > tolerance 151"}
  ]
}
```

Drift resolution: regenerate the cover letter from the manuscript at
v_(N+1) build time. The script never edits the cover letter — that is
left to the manuscript build pipeline so the cover letter stays a
deliberate authored artifact.

## Phase 5 — Cross-document N consistency

Multi-document cohort-size drift is a high-frequency desk-reject pattern.
Manuscript abstracts, body prose, PROSPERO records, supplementary extraction
sheets, and PRISMA flow captions all repeat the same `k included` / `k excluded`
/ `N patients` totals — and any disagreement between them is read by reviewers
as either a data-integrity failure or a late-edit failure. Either reading
ends the round.

`scripts/cross_document_n_check.py` scans the submission package, extracts
every "N <noun>" claim by category (patients, cases, included, excluded,
nodules, tumors, studies_total), and groups them by category. A category with
more than one distinct integer value is a P0 drift.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/cross_document_n_check.py" \
    --root . \
    --out qc/cross_document_n.json
```

When the project has frozen a `2_Data/FINAL_POOL_LOCK.yaml` from `/meta-analysis`
Phase 3f.5, pass it as the authoritative anchor:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/cross_document_n_check.py" \
    --root . \
    --pool-lock 2_Data/FINAL_POOL_LOCK.yaml \
    --out qc/cross_document_n.json
```

Output `qc/cross_document_n.json`:

```json
{
  "submission_safe": false,
  "drift_count": 1,
  "drifts": [
    {
      "category": "included",
      "values": [63, 64],
      "locations": [
        {"file": "abstract.md", "line": 4, "value": 63, "context": "..."},
        {"file": "supplementary/s1.md", "line": 12, "value": 64, "context": "..."}
      ],
      "severity": "MAJOR"
    }
  ],
  "lock_violations": []
}
```

Treat `submission_safe: false` as a halt. Resolve drift by tracing each
location to its data artifact (extraction sheet, PRISMA cascade TSVs) and
correcting the document(s) that disagree with the locked count.

## Phase 6 — Intra-manuscript scope drift

Late-revision sensitivity analyses sometimes get introduced in the
Discussion or Limitations subsection without ever propagating back to
Methods + Results. The manuscript then makes claims (with explicit AUC,
OR, sensitivity numbers) whose primary report never exists. Reviewers
read this as a fabrication-grade red flag, and editors desk-reject.

A second variant of the same anti-pattern: the PROSPERO record commits to
a synthesis method (Freeman-Tukey, random-effects DerSimonian-Laird,
bivariate, HSROC, Bayesian, etc.) but the Methods section uses a
different one — or the PROSPERO record was updated and Methods stayed
behind. When accompanied by a Methods line saying "no amendment lodged",
this becomes a documented silent protocol deviation.

`scripts/scope_drift_check.py` detects both patterns:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/scope_drift_check.py" \
    --manuscript manuscript.md \
    --prospero prospero/prospero_v2.md \
    --out qc/scope_drift.json
```

Output:

```json
{
  "submission_safe": false,
  "limitations_only_anchors": [
    {
      "anchor": "0.869",
      "kind": "AUC",
      "found_in": ["Limitations:31"],
      "missing_from": ["Methods", "Results"]
    }
  ],
  "synthesis_method_drift": [
    {"method": "Freeman-Tukey", "prospero": true, "methods": false}
  ]
}
```

Resolution: either (a) propagate the anchor into Methods + Results as a
primary report or (b) remove it from Limitations / Discussion. For
synthesis-method drift, file a PROSPERO amendment and update Methods to
match — both must agree before submission.

## Phase 7 — v_(N+1) docx regeneration gate

When a v_N submission package was frozen and a v_(N+1) is being built
(after a markdown body edit, reviewer round, or cascade-rejection
re-target), the v_(N+1) docx MUST differ from the v_N docx. The most
common silent-revert pattern is a `cp v_N/manuscript.docx
v_(N+1)/manuscript.docx` step that skips the pandoc / Zotero CWYW
regeneration entirely. The markdown body is then edited, but the docx
the portal receives is the frozen v_N — the change silently reverts at
peer review.

Run the byte-identity assertion at the top of the v_(N+1) submission
gate:

```bash
python3 /path/to/medsci-skills/scripts/verify_package_integrity.py \
    --assert-vN-docx-changed \
    --vN-docx SUBMISSION/<journal>/v<N>/manuscript.docx \
    --new-docx SUBMISSION/<journal>/v<N+1>/manuscript.docx
```

Identical MD5 → exit 1 with explanatory error. Block submission until
the regeneration step is fixed.

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

### B3a. Double-blind compliance must cover ALL upload artifacts

A clean manuscript-level blind sweep does not imply a clean portal-level blind. Author identifiers commonly leak through:

- Supplementary materials (per-material `.md`/`.docx` files, especially methodology logs, agreement metrics, amendment logs)
- Cover letter (separately-uploaded file is portal-default visible to reviewers unless explicitly toggled "Don't show in review PDF")
- Registry record PDFs (PROSPERO, ClinicalTrials.gov, IRB approval PDFs)
- Portal free-text Letter field if cover-letter signature was pasted
- Response-to-reviewers (revision rounds)

Blind sweep regex coverage must include both period and no-period initial forms (e.g., `Y.N.` and `YN`), full names in roman + native scripts, institution names, ORCID IDs, and submission email domains. The first blind PDF export from the portal is the authoritative drift detector — always export and grep before final submit.

### B3b. PROSPERO public-record PDF shows only current amendment

PROSPERO's "Print/PDF" export from the public record renders only the current amendment narrative. Previous versions are accessible only by selecting older versions in the public-record version-history dropdown. When citing PROSPERO version state, never rely on a single PDF export to verify cross-version consistency — record each published version's PDF independently and clarify in cover/supplementary which version anchors the methodology vs. which version reflects documentation-only erratum.

For documentation-only PROSPERO errata (correcting a narrative fact without changing methods/eligibility/synthesis), prefer a single Revision-Note append over a new structured amendment entry. Preserves historical audit trail and minimizes portal edit surface.

### B3c. Text-only docx rebuilds must not inherit manuscript media

If `response_to_reviewers.docx` / `cover_letter.docx` / supplementary text-only docx grow to >100 KB after a rebuild, suspect `--reference-doc` pulling manuscript figure media. Verify with `unzip -l output.docx | grep word/media/` — should be empty for text-only artifacts.

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
