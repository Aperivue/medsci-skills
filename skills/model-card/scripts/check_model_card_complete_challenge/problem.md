# Challenge card — Model Card / Datasheet completeness (model-card)

## Problem
A clinician who receives an engineer-built model is expected to ship a **Model Card**
(Mitchell et al., *FAccT* 2019) and a dataset **Datasheet** (Gebru et al., *CACM* 2021)
for the repo / Hugging Face card / manuscript supplement. The common failure is a card
that *looks* complete but quietly omits the load-bearing sections — Intended Use,
Out-of-Scope Use, the subgroup analysis, Caveats — or leaves them as unfilled
`[NEEDS INPUT]` placeholders. A reviewer (or a deployer) then cannot tell what the model
is for or where it must not be used.

## What the gate does
`scripts/check_model_card_complete.py` verifies that every **required** Model Card and
Datasheet section is **present** and **non-empty** — not missing, and not left as an
unfilled placeholder. It is a presence check (the documentation analogue of
`check_disclosure_availability`); it does **not** judge whether a stated fact is true
(that is `/model-validation` and the human). It never fills a section itself — the
deliverable is a card the user completed from real facts.

## Fixture (synthetic only — no real model, no PII)
- `fixture/complete/MODEL_CARD.md` + `fixture/complete/DATASHEET.md` — a fully filled,
  synthetic example (a tertiary-care-hospital liver-lesion segmentation model).
- `fixture/incomplete/MODEL_CARD.md` — omits **Out-of-Scope Use** entirely and leaves
  **Caveats and Recommendations** as `[NEEDS INPUT]`.

## Expected (`verify.sh`, network-free)
1. the complete card + datasheet **pass** (exit 0).
2. the incomplete card **fails** with `MISSING_SECTION` (Out-of-Scope Use) +
   `EMPTY_REQUIRED_SECTION` (Caveats).
3. the **unfilled template** itself fails — the gate exists precisely to force the user
   to fill every section before the card is shipped.
