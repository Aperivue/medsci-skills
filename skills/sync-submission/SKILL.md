---
name: sync-submission
description: Audit SSOT-to-submission drift and create journal submission manifests from canonical manuscript artifacts.
triggers: sync submission, build submission, submission drift, SSOT sync, journal package, retarget journal, freeze submission
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Sync Submission

Keep the canonical manuscript and journal-specific submission packages from drifting apart.
Treat `submission/{journal}/` as derived output and record whether it is current, stale, or frozen.

## Inputs

1. Project root containing `project.yaml`, or a direct canonical manuscript path.
2. Journal short name, e.g. `chest`, `ryai`, `academic_radiology`.
3. Optional mode:
   - `audit`: compare existing submission against canonical source.
   - `build`: copy canonical source and optional declared final artifacts, preserving file bytes, and write metadata.
   - `freeze`: freeze the chosen byte snapshot with its available check context (not submission approval).

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

The registry is a project-local YAML mapping author identifiers (full names, native scripts, initials with/without periods, email, ORCID) to role labels (e.g., "Reviewer 1"); schema in `scripts/author_registry_example.yaml`. Never commit a populated registry to a public repository, because it lists the authors' identities — keep it next to the manuscript.

## Output Contract

| Artifact | Path | Purpose |
|---|---|---|
| Submission metadata | `submission/{journal}/.journal_meta.json` | Source hash, status, canonical path |
| Sync audit | `qc/submission_sync_{journal}.json` | Drift result consumed by orchestrator |
| Manifest update | `artifact_manifest.json` | Submission package registry |
| Pre-flight gate | `qc/preflight_gate_report.json` | Aggregated halt-on-failure manifest (see "Pre-flight gate" below) |
| Supplement structure | `qc/supplement_structure.json` | Gate 14: index↔file 1:1, sub-section gaps, callout coverage |

For a complete bundle, run the existing renderers first, then `build --bundle-spec bundle.json`.
The declaration adds final Word/PDF, supplement, cover-letter, table/figure and notice files with
pinned render-input hashes and reuse-rights records. Copies preserve file bytes; content and visual
fidelity stay `not_assessed` until separately reviewed. Build refuses edited or frozen outputs and
destructive path collisions. Read [bundle workflow](references/bundle_workflow.md) for the schema,
a runnable synthetic example and the limits of each recorded check.

## Pre-flight gate (single command — last step before freeze)

Run this once, right before `freeze`/submission:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/preflight_gate.py" --project-root . --journal chest
# add --strict to also halt on the heuristic/conditional (P1) checks
# add --online to make fabricated / author-mismatched references halt (PubMed/CrossRef)
# add --double-blind to make the asset-anonymization scan halt
```

It shells out to the per-check scripts (reimplementing none), writes
`qc/preflight_gate_report.json`, and exits `0` clean, `1` halt (≥1 blocker), `2` gate config error
(e.g. a `--require`'d check could not run). A non-zero exit blocks the freeze.

- **P0 — halts by default** (unambiguous, deterministic errors): leftover placeholder/markers
  (`check_placeholders.py`), undefined `[@key]` citations (`check_citation_keys.py`), duplicate
  references (`verify_refs.py`, offline-deterministic), a canonical-vs-submission hash mismatch
  (`sync_submission.py audit`), and an internal-audit dump in a reviewer-facing file
  (`check_checklist_dump_leak.py`).
- **P1 — runs and reports `warn`, halts only with `--strict` or `--require ID`:** `check_xref`,
  `detect_copy_divergence`, `scope_drift_check`, `cover_letter_drift_check`,
  `cross_document_n_check`, `check_cross_artifact_stale`; `check_asset_anonymization` is P1 unless
  `--double-blind`.
- A check whose inputs are absent (no rendered docx, no cover letter, no copies, no journal) is
  recorded `skipped`, never a blocker.

Do not read the report as approval. Its legacy `submission_safe` field means only "no configured
blocker/error"; `readiness` stays `not_assessed`; the optional bundle hash binding identifies the
package present during the run, not per-file visual inspection or every external check input. Run
`audit` again after preflight to expose current, stale or unbound evidence. Freeze records a byte
snapshot and its available check context; it does not run preflight or approve source fidelity or
reuse permissions.

**Audit-dump leak check (P0).** A `/check-reporting` or `/self-review` report is an internal working audit — auto-fix annotations, a raw JSON block (`compliance_pct`, `fixable_by_ai`, `check_reporting_version`), pipeline-log paths, "Action Items". It is not the official reporting checklist a journal expects and must never reach a reviewer, even when its filename looks official (e.g. `STROBE_checklist_v4.pdf` reused into a later package). `scripts/check_checklist_dump_leak.py --dir submission/` scans every `.md`/`.docx`/`.pdf` in the package for these tokens; any hit is a P0 `leak`. The pre-flight runs it over the journal asset directory; confirm `submission_safe: true` before freeze. Writes `qc/checklist_dump_leak.json`.

**Disclosure & availability check (standalone).** Top medical-AI journals require, before review, an AI-use disclosure carrying four tokens (version + access channel + date/date-range + responsible party — the tool name only *triggers* the check) and Data/Code Availability statements. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/check_disclosure_availability.py --manuscript <file> --journal <stem> [--ai-study] [--require data_availability ...] [--strict]` (reads `references/journal_availability_policy.json`). It blocks on a missing required statement or an AI disclosure that is present but missing a token / carrying a placeholder; "available on reasonable request" where the journal expects a repository is a P1 warning. Writes `qc/disclosure_availability_report.json`.

