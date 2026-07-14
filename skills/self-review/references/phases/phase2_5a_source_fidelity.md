# Phase 2.5a — Numerical Source-Fidelity Audit (External)

Load-on-demand companion to `/self-review` Phase 2.5a. SKILL.md keeps the entry
condition, the displayed-arithmetic gate, and the escalation rule; this file carries
the 3-layer traversal procedure, the sampling strata, the precedent failure, and the
four prose-judgement rules (hand-entered script inputs, statistic-type fidelity, stale
derived CSVs, `[VERIFY-CSV]` tags).

Read it when you are actually tracing sampled claims back to their primary sources.

Internal consistency (Phase 2.5) is necessary but not sufficient. Numbers can be fully self-
consistent across Abstract / Table / Text and still be wrong at the source — a single
transcription error propagates cleanly through every downstream stage.

Also run the **displayed-arithmetic** gate — a stated difference must equal the subtraction of
its two displayed component values at the SAME precision:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_rounded_delta.py" \
  --manuscript manuscript.md --out qc/rounded_delta.json
```

`ROUNDED_DELTA_MISMATCH` (Minor) fires when e.g. AUCs are shown as `0.70` and `0.73` (a displayed
gap of 0.03) while the between-arm difference is stated as `0.02` — self-consistent only on the
unrounded values. Fix: report components and the delta at one precision, or footnote that the delta
is computed on unrounded values. A higher-precision component pair (`0.703` vs `0.726`) with a 2-dp
delta is the legitimate unrounded case and is not flagged.

**Precedent failure pattern:**
> A revision-era comparative meta-analysis reported a safety-outcome 2x2 with the
> arm-level events direction-reversed relative to the primary-source Table. Internal
> consistency passed because Abstract, Discussion, Table, and the R script all echoed
> the same wrong values. The reversal was caught only by an explicit second-pass audit
> that randomly sampled claims and traced each back to the primary paper.

**When to run:** MA revisions, submissions, or any review where the user mentions "check
against the source," "verify extraction," or "random sample."

**Inputs the reviewer should expect:**
- `manuscript.md` (or .docx converted to .md)
- `extraction_final.csv` (or equivalent data-extraction spreadsheet)
- A directory of primary-source PDFs (or equivalent accessible text)

**Procedure:**

1. **Inventory numerical claims** in Abstract, Results, and Discussion (patterns: `\\d+/\\d+`,
   `\\d+\\.\\d+%`, `(95% CI:`, `p\\s*=\\s*0\\.`, `I\\^2`, `n\\s*=`, etc.).

2. **Stratified random sample** — draw 5 claims across: (a) pooled estimates, (b) subgroup
   / sensitivity results, (c) comparative-arm specific values, (d) study-level numbers
   (first-cited in narrative), (e) a claim introduced during revision if the draft is post-v1.
   Comparative-arm specific values and revision-introduced numbers are the two highest-
   yield strata — always include one of each.

3. **For each sampled claim, traverse 3 layers:**
   - **Layer 1 (Manuscript → CSV):** Find the row / column in the extraction CSV.
   - **Layer 2 (CSV → Primary source):** Locate the exact Table, Figure, or paragraph in the
     original paper. Record page number.
   - **Layer 3 (Analysis script → CSV):** If the claim came from an analysis script, read the
     script and confirm its input value matches the CSV cell.

4. **Record results in a table** and append to the report:

   | Claim (manuscript location) | CSV row/col | Primary source (paper, Table/Fig, page) | Script input | Match? |
   |---|---|---|---|---|

5. **Any mismatch is a Major Comment (M-level), not Minor.** Mismatches that reverse a
   direction or change a significance boundary are P0 blockers for submission.

**Revision-specific rule:** If the manuscript contains `[VERIFY-CSV]` tags, treat each as a
mandatory audit item regardless of the sampling size. The tag exists precisely because that
number was introduced after the initial extraction pass and has not yet been independently
checked.

**Hand-entered analysis-script inputs are a code smell.** When Layer 3 reveals a `matrix(...)`,
`c(1, 2, 3)`, or `data.frame(...)` line with numerical data and no CSV-coordinate comment,
escalate to a Major Comment even if the audited values happen to match — the next revision
will re-introduce the same risk.

**Statistic-type fidelity (not just the value).** A prose sentence must match the table/CSV not
only on the **number** but on the **statistic type**. A body sentence that reports a *median*
("median eGFR 92.8") while Table 1 reports a *mean* ("mean 91.3") for the same variable cannot
be reconciled by a reviewer comparing the two — and the mismatch usually means one of them was
not regenerated after a Table 1 rule change (see the mean/median-by-skewness rule in
`/analyze-stats` `table-types/table1_demographics.md`). Treat a prose↔table statistic-type
mismatch (mean vs median, SD vs IQR, n vs %) as a Minor Comment, or Major if it sits on a
primary characteristic the conclusion leans on. Also re-check that any descriptive figure the
prose quotes (e.g. "78.4% male") matches the *current* table value, not a stale earlier one.

**Stale derived CSVs after a model/adjustment-set change (n mismatch).** When the primary model
or adjustment set changes mid-revision, **every** derived CSV (Table 2, sensitivity tables,
supplements) must be regenerated, or a stale file silently contradicts the new primary. The
fastest tell is the analytic **n**: if a derived CSV's `n` differs from the manuscript's current
primary n, suspect it is stale — and the conflict can flip a result's significance (a proteinuria
sensitivity CSV left at the old `n = 4,914` / OR 4.52 contradicted the new primary `n = 4,214` /
OR 3.99, significant ↔ not). Grep each derived CSV's `n` against the primary n; any divergence
that is not explained by a stated sub-analysis restriction is a Major Comment, `requires_reanalysis`
(re-run, not a prose edit — see Phase 4).
