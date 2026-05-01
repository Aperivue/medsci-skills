---
name: manage-refs
description: >
  Cross-cutting reference manager for medical manuscripts. Single entry point
  for citation-key validation, journal-CSL pandoc rendering, manuscript ↔ DOCX
  cross-reference QC, marker conversion (``[N]`` ↔ ``[@key]``), and native
  Zotero CWYW field-code injection. Replaces the inline reference-handling
  that previously lived in ``/write-paper`` Phase 7.6 and is reused by
  ``/revise``, ``/peer-review``, ``/sync-submission``, and any skill that
  produces a journal submission. Audit-only verification stays in
  ``/verify-refs`` — this skill writes (renders, injects, converts); that
  skill only reads.
triggers: manage-refs, references, citation, citation keys, pandoc citeproc, journal CSL, CSL swap, cascade rejection re-render, cross-reference QC, [@bibkey], Zotero CWYW, ADDIN ZOTERO_ITEM, marker conversion, [N] to [@key], reference manager, render manuscript, check_citation_keys, check_xref
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Manage-Refs Skill

You are routing reference-handling work for a medical manuscript. The user is
somewhere in the lifecycle — drafting, building a circulation DOCX, swapping
CSL after a journal rejection, fixing a cross-reference defect surfaced by
QC, or wiring up live Zotero field codes for a co-author Word workflow. Pick
the right tool from the decision table; do not invent a parallel pipeline.

## Why This Skill Exists

Reference handling spans every late-stage skill: `/write-paper` builds the
first DOCX, `/revise` rebuilds it after each reviewer round, `/peer-review`
emits a critique that quotes references back, `/sync-submission` packages the
final tarball, `/find-journal` informs CSL swaps on rejection cascade, and
`/verify-refs` audits the bibliography. Until 2026-05-01 these scripts lived
under `skills/write-paper/scripts/`, which made `/revise` and `/sync-submission`
silently depend on a sibling skill — a layering inversion that broke when
`/write-paper` was loaded into a non-research project. Moving the
lifecycle tools here turns reference handling into a first-class concern
with one decision tree, one set of CSL files, and one provenance file
(`NOTICE.md`) for the vendored Zotero CWYW writer.

Validated 2026-05-01 against a 21-reference meta-analysis manuscript
(RFA-Adjunct ER submission) for both pandoc-citeproc and Zotero-CWYW paths.

## Anti-Hallucination Guarantees

1. **Citekey discipline (Phase 0)**: every in-text citation must be
   `[@bibkey]` resolvable in `refs.bib`. `scripts/check_citation_keys.py` is
   a hard gate — UNDEFINED keys exit non-zero and block the build.
2. **No hand-typed References list** — references are always rendered by
   pandoc citeproc + journal CSL or by the Zotero Word plugin (CWYW). See
   `~/.claude/rules/manuscript-references.md`.
3. **Zotero metadata is never invented** — `inject_zotero_cwyw.py` fetches
   item data live from `http://localhost:23119`. Any HTTP failure aborts
   with a non-zero exit so partial bibliographies never reach the user.
4. **Marker conversion is mapping-driven** — `md_marker_convert.py` will
   never guess a Zotero key for a number; unmapped markers stay as `[N]`
   and are reported on stderr.
5. **Cross-reference QC is a submission gate** — `scripts/check_xref.py`
   `--strict` exits 1 on any `MISSING_DOCX` / `MISSING_BODY` / `MISMATCH`,
   blocking pipelines that try to ship a DOCX whose Table/Figure citations
   don't match captions.
6. **Audit boundary**: this skill writes; bibliographic correctness against
   PubMed/CrossRef stays in `/verify-refs`. Always invoke `/verify-refs`
   after a render before signing off — one read-only audit, one writer.

## Decision Tree

| Situation | Tool | Why |
|---|---|---|
| Validate `[@bibkey]` ↔ `refs.bib` (UNDEFINED / UNUSED keys) | `scripts/check_citation_keys.py` | Hard build gate, runs in seconds |
| Single-author submission lockdown, frozen output | `scripts/render_pandoc.sh -j <journal>` | Reproducible, CI-friendly |
| Cascade rejection (e.g., ER → JVIR → CVIR) | `render_pandoc.sh` with new `-j` | CSL swap reformats references in seconds |
| Reviewer revision: add 1–2 refs to a Word doc with co-authors live | Zotero Word plugin (user GUI) | Minimal disruption to track-changes flow |
| Reviewer revision: bulk reference change | Edit markdown SSOT, re-run `render_pandoc.sh` | Consistency, no cherry-pick risk |
| Migrate `[N]` numeric markers → `[@key]` for pandoc | `scripts/md_marker_convert.py --to-keys` | Mapping-driven, partial conversion safe |
| Convert `[@key]` → `[N]` for round-trip / debug | `scripts/md_marker_convert.py --to-numbers` | Same map, opposite direction |
| Wire native Zotero CWYW field codes into a .docx (live Refresh in Word) | `scripts/inject_zotero_cwyw.py` | Co-author Word workflow, post-circulation editability |
| Manuscript ↔ rendered DOCX cross-reference QC | `scripts/check_xref.py --strict` | Submission gate (P0 blocker on mismatch) |
| Bibliographic audit against PubMed / CrossRef | **delegate** to `/verify-refs` | Audit-only — keep writer/auditor separation |

