# Phase 2.5c / 2.5c-2 — Reference hallucination and adequacy scans

Numerical audits (2.5/2.5a/2.5b) cover in-text numbers; they do **not** cover reference-list integrity. LLM-drafted or co-author-handed-in bibliographies frequently contain fabricated DOIs, wrong author/year combinations for a real DOI, or plausible-looking references that never existed. These slip past human proofreading because the surface form looks canonical.

**When to run:** every manuscript at self-review, regardless of stage. Mandatory before submission and before any revision circulation to co-authors or the editor.

**Procedure:**

1. **Locate the bibliography.** From `SSOT.yaml` → `truth.refs_bib` (fallback `manuscript/_src/refs.bib` for legacy projects). If `SSOT.yaml` is absent, scan `references/library.bib` as a last resort.

2. **Invoke `/verify-refs`** on the resolved bib. The skill writes `qc/reference_audit.json` with a per-entry verdict (`VERIFIED` / `FABRICATED` / `UNVERIFIED`) and a top-level `submission_safe` boolean.

   ```bash
   # equivalent CLI form (same result as invoking the skill).
   # verify_refs.py takes a positional input (the .bib path) and writes its audit
   # to <project-root>/qc/reference_audit.json (path derived from --project-root).
   BIB="$(python3 -c "import yaml; print(yaml.safe_load(open('SSOT.yaml'))['truth']['refs_bib'])")"
   python3 skills/verify-refs/scripts/verify_refs.py "$BIB" --project-root . --strict
   ```

   When both reference QC and cross-reference QC are needed in one pass, prefer
   the master orchestration entry point in `/manage-refs` — it chains
   `check_citation_keys.py` → `verify_refs.py --strict` → `render_pandoc.sh`
   (optional) → `check_xref.py --strict` and writes
   `qc/pre_submission_gate.json` as the single submission-readiness artifact:

   ```bash
   bash "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/manage-refs/scripts/pre_submission_gate.sh" \
       --md manuscript/manuscript.md \
       --bib manuscript/_src/refs.bib \
       --docx submission/<journal>/manuscript.docx \
       --allow-separate-attachments  # see Phase 2.5d for when this is appropriate
   ```

3. **Read `qc/reference_audit.json`.** For each entry not marked `VERIFIED`, add a row to the reconciliation block below. `FABRICATED` entries are P0 Major Comments (block submission). `UNVERIFIED` entries are Minor Comments unless the manuscript is at a circulation/submission gate, in which case they escalate to Major. For each `duplicate_findings[]` entry (category `duplicate_pmid` / `duplicate_doi`), add a Major Comment row noting the duplicated `ref_ids` pair and recommend cite renumbering — duplicates block submission (P0 Major) regardless of per-record `VERIFIED` status.

4. **Cross-check placeholder + pagination drift.** Run, on every round:

   ```bash
   grep -nE '\[@NEW:|\[N\]|\[N–N\]|e0{3}.{0,5}e0{3}|in[ .]?press|\bTBD\b|forthcoming' manuscript/
   ```

   Two failure classes:
   - **Citation-queue placeholders** (`[@NEW:topic]`, `[N]`, `[N–N]`): a citation slot that was never resolved. Any remaining at self-review is a P0.
   - **Pagination placeholders** (`e000–e000`, `in press`, `TBD`, `forthcoming`): `/verify-refs` (Phase 2.5c step 2) marks these `UNVERIFIED` with `note = "pagination_placeholder"` but cannot judge centrality from the .bib alone. **Here, with the manuscript in hand, decide centrality:** if the unresolved reference supports a method choice or a headline claim (grep the citekey/marker against the Abstract, the Statistical Analysis subsection, and the first Results paragraph), escalate it to a **P0 Major** rather than a generic Minor. A method-load-bearing citation that is still "in press / e000" at submission is a blocker. Include each in the reconciliation block.