## Workflow

1. Resolve canonical manuscript from `project.yaml` or explicit input.
2. Run the script in the requested mode.
3. If `audit` reports `DRIFT`, do not retarget or freeze until the user either
   patches the canonical manuscript or records the difference as journal-only.
   Never silently merge submission edits back into the SSOT, and never hide a
   journal-only difference — record it as drift or an explicit exception.
4. If `build` succeeds, run `/verify-refs` before final submission.
5. Call a package current only when its source hashes match, and mark it submitted
   only through `freeze`, which writes `.journal_meta.json`.

## Quality Gates

- Gate 0 (pre-flight, last step before freeze): run `scripts/preflight_gate.py` as in "Pre-flight gate" above; non-zero exit blocks the freeze. It orchestrates Gates 1–3, 5b, 5c, 5d, 8, 9, 11, 11b, the Phase 3b/3c checks, and the placeholder and citation-key checks; each gate also runs on its own.
- Gate 1: block freezing when canonical manuscript is missing.
- Gate 2: block retargeting when the previous submission has unresolved drift.
- Gate 3: require `/verify-refs` audit before marking a package submission-safe. The pre-flight's offline references pass covers only duplicates and pagination placeholders; an online `/verify-refs --strict` against PubMed/CrossRef is the authoritative fabrication and author-name check.
- Gate 4 (recursive docx walk): every docx stale-string audit must walk paragraphs + tables + nested-table cells recursively. `document.paragraphs` skips table cells, `document.tables` does not recurse, and `paragraph.runs` hides runs inside `<w:hyperlink>` — and figures, captions and reporting checklists often sit in 1×1 or nested tables. For run-level edits near hyperlinks or fields, inspect the paragraph XML, not `.runs`: a hidden inline element can look like an empty `()` and be "fixed" into a real defect.
- Gate 5 (portal free-text fields): cover letter, data availability, acknowledgements, abstract and author contributions are often typed into the portal, outside any docx this skill audits. Before freeze, diff the portal's final review page against the manuscript body 1:1 and treat each field as its own drift target.
- Gate 5c (portal-field markdown residue): portal paste-verbatim `.txt` fields (`abstract.txt`, `keywords.txt`, …) are cut from the markdown but never stripped of it, so a trailing `---`, a `**bold**`, or a `cm^2^` superscript publishes literally. The pre-flight runs `scripts/check_portal_field_residue.py --dir portal_fields/` (P1, `--strict`-promotable); only `.txt` is scanned (a `.md` is meant to carry markdown). Its Minor `char_expansion` advisory flags `≥`/`≤`, which ScholarOne expands to "{greater than or equal to}" (five words), inflating the word count — pre-substitute `>=`/`<=` (only `≥`/`≤`; `×` and the en-dash paste cleanly).
- Gate 5d (figure portal readiness): a figure bounces at the upload button for reasons decidable from the file on disk — byte size (JACC: Asia caps a figure at **25 MB**) and extension (SNAPP accepts only `.tiff`/`.jpeg`/`.eps`, rejecting `.png`). The pre-flight runs `scripts/figure_portal_readiness_check.py --figures-dir <dir>` (P1) over `submission/<journal>/figures` (or `./figures`), emitting `FIGURE_OVERSIZE` and — when the portal's formats are supplied, e.g. `--figure-accept tiff --figure-accept jpeg --figure-accept eps` — `FIGURE_FORMAT_REJECTED`. Fix by regenerating with `/make-figures export_portal_tiff.py` (LZW + RGBA→RGB flatten). No figures directory → skipped, never an error.
- Gate 6 (double-blind journals): a clean manuscript blind does not imply a clean portal blind. Before freeze, export the portal's blinded review PDF — the authoritative drift detector — and grep for all author identifiers across the entire upload set: manuscript; supplementary materials (especially methodology logs, agreement metrics, amendment logs); cover letter (a separately uploaded file is reviewer-visible unless toggled "Don't show in review PDF"); registry/approval PDFs (PROSPERO, ClinicalTrials.gov, IRB); portal Letter-field text if a signature was pasted; response-to-reviewers in revision rounds. Cover both period and no-period initials (`G.S.` and `GS`), full names in roman + native scripts, institution names, ORCID IDs and submission email domains.
- Gate 7 (text-only docx rebuilds): never use `pandoc --reference-doc=manuscript.docx` for response/cover/supplementary text-only docx, because the reference docx ships its embedded media (figure files) into the new docx, bloating it 50–100×. Use plain `pandoc input.md -o output.docx`. If such a file grows past 100 KB, `unzip -l output.docx | grep word/media/` should come back empty.
- Gate 5b (cover-letter free-text drift): before freeze — see Phase 4.
- Gate 8 (cross-document N consistency): before freeze — see Phase 5.
- Gate 9 (intra-manuscript scope drift): see Phase 6.
- Gate 10 (v_(N+1) docx regeneration): when building from a frozen prior version — see Phase 7.
- Gate 11 (multi-copy divergence): before freeze or circulation — see Phase 8.
- Gate 11b (reframe / headline-change survivor scan): after a revision that **reframes a claim class** (e.g. retires "location-stratified benchmark" for "overall pooled") or **changes a headline number**, the old term/value often survives in an untouched paragraph, legend, the supplement or the response letter — even when the letter claims the change was applied "throughout". Pass the retired vocabulary and superseded values from the reframe diff to the cross-artifact gate, which scans the **body and every aux artifact**:
  ```bash
  python3 "${CLAUDE_SKILL_DIR}/scripts/check_cross_artifact_stale.py" \
      --manuscript manuscript.md --aux supplement/ --aux figures/legends.md --aux revision/response_to_reviewers.md \
      --retired-term "location-stratified benchmark" --old-value 1.72
  ```
  A `retired_framing_survivor` / `stale_old_value` finding is a P1 stale claim-site. `--aux` takes files or folders: `.docx` sidecars are read, and figure scripts (`.py`/`.R`) are swept for stale literals only. An `--aux` that holds no readable file exits 2 instead of passing, and unreadable documents (`.pdf`, `.pptx`, …) are listed as not checked. For any wording or number change, also grep the OLD string across the entire SSOT tree, never a subset, and watch for substring near-misses — an exact grep for `expertise-dependent patterns` passes while `expertise-dependent evaluation patterns` stays stale.