## Workflows

### A. Pandoc citeproc (default for solo authors and final submissions)

User provides `manuscript.md` with `[@bibkey]` citations + `refs.bib`.
1. **Gate**: `python "${CLAUDE_SKILL_DIR}/scripts/check_citation_keys.py" manuscript.md refs.bib`
   — exits non-zero on UNDEFINED keys. Fix and re-run.
2. **Render**:
   ```bash
   "${CLAUDE_SKILL_DIR}/scripts/render_pandoc.sh" \
     -j european-radiology \
     -i manuscript.md \
     -b refs.bib \
     -o manuscript_final.docx
   ```
   Bundled CSLs (in `citation_styles/`): `european-radiology`, `radiology`,
   `american-journal-of-roentgenology`, `cardiovascular-and-interventional-radiology`,
   `korean-journal-of-radiology`, `vancouver`, `vancouver-superscript`,
   `springer-basic-brackets`, `springer-vancouver-brackets`. Use
   `radiology` for RYAI; use `vancouver` for JVIR (no dedicated CSL).
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
   Optionally stage with `--active-ns 1,2,3,4,19` for a sample build first
   (validated on RFA-Adjunct: 5-ref sample reduces Word Refresh blast radius
   when debugging).
2. **Render to .docx** with pandoc (workflow A) so the body has plain text
   `[@key]` markers, OR pre-build a .docx some other way that still contains
   plain `[@key]` text.
3. **Inject CWYW**:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/inject_zotero_cwyw.py" \
     --input manuscript_keys.docx --output manuscript_cwyw.docx \
     --user-id 16613550 --keys-from keys.txt
   ```
   The script fetches Zotero metadata via the local connector (port 23119);
   any HTTP failure aborts with non-zero exit.
4. **First-build instruction** (REQUIRED — see Known Limitation #1): open
   the output in Word → Zotero tab → **Add/Edit Bibliography** once. After
   that, **Refresh** keeps citations and bibliography in sync as authors
   edit.
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

## Quality Gates

This skill defines **three submission gates** and **one user approval gate**:

- **Gate 1 (citekey integrity)**: `check_citation_keys.py` exits non-zero on
  UNDEFINED keys. The pipeline halts; the user reviews and fixes.
- **Gate 2 (cross-reference integrity)**: `check_xref.py --strict` exits 1 on
  any `MISSING_DOCX` / `MISSING_BODY` / `MISMATCH` row. The user reviews
  `qc/xref_audit.json` and resolves before proceeding.
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

## Related

- `~/.claude/rules/manuscript-references.md` — global rule (decision tree
  this skill implements)
- `~/.claude/rules/agent-skill-routing.md` — skill router (this skill is the
  reference-handling row)
- `~/.claude/rules/zotero-workflow.md` — BBT auto-export, MCP setup
- `/verify-refs` — read-only audit (PubMed / CrossRef + first-author
  cross-check)
- `/lit-sync` — Zotero ↔ Obsidian sync, `refs.bib` provider
- `/write-paper` Phase 7.6 — calls this skill (one-line delegation)
- `/revise`, `/sync-submission`, `/find-journal` — call this skill on
  rebuild / re-render / cascade

## Known Limitations

1. **First-build empty BIBL field (CWYW)**: `inject_zotero_cwyw.py` writes a
   stub `ADDIN ZOTERO_BIBL` field; Word's Zotero Refresh treats an empty
   stub as user-customized and refuses to populate it. User must run
   Add/Edit Bibliography once. Subsequent Refresh works as expected.
   Validated on Word for Mac, RFA-Adjunct (2026-05-01).
2. **Webpage / non-journal item types**: handled by the patched
   `zotero_to_csl_json` that fetches Zotero's native CSL-JSON; do not bypass
   this patch.
3. **Surgical post-build regex patches are unsafe** — see Workflow B step 5.
4. **Local Zotero required for CWYW** — port 23119 must be reachable; no
   web-API fallback yet (would need `ZOTERO_API_KEY`). On failure the script
   aborts with non-zero exit so partial builds never ship.
