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
  ]
}
```

**Field definitions:**
- `overall_score`: Integer 0-100 reflecting manuscript submission readiness
- `verdict`: `"PASS"` (score >= 85, no fatal issues) or `"REVISE"`
- `severity`: `"fatal"`, `"major"`, or `"minor"`
- `category`: Letter code from the 10-category system (A-J)
- `fixable_by_ai`: `true` if the issue can be resolved by editing manuscript text with existing data; `false` if it requires new data, analyses, or human judgment (e.g., design changes, IRB decisions, missing experiments)
- `requires_reanalysis` *(optional, default `false`)*: `true` when closing the finding needs a **committed analysis re-run against the real data**, not a prose edit — power/MDE re-simulation under the full model, first-visit/one-record-per-subject dedup, an extended- or reduced-adjustment sensitivity model, optimism correction of calibration. Always implies `fixable_by_ai: false`. Additive and backwards-compatible; parsers that do not expect it must ignore it. Route these to `/analyze-stats` (see Phase 4).
- `suggested_fix`: Specific, actionable instruction. If `fixable_by_ai` is true, this must be concrete enough for the fixer to execute without ambiguity.
- `consensus` *(optional, panel mode only)*: array of reviewer ids that raised the issue, e.g. `["R1","R3"]`. Additive and backwards-compatible — present only when Phase 2.6 ran; parsers that do not expect it must ignore it.
- `action` *(optional, editorial-impression findings only)*: `"REMOVE" | "MOVE" | "TIGHTEN"` — the SUBTRACTION direction for a category-L finding (Phase 2.5g). Present alongside `issue_type: "editorial_impression"` and `subtype: <verdict>` (e.g. `HEDGE_REPEAT`). Additive and backwards-compatible; these are always `severity: "minor"`, never block, and are `fixable_by_ai: false` by default (except a redundant `HEDGE_REPEAT`, which `--fix` may collapse). Parsers that do not expect it must ignore it.
