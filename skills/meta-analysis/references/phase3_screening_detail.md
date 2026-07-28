# Phase 3 — Screening & Selection: round procedures and gate detail

Load-on-demand companion to `/meta-analysis` Phase 3. SKILL.md keeps the four screening
rounds, the two MANDATORY gates (3f reconciliation, 3f.5 pool lock), and their hard rules;
this file carries the detail.

Read the block you need:

- **Rounds 3a–3d** — exclusion-code sets, the AI-assisted pre-screening template and its
  Methods boilerplate, the full-text exclusion codes.
- **3f reconciliation** — the ID-set algebra, the reconciliation-table template, and the
  precedent incident where four downstream artifacts echoed one unreconciled prose total.
- **3f.5 pool lock** — why the lock exists, how to build it, and every downstream gate that
  reads it.

**Goal**: Systematic title/abstract and full-text screening with two independent reviewers.

#### 3a. Round 1 — Initial Title/Abstract Screening (single reviewer)
1. Define exclusion codes from protocol (e.g., E1=Not target population, E2=Not intervention, E3=Ineligible type, E4=Non-human, E5=Duplicate).
2. For each record, screen title+abstract against eligibility criteria.
3. Mark each record as INCLUDE / EXCLUDE / MAYBE with reason code.
4. Output: `round1_{date}.tsv` with color-coded decisions.

#### 3b. Round 2 — Dual Independent Title/Abstract Screening
1. A second independent reviewer (or AI as a documented second-pass tool with human verification) re-screens all R1 records.
2. Compute Cohen's kappa at title/abstract stage; report in Methods.
3. Tag each record's `round2_tag` as INCLUDE / EXCLUDE / MAYBE based on R1+R2 agreement (MAYBE = disagreement OR either reviewer flagged uncertain).
4. Output: `round2_{date}.tsv` (adds `round2_tag`, `round2_reason` columns).

#### 3c. Round 3 — Adjudication of Disagreements (first reviewer)
1. Build R3 sheet: all MAYBE records first, followed by INCLUDE records (which receive a brief confirmation pass).
2. The **first reviewer** independently adjudicates each row, recording `round3_decision` (INCLUDE/EXCLUDE) and `round3_reason` (only when overturning R2).
3. **Optional AI-assisted pre-screening** to compress R3 effort:
   - Use `references/ai_pre_screening_template.py` (customize per project).
   - Pre-screen produces `ai_suggestion` (INCLUDE/EXCLUDE/UNCERTAIN/CONFIRM-INCLUDE) + `ai_reason` columns.
   - Sort priority: UNCERTAIN → EXCLUDE → INCLUDE → CONFIRM-INCLUDE.
   - First reviewer must independently confirm or overturn every AI suggestion against the title, abstract, and (when needed) full text. AI suggestions are **not** final decisions.
   - Methods boilerplate: "Round 3 adjudication was performed by the first reviewer with AI-assisted pre-screening ({model name and version}). The AI was prompted with the prespecified PECOS criteria and produced a suggestion plus brief justification for each record; the first reviewer independently confirmed or overturned every suggestion. AI suggestions were not used as final inclusion decisions."
4. Output: `round3_{date}.tsv` with finalized `round3_decision`.

#### 3d. Round 4 — Full-text Screening
1. For records with `round3_decision = INCLUDE`, retrieve full-text PDFs (use `/fulltext-retrieval`).
2. Apply full-text exclusion criteria (F1=No extractable outcome, F2=No comparative data, F3=Cannot separate target population data, F4=Inadequate sample/follow-up, F5=Full-text unavailable).
3. Two independent reviewers; compute Cohen's kappa at full-text stage.
4. Resolve disagreements by consensus or third reviewer.
5. Flag comparative studies for priority extraction.

#### 3e. PRISMA Flow
Track numbers at each stage for PRISMA flow diagram (R1 → R2 → R3 → R4 → final included).
Use `/make-figures` to generate PRISMA flow diagram when numbers are finalized.

#### 3f. Post-Consensus Count Reconciliation Gate (MANDATORY before Phase 5 write-up)

Before handing the screening artifacts to Phase 5 (statistical synthesis) or to `/write-paper` / `/self-review`, run an explicit ID-set reconciliation and record the canonical totals in a single source-of-truth file (typically `2_Screening/screening_consensus.md` §Net Impact or equivalent):

Use the deterministic helper when TSV/CSV artifacts are available:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/screening_reconcile.py" \
  --screening 2_Screening/fulltext_screening.tsv \
  --consensus 2_Screening/consensus_decisions.tsv \
  --table1 6_Tables/table1_studies.csv \
  --output 2_Screening/screening_consensus.json
