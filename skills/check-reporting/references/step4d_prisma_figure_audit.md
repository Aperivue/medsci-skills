# Step 4d — PRISMA Figure 1 Arithmetic & Cross-Reference Audit (Procedural Detail)

Load-on-demand from `SKILL.md` Step 4d. Applies to PRISMA 2020 / PRISMA-DTA / PRISMA-P
systematic reviews and meta-analyses where Item 16a (flow diagram) is PRESENT.

## Inputs

| Source | Path | Required |
|--------|------|----------|
| Manuscript body | `manuscript/manuscript.md` (or path provided) | yes |
| Figure 1 manifest | `analysis/figures/Figure1_PRISMA.md` (preferred) | one of |
| Figure 1 PPTX | `analysis/figures/Figure1_PRISMA.pptx` (text-extractable) | one of |
| Figure 1 caption | embedded in `manuscript.md` | one of |
| Figure 1 PNG/SVG | `analysis/figures/Figure1_PRISMA.{png,svg}` | fallback (manual entry) |

If no machine-readable Figure source exists, Step 4d emits `MISSING` for the cross-reference
checks and asks the user to supply numbers manually.

## Number extraction (regex)

```python
KEYWORDS = {
    "identified": r"(\d[\d,]*)\s+(?:records?|reports?)\s+identified",
    "duplicates": r"(\d[\d,]*)\s+(?:records?|reports?|duplicates?)\s+(?:removed|duplicates? removed)",
    "screened": r"(\d[\d,]*)\s+(?:records?|reports?)\s+screened",
    "excluded_screening": r"(\d[\d,]*)\s+(?:records?|reports?)\s+excluded(?:\s+(?:at|after|during)\s+screening)?",
    "sought": r"(\d[\d,]*)\s+(?:reports?|records?)\s+sought(?:\s+for\s+retrieval)?",
    "not_retrieved": r"(\d[\d,]*)\s+(?:reports?|records?)\s+(?:not\s+retrieved|unobtainable)",
    "retrieved": r"(\d[\d,]*)\s+(?:reports?|records?)\s+retrieved",
    "assessed": r"(\d[\d,]*)\s+(?:reports?|records?)\s+assessed(?:\s+for\s+eligibility)?",
    "excluded_eligibility": r"(\d[\d,]*)\s+(?:reports?|records?)\s+excluded(?:\s+with\s+reasons?)?",
    "included": r"(\d[\d,]*)\s+(?:studies|records?|reports?)\s+included",
}
```

Apply to body text and Figure source independently → produce two dictionaries
`body_numbers` and `figure_numbers`.

## Arithmetic checks (4)

```python
def check_arithmetic(n: dict) -> list[dict]:
    results = []
    if all(k in n for k in ["identified", "duplicates", "screened"]):
        ok = n["identified"] - n["duplicates"] == n["screened"]
        results.append({"eq": "screened = identified - duplicates",
                        "lhs": n["screened"], "rhs": n["identified"] - n["duplicates"],
                        "status": "PRESENT" if ok else "MISMATCH"})
    if all(k in n for k in ["screened", "excluded_screening", "sought"]):
        ok = n["screened"] - n["excluded_screening"] == n["sought"]
        results.append({"eq": "sought = screened - excluded_screening",
                        "lhs": n["sought"], "rhs": n["screened"] - n["excluded_screening"],
                        "status": "PRESENT" if ok else "MISMATCH"})
    if all(k in n for k in ["sought", "not_retrieved", "retrieved"]):
        ok = n["sought"] - n["not_retrieved"] == n["retrieved"]
        results.append({"eq": "retrieved = sought - not_retrieved",
                        "lhs": n["retrieved"], "rhs": n["sought"] - n["not_retrieved"],
                        "status": "PRESENT" if ok else "MISMATCH"})
    if all(k in n for k in ["assessed", "excluded_eligibility", "included"]):
        ok = n["assessed"] - n["excluded_eligibility"] == n["included"]
        results.append({"eq": "included = assessed - excluded_eligibility",
                        "lhs": n["included"], "rhs": n["assessed"] - n["excluded_eligibility"],
                        "status": "PRESENT" if ok else "MISMATCH"})
    return results
```

Run independently on `body_numbers` and `figure_numbers`.

## Cross-reference check (body ↔ figure)

For each key in `KEYWORDS`:
- Both present + agree → `PRESENT`
- Both present + disagree → `MISMATCH` (record both values)
- Only one source has it → `MISSING` (record which side)
- Neither → skip

## JSON schema (`qc/prisma_figure_audit.json`)

```json
{
  "manuscript": "manuscript/manuscript.md",
  "figure_source": "analysis/figures/Figure1_PRISMA.md",
  "body_numbers": { "identified": 315, "duplicates": 122, "screened": 186, "...": "..." },
  "figure_numbers": { "identified": 315, "duplicates": 122, "screened": 186, "...": "..." },
  "arithmetic_body": [
    {"eq": "screened = identified - duplicates", "lhs": 186, "rhs": 193, "status": "MISMATCH"}
  ],
  "arithmetic_figure": [],
  "cross_reference": [
    {"key": "screened", "body": 186, "figure": 186, "status": "PRESENT"}
  ],
  "audit_safe": false,
  "action_items": [
    "[PRISMA-FIGURE] body arithmetic 'screened = identified - duplicates' fails: 186 vs 315-122=193"
  ]
}
```

`audit_safe: true` ⟺ all arithmetic_body, arithmetic_figure, cross_reference rows are
`PRESENT`. Anything else → `false` and Step 5 must surface action_items.

## Edge cases

- **Multi-database identification**: PRISMA 2020 supports separate boxes for database vs
  register vs other methods. Sum across boxes for `identified` total — extraction regex must
  handle `321 records (213 from databases, 108 from citation searching)`.
- **Citation searching strand**: separate flow on right side of PRISMA 2020 diagram. If
  present, run arithmetic checks on each strand independently + a combined `total identified`
  check.
- **Dual-reviewer screening**: numbers should reflect post-consensus counts. If body reports
  pre/post-consensus separately, use post-consensus.
- **Reports vs records**: PRISMA 2020 distinguishes records (citations) from reports
  (full-text). Regex captures both; treat them as the same key for arithmetic but flag
  inconsistent terminology (`[PRISMA-FIGURE-TERMINOLOGY]`).
- **Duplicates split across stages**: some manuscripts list duplicates removed automatically
  (deduplication tool) separately from manual deduplication. Sum.
- **Reasons for exclusion**: Step 4d does not enforce specific reasons but checks that
  the count of "with reasons" categories sums to `excluded_eligibility`. Add as optional
  check `excluded_eligibility = sum(reason_counts)`.

## Cross-cutting rules

- `~/.claude/rules/numerical-safety.md`: PRISMA 5-way consistency (text ↔ Figure ↔
  extraction CSV ↔ analysis script ↔ supplementary). Step 4d covers text ↔ Figure;
  extraction CSV ↔ script ↔ supplementary belong to `/meta-analysis` Phase 6 and
  `/write-paper` Step 7.3a.
- `~/.claude/rules/manuscript-style-classical.md`: number formatting (Arabic numerals,
  thousands separator consistent with journal style).

## Related

- `/check-reporting prisma` (this step caller)
- `/write-paper` Step 7.3a (Numerical Claim Audit — different scope: pooled estimates,
  not flow diagram)
- `/make-figures` (PRISMA flow diagram generation — produces `Figure1_PRISMA.md` manifest
  this step consumes)
- Sample 1차 source (motivation): an active meta-analysis project v3 Figure 1 PRISMA verification, 2026-04-26
