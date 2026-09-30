---
name: manage-refs
description: Use when references must be written, rendered or converted. Checks [@key] citation keys, renders the reference list with a journal CSL via pandoc, converts [N] markers, injects Zotero Word field codes and runs manuscript-DOCX cross-reference QC. Read-only auditing is /verify-refs.
model: inherit
metadata:
  triggers: "manage-refs, references, citation, citation keys, pandoc citeproc, journal CSL, CSL swap, cascade rejection re-render, cross-reference QC, [@bibkey], Zotero CWYW, ADDIN ZOTERO_ITEM, marker conversion, [N] to [@key], reference manager, render manuscript, check_citation_keys, check_xref"
---

# Manage-Refs Skill

Pick the tool from the Decision Tree; do not invent a parallel pipeline. References are never
hand-typed: the list is always rendered by pandoc citeproc + journal CSL or by the Zotero Word
plugin (CWYW). This skill writes (renders, injects, converts); bibliographic correctness against
PubMed/CrossRef stays in `/verify-refs` — one read-only audit, one writer.

## Decision Tree

| Situation | Tool | Why |
|---|---|---|
| Validate `[@bibkey]` ↔ `refs.bib` (UNDEFINED / UNUSED keys) | `scripts/check_citation_keys.py` | Hard build gate, runs in seconds |
| Single-author submission lockdown, frozen output | `scripts/render_pandoc.sh -j <journal>` | Reproducible, CI-friendly |
| Cascade rejection (e.g., ER → JVIR → CVIR) | `render_pandoc.sh` with new `-j` | CSL swap reformats references in seconds |
| Verify a journal CSL renders the in-text format / DOI / journal-name style the author guide actually requires | `scripts/check_csl_render.py --csl <x>.csl --bib refs.bib --journal <key>` | A stub/"dependent" CSL inherits its parent's format, which may differ from the guide (parenthetical vs superscript, DOI kept, full journal names). Run BEFORE submission, not after the proof PDF |
| Reference list prints FULL journal names but the journal wants NLM abbreviations | `scripts/fill_journal_abbrev.py` | Resolves each entry DOI → PMID → PubMed NLM `shortjournal` into the `.bib` so CSL `form="short"` renders abbreviations; never invents abbreviations |
| Reviewer revision: add 1–2 refs to a Word doc with co-authors live | Zotero Word plugin (user GUI) | Minimal disruption to track-changes flow |
| Reviewer revision: bulk reference change | Edit markdown SSOT, re-run `render_pandoc.sh` | Consistency, no cherry-pick risk |
| Migrate `[N]` numeric markers → `[@key]` for pandoc | `scripts/md_marker_convert.py --to-keys` | Mapping-driven, partial conversion safe |
| Convert `[@key]` → `[N]` for round-trip / debug | `scripts/md_marker_convert.py --to-numbers` | Same map, opposite direction |
| Wire native Zotero CWYW field codes into a .docx (live Refresh in Word) | `scripts/inject_zotero_cwyw.py` | Co-author Word workflow, post-circulation editability |
| Manuscript ↔ rendered DOCX cross-reference QC | `scripts/check_xref.py --strict` | Submission gate (P0 blocker on mismatch) |
| Figures/tables submitted as separate attachments (radiology, most medical journals) | `check_xref.py --strict --allow-separate-attachments` | Downgrades `MISSING_DOCX` to WARN; `MISSING_BODY`/`MISMATCH` remain P0 |
| **v_(N+1) docx build-time regeneration check** | `check_xref.py --vN-docx-md5 <prev>.docx [--vN-md <prev>.md]` | Identity = unmodified seed copy; missing diff lines = body not regenerated |
| **Duplicate bibliography in the built artifact** | `scripts/check_reference_duplication.py --docx <built>.docx` (or `--text <rendered>.md`) | `DUP_REF_HEADING` / `REF_NUMBER_RESTART` / `REF_SIGNATURE_DUP` (Major). Catches a hand-typed `## References` list plus the pandoc `--citeproc` auto-bibliography, which renders **two** lists (the second often after the legends). Run after any citeproc build |
| **Publisher markup in a `.bib` title** (renders as garbage) | `scripts/check_bib_title_markup.py --bib refs.bib --strict` | CrossRef titles carry `<scp>WHO</scp>` / `<i>IDH</i>`; BBT escapes them (`{$<$}scp{$>$}`) or strips them without restoring the space (`andTERTPromoter`). `verify_refs` proves the reference is *true*; this proves it will *print*. `TITLE_MARKUP` / `TITLE_FUSION` (Major) |
| **Master pre-submission gate** (recommended before any submission) | `scripts/pre_submission_gate.sh` | Chains `check_citation_keys` → `check_bib_title_markup` → `verify_refs --strict` → `render_pandoc` (optional) → `check_xref --strict`; single artifact `qc/pre_submission_gate.json` |
| Direct render with a built-in reference audit | `scripts/render_pandoc.sh` (audits the `.bib` via `/verify-refs` first; blocks on FABRICATED/MISMATCH/duplicates; reports UNVERIFIED rows as not clean, without blocking) | Best-effort (skips with a warning if `/verify-refs` is not alongside); opt out with `-S`. The master gate passes `-S` because it runs `verify_refs` in its stage 3 |
| Bibliographic audit against PubMed / CrossRef | **delegate** to `/verify-refs` | Audit-only — keep writer/auditor separation |