- Gate 12 (target-journal metadata drift): on `build` / retarget, compare the target the manuscript is written *for* — `project.yaml` `target` (and any in-manuscript header/footer "for submission to X" string) — against the journal the package is built for, and check the structural metadata the target dictates — abstract heading structure (4- vs 5-heading), body word limit, citation style (Vancouver / AMA), required elements (Highlights / Central Illustration / Key Points). A mismatch (e.g., a header still reading the previous journal after a cascade retarget, or a 4-heading abstract for a 5-heading target) is a target-restructure trigger — branch to v_(N+1) and sync every sidecar (cover letter, title page, ICMJE COI list) — not a silent build.

  ```bash
  # header target vs project.yaml target
  TGT=$(python3 -c "import yaml;print(yaml.safe_load(open('project.yaml')).get('target',''))" 2>/dev/null)
  grep -niE 'for submission to|submitted to|prepared for' manuscript/manuscript.md   # compare against "$TGT"
  ```

- Gate 13 (body word count vs journal cap — the revision-inflation trap): resolving reviewer majors adds words, so a revised body silently breaches the journal's limit. Before freeze and after **every** `/revise` pass, run `scripts/check_wordcount_cap.py` against the target journal profile's body cap. `WORDCOUNT_OVER_CAP` is a P0 (relocate methods/sensitivity detail to the Supplement); `WORDCOUNT_NEAR_CAP` (>0.95×) warns that the next pass will breach. The binding number is the **rendered** count (citeproc expands `[@key]` → "(Author Year)"), so prefer the built DOCX count with `--rendered-words N`; otherwise the script estimates it from the markdown body + inline-citation expansion.

  ```bash
  python3 "${CLAUDE_SKILL_DIR}/scripts/check_wordcount_cap.py" \
    --manuscript manuscript/manuscript.md \
    --journal-profile "${CLAUDE_SKILL_DIR}/../find-journal/references/journal_profiles/<Journal>.md" \
    --article-type "Original Article" --out qc/wordcount_cap.json --strict
  # or, deterministic: --limit 4000   (and --rendered-words N from the built DOCX when available)
  ```