5. **Record results in a short reconciliation block** and append to the Phase 3 report:

   ```
   | Citekey | Verdict | Source check | Status |
   |---|---|---|---|
   | Kim_2024_Validation | VERIFIED | DOI + PubMed match | ✓ |
   | Park_2023_Radiomics | FABRICATED | DOI resolves to unrelated paper | ✗ P0 |
   | Lee_2022_DeepLearning | UNVERIFIED | No DOI/PMID, title not found | △ Major before submission |
   | [@NEW:segmentation_review] | PLACEHOLDER | unresolved citation queue | ✗ P0 |
   ```

**Short-circuit rule:** if `qc/reference_audit.json` already exists with a bib-hash match within 60s (P9 cache TTL, pending), the scan MAY reuse it; otherwise re-run. Never consume a stale audit from a prior manuscript revision.

**Do NOT fabricate replacement references** if any entry fails. Fix-forward belongs to `/search-lit` and `/lit-sync`, not to this skill. Self-review only reports the failure and blocks submission.

### Phase 2.5c-2: Reference Adequacy Scan

Phase 2.5c covers reference **integrity** — are the cited references real (fabricated / unverified / duplicate / placeholder)? It does **not** ask whether there are *enough* references, in the right sections, grounding every named method. That is reference **adequacy**, and it is the failure mode behind a draft with thirteen references where the Statistical Analysis subsection names a competing-risk model, multiple imputation, the E-value, and an eGFR equation with zero citations. Keep the two strictly separate: an integrity failure blocks because a citation is *wrong*; an adequacy failure flags because a citation is *missing*.

**When to run:** every manuscript at self-review, after the integrity scan. The two share the manuscript and the resolved bib path.

**Procedure:**

1. **Run the deterministic checker.** Resolve the article type from `project.yaml` (passed verbatim; the script's alias map handles repo paper-type names) and the journal cap from the target journal profile when known:

   ```bash
   python3 "${MEDSCI_SKILLS_ROOT:-$HOME/workspace/medsci-skills}/skills/self-review/scripts/check_reference_adequacy.py" \
     --manuscript manuscript/manuscript.md --bib "$BIB" \
     --article-type "$TYPE" ${CAP:+--journal-cap "$CAP"} \
     --out qc/reference_adequacy.json --strict
   ```

   It reports the cited-reference count vs the article-type target, the section distribution (Introduction / Methods / Results / Discussion), every named method found in the Methods/Statistical-Analysis block, which of them lack a citation in their paragraph, and a `methods_zero_citations` flag.

2. **Fold `findings[]` into the review.** Each finding becomes a standard `issues[]` entry (so `/revise` and downstream consumers ingest adequacy and other comments uniformly), **additively** carrying the machine-readable `issue_type` + `subtype` alongside the usual fields, under `category: "F" / category_name: "Reporting Completeness"`:

   ```json
   {"id":"M2","severity":"major","category":"F","category_name":"Reporting Completeness",
    "issue_type":"reference_adequacy","subtype":"methods_named_method_uncited",
    "location":"Methods - Statistical Analysis",
    "description":"Fine-Gray competing-risk model is named without a canonical citation.",
    "fixable_by_ai":false,
    "suggested_fix":"Run /search-lit for the canonical Fine-Gray competing-risk source, sync via /lit-sync, then rerun /verify-refs --strict."}
   ```

   **Severity:** `methods_zero_citations` (original / AI-validation / meta-analysis) and each uncited statistical method → **Major** (a P0 candidate before submission when the method is central to the primary or a sensitivity analysis); each uncited reporting/diagnostic standard → **Minor**; a total count below the article-type target → **Major** when far below (under half the floor), otherwise **Minor**, scaled also by stage (escalate at a submission/circulation gate).

3. **Fix-forward, not fabricate.** As in Phase 2.5c, this skill never writes replacement references. Every adequacy finding carries `fixable_by_ai: false`; the remedy is `/search-lit` (Manuscript Paper Reference Pool mode) → `/lit-sync` → `/verify-refs --strict`, which the author runs.