## Workflows

### A. Pandoc citeproc (default for solo authors and final submissions)

User provides `manuscript.md` with `[@bibkey]` citations + `refs.bib`.
1. **Gate**: `python3 "${CLAUDE_SKILL_DIR}/scripts/check_citation_keys.py" manuscript.md refs.bib`
   — exits non-zero on UNDEFINED keys. Fix and re-run. A `[@NEW:topic_slug]` drafting
   placeholder from `/write-paper` is reported as UNDEFINED too: resolve each by adding the
   citation to Zotero (`/lit-sync` then refreshes `refs.bib`) and replacing the placeholder with
   the real `[@bibkey]`. Never let a `[@NEW:...]` reach a rendered DOCX.
2. **Render**:
   ```bash
   "${CLAUDE_SKILL_DIR}/scripts/render_pandoc.sh" \
     -j european-radiology \
     -i manuscript.md \
     -b refs.bib \
     -o manuscript_final.docx
   ```
   For the current inventory and what each style renders, read
   `citation_styles/README.md` — that table is the registry. `render_pandoc.sh` also lists
   what is on disk when `-j` names a style it cannot find, so ask the script rather than
   trusting a list written here. Two standing fallbacks: use `radiology` for RYAI and
   `vancouver` for JVIR (neither has a dedicated CSL).
3. **QC**:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_xref.py" \
     --md manuscript.md --docx manuscript_final.docx \
     --out qc/xref_audit.json --strict
   ```
   Treat `submission_safe: false` as a halt. Route fixes by symptom — see
   the table in `references/check_xref_symptoms.md`.
4. **Audit hand-off**: invoke `/verify-refs` for the PubMed/CrossRef audit
   before sign-off.

### B. Zotero CWYW (co-author Word workflow)

User has a markdown SSOT and wants reviewers to edit citations directly in
Word. Each reference must already exist as a Zotero item; the user supplies
a `[N] → ZoteroKey` mapping.
1. **Convert markers**:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/md_marker_convert.py" \
     --input manuscript.md --output manuscript_keys.md \
     --map ref_map.json --to-keys
   ```
   The conversion never guesses a Zotero key for a number: unmapped markers stay as `[N]` and
   are reported on stderr. Optionally stage with `--active-ns 1,2,3,4,19` for a sample build
   first (a 5-reference sample limits the Word Refresh blast radius while debugging).
2. **Render to .docx** with pandoc (workflow A) so the body has plain text
   `[@key]` markers, OR pre-build a .docx some other way that still contains
   plain `[@key]` text.
