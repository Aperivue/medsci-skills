# Phase 2.5d — Cross-Reference QC (Manuscript ↔ rendered DOCX)

Load-on-demand companion to `/self-review` Phase 2.5d. SKILL.md keeps the two gates,
the severity policy table, and the no-auto-fix rule; this file carries the precedent
failure, the input-location procedure, the reconciliation-block template, and the
comment-emission convention.

Read it when a rendered DOCX exists and the xref gate has fired.

Before the DOCX is built, run the **markdown-stage orphan gate** — every captioned
`Figure N.` / `Table N.` must be cited at least once elsewhere in the body:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_figure_citation.py" \
  --manuscript manuscript.md --out qc/figure_citation.json
```

`FIGURE_ORPHAN` / `TABLE_ORPHAN` (Minor) catch a newly-added float that has a legend
but no in-text citation — the early, no-build counterpart to `check_xref`'s `UNCITED`
verdict, which catches the same class on the rendered DOCX (below).

Reference-list integrity (Phase 2.5c) does **not** cover Table/Figure
cross-references. This is a separate failure mode where in-text citations
("Supplementary Table S4 reports a sensitivity analysis") resolve to a different
caption in the rendered DOCX ("Supp Table S4 = a diagnostics table") because the
build script carries its own legacy SSOT. Internal consistency (Phase 2.5)
cannot detect it — both the prose and the build artifact echo their own
divergent truths cleanly.

**Precedent failure pattern (an STROBE cohort manuscript revision):**
> Body prose cited Supp Table S4 as a sensitivity analysis; the rendered DOCX
> S4 instead contained a diagnostics table. S1, S6, S7 also mismatched. S8 and S9
> were cited in the manuscript but absent from the rendered DOCX entirely.
> Caught only on co-author circulation review.

**When to run:** every manuscript at self-review when a rendered DOCX exists
(e.g., circulation drafts, post-build pre-submission checks). Skip only if no
DOCX build has occurred yet (early drafts).

**Procedure:**

1. **Locate inputs.** `manuscript/manuscript.md` (or the SSOT `truth.manuscript_md`)
   and the rendered DOCX (typically `manuscript/manuscript_final.docx` or the
   most recent circulation `.docx`).

2. **Invoke the shared script** (lives in `/manage-refs`):

   ```bash
   python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/check_xref.py" \
     --md manuscript/manuscript.md \
     --docx manuscript/manuscript_final.docx \
     --out qc/xref_audit.json \
     [--allow-separate-attachments]
   ```

   The script writes `qc/xref_audit.json` with per-label rows tagged
   `OK | MISSING_DOCX | MISSING_BODY | MISMATCH | UNCITED | NOT_CITED_NO_BODY`,
   a top-level `submission_safe` boolean, and a `policy.allow_separate_attachments`
   field that records which severity policy applied.

3. **Translate findings to anticipated comments.** Severity mapping depends on
   the journal's figure/table submission policy. Many radiology and medical
   journals (e.g., European Radiology, Radiology, AJR) accept figures and tables
   as separate attachment files rather than inline in the manuscript DOCX; for
   those workflows pass `--allow-separate-attachments`. That flag downgrades two
   things, and they are not equally well evidenced — the audit JSON and the console
   output keep them apart, and so should you:

   - `MISSING_DOCX` — a `--docx` was supplied and PROVED the float is not in the
     rendered main document. That is what a separate attachment looks like.
   - `MISSING_BODY` where **no `--docx` was supplied** — nothing was checked. The
     float is either separately attached, as declared, or a caption nobody wrote.
     Excused on the author's word; counted in `summary.downgraded_unchecked`.

   `MISMATCH` remains P0 regardless. So does `MISSING_BODY` when the float IS in the
   rendered DOCX: the build pipeline is then the only place that knows the caption
   text, which is SSOT drift and not an attachment style.

   | Status | Default policy | With `--allow-separate-attachments` |
   |---|---|---|
   | `MISSING_DOCX` | **Major (P0)** — cited Table/Figure absent from rendered output | **Minor** — figure/table is separately attached per journal policy |
   | `MISSING_BODY` | **Major (P0)** — no body caption definition | **Major (P0)** when the float IS in the rendered DOCX (SSOT drift). **Minor** when no `--docx` was supplied — excused without evidence, and reported as such |
   | `MISMATCH` | **Major (P0)** — caption text disagrees between body and rendered DOCX | **Major (P0)** (no change) |
   | `UNCITED` | Minor — orphan caption that should be cited or removed | Minor (no change) |

4. **Append a reconciliation block to the Phase 3 report:**

   ```
   | Label | Status | Body caption | DOCX caption | Verdict |
   |---|---|---|---|---|
   | Supplementary Table S4 | MISMATCH | Sensitivity analysis | Diagnostics table | ✗ P0 |
   | Supplementary Table S8 | MISSING_DOCX | (defined in body) | — | ✗ P0 |
   | Figure 2 | UNCITED | Forest plot of subgroups | Forest plot of subgroups | △ Minor |
   ```

5. **Emit each P0 row as a separate `M`-numbered Major Comment** with
   `category: "F"` (Reporting Completeness) and `fixable_by_ai: false`
   (build script changes are out of scope for the auto-fix loop — they
   require pipeline-side fixes per `/write-paper` Step 7.6a routing).

**Do NOT auto-fix cross-reference defects in `--fix` mode.** Caption rewrites
in the body without re-running the DOCX build will simply move the mismatch.
Surface as Major Comments and let the user route to `/write-paper` Step 7.6a.