- Gate 14 (supplement structure — the numbering lock): a supplement of `S{N}_*.md` sections plus an index, hand-concatenated into `_combined.md`, desynchronizes across revision rounds — an index row with no file, a file the index never lists, two files claiming the same `S{N}`, a sub-section gap after an insert (`S6.3` then `S6.5`) — and "Supplementary Table S9" opens the wrong content. Before freeze, run `scripts/assemble_supplement.py` to validate index↔file 1:1, rebuild `_combined.md` in index order (reproducible rather than hand-maintained), and — with `--manuscript` — report body callouts with no section file (`CALLOUT_WITHOUT_SECTION`) and section files the body never cites (`SECTION_UNCITED`). The four structural kinds are P0 under `--strict`; coverage findings are advisory.

  ```bash
  python3 "${CLAUDE_SKILL_DIR}/scripts/assemble_supplement.py" \
    --dir submission/{journal}/supplementary --index 00_index.md \
    --manuscript manuscript/manuscript.md \
    --out submission/{journal}/supplementary/_combined.md \
    --json qc/supplement_structure.json --strict
  ```

## Phase 3b — Portal fields that REPLACE the manuscript

On some portals the box, not the manuscript, is what gets published. SNAPP says so at Author
Contributions, Competing Interests, Data Availability and Acknowledgements: "This replaces any
statement written within the manuscript and is the one that we will publish." A declaration that
lives only in the manuscript then vanishes from the published record, and nothing warns you. Two
that nearly did:

- **Co-first authorship.** A `†` title-page footnote. There is **no equal-contribution
  checkbox** — unless "X and Y contributed equally to this work" is typed into the Author
  Contributions box, the published paper has no co-first authors.
- **"The funder had no role in study design…"** The structured *Research funding* field takes a
  funder and a grant ID and has nowhere to put a role disclaimer, so pasting only an AI-use note
  into the Acknowledgements box drops it.

**Do not hand-compose the boxes.** Generate them from the manuscript, then check:

```bash
SS="${CLAUDE_SKILL_DIR}/scripts"
# scaffold every replacing field straight from the manuscript (lifts the equal-contribution
# sentence in from the title page, which is the one place --emit cannot copy it from)
python3 "$SS/check_portal_mirror.py" --manuscript manuscript/manuscript.md \
  --profile "<...>/journal_profiles/npj_Digital_Medicine.md" --emit portal_fields/

# then verify nothing was lost on the way to the box
python3 "$SS/check_portal_mirror.py" --manuscript manuscript/manuscript.md \
  --portal-dir portal_fields/ --profile "<...>/npj_Digital_Medicine.md" \
  --out qc/portal_mirror.json
```

| Verdict | Fires when |
|---|---|
| `PORTAL_FIELD_NOT_MIRRORED` | A sentence in a replacing manuscript section has no home in that field's paste artifact. |
| `PORTAL_FIELD_MISSING` | The manuscript has the section, the journal replaces it, and no artifact exists — the field publishes empty or as the portal's auto-extraction guessed it. |
| `EQUAL_CONTRIBUTION_NOT_IN_PORTAL` | The manuscript asserts equal / co-first contribution and the Author Contributions text does not. |

All three are major and exit 1; the pre-flight runs this as P1 (`--strict`-promotable).

**Which fields replace is a journal fact, not a guess.** It is read from the journal profile's
`## Portal Mechanics` block (`Fields that REPLACE the manuscript: …`). For a journal whose portal
contract was never recorded the check exits 2 and asserts nothing — record the block at first
submission rather than inventing a contract. Matching is graded through `_quote_match.py`, so a
sentence re-flowed while pasting is not reported as lost.

## Phase 3c — CRediT integrity (not author order)