3. **Inject CWYW**:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/inject_zotero_cwyw.py" \
     --input manuscript_keys.docx --output manuscript_cwyw.docx \
     --user-id <zotero-user-id> --keys-from keys.txt
   ```
   The script fetches item metadata live from the local Zotero connector (port 23119), so
   Zotero must be running locally; there is no web-API fallback. Any HTTP failure aborts with a
   non-zero exit, so a partial bibliography never reaches the user. Never invent Zotero metadata.
4. **First-build instruction** (REQUIRED): the script writes an empty `ADDIN ZOTERO_BIBL`
   stub, which Word's Zotero Refresh treats as user-customized and refuses to populate. Open
   the output in Word → Zotero tab → **Add/Edit Bibliography** once. After that, **Refresh**
   keeps citations and bibliography in sync as authors edit.
5. **Surgical patches are unsafe**: for ref additions in later rounds, edit
   the markdown SSOT and rebuild the whole .docx instead of regex-patching
   the post-CWYW file. Zotero's rendered `[N]` superscripts can collide
   with plain `[N]` markers and corrupt the field codes.

### C. Cascade rejection re-render (find-journal hand-off)

User got rejected from journal A and `/find-journal` recommended journal B.
1. Confirm the new CSL exists in `citation_styles/` (or fetch from
   https://citationstyles.org/styles and drop in).
2. Re-run `render_pandoc.sh -j <new-csl>` against the same `manuscript.md` +
   `refs.bib`.
3. Re-run `check_xref.py --strict`.
4. Re-run `/verify-refs` if any new references were added during the
   inter-journal revision.

### D. Cross-reference QC only

User shipped a manuscript and a reviewer flagged a Table/Figure mismatch.
1. Run `check_xref.py --strict` on the current `manuscript.md` + `.docx`.
2. Inspect `qc/xref_audit.json`. Body caption is the SSOT — fix `manuscript.md`
   and rebuild, never patch the .docx by hand.
3. See `references/check_xref_symptoms.md` for the
   `MISSING_BODY` / `MISSING_DOCX` / `MISMATCH` triage table.
4. For journals that accept figures and tables as **separate attachment files**
   (European Radiology, Radiology, AJR, JVIR, KJR, and most medical journals), pass
   `--allow-separate-attachments`. It downgrades two rows, reported apart because their
   evidence differs:

   - `MISSING_DOCX` — a `--docx` was supplied and **proved** the float is not in
     the rendered main document. That is what a separate attachment looks like.
   - `MISSING_BODY` with **no `--docx` supplied** — nothing was checked. Excused on your word,
     printed as `EXCUSED WITHOUT EVIDENCE`, and counted in `summary.downgraded_unchecked`.

   `MISMATCH` stays P0. So does `MISSING_BODY` when the float **is** in the
   rendered DOCX — that is SSOT drift, which no attachment policy excuses.

   **Run once with `--docx` before submitting.** The flag is a declaration, not a
   verification; supplying the DOCX is what converts an excuse into evidence.

### D'. v_(N+1) docx regeneration check (build-time companion)

When building v_(N+1) from a frozen v_N, the v_(N+1) docx MUST differ
from v_N docx by content — a byte-identical copy is a silent seed-copy
that will revert markdown edits at peer review. `check_xref.py` carries
two flags for the build-time companion to the submission-time gate
in `/sync-submission`'s `scripts/verify_package_integrity.py --assert-vN-docx-changed`:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_xref.py" \
    --md manuscript_v2.md \
    --docx manuscript_v2.docx \
    --vN-docx-md5 manuscript_v1.docx \
    --vN-md manuscript_v1.md \
    --strict
```

- `--vN-docx-md5` alone: MD5 identity check. Identical bytes = FAIL.
- `--vN-docx-md5 + --vN-md`: additionally extracts the markdown-only diff
  between v_N and v_(N+1) and verifies each ≥40-char diff line appears
  verbatim (whitespace-normalized, case-insensitive) in the new docx
  body XML. Missing diff lines = body did not pick up the markdown edits.

Output records the result under `vN_docx_check` in `qc/xref_audit.json`.
Either failure mode causes a non-zero exit even without `--strict`.

