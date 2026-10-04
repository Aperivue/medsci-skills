# Phase 3c — Structured JSON output

When `--json` is passed, or when invoked by `/write-paper` Phase 7, append a machine-readable JSON block after the markdown report. Fence it with triple backticks and the `json` language tag so downstream parsers can extract it.

```json
{
  "self_review_version": "1.0",
  "manuscript_title": "...",
  "date": "YYYY-MM-DD",
  "overall_score": 72,
  "verdict": "REVISE",
  "fatal_count": 0,
  "major_count": 3,
  "minor_count": 4,
  "issues": [
    {
      "id": "M1",
      "severity": "major",
      "category": "C",
      "category_name": "Validation & Stats",
      "location": "Methods, paragraph 5",
      "description": "Calibration plot and Brier score absent for prediction model",
      "fixable_by_ai": true,
      "suggested_fix": "Add calibration analysis paragraph after discrimination results. Generate calibration plot via /make-figures."
    },
    {
      "id": "m1",
      "severity": "minor",
      "category": "F",
      "category_name": "Reporting Completeness",
      "location": "Abstract, line 3",
      "description": "Abstract reports AUC 0.91 but Table 2 shows 0.912 -- rounding inconsistency",
      "fixable_by_ai": true,
      "suggested_fix": "Change abstract to match table: AUC 0.91 (95% CI: 0.87-0.95)"
    }
  ],
  "coverage": {
    "categories": {
      "A": {"status": "assessed", "evidence": ["Methods, Data split para 2", "Figure 1"]},
      "B": {"status": "assessed", "evidence": ["Methods, Reference standard para 1"]},
      "C": {"status": "assessed", "evidence": ["Methods, Statistical analysis para 1-4", "Table 2"]},
      "...": "... one entry for every letter D-J and L ...",
      "K": {"status": "not_applicable", "reason": "Not a systematic review"},
      "I": {"status": "not_assessed", "reason": "Scanner protocol table not supplied"}
    },
    "probes": {
      "ai_overclaiming": {"status": "assessed", "evidence": ["Abstract, Conclusion", "Discussion para 1"]}
    }
  }
}
```

(The `"..."` line stands for the omitted letters; a real ledger has exactly the keys A-L.)

**Field definitions:**
- `overall_score`: Integer 0-100 reflecting manuscript submission readiness
- `verdict`: `"PASS"` (score >= 85, no fatal issues, and no applicable `coverage` entry `not_assessed` — see the coverage rule below) or `"REVISE"`
- `severity`: `"fatal"`, `"major"`, or `"minor"`
- `category`: Letter code from the 12-category system (A-L; K is SR/MA-only, L is advisory)
- `fixable_by_ai`: `true` if the issue can be resolved by editing manuscript text with existing data; `false` if it requires new data, analyses, or human judgment (e.g., design changes, IRB decisions, missing experiments)
- `requires_reanalysis` *(optional, default `false`)*: `true` when closing the finding needs a **committed analysis re-run against the real data**, not a prose edit — power/MDE re-simulation under the full model, first-visit/one-record-per-subject dedup, an extended- or reduced-adjustment sensitivity model, optimism correction of calibration. Always implies `fixable_by_ai: false`. Additive and backwards-compatible; parsers that do not expect it must ignore it. Route these to `/analyze-stats` (see Phase 4).
- `suggested_fix`: Specific, actionable instruction. If `fixable_by_ai` is true, this must be concrete enough for the fixer to execute without ambiguity.
- `consensus` *(optional, panel mode only)*: array of reviewer ids that raised the issue, e.g. `["R1","R3"]`. Additive and backwards-compatible — present only when Phase 2.6 ran; parsers that do not expect it must ignore it.
- `action` *(optional, editorial-impression findings only)*: `"REMOVE" | "MOVE" | "TIGHTEN"` — the SUBTRACTION direction for a category-L finding (Phase 2.5g). Present alongside `issue_type: "editorial_impression"` and `subtype: <verdict>` (e.g. `HEDGE_REPEAT`). Additive and backwards-compatible; these are always `severity: "minor"`, never block, and are `fixable_by_ai: false` by default (except a redundant `HEDGE_REPEAT`, which `--fix` may collapse). Parsers that do not expect it must ignore it.
- `coverage` *(required for new output; absent in JSON written before it existed)*: the ledger of what the review **worked**, as opposed to what it found.
  - `categories`: exactly one entry per letter **A-L**. `probes`: one entry per domain-probe module loaded in Phase 2, keyed by its file stem in `references/domain-probes/` (e.g. `sr_ma`, `observational_confounding`); `{}` when none was loaded.
  - Each entry has `status`: `"assessed"` (with `evidence`, a non-empty list of section / paragraph / line / table references you actually read), `"not_applicable"` (with `reason`, one line — e.g. the Research-Type Adaptation table marks it N/A for this type), or `"not_assessed"` (optional `reason`: what was missing).
  - Record it while you work Phase 2, not after the fact: an `assessed` entry without a reference you read is a false ledger.

**Coverage rule — the review cannot return `PASS` while any applicable category or loaded probe module is `not_assessed`.** Either assess it, mark it `not_applicable` with a reason, or return `REVISE` and name the gap in the report. This adds a condition to `PASS`; the score and the other `PASS` conditions are unchanged.

**Finalise the JSON with the coverage gate** — after writing `qc/self_review.json`, run:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_review_coverage.py" \
  --review qc/self_review.json --out qc/review_coverage.json --strict
```

- `COVERAGE_GAP_PASS` (**Major**, exit 1 under `--strict`): `PASS` over a `not_assessed` entry. Do not hand this JSON to a consumer: assess the entry or change the verdict to `REVISE`, rewrite the JSON, and re-run.
- `COVERAGE_GAP` (Minor): a `not_assessed` entry under `REVISE`. List it in the report so the gap is not read as a clean category.
- `COVERAGE_NOT_RECORDED` (Minor): no `coverage` object — a legacy JSON. Nothing can be checked, so the verdict is `NOT_ASSESSED` (exit 0, or 2 under `--strict`); new output must carry the ledger. An empty `reason` on a `not_assessed` entry counts as none, and `evidence` may be one string. Category L is advisory: L `not_assessed` under PASS is Minor `COVERAGE_GAP`.
- Exit 2 names the malformed field (a missing letter, `assessed` without `evidence`, `not_applicable` without `reason`, an unknown probe module or verdict). Fix the JSON; never drop the ledger to get past it.

The gate checks the ledger as declared (`"basis": "declared"`): that it is complete and consistent with the verdict, not that the work behind an `assessed` entry was done or that a `not_applicable` call is right for the manuscript type.