A contribution taxonomy is a published factual claim, but the work behind a term often leaves no
repository artifact (a legitimate Conceptualization may live only in email). So the taxonomy is
gated and corroboration is only a prompt.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_credit_integrity.py" \
  --manuscript manuscript/manuscript.md --out qc/credit_integrity.json
```

| Verdict | Severity | Fires when |
|---|---|---|
| `CREDIT_TERM_INVALID` | major | A term outside the official fourteen in a section that says CRediT — "Statistical analysis", "Manuscript writing", "Study design" read as CRediT and are not. The message names the intended term. |
| `CREDIT_INITIALS_UNRESOLVED` | major | Initials matching no author, or two — the residue a byline edit leaves. |
| `CREDIT_AUTHOR_UNLISTED` | major | A byline author with no contribution attributed (under ICMJE, an authorship question or a dropped clause). |
| `CREDIT_UNCORROBORATED` | **prompt** | A term whose footprint is absent — Visualization on a paper with no figures, Software with no Code Availability statement, or (only with `--contribution-record`) a contributor absent from the record. |

**Never gate author order or equal-contribution designation** — they are negotiated, and
negotiation is legitimate. Answer a corroboration prompt with an attestation; do not fail the
build on an off-repo contribution. With fewer than two resolvable byline names the
author/initials cross-check is **skipped and says so**; with no contributions section the script
exits 2 and asserts nothing.

## Phase 4 — Cover-letter free-text drift

The cover letter's `## Article details` block — body word count, abstract word count, reference
count, table/figure count — is a sidecar that goes stale when a manuscript branches v_N →
v_(N+1) (word-limit retarget, abstract restructure, late reference batch), and no docx-level
audit covers it. `scripts/cover_letter_drift_check.py` measures the manuscript and compares it
to the letter's numeric claims:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/cover_letter_drift_check.py" \
    --manuscript manuscript.md \
    --cover-letter cover_letter.md \
    --refs refs.bib \
    --out qc/cover_letter_drift.json
```

Reference / table / figure counts must match exactly; abstract words tolerate ±5; body words
tolerate 5%, narrowed to the headroom when the letter states the count against the cap
("3,998/4,000 words"). Resolve drift by regenerating the cover letter from the manuscript at
v_(N+1) build time. The script never edits the cover letter, which stays a deliberate authored
artifact.

## Phase 5 — Cross-document N consistency

Abstract, body prose, PROSPERO record, cover letter, supplementary extraction sheets, INDEX and
PRISMA flow caption all repeat the same `k included` / `k excluded` / `N patients` totals, and
any disagreement reads to reviewers as a data-integrity or late-edit failure.
`scripts/cross_document_n_check.py` extracts every "N <noun>" claim by category (patients, cases,
included, excluded, nodules, tumors, studies_total); a category with more than one distinct
integer value is a P0 drift.

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

Treat `submission_safe: false` in `qc/cross_document_n.json` as a halt. Resolve drift by tracing
each location to its data artifact (extraction sheet, PRISMA cascade TSVs) and correcting the
document(s) that disagree with the locked count.

## Phase 6 — Intra-manuscript scope drift

`scripts/scope_drift_check.py` detects two P0 patterns:

- **SCOPE_DRIFT** — a numeric anchor (AUC, OR/HR/RR, sensitivity/specificity) in Limitations /
  Discussion but absent from Methods + Results, typically a late sensitivity analysis whose
  primary report never exists.
- **PROSPERO_DRIFT** — the PROSPERO record commits to one synthesis method (Freeman-Tukey,
  random-effects DerSimonian-Laird, bivariate, HSROC, Bayesian, etc.) and Methods uses another,
  or the record was updated and Methods stayed behind. With a Methods line saying "no amendment
  lodged", this is a documented silent protocol deviation.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/scope_drift_check.py" \
    --manuscript manuscript.md \
    --prospero prospero/prospero_v2.md \
    --out qc/scope_drift.json
```

Resolution: either (a) propagate the anchor into Methods + Results as a primary report or (b)
remove it from Limitations / Discussion. For synthesis-method drift, file a PROSPERO amendment
and update Methods to match — both must agree before submission.

PROSPERO's public-record "Print/PDF" export renders only the current amendment; older versions
are reachable only through the version-history dropdown. When citing PROSPERO version state,
never rely on a single PDF export — save each published version's PDF independently and state in
the cover letter/supplement which version anchors the methodology and which reflects a
documentation-only erratum. For such an erratum (a narrative fact, no change to
methods/eligibility/synthesis), prefer a single Revision-Note append over a new structured
amendment.

