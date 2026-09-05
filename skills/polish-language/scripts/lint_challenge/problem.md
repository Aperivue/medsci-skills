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

## What the linter does

`scripts/lint_consistency.py` deterministically reports (never rewrites) eight
families of inconsistency with line numbers and a per-category + total count.
It changes no text, numbers, or citations — it is advisory input for a
human/LLM polish pass.

## Fixture (synthetic only — no real manuscript/PII)

`fixture/manuscript.md` seeds exactly one or more defect per category:
abbreviation (PET unused, DKA undefined), spelling (analyse/analyze in a
UK-dominant doc), numeric range (`5-10`), p-values (`p` vs `P`, impossible
`P = 0.000`), hyphenation (follow-up/followup, healthcare/health care),
small number (`3 patients`), unit (`5mg`).

`fixture/consistent_us.md` and `fixture/consistent_uk.md` contain normal
synthetic prose. They combine consistent regional spelling, defined abbreviations,
spaced units, and grammatical noun/verb pairs. Both must produce zero findings
under `--strict`; a detector that only catches planted errors is not enough.

`follow-up` (noun/adjective) may coexist with `follow up` (verb), as in the
[CDC writing guidance](https://www.cdc.gov/nceh/clearwriting/writing-tips/2024/writing-tip-wed-05-22-2024.html).
The same distinction applies to `long-term` versus `in the long term`.
The fixed variant lists are advisory; they do not adjudicate every grammar or
journal-style choice. Numeric/hyphenated uppercase abbreviations such as
`COVID-19` are kept whole when comparing definitions and uses.

## Expected

`expected/report.txt` — 11 issues across 8 categories.

## Baseline vs linter

| | Baseline (humanize / check-reporting) | Consistency linter |
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
