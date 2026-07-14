# Phase 2.5f — Claim-vs-Artifact Cross-Check: procedure and verdict rationale

Load-on-demand companion to `/self-review` Phase 2.5f. SKILL.md keeps the gate
invocations and the verdict-severity map; this file carries the precedent failure,
the per-verdict rationale, the resolution paths, and the four checks no script makes.

Read it when a Phase 2.5f gate fires and you need to know what the verdict means and
how to resolve it — or when the manuscript has a pre-registration to reconcile against.

Phases 2.5–2.5e check numbers and adjustment sets. This phase checks **claims
against the external artifacts they should trace to** — the pre-registration, the
protocol, the analysis outputs. These are the errors that survive a single-pass
review because the manuscript prose is internally consistent yet disagrees with
the registration or the analysis it reports. The first scope is the two highest-
value, deterministic instances; figure/flow-count reconciliation, Methods-promised-
analysis completeness, and imputation-input integrity are separate subchecks (run
`/make-figures` legend reconciliation and `/write-paper`'s Methods-promised gate).

**Precedent failure pattern:**
> A manuscript reported a null primary association from a multiple-imputation model
> and described it as "pre-specified," while the registered primary had been the
> complete-case model that was significant — the primary had been re-designated after
> the results were known. In the same paper an E-value of 2.79 was attached to the
> primary HR of 1.34, but 2.79 does not recompute from 1.34 (it came from a different,
> non-primary estimate), and a second E-value bounded an exploratory cancer-specific
> hazard, not the headline contrast. None of these tripped the internal-consistency
> checks; all three are deterministic against the registration and the arithmetic.

**Procedure:**

1. **Run the cross-check** with the manuscript and (if available) the pre-registration
   / protocol / `project.yaml`:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_claim_artifact.py" \
     --manuscript manuscript.md --prereg prereg.md \
     --out qc/claim_artifact.json --strict
   ```

2. **Estimand provenance.** The script raises `PRIMARY_REASSIGNED` (Major,
   category: A. Study Design & Data Integrity) only on **explicit** language that the
   primary was re-designated / switched / chosen post-hoc after results were known — a
   genuine P0. The fix is to report the pre-specified and the revised models
   **coequally** and disclose the change in the Abstract and Limitations, not to
   silently lead with the more favourable estimate. Two related verdicts are
   **advisory, not Major** — surface them as Anticipated Minor Comments to confirm,
   never as a blocker: `ESTIMAND_DRIFT` (the fuzzy manuscript↔registration primary
   token overlap is below threshold — noisy; confirm against the actual registration
   before treating it as drift) and `PRIMARY_DISCLOSURE_NOTE` (the manuscript discloses
   a manuscript-stage analytical decision — the honest disclosure estimand-provenance
   guidance *recommends writing*; confirm it is reported coequally, do not penalise it).

3. **E-value.** `EVALUE_ARITHMETIC` means the reported E-value does not recompute from
   its adjacent effect estimate (the value was likely produced for a different estimate);
   `EVALUE_NON_PRIMARY` means the E-value is attached to a secondary/exploratory estimate
   but presented as if it bounded the headline claim. Both warrant a Major/Minor comment —
   recompute the E-value for the **declared primary** estimate and its near-null confidence
   limit, and quote it there.

4. **Primary-change guard.** Independently of the script, if the manuscript reports two
   models for the same contrast where one is significant and the other null and the
   significant one is foregrounded, confirm which was pre-specified; an outcome-dependent
   choice of primary model is a Major comment even when each model is individually correct.

5. **Headline vs own-sensitivity direction.** Read the sensitivity series (S1 etc.) the
   manuscript itself reports. If the headline causal/association claim points the *opposite*
   way from the authors' own adjusted or sensitivity estimate — a positive lead sentence over
   a sensitivity model that attenuates to the null, or vice versa — that is a Major: the paper
   is contradicting its own robustness check. This is a prose judgement, not a script verdict.

6. **Methods ↔ Results ↔ disk coverage.** Run the deterministic coverage gate:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_artifact_coverage.py" \
     --manuscript manuscript.md --analysis-dir output/analysis \
     --out qc/artifact_coverage.json --strict
   ```

   `PROMISED_ABSENT` (an analysis named in Methods that never reaches Results) and
   `DISK_UNREPORTED` (an analysis output on disk — an added-value DeLong CSV, a calibration
   table — never mentioned in the manuscript) are Anticipated Major Comments. The reverse
   direction matters because a run-but-unreported result can be the one that undercuts the
   headline. When an `_analysis_outputs.md` manifest exists the gate uses it as the source of
   truth; otherwise it globs `--analysis-dir` and only escalates analysis-bearing file names.

   The same gate also flags `PROMISED_STAT_NO_VALUE`: a statistic framed as a **bound/
   ceiling/de-confounded** value (e.g. "the de-confounded reader AUC is reported in
   Table S16", "the classifier ceiling AUC") promised with a reporting verb but never
   given a numeric value anywhere in the manuscript **or supplement** — the bound that
   makes the primary estimand interpretable, sometimes marked "Addressed" in a checklist
   yet absent from every table. Pass the rendered supplement so the corpus is complete:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_artifact_coverage.py" \
     --manuscript manuscript.md --supplement supplement.md \
     --out qc/artifact_coverage.json --strict
   ```

7. **Supplement / tables / caption hygiene.** Phases 2.5–2.5e and the classical-style
   gate lint `manuscript.md` only; the rendered **supplement, a separately-built tables
   file, and figure-caption files** are never linted — yet that is where technical-check-
   fatal residue hides (internal §/§L SAP labels, unfilled `Table SX`/`[Authors]`
   placeholders, `[VERIFY]`/`TODO` build markers, response-to-reviewers framing, planning
   residue, and body↔supplement cross-reference numbers that do not resolve). Run the
   supplement-hygiene gate over **every** rendered reader-facing artifact:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_supplement_hygiene.py" \
     --supplement supplement.md --supplement tables.md --supplement captions.md \
     --manuscript manuscript.md --out qc/supplement_hygiene.json --strict
   ```

   All verdicts (`SUPP_INTERNAL_LABEL`, `SUPP_PLACEHOLDER`, `SUPP_BUILD_MARKER`,
   `SUPP_RESPONSE_FRAMING`, `SUPP_PLANNING_RESIDUE`, `SUPP_XREF_UNRESOLVED`) are
   Anticipated Major Comments — a reader-facing slip in a supplement is as fatal at a
   technical check as one in the body.

   **Float citation order (same technical-check pass).** Editorial offices "unsubmit"
   manuscripts *before* peer review when numbered floats are not cited in ascending
   order of first appearance — a fully deterministic desk-check item the hygiene gate
   above does not cover (it lints xref *resolution*, not *order*). Run the citation-order
   gate, which checks each series independently (main Tables, main Figures, Supplementary
   Tables, Supplementary Figures), scanning only the narrative body (it auto-excludes the
   Figure Legends / back-matter so an in-order legends block cannot mask an out-of-order
   body):

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_citation_order.py" \
     --manuscript manuscript.md --out qc/citation_order.json --strict
   ```

   `CITATION_ORDER` (Major) — a series cited out of numerical order (e.g. Table 3 before
   Tables 1–2, or Supplementary Tables cited S4, S9, S16, S12, …); fix by renumbering the
   series by first-citation order (and reordering the float/supplement document + remapping
   every cross-reference, expanding ranges like `S12–S15` by hand and leaving non-float
   sensitivity-spec labels such as `S1–S6` untouched) or by rephrasing away the early
   citation. `CITATION_GAP` (Minor) — cited numbers not contiguous from 1 (a possible
   missing/mis-numbered float).

8. **Re-run cross-artifact staleness after any audit or reframe.** When a headline number
   is corrected or an analysis is re-framed, the fix often lands only in the body while a
   supplement footnote or a figure-source data file keeps the stale (sometimes *reversed*)
   value. Re-run `/sync-submission`'s `check_cross_artifact_stale.py` across the body, the
   supplement, and any figure-source data immediately **after** the reframe — not just once
   at the start — so a corrected body never ships next to a stale supplement.

9. **Power-aware null interpretation.** A headline negative claim ("no synergy", "not
   associated", "showed no difference") is interpretable only next to a precision
   statement — a minimum-detectable-effect, a power calculation, an equivalence
   margin/TOST, or a CI-compatibility sentence. Run the null-calibration gate:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_null_calibration.py" \
     --manuscript manuscript.md --out qc/null_calibration.json --strict
   ```

   `CONFIRM_NULL_NO_MDE` (Major) fires when a negative/equivalence claim in the Title/
   Abstract/Conclusion has no such token anywhere in those regions — a non-significant
   result is not evidence of no effect without one. (A single MDE/power/equivalence/CI-
   compatibility sentence suppresses it.) Pair with the interaction-scale checks (`O14`)
   when the null is a synergy/interaction claim.

10. **Confidence-weighted / rating → AUC monotonicity.** For an observer or reader study
    that collapses a (binary-call × confidence) rating into a single score used as the
    ROC/AUC predictor, verify the encoding is **strictly monotonic** across the full
    ladder — a *folded* score (`cws = confidence if positive-call else 6 − confidence`)
    collapses opposite (call × confidence) cells and silently mis-estimates the AUC; a
    prose review cannot see an estimator bug. Run the encoding through the reusable
    monotonicity probe and ship its 10-combination unit test:
    `python3 "${MEDSCI_SKILLS_ROOT}/skills/analyze-stats/scripts/rating_monotonicity.py" --encoding score_def.json`.

11. **Figure-embedded numbers are text-grep blind.** PRISMA/flow/forest/statistic figures
    are rasterised, so every numeric audit above is blind to the numbers *inside* them.
    Before submission, (a) **visually** read each such figure page in the rendered/blind
    PDF, and (b) reconcile the **hard-coded integers** in the figure-generation script
    (`create_figure*.R`, `make_*.py`) against the body/flow-source counts
    (`grep -nE '<-\s*[0-9]+|=\s*[0-9]+' figures/*.R`). See `submission-portal-verification`
    §9.5 (figure-image DATA drift) for the full procedure.

The script is deterministic but its provenance match is fuzzy (token overlap): read the
reconciliation in `qc/claim_artifact.json` and confirm against the actual registration
before raising `ESTIMAND_DRIFT`. For time-to-event manuscripts, also apply probe **S8
(estimand provenance)** of `references/domain-probes/survival_prognostic.md`.
