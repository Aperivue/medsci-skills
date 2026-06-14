# Challenge card — Consistency linting (polish-language)

## Problem

Medical manuscripts routinely ship mechanical inconsistencies that copy-editors
catch but that content-focused passes ignore: an abbreviation used before it is
defined (or never defined), mixed US/UK spelling, hyphen-vs-en-dash numeric
ranges, mixed `P`/`p` case, variant hyphenation of the same term, single-digit
numbers written as digits in prose, and missing spaces between a value and its
unit. `/humanize` explicitly does **not** do general copy-editing (it only
removes AI tells), and `/check-reporting` checks guideline items, not house
style — so none of the existing skills caught these.

## What the new gate does

`scripts/lint_consistency.py` deterministically reports (never rewrites) seven
families of inconsistency with line numbers and a per-category + total count.
It changes no text, numbers, or citations — it is advisory input for a
human/LLM polish pass.

## Fixture (synthetic only — no real manuscript/PII)

`fixture/manuscript.md` seeds exactly one or more defect per category:
abbreviation (PET unused, DKA undefined), spelling (analyse/analyze in a
UK-dominant doc), numeric range (`5-10`), p-values (`p` vs `P`, impossible
`P = 0.000`), hyphenation (follow-up/followup, healthcare/health care),
small number (`3 patients`), unit (`5mg`).

## Expected

`expected/report.txt` — 10 issues across 7 categories.

## Baseline vs new gate

| | Baseline (humanize / check-reporting) | New consistency linter |
|---|---|---|
| Abbreviation define-once | not checked | reported |
| US/UK spelling drift | not checked | reported (minority side) |
| en-dash numeric ranges | not checked | reported |
| `P`/`p` case + `P = 0.000` | not checked | reported |
| hyphenation variants | not checked | reported |
| value/unit spacing | not checked | reported |

## Verifier (deterministic, no network)

```bash
bash verify.sh
```

## Acknowledgement

The "fixture + expected + deterministic verifier" packaging is inspired by
public reproducible-audit layouts such as
[EinsteinArena](https://einsteinarena.com/) (design inspiration only; no code,
solutions, or data were copied).
