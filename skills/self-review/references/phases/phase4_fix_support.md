# Phase 4 — Fix support

#### Standard mode (no --fix flag)

After presenting the report, offer to help fix specific issues:
- Rewrite overclaiming sentences
- Draft missing limitation statements
- Suggest statistical additions (e.g., calibration analysis code via `/analyze-stats`)
- Draft intended use, decision-impact, or novelty-delta statements
- Check specific tables/figures for consistency
- Generate missing flow diagrams via `/make-figures`

**`requires_reanalysis` findings route to `/analyze-stats`, not a prose edit (observational/cohort).**
For cohort and observational manuscripts, the highest-value fixes are usually *data-level*: a
power/MDE re-simulation under the full primary model, a first-visit / one-record-per-subject dedup
sensitivity, an extended- or reduced-adjustment (over-adjustment) sensitivity model, or optimism
correction of calibration. These are **not** `fixable_by_ai` text edits — `--fix` is text-only and
will silently skip them. Tag each such finding `requires_reanalysis: true` and route it to
`/analyze-stats` for a committed script + CSV, then feed the regenerated numbers back into the
manuscript and re-run the relevant Phase 2.5 gate. Surface these explicitly to the author rather
than letting an auto-fix pass appear to "resolve" them.

#### Auto-fix mode (--fix flag)

When `--fix` is passed:

1. **Filter fixable issues**: Select all issues where `fixable_by_ai` is true.
2. **Apply fixes sequentially**: For each fixable issue, edit the manuscript file directly:
   - Text rewrites (overclaiming, missing sentences, terminology) → Edit in place
   - Missing reporting items (ethics statement, data availability) → Insert at suggested location
   - Numerical inconsistencies (abstract-table mismatch) → Correct to match tables
   - Do NOT attempt: new statistical analyses, new figures, design changes, IRB-dependent items, or any issue tagged `requires_reanalysis` (route those to `/analyze-stats`)
   - Do NOT invoke other skills (`/make-figures`, `/analyze-stats`) during fix — text edits only
3. **Report changes**: After all fixes, output a summary:
   ```
   ## Auto-Fix Summary
   - Fixed: {N} issues
   - Skipped (requires human): {M} issues
   - Changes: {list of id + one-line description of what was changed}
   ```
4. **Post-edit paren-span safety scan**: if any fix reduced em-dashes (e.g. a `— X —` appositive → `(X)`), run the parenthesis-span gate before re-review — a bulk conversion can pair two unrelated dashes across a sentence boundary and wrap a whole sentence (or an ordinal "Sixth, …" limitation) inside one parenthesis (paren-balanced, so a balance check misses it):

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_paren_spans.py" \
     --manuscript manuscript.md --out qc/paren_spans.json --strict
   ```

   `PAREN_SPAN_ORDINAL` / `PAREN_SPAN_SENTENCE` is a Major — undo or repair that conversion before continuing.
5. **Re-review**: Run Phase 2 (systematic check) again on the modified manuscript.
6. **Iterate**: If new fixable issues emerge, apply one more round (maximum 2 total fix iterations).
7. **Final output**: Regenerate the Phase 3 report and Phase 3c JSON with updated scores.

**Iteration limit**: Maximum 2 fix-and-re-review cycles. If the score has not reached "PASS" after 2 iterations, output the final report with remaining issues and flag: "Auto-fix limit reached. Remaining issues require human review."
