# Exemplar reviewer comments — anchoring + phrasing models

The skill teaches *what* to look for (signature checks + domain probes) and *what tone*
to use (`aczel_2021_reviewer2_patterns.md`), but until now carried no worked examples of
how an experienced reviewer turns a finding into a comment. This directory fills that gap.

Each file models one recurring finding for medical-AI / clinical papers and shows the
same four moves a strong review makes:

1. **Anchor** — name the exact location (section, figure/table, page) the concern sits in.
2. **State the gap** — what is claimed vs what the evidence supports, concretely.
3. **Phrase it as a partner** — hedged, first-person, critique-the-work-not-the-author
   (Aczel-compliant: "I'd suggest…", "it would help to…", never "the authors fail to…").
4. **Calibrate severity** — when the finding is design-level it becomes Major #1; when it
   is fixable-as-reported it stays a Minor; the example says which and why.

## How these are used

The reviewer (or `/self-review`) reads the relevant exemplar before drafting Phase 3
comments, to model the anchoring + phrasing — not to copy text. They are **teaching
models, authored from scratch**, not extracted from any published review.

## Contents

- `ai_overclaiming.md` — generalizability / "outperforms" / "can replace" claims that
  outrun single-center or single-reader evidence.
- `reference_standard_validity.md` — an imprecise, unblinded, or mistimed reference
  standard in a diagnostic-accuracy study.
- `data_leakage.md` — patient-level split violations and label-bearing input features.
- `calibration_missing.md` — discrimination (AUC) reported for a clinical prediction
  model with no calibration assessment.

## Curator guidelines (for adding more)

- **Synthetic only.** Author the example; never paste a real reviewer's words or a real
  manuscript's text. Use placeholder study details ("a single-center retrospective
  cohort", "Figure 3").
- **One finding per file**, showing the four moves above end to end.
- **Show both the weak and the strong phrasing** so the contrast is teachable.
- **Tie severity to the fatal-flaw hierarchy** the skill already uses (design-level →
  Major #1; reporting-level → Minor).
- Keep each file ~40–80 lines. Cross-reference the relevant domain probe or signature
  check by name, not by copying it.
