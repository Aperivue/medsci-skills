# Reporting Guideline → Figure Requirements Map

> **Bridge**: this file connects `/make-figures` to `/check-reporting`
> (32 reporting guidelines). Each row tells you which figures the guideline
> **mandates** and how this skill currently supports them. Use during
> Step 1 (Specify) once the study type is known.

When `/check-reporting` flags missing figures for a target guideline, look
up the row here and either render the supported template or fall back to
the documented manual approach.

---

## Mandatory-figure map

Legend for **Status** column:
- ✅ Official template + R/Python generator shipped with this skill
- ⚠️ Generic flow generator (`generate_flow_diagram.R`) covers the layout
  but no official-template fidelity check
- ❌ No template; user produces with D2 / Graphviz / Inkscape from the
  guideline document, then runs critic_rubric manually

| Guideline (year) | Study type | Mandatory figure(s) | Status | Source / where the official asset lives |
|---|---|---|---|---|
| **PRISMA 2020** | Systematic review | Flow diagram (4-phase: identification → screening → eligibility → included) | ✅ | `templates/official/prisma2020/`; R `PRISMA2020` package |
| **PRISMA-DTA** | DTA systematic review | Modified PRISMA flow + DTA-specific exclusion reasons | ⚠️ | Salameh et al., *BMJ* 2020 (PMID 32312813); use generic flow + extra columns |
| **PRISMA-NMA** | Network MA | PRISMA flow + network plot | ❌ | Hutton et al., *Ann Intern Med* 2015; network plot via R `netmeta::netgraph()` |
| **PRISMA-P** | Protocol of SR | (none mandated; PRISMA-S search strategy figure recommended) | ❌ | Rethlefsen et al., *Syst Rev* 2021 |
| **CONSORT 2025** | RCT | Participant-flow diagram (enrollment → allocation → follow-up → analysis) | ✅ | `templates/official/consort2010/` (now CONSORT 2025); R generator |
| **CONSORT-AI 2020** | AI intervention RCT | CONSORT flow extended with AI training/validation/deployment dataset boxes | ❌ | Liu et al., *Nat Med* 2020 (PMID 32908283), Fig. 1; D2 / Graphviz custom |
| **STARD 2015** | Diagnostic accuracy | Flow diagram (eligible → index test → reference standard → 2×2) + ROC | ✅ | `templates/official/stard2015/`; R generator |
| **STARD-AI 2025** | AI diagnostic accuracy | STARD flow + dataset-flow (training / tuning / test) + subgroup-overlaid ROC/PR | ❌ | Sounderajah et al., *Nat Med* 2025 (PMID 40954311); produce manually, see `flow_diagram_lessons.md` |
| **STROBE** | Observational cohort/case-control | (Flow diagram **recommended** but not strictly mandated) | ⚠️ | von Elm et al., *Ann Intern Med* 2007; use generic flow generator |
| **TRIPOD 2015** | Prediction model | Calibration plot (mandatory) + discrimination (ROC, c-stat with CI) | ✅ (data plots) | Collins et al., *Ann Intern Med* 2015 |
| **TRIPOD+AI 2024** | AI prediction model | TRIPOD figures + **fairness/subgroup panels** + **dataset-flow** + **decision-curve analysis** | ❌ (subgroup, DCA) | Collins et al., *BMJ* 2024 (PMID 38636956); produce manually |
| **CLAIM 2024** | Medical imaging AI | Architecture diagram (model card style) + dataset-flow + calibration + per-subgroup performance + saliency/attention | ❌ | Tejani et al., *Radiology: AI* 2024 (PMID 38809149); 44 items total |
| **DECIDE-AI 2022** | AI clinical eval (Stage 1–2) | Human-AI interaction diagram + safety-signal plot + override-rate over time | ❌ (uncertain — verify in full text) | Vasey et al., *Nat Med* 2022 (PMID 35585198) |
| **CHEERS 2022** | Economic evaluation | Cost-effectiveness plane + cost-effectiveness acceptability curve | ❌ | Husereau et al., *BMJ* 2022 |
| **SPIRIT 2025** | Trial protocol | Schedule-of-enrollment timeline (Figure 1 in published trials) | ✅ | `templates/official/spirit2013/` (updated to 2025); see also Robinson timeline figures |
| **CARE 2016** | Case report | Timeline of patient course (recommended) | ⚠️ | Riley et al., *J Clin Epidemiol* 2017; use generic flow generator |
| **SQUIRE 2.0** | Quality improvement | Run chart / SPC chart | ❌ | Ogrinc et al., *BMJ Qual Saf* 2016 |

---

## When the status is ⚠️ (generic flow only)

The R `generate_flow_diagram.R` script handles the layout, but the layout
will not match the canonical guideline document exactly. For circulation
to senior co-authors, that is usually acceptable; for reviewer-facing
journals where fidelity is checked (esp. in *BMJ*, *Lancet*, *Ann Intern
Med*, *JAMA*), prefer the official template route documented in
`flow_diagram_lessons.md` Lesson 1.

## When the status is ❌

For AI-extension guidelines (CONSORT-AI, STARD-AI, TRIPOD+AI, CLAIM 2024,
DECIDE-AI), there is no shipped official template **as of 2026-05**.
Production path:

1. Read the original article to extract the canonical figure layout.
2. Sketch in D2 (`flow.d2`) or Graphviz DOT, layout via ELK.
3. Render to PDF with the platform-appropriate exporter
   (`flow_diagram_lessons.md` Lesson 2).
4. Apply the cognitive-load + key-message-visibility checks from
   `critic_rubrics/flow_diagram.md` Section G.
5. Cross-check against the corresponding `/check-reporting` checklist
   (item-by-item).

When 2 or more projects need the same custom guideline figure, propose
adding a new template under `templates/official/{guideline}/` so the
deterministic generator can support it.

---

## AI-specific figures most often missing (priority for new templates)

These are the figures that medical AI manuscripts most often omit, ranked
by how frequently a reviewer-facing checklist (CLAIM 2024 / TRIPOD+AI)
flags them:

1. **Dataset-flow diagram** — patient/image counts at each split
   (training / tuning / internal test / external test). Required by
   STARD-AI, CLAIM 2024, TRIPOD+AI.
2. **Calibration plot** — supported by `critic_rubrics/data_plot.md` §C.
3. **Fairness / subgroup panel** — performance by sex / race / device /
   site. Required by TRIPOD+AI, CLAIM 2024.
4. **Decision-curve analysis** — net benefit vs threshold. Required by
   TRIPOD+AI; recommended by CLAIM 2024.
5. **Architecture diagram** — input modality → preprocessing → backbone →
   head → output. See `pipeline_concepts_medical_ai.md`.
6. **Saliency / attention overlay** — qualitative panels showing model
   attention. Required by CLAIM 2024 §4.

---

## Cross-references

- `/check-reporting` skill — supports all 32 guidelines, item-level audit
- `flow_diagram_lessons.md` — production lessons that apply across all flows
- `pipeline_concepts_medical_ai.md` — DICOM / annotation / federated /
  architecture diagram conventions
- `design_principles.md` — communication-first design (Nat Hum Behav 2026)
- `critic_rubrics/flow_diagram.md` — extended checklist (Sections A–G)
- `critic_rubrics/data_plot.md` — calibration / fairness / colorblind checks