```

Downstream stages should consume `screening_consensus.json` for counts and
ID sets. The Markdown consensus document remains the human explanation.

1. **Enumerate ID sets from raw artifacts (not from prose summaries):**
   - A = screening TSV INCLUDE IDs
   - B = consensus spreadsheet Exclude IDs
   - C = consensus spreadsheet Include-qualitative IDs (FLAG-resolved additions)
   - T = Table 1 / bivariate-eligible IDs (2×2-extractable studies)

2. **Compute canonical totals via set algebra:**
   - k_qualitative = |A \ B| + |C|
   - k_bivariate = |T|
   - k_narrative-only = k_qualitative − k_bivariate
   - k_FT-excluded = |full-text reviewed| − k_qualitative

3. **List the narrative-only IDs explicitly.** The highest-yield red flag is a numeric claim ("10 narrative-only studies") that does not match the enumerable ID set (A ∪ C) \ B \ T.

4. **Prohibit "N → M" transitions without ID receipts.** Any sentence of the form "k rose from 30 to 32 after FLAG consensus" must cite the specific added/removed IDs. A transition claim with no enumerable ID set is a P0 error and blocks the Phase 5 hand-off.

5. **Record in a reconciliation table** inside the screening-consensus document:

   | Quantity | v_prev draft | v_current (ID-verified) | Derivation |
   |---|---|---|---|
   | k_full-text | ... | ... | ... |
   | k_FT-excluded | ... | ... | |TSV EXCLUDE| + |consensus-downgrades| |
   | k_qualitative | ... | ... | |A \ B| + |C| |
   | k_bivariate | ... | ... | |T| |
   | k_narrative-only | ... | ... (explicit IDs listed) | (A ∪ C) \ B \ T |

**Precedent incident (a PRISMA-DTA meta-analysis revision):** a late-revision manuscript shipped with k_qualitative = 32 / k_narrative-only = 10 / k_FT-excluded = 46. ID-set reconciliation (performed only after an adversarial audit at post-Stage 4 QC) revealed true counts 24/2/54. An early-draft prose total ("30 → 32 after FLAG consensus") had been carried forward without ever being reconciled against the screening TSV intersected with the consensus spreadsheet; four downstream artifacts echoed the same wrong total. This gate would have caught the drift at the Phase 5 hand-off.

##### Why `STAGE_TRANSFER_LOSS` needs its own verdict

The set algebra above reconciles *counts*. On its own it does not distinguish the two ways an id
can be missing from set `B`:

| Case | Meaning | Where it lands |
|---|---|---|
| consensus says **exclude** | a decision was made and recorded | out of `qualitative` — correct |
| consensus **has no row at all** | the record fell out of the pipeline; nobody adjudicated it | into `qualitative`, then `narrative_only` — **wrong, and silent** |

Both leave the id out of `B`, so both look identical to a count-based check. And because a
diagnostic-accuracy review legitimately contains narrative-only studies (eligible, but no
extractable 2×2), a lost record parked in that set is indistinguishable from a real one. The
totals still reconcile — they were recomputed from the downstream artifact, which is exactly
where the record is already absent.

`screening_reconcile.py` therefore reports `stage_transfer_loss` (= `screening_include` −
`consensus_ids`) as a blocking issue, and splits `narrative_only` into `_adjudicated` (a decision
exists) and `_unadjudicated` (none does). Only the first is a legitimate category.

**Precedent incident (a single-arm intervention review):** the review reached journal submission
with 15 studies and was withdrawn by the authors when 5 eligible studies were found **inside its
own retrieved records** — none were search failures. One had passed both title/abstract screening
passes and was never entered into the consensus stage; three others sat under an exclusion code
that contradicted the registered eligibility criteria (single-arm case series were eligible by
protocol but were coded "not comparative"). A pre-specified sensitivity analysis flipped from
P = 0.064 to P = 0.033 once the pool was corrected to 18 studies. Note the shape: every count in
the submitted manuscript reconciled, because each had been recomputed from an artifact the lost
studies had already dropped out of.

#### 3f.5 Pool composition lock (MANDATORY at adjudication freeze)

After Phase 3f reconciliation passes, freeze the pool composition into a
single source-of-truth YAML so every downstream artifact (extraction TSV,
manuscript prose counts, PRISMA flow caption, supplementary INDEX, cover
letter free-text) can be checked against it.

Why this lock exists
^^^^^^^^^^^^^^^^^^^^

Cross-project precedent (anonymized): an LLM reporting-quality SR carried
five documents that disagreed on INCLUDE (63 vs 64) and EXCLUDE
(108/109/111). Three EXCLUDE rows existed in the extraction sheet without
matching INCLUDE. The drift traced to a late round-3 adjudication whose
result was applied to some artifacts and not others — there was no single
canonical post-freeze count to reference.

How to lock
^^^^^^^^^^^

1. Copy the template:
   ```bash
   cp "${CLAUDE_SKILL_DIR}/templates/FINAL_POOL_LOCK.yaml.template" \
       2_Data/FINAL_POOL_LOCK.yaml
   ```
2. Fill in counts and UID lists from the reconciliation in Phase 3f.
3. Compute the SHA-256 integrity hash from the sorted UID list.
4. Commit the lock to git BEFORE starting Phase 4 extraction.

Downstream gates
^^^^^^^^^^^^^^^^

- `/meta-analysis` Phase 4 entry: extraction TSV's UID set MUST equal
  `include_uids` ∪ `mixed_uids` from the lock. See Phase 4 entry gate.
- `/sync-submission` Phase 5
  (`scripts/cross_document_n_check.py --pool-lock`): every numeric claim
  in manuscript / abstract / supplementary that maps to a locked
  category must match the locked value.
- Manuscript prose: NEVER re-derive `k included` from extraction TSV at
  manuscript build time. Always reference `final_pool_n` from the lock.
- **Aggregate patient/lesion totals are locked too, not just study counts.**
  The Abstract/Results aggregate denominators ("a total of 483 patients /
  531 lesions") are derived from the lock, never hand-carried. Lock them as
  explicit fields and distinguish **arm-separable** from **both-arm** rows:
  a study contributing one arm to a comparison must not have its full-cohort
  patient count folded into a pooled total. A hand-carried headline total that
  does not re-derive from the locked per-study values is a P0 (the analysis-side
  mirror of `/self-review` `check_cohort_arithmetic.py` partition checks).

If a late post-freeze decision changes the pool, treat it as a formal
PROSPERO amendment: file the amendment, re-freeze the lock as a new
file (`FINAL_POOL_LOCK_v2.yaml`), and propagate to every artifact.