## Phase 7 — v_(N+1) docx regeneration gate

When a v_(N+1) is built from a frozen v_N package (after a markdown body edit, reviewer round,
or cascade-rejection re-target), the v_(N+1) docx MUST differ from the v_N docx. The common
silent revert is a `cp v_N/manuscript.docx v_(N+1)/manuscript.docx` step that skips the pandoc /
Zotero CWYW regeneration: the markdown is edited, but the portal receives the frozen v_N docx.
Run the byte-identity assertion at the top of the v_(N+1) submission gate — even when the
upstream pipeline appears to have regenerated the docx:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/verify_package_integrity.py" \
    --assert-vN-docx-changed \
    --vN-docx SUBMISSION/<journal>/v<N>/manuscript.docx \
    --new-docx SUBMISSION/<journal>/v<N+1>/manuscript.docx
```

Identical MD5 → exit 1. Block submission until the regeneration step is fixed.

## Phase 8 — Multi-copy manuscript divergence

When a project hand-maintains several manuscript copies — `manuscript.md` (the working SSOT),
`manuscript_circulation.md` (co-author feedback), and `submission/<journal>/manuscript.md`
(portal) — SSOT edits routinely land in only some copies. Before freezing a package or sending a
circulation round, run the directional detector (SSOT → each copy):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/detect_copy_divergence.py \
  --ssot manuscript.md \
  --copy manuscript_circulation.md \
  --copy submission/<journal>/manuscript.md \
  --out qc/copy_divergence.json --strict
```

It reports, per copy, the SSOT *claims* (numeric assertions — `n = N`, percentages, `p`,
OR/HR/RR, 95% CI — and section headings) that did not propagate. A `STALE_COPY` (`DIVERGENT`
overall) is a **P0 blocker**: re-propagate the claims, or — better — stop hand-maintaining
parallel copies and **generate the circulation / submission variants from the single SSOT via a
build step** (pandoc transform). Only a changed or absent number/heading registers, not wording;
legitimately copy-specific content (a circulation cover note) shows up as `copy_only` and can be
ignored.

## Phase 9 — Springer Editorial Manager packaging (no title-page slot)

Read `${CLAUDE_SKILL_DIR}/references/springer_em_packaging.md` when a Springer Editorial Manager
journal offers only Manuscript / Figure / Table / Supplementary / LaTeX upload item types (no
Title Page or Cover Letter slot).

## Phase 10 — Marked (tracked-changes) manuscript for a revision round

Every revision round asks for a **marked** manuscript: the revised paper with tracked changes against the version the reviewers saw.

**The baseline is R0, not the previous round.** The base of the diff is always the *originally reviewed* submission; only the target advances each round. An editor wants every change made since the version under review, so do not diff v7 against v8.

**Word's Compare is the only safe producer — but it is scriptable.** `pandiff` and LibreOffice `--compare` corrupt OOXML on real manuscripts (tables collapse, affiliation superscripts are lost); do not use them. Word for Mac exposes `compare` through AppleScript with `author name`, so the build needs no GUI pass and no post-hoc rewriting of `w:author`:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_marked_manuscript.py" \
  --original submission/{journal}/R0/manuscript.docx \
  --revised  submission/{journal}/R1/manuscript_clean.docx \
  --out      submission/{journal}/R1/manuscript_marked.docx \
  --author   "Submitting Author" --line-numbers
```

(macOS + Word only. On any other platform, produce the marked file in Word by hand — then still run the gate below.)

### The gate: a round trip, not a grep

"The marked file contains sentence X" passes even when Compare has dropped a paragraph, duplicated one, or split the revisions between two authors. Verify by construction — **accepting every revision must reproduce the revised manuscript exactly, and rejecting every revision must reproduce the original**:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_marked_manuscript.py" \
  --marked   submission/{journal}/R1/manuscript_marked.docx \
  --original submission/{journal}/R0/manuscript.docx \
  --revised  submission/{journal}/R1/manuscript_clean.docx \
  --author   "Submitting Author" --strict
```

The gate is move-aware: Word encodes relocated content as `w:moveFrom` / `w:moveTo`, not `w:ins` / `w:del`, and a verifier that knew only insert/delete would see a moved paragraph twice and call a good file corrupt. Read `${CLAUDE_SKILL_DIR}/references/marked_manuscript.md` when the gate reports a verdict, before writing any other docx probe, or when the marked file is too large to upload.
