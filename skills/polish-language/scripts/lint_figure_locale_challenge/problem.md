# Challenge — figure-SOURCE locale drift (no OCR)

A manuscript declares US spelling. Every text gate enforces it across the prose. Then a
co-author builds a panel in PowerPoint and types **"Behavioural alignment"**, or a plotting
script sets `ax.set_title("Tumour colour")` — and the word ships inside a **rendered raster**,
where no grep can reach it. A full locale sweep over manuscript + supplement + cover letter
returns exactly one hit, and it is an internal YAML comment. The real one is found by opening
the image, on submission day.

`lint_figure_locale.py` reads the figure **sources** instead of the raster — `<a:t>` runs inside
`*.pptx` slide XML, and the text of `*.py` / `*.R` plotting scripts — and compares them against
the manuscript's spelling (a `spelling:` front-matter field, or the body's own US/UK majority).

## The precision trap this card exists to lock down

The shared US↔UK families in `lint_consistency.py` originally matched the UK side with a greedy
`\w*` suffix, so words that are **identical in both dialects** counted as UK evidence:

| greedy pattern | universal word it wrongly matched |
|---|---|
| `analys` + `\w*` | **analysis**, **analyses** |
| `organis` + `\w*` | **organism(s)** |
| `characteris` + `\w*` | **characteristic(s)** — the most common table label in medicine |
| `optimis` + `\w*` | **optimism** |

A figure-source gate inherits that noise directly: "Baseline characteristics" is a figure label
in almost every clinical paper, and it is not a spelling error. The families now enumerate the
genuinely dialectal inflections, and this card asserts both halves of the contract.

## What `verify.sh` asserts (network-free, no committed binaries)

- **Positive**: in a US manuscript, `Behavioural` (a `.py` label) and `Randomised` / `centre`
  (a `.pptx` `<a:t>` run) are flagged `FIGURE_LOCALE_DRIFT`.
- **Negative — the precision guard**: `characteristics`, `analysis`, `organisms` appear in the
  very same sources and **must stay silent**.
- **Negative — clean**: US-spelled figure sources in a US manuscript produce nothing.
- **No sources**: a missing figures directory exits 0 (nothing to judge), never an error.

Fixtures are written at runtime (the `.pptx` via python-pptx), so nothing binary is committed.
