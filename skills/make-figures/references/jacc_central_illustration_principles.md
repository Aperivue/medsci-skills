# JACC Central Illustration — Principles & Layout Spec

Distilled from Fuster V, Mann DL. **The Art and Challenge of Crafting a Central Illustration or Visual Abstract.** *J Am Coll Cardiol.* 2019;74(22):2816–2820. doi:10.1016/j.jacc.2019.10.035

This document is the canonical reference when generating Central Illustrations for JACC, JACC: Asia, JACC: Cardiovascular Imaging, JACC: Heart Failure, JACC: Basic to Translational Science, JACC: CardioOncology, and JACC: Clinical Electrophysiology.

## CI vs Visual Abstract — they are different artifacts

| Aspect | Central Illustration | Visual Abstract |
|---|---|---|
| Purpose | Single key finding / take-home message | Methods + Results pictorial summary |
| Where referenced in paper | End of Results / start of Discussion | Beginning of paper |
| Methods content | **None** | Required |
| Audience | Cardiovascular clinicians + readers of the journal issue | Broad including non-specialists / social media |
| Used by | All JACC family journals + JACC: Asia | Originally JACC: Basic to Translational Science |
| Text density | Minimal (graphical priority) | More allowed (methods labels) |
| Bar graphs | OK if they capture entire message | Avoid — use ↑↓ arrows |
| Default complexity | Simple (1–3 visual zones) | Simple (Q→M→R three blocks) |

If a paper requires *both* a central illustration and a visual abstract (some JACC sister journals), they must convey complementary content; do not duplicate.

## Five Fuster-Mann rules (must pass all)

1. **Know the message.** Decide one finding the figure must convey. Do not stuff in the study design + multiple findings + take-homes — that "causes confusion and excess that does not inform the reader."
2. **Convey graphically, not textually.** Even a simple Kaplan–Meier curve is acceptable if it captures the entire message. Bar graphs are tolerated if they earn their space.
3. **Avoid using too much text.** Any text that can be replaced by an icon or arrow should be.
4. **Avoid secondary messages.** If a viewer cannot state the main finding within 5 seconds of looking at the figure, the figure has too much.
5. **Simplicity is superior.** Authors "truly struggle with the concept" early; default to fewer panels rather than more.

## CI mode validation rules (enforced by `generate_visual_abstract.py --type central-illustration`)

A submission rejects with a warning if any of the following holds:

| Rule | Threshold | Rationale (Fuster-Mann) |
|---|---|---|
| `n_visual_zones` | ≤ 3 | "Simplicity is superior" |
| `total_label_word_count` | ≤ 30 | "Avoid using too much text" |
| `methods_terms_present` | none of: `cohort flow`, `inclusion`, `exclusion`, `study design`, `enrollment`, `randomized`, `sample size` | CI ≠ VA; methods belong in VA |
| `numerical_data_points` | ≤ 4 | "Avoid incorporating secondary messages" |

Override a single rule with `--allow rule=name` and a justification note recorded in the output PPTX speaker notes.

## JACC PPTX layout (verified from official submission templates)

Reference: 4 official JACC PPTX submission files (Figures 1–4 of Fuster-Mann editorial, doi:10.1016/j.jacc.2019.10.035). All four share an identical layout:

| Slot | Type | Position (left, top) inches | Size (W × H) inches | Content |
|---|---|---|---|---|
| 1 | TEXT_BOX | (0.4, 5.3) | 9.4 × 0.5 | Citation: `"FirstAuthor et al. JACC YYYY; vol(issue):pages."` |
| 2 | PICTURE | (3.0, 0.8) | 4.0 × 4.2 | **Author-provided content figure** (the only thing the author owns) |
| 3 | TEXT_BOX | (0.4, 7.0) | 4.1 × 0.5 | Reserved (often empty in production templates) |
| 4 | PICTURE | (7.3, 6.7) | 2.7 × 0.8 | JACC family logo (placeholder; supplied by editorial) |

Slide size: **10 × 7.5 inches (4:3)**. Background white.

The red border + the blue "CENTRAL ILLUSTRATION:" header bar visible in published JACC issues are **applied by the JACC editorial team after acceptance** — authors should not pre-render those elements in their submission.

Authors submit:
- Slot 1 (citation text)
- Slot 2 (the content figure as PNG/TIFF, ≥600 DPI, content area ~4 × 4.2 in at print)

Slots 3 and 4 stay as placeholders.

## Author-provided content figure spec

| Spec | Value |
|---|---|
| Aspect ratio | ~1:1 to slightly portrait (4 × 4.2 in) |
| Print resolution | 600 DPI for PNG, vector preferred (PDF) |
| Font | Sans-serif; minimum 9 pt at print scale |
| Color | Allowed; high-contrast for grayscale fallback |
| Visual zones | 1–3 (rule above) |
| Total label words | ≤ 30 |
| Numerical highlights | ≤ 4 |
| Photographs | Allowed (Fuster-Mann Figure 4 example) |

Reference good examples cited in the editorial:
- *Moccetti F, et al. J Am Coll Cardiol. 2018;72(9):1015–26.* — heart anatomy + 3 concept boxes + vessel cross-section + brain image. Total ~20 words. (Fuster-Mann Figure 1)
- *Brugada J, et al. J Am Coll Cardiol. 2018;72(9):1046–59.* — 3-column "Diagnosis / Pathophysiology / Management" grid with ECG, sequencing, defibrillator imagery. (Fuster-Mann Figure 2)

## Common author mistakes (rejected examples)

- Embedding the cohort flow / CONSORT-style diagram → that is a study Figure 1 or a Visual Abstract, never a Central Illustration.
- Side-by-side forest plot + KM curve + heat map → too many secondary messages.
- Text-heavy "Clinical takeaway" tile boxes summarizing multiple bullets → reduce to one icon-anchored sentence or move to Discussion narrative.
- Multiple HR/CI/p-value annotations across rows → keep ≤ 4 numerical highlights total.
- Methodology labels ("Inclusion criteria", "N=...") → CI must not look like Methods.

## Adding a non-JACC cardiology CI template

Other journals using a CI-style figure (Circulation family, EHJ, JAHA) tend to follow the same simplicity rules. For these, reuse the Fuster-Mann 5 rules above and the validation thresholds, but adjust the PPTX template to the journal's published submission size and citation footer pattern.
