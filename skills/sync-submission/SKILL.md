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
| Pre-flight gate | `qc/preflight_gate_report.json` | Aggregated halt-on-failure manifest (see "Pre-flight gate" below) |

## Pre-flight gate (single command — last step before freeze)

Run this once, right before `freeze`/submission. It orchestrates the existing
deterministic checks and the `/verify-refs` audit into one halt-on-failure gate,
writes a single aggregated manifest (`qc/preflight_gate_report.json`), and exits
**non-zero** so a build wrapper or CI step can stop the freeze. It shells out to
the per-check scripts and reimplements none of them — the halt decision is driven
by each sub-check's normalized exit code.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/preflight_gate.py" --project-root . --journal chest
# add --strict to also halt on the heuristic/conditional (P1) checks
# add --online to make fabricated / author-mismatched references halt (PubMed/CrossRef)
# add --double-blind to make the asset-anonymization scan halt
```

By default the gate **halts only on the unambiguous, deterministic errors** (P0):
leftover placeholder/markers (`check_placeholders.py`), undefined `[@key]`
citations (`check_citation_keys.py`), duplicate references (`verify_refs.py`,
offline-deterministic), and a canonical-vs-submission hash mismatch
(`sync_submission.py audit`). The heuristic or conditional checks — `check_xref`,
`detect_copy_divergence`, `scope_drift_check`, `cover_letter_drift_check`,
`cross_document_n_check`, `check_cross_artifact_stale` — **run and report as P1
`warn` but do not halt** unless promoted with `--strict` or `--require ID`;
`check_asset_anonymization` is P1 unless `--double-blind`. A check whose inputs are
absent (no rendered docx, no cover letter, no copies, no journal) is recorded
`skipped`, never a blocker. Exit codes: `0` clean, `1` halt (≥1 blocker), `2` gate
config error (e.g. a `--require`'d check could not run).

The gate's offline references pass is the deterministic subset (duplicates +
pagination placeholders); an online `/verify-refs --strict` against PubMed/CrossRef
remains the authoritative fabrication and author-name check before submission.

## Workflow

1. Resolve canonical manuscript from `project.yaml` or explicit input.
2. Run the script in the requested mode.
3. If `audit` reports `DRIFT`, do not retarget or freeze until the user either
   patches the canonical manuscript or records the difference as journal-only.
4. If `build` succeeds, run `/verify-refs` before final submission.

## Quality Gates

- Gate 0 (pre-flight, last step before freeze): run `scripts/preflight_gate.py --project-root . --journal {journal}` to aggregate the deterministic checks below into one halt-on-failure manifest (`qc/preflight_gate_report.json`). Non-zero exit blocks the freeze. See "Pre-flight gate" above for the P0/P1 tiering and flags. This orchestrates Gates 1–3, 5b, 8, 9, 11 plus the placeholder and citation-key checks; the individual gates remain runnable on their own.
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
- Gate 11 (Phase 8 multi-copy divergence): when the project hand-maintains more than one manuscript copy (working SSOT, circulation, portal), run `scripts/detect_copy_divergence.py --ssot <ssot>.md --copy <copy>.md ...` before freeze or circulation. Any `STALE_COPY` (an SSOT numeric claim or heading that did not propagate to a copy) is a P0 drift. See "Phase 8 — Multi-copy manuscript divergence" below.
- Gate 12 (target-journal metadata drift): on `build` / retarget, cross-check the target the manuscript is written *for* against the target the project is being submitted *to*. Compare `project.yaml` `target` (and any in-manuscript header/footer "for submission to X" string) against the journal the package is built for, and check the structural metadata the target dictates — abstract heading structure (4- vs 5-heading), body word limit, citation style (Vancouver / AMA), required elements (Highlights / Central Illustration / Key Points). A mismatch (e.g., a header still reading the previous journal after a cascade retarget, or a 4-heading abstract for a 5-heading target) is a target-restructure trigger — branch to v_(N+1) per `manuscript-versioning.md` §2 and sync every sidecar (cover letter, title page, ICMJE COI list) — not a silent build.

  ```bash
  # header target vs project.yaml target
  TGT=$(python3 -c "import yaml;print(yaml.safe_load(open('project.yaml')).get('target',''))" 2>/dev/null)
  grep -niE 'for submission to|submitted to|prepared for' manuscript/manuscript.md   # compare against "$TGT"
  ```

- Gate 13 (body word count vs journal cap — the revision-inflation trap): resolving reviewer majors monotonically *adds* words, so a revised body silently breaches the target journal's limit. Before freeze (and after **every** `/revise` pass), run `scripts/check_wordcount_cap.py` against the target journal profile's body cap. `WORDCOUNT_OVER_CAP` is a P0 (relocate methods/sensitivity detail to the Supplement); `WORDCOUNT_NEAR_CAP` (>0.95×) warns that the next pass will breach. The binding number is the **rendered** count (citeproc expands `[@key]` → "(Author Year)"), so prefer the built DOCX count with `--rendered-words N`; otherwise the script estimates it from the markdown body + inline-citation expansion.

  ```bash
  python3 "${CLAUDE_SKILL_DIR}/scripts/check_wordcount_cap.py" \
    --manuscript manuscript/manuscript.md \
    --journal-profile "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/find-journal/references/journal_profiles/<Journal>.md" \
    --article-type "Original Article" --out qc/wordcount_cap.json --strict
  # or, deterministic: --limit 4000   (and --rendered-words N from the built DOCX when available)
  ```

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

## Phase 8 — Multi-copy manuscript divergence

When a project keeps several hand-maintained manuscript copies — `manuscript.md`
(the working SSOT), `manuscript_circulation.md` (co-author feedback), and
`submission/<journal>/manuscript.md` (portal) — a batch of edits applied to the
SSOT routinely lands in only some of the copies. The portal then receives a copy
missing a subset of the edits, and the divergence surfaces (if at all) only when a
reviewer notices the inconsistency.

Before freezing a package or sending a circulation round, run the directional
detector (SSOT → each copy):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/detect_copy_divergence.py \
  --ssot manuscript.md \
  --copy manuscript_circulation.md \
  --copy submission/<journal>/manuscript.md \
  --out qc/copy_divergence.json --strict
```

