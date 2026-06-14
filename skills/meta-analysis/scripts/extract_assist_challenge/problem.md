# Challenge card — AI-assisted extraction suggestions (meta-analysis Phase 4)

## Problem

Data extraction is the bottleneck and a top source of SR/MA errors (2x2
cell-swaps, denominator confusion, % vs decimal mix-ups). Tools like Elicit and
SciSpace auto-fill extraction columns from full text — but a raw auto-fill is
hallucination-prone and unauditable. Before this gate, `meta-analysis` shipped a
manual extraction form (`extraction_form_v2.md`) and a confirmed-table QC
(`dta_extraction_qc.py`), but **nothing to scaffold candidate values from the
full text with provenance** for a human to confirm.

## What the new gate does

`scripts/extract_assist.py` scans a full-text Markdown paper for schema-defined
fields and emits **AI_SUGGESTED** candidates — each with a `source_page_ref` and
a **verbatim_quote** copied literally from the text. It invents nothing: values
and quotes are pulled from the document; missing fields become explicit
`not_found` rows. Every row is `needs_review = true`.

It is the extraction-stage analog of `ai_pre_screening_template.py`:
**suggestions, never decisions.**

## Pipeline (suggestions → human confirm → QC)

```
extract_assist.py  ──►  AI_SUGGESTED candidates (+page +quote)
                         │   human reconciles vs source PDF
                         ▼   (e.g., picks 0.92 over the "92%" duplicate)
                   confirmed DTA CSV  ──►  dta_extraction_qc.py  ──►  OK
```

`dta_extraction_qc.py` is **only** run on the human-confirmed CSV — never on the
suggestion TSV. Passing QC is not extract-assist's acceptance criterion.

## Fixture (synthetic only — no real paper/PII)

- `fixture/paper.md` — synthetic DTA paper with `<!-- page: N -->` markers.
- `fixture/schema.yaml` — fields incl. 2x2 cells, a custom-regex country, and a
  deliberately-absent `comparator_design` (→ `not_found`).
- `fixture/confirmed_example.csv` — the human-confirmed table after reconciling
  the unit-ambiguous sensitivity (`92%` vs `0.92`).

## Expected

- `expected/suggestions.tsv` — 11 candidates + 1 `not_found`; `source_sens`
  surfaces **two** candidates (`92%`, `0.92`) so the reviewer must reconcile the
  unit; all rows `AI_SUGGESTED` / `needs_review=true`.
- Confirmed CSV then yields `DTA QC: OK=1 | SWAP=0 | MISMATCH=0`.

## Baseline vs new gate

| | Baseline | New extract-assist gate |
|---|---|---|
| Candidate values from full text | manual typing | scaffolded suggestions |
| Per-cell provenance | author discipline | page_ref + verbatim_quote on every row |
| Hallucination posture | — | literal-only; `AI_SUGGESTED`/`needs_review`; not_found explicit |
| Unit-ambiguity surfacing | — | multiple candidates emitted side by side |

## Verifier (deterministic, no network)

```bash
bash verify.sh
```

## Acknowledgement

The "fixture + expected + deterministic verifier" packaging is inspired by
public reproducible-audit layouts such as
[EinsteinArena](https://einsteinarena.com/) (design inspiration only; no code,
solutions, or data were copied).
