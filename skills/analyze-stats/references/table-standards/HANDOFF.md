# Table Standards — Handoff for Statistician Skill Upgrade

> Created: 2026-04-11
> Context: table formatting research completed in a separate session. Use this to integrate table standards into the statistician skill upgrade.

## What Was Done

3-way parallel research (journal guidelines + YouTube tutorials + tool landscape) → knowledge base:

```
references/table-standards/
  table-standards.md          ← Master doc: universal rules, AMA rules, footnote system, mistakes checklist
  tool-comparison.md          ← R/Python tool comparison + recommended pipelines
  journal-profiles/           ← 6 YAML files (radiology, jama, nejm, lancet, eur_rad, ajr)
  table-types/                ← 5 templates (demographics, diagnostic accuracy, regression, meta-analysis, model comparison)
```

## Key Decisions for Implementation

### 1. gtsummary is the primary engine
- Built-in journal themes (JAMA, Lancet, NEJM) handle 80% of formatting
- `as_flex_table()` → Word, `as_hux_table()` → LaTeX
- Auto-selects statistical tests, auto-generates footnotes

### 2. Journal-specific differences that MUST be parameterized

| Parameter | AMA (Radiology/JAMA/AJR) | NEJM | Lancet |
|---|---|---|---|
| Footnote markers | a, b, c (letters) | *, †, ‡ (symbols) | *, †, ‡ (symbols) |
| P leading zero | No (.05) | No (.05) | Yes (0.05) |
| P case/italic | *P* uppercase italic | *P* uppercase | p lowercase |
| CI separator | comma: (0.8, 1.2) | "to": 0.8 to 1.2 | "to": 0.8 to 1.2 |
| Title separator | Period: Table 1. | Period: Table 1. | Colon: Table 1: |

### 3. Footnote placement order (universal)
1. General note (no marker) — e.g., "Data are mean (SD) unless noted"
2. Abbreviations — in appearance order (AMA) or alphabetical (JAMA)
3. Specific notes (superscript markers) — per-cell explanations
4. Probability notes (asterisks) — significance thresholds

### 4. Table-maker agent: defer or integrate?
- **Original discussion**: split table-maker as separate agent
- **Recommendation**: integrate into statistician skill first. Split only if table formatting becomes >50% of the agent's logic
- **Rationale**: gtsummary handles both statistics AND formatting in one pipeline. Splitting would create unnecessary handoff between agents

## What to Read

Priority order:
1. `table-standards.md` §1-4 (universal rules, journal diffs, AMA, footnotes)
2. `journal-profiles/radiology.yaml` + `jama.yaml` (most common targets)
3. `table-types/table1_demographics.md` (most common table type)
4. `tool-comparison.md` (pipeline decisions)

## Common Mistakes to Encode as Validation

From `table-standards.md` §5, the most impactful:
- Binary variables showing both levels (Male 53% / Female 47%)
- Missing units in column headers
- Inconsistent decimal places within a column
- P values without naming the statistical test
- "NS" instead of exact P values
- Regression tables without reference category stated
- Effect sizes per 1-unit instead of clinically meaningful units