### E. Master pre-submission gate (recommended end-to-end chain)

The single entry point that combines workflows A and D plus `/verify-refs`
into one aborting chain. Use this immediately before submission or before
circulating a v_N package to senior co-authors.

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/pre_submission_gate.sh" \
    --md manuscript/manuscript.md \
    --bib manuscript/_src/refs.bib \
    --docx submission/<journal>/manuscript.docx \
    --allow-separate-attachments    # omit if the journal accepts inline figures/tables
```

Stage order (first failure aborts):
1. `check_citation_keys.py manuscript.md refs.bib` — UNDEFINED / UNUSED keys
2. `check_bib_title_markup.py --strict` — publisher markup / tag-strip fusion in `.bib` titles
3. `verify_refs.py refs.bib --strict` — PubMed / CrossRef per-entry verification
4. `render_pandoc.sh -S -j <csl> -i ... -b ... -o ...` — invoked only when `--docx` is omitted
   (`--journal <csl>`, default `vancouver`)
5. `check_xref.py --md ... --docx ... --strict [--allow-separate-attachments]`

On success the chain writes `qc/pre_submission_gate.json` (plus the
per-stage artifacts `qc/bib_title_markup.json`, `qc/reference_audit.json` and
`qc/xref_audit.json`) with `submission_safe: true`. On any failure the JSON records the failing
stage and exit code, and the script exits non-zero — do not submit until
the failing stage passes.

The gate does **not** reimplement any check; it calls the existing scripts as subprocesses. A
new check belongs in the underlying script, which the gate then picks up.

### F. BibTeX author-format corruption (rendered-name check)

Entries written as `author = {Surname AB and Surname2 CD}` (family + initials, **no comma**) make BibTeX treat the last token as the family name, rendering "AB S, CD S2". Always store `author = {Family, Full Given}`. Concatenated initials even with a comma (`Family, AB`) still collapse to a single initial under CSL `initialize-with`, so use the full forename from PubMed `efetch`.

`/verify-refs` compares bib content against PubMed but does not see the rendered output; grep the rendered docx and the bib separately:

```bash
unzip -p out.docx word/document.xml | sed 's/<[^>]*>//g' | grep -oE "[A-Z]{2} [A-Z], [A-Z]{2} [A-Z]"   # corruption signature in output
grep -nE 'author\s*=\s*\{[A-Z][a-z]+ [A-Z]{1,3}( |\})' refs.bib                                          # no-comma source entries
```

## Quality Gates

This skill defines **three submission gates** and **one user approval gate**:

- **Gate 1 (citekey integrity)**: `check_citation_keys.py` exits non-zero on
  UNDEFINED keys. The pipeline halts; the user reviews and fixes.
- **Gate 2 (cross-reference integrity)**: `check_xref.py --strict` exits 1 on
  any `MISSING_DOCX` / `MISSING_BODY` / `MISMATCH` row. The user reviews
  `qc/xref_audit.json` and resolves before proceeding. Under
  `--allow-separate-attachments`, check `summary.downgraded_unchecked` as well as
  `submission_safe`: a non-zero count means rows passed without being checked.
- **Gate 3 (audit hand-off)**: before sign-off, the user must run
  `/verify-refs` and confirm `submission_safe: true` in
  `qc/reference_audit.json`. This skill never marks the bibliography
  audited on its own.
- **User approval gate (CWYW first build)**: the user must perform Word →
  Zotero → Add/Edit Bibliography manually after the first
  `inject_zotero_cwyw.py` build. The skill cannot automate this and warns
  on stderr that it is required.

## Provenance

`scripts/_vendor_citation_writer.py` is vendored from
`alisoroushmd/zotero-mcp` @ `ed5dfb71`, MIT licensed. See
[`NOTICE.md`](./NOTICE.md) and [`LICENSE.zotero-mcp`](./LICENSE.zotero-mcp).

## Known Limitations

- **Webpage / non-journal item types**: handled by the patched
  `zotero_to_csl_json` that fetches Zotero's native CSL-JSON; do not bypass
  this patch.