It reports, per copy, the SSOT *claims* (numeric assertions — `n = N`, percentages,
`p`, OR/HR/RR, 95% CI — and section headings) that did not propagate. A `STALE_COPY`
(`DIVERGENT` overall) is a **P0 blocker**: re-propagate the unpropagated claims, or —
better — stop hand-maintaining parallel copies and **generate the circulation /
submission variants from the single SSOT via a build step** (pandoc transform), so
there is only one editable source. Claims are matched as normalized strings, so
wording differences do not register — only a changed or absent number/heading does;
legitimately copy-specific content (a circulation cover note) shows up as `copy_only`
and can be ignored.

## Phase 9 — Springer Editorial Manager packaging (no title-page slot)

Some Springer Editorial Manager journals offer only **Manuscript / Figure / Table / Supplementary / LaTeX** upload item types — no separate Title Page or Cover Letter slot, and sometimes no Graphical Abstract slot. Common for observational / cohort submissions.

- **Title page → page 1 of the Manuscript file.** Build via pandoc: title-page markdown (strip internal-only blocks such as a "Manuscript Metrics" QC block, plus any Funding / Author Contributions / Keywords that also appear later) + a real docx page break (raw OpenXML `<w:br w:type="page"/>`; a bare `\newpage` is silently dropped in docx output) + the manuscript body **with its byline / affiliations / corresponding-author footnote removed** so the title page is not duplicated.
  - Verify: at least one page break; the affiliation block appears once; the article title is followed directly by the Abstract (no repeated byline); no internal QC strings leak.
- **Cover letter → paste into the "comments to the publication office" free-text field.**
- **Graphical Abstract (no dedicated slot) → upload as a Figure with Description = "Graphical Abstract".**
- **Declarations completeness (portal hard checkbox).** The manuscript "Statements and Declarations" must carry all seven Springer subheadings: Funding; Competing Interests; Ethics Approval; Consent to Participate; Consent for Publication; Author Contributions; Data Availability. For de-identified observational / registry studies, Consent to Participate = waived (existing de-identified records) and Consent for Publication = "Not applicable; only de-identified data, no individual person's identifying details, images, or videos".

```bash
for s in Funding "Competing Interests" "Ethics Approval" "Consent to Participate" "Consent for Publication" "Author Contributions" "Data Availability"; do
  unzip -p manuscript.docx word/document.xml | sed 's/<[^>]*>//g' | grep -q "$s" && echo "OK $s" || echo "MISSING $s"; done
```

- **Ethics approval / exemption number (observational or exempt cohort).** State the IRB approval or exemption reference number in the ethics statement. Institutional exemption notices carry the reference in the document body; filename digits are usually a receipt number, not the approval number — open the notice before writing the ethics block.
- **Word limit "including references".** When the limit counts references, the binding constraint is body+references words, not the reference-count ceiling. Measure body+refs on the rendered docx before adding references; each Vancouver reference is roughly 25–33 rendered words.
- **Submitting via a co-author's account.** Editorial Manager auto-adds the account holder at the top of the author list, tagged first/corresponding. De-duplicate, reorder to the intended position, reassign the first-author tag to the true first author, and fill missing co-author email/ORCID.
- **Re-read the EM-compiled submission PDF before Approve** — author order, degrees, ethics number, references, declarations, and figures.

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
