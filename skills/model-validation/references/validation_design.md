# Validation-design reference (model-validation)

Load-on-demand backbone for Phases 2–7 — the leakage taxonomy, the internal-vs-external
tier ladder, comparator design, run variance, test-set sizing, and the reporting map. Anchored
to **Kapoor & Narayanan** (*Patterns* 2023, leakage taxonomy), **Varoquaux & Cheplygina**
(*npj Digital Medicine* 2022, medical-imaging ML failure modes), **Metrics Reloaded**
(Maier-Hein & Reinke et al., *Nature Methods* 2024), **CLAIM 2024**, **TRIPOD+AI** (*BMJ* 2024),
and **STARD-AI** (*Nature Medicine* 2025). It explains *what to check and advise*; the patient-disjointness
verdict is proven by `scripts/check_split_leakage.py`, not by this prose.

## 1. The data-leakage taxonomy

Leakage = any information about a test case that could influence training. Organise the audit by
the three Kapoor-Narayanan (*Patterns* 2023) categories; the deterministic gate covers only the
first row.

| Category (Kapoor-Narayanan) | Imaging-specific leak | How it inflates the metric | How to catch |
|---|---|---|---|
| **No clean train/test separation** | **Patient-level overlap** — the same patient's images straddle train and test | Model memorises patient anatomy, not pathology | `check_split_leakage.py` → `PATIENT_OVERLAP` (set arithmetic on IDs) |
| ″ | **Near-duplicate / repeated-acquisition** — repeat scans, follow-ups, augmented copies, overlapping patches of one volume across splits | Test cases are not independent of training | Split on the **patient**, not the image/slice/series; dedup by patient before partitioning |
| ″ | **Preprocessing-before-split** — normalisation stats, intensity windowing, resampling, feature selection, ComBat harmonisation, or foundation-model embeddings fit on the **whole cohort** | Test statistics bleed into the training pipeline | Fit every transform on the **training fold only**; the test set is touched only at scoring time |
| ″ | **Temporal leakage** — a random split where future and past coexist, under a prognostic/surveillance claim | Model peeks at later-era data | Use a **temporal split** (train on earlier, test on later) when the claim is temporal |
| **Illegitimate features** | **Site / scanner / burned-in-label shortcut** — the model keys on acquisition site, vendor signature, a laterality token, or a body-part marker rather than the finding | Discrimination collapses off-site | Standalone confound check (shortcut-learning, Geirhos et al. *Nat Mach Intell* 2020; DeGrave et al. *Nat Mach Intell* 2021; Zech et al. *PLOS Med* 2018); subgroup-by-site slice |
| **Test set ≠ population of interest** | **Spectrum / selection bias** — test cases curated, enriched, or selected on an optional modality | Reported accuracy does not transfer to deployment | Confirm the test set reflects the intended-use population; see §2 / §6 |

The decisive question to ask of every preprocessing and selection step: **could any value used in
training have been computed only with knowledge of a test case?** If yes, it is leakage even when
the split table itself looks disjoint.

### Tuning-on-test (the test set must be touched once)
Architecture search, hyperparameter sweeps, early-stopping, **and operating-point / threshold
selection** that read the test set are all forms of the first category — the test set has become a
development set, and the headline metric is optimistic. Fix the threshold and select the model on
the **training/validation folds**, then evaluate the frozen model on the test set exactly once.
"Developed with external validation" where the single external set was also used for tuning is no
longer external validation (§2).

## 2. Internal vs genuine external validation

Classify the evidence honestly and let the tier cap the claim. Cross-validation and bootstrap are
development-time **optimism corrections** (apparent-performance debiasing), **not** external
validation — this is the long-standing TRIPOD / prediction-model distinction (Collins et al.,
TRIPOD 2015; TRIPOD+AI, *BMJ* 2024).

```
apparent (train=test, never sufficient)
  → internal random split
    → k-fold cross-validation / bootstrap   ← still internal (optimism correction)
      → temporal split (later era held out)
        → geographic / external (different site, scanner, vendor)
          → multi-site / prospective external      ← retrospective evidence ends here
            → silent / shadow deployment            ┐
              → prospective comparative (impact) RCT  ├ early clinical evaluation + use
                → live deployment + monitoring        ┘  (DECIDE-AI; see §2b)
```

- A **generalisability or deployment-readiness** claim needs at least a genuine external tier
  (different site/scanner/vendor), not an internal split.
- Single-centre external validation supports a narrower claim than multi-site; say which.
- Reusing the external set for any tuning demotes it back to internal — flag the contradiction.
- A **clinical-use, workflow-impact, or patient-outcome** claim needs the prospective tiers
  in §2b (silent trial → impact study), not retrospective external accuracy.

## 2b. Beyond retrospective external — prospective evaluation & deployment monitoring

Retrospective external validation establishes that accuracy transfers; it does **not**
establish that the model is safe and useful *in the clinical workflow*. That is a separate,
higher tier the lane previously stopped short of. Design it explicitly when the claim is
clinical use, not just discrimination:

- **Silent / shadow deployment.** The model runs on live prospective cases without acting on
  care; compare its outputs to the real-time reference and to clinician decisions. Catches
  prospective performance drop, input/workflow mismatch, and edge-case failures before any
  patient is affected. Pre-specify the prospective performance and calibration targets.
- **Prospective comparative (impact) study / RCT.** To claim a workflow or patient-outcome
  benefit, randomise or prospectively compare the AI-assisted pathway against standard care
  on a **clinical** endpoint (time-to-diagnosis, recall rate, downstream outcome), not just
  standalone accuracy. This is the top of the evidence hierarchy for clinical AI.
- **Post-deployment monitoring.** A deployed model is not a finished artifact: pre-specify a
  monitoring plan for **performance drift, dataset / population shift, and calibration
  drift** over time, with trigger thresholds for recalibration or withdrawal, and an audit of
  subgroup performance over time (equity does not hold automatically post-deployment).

**Reporting.** Early-stage live evaluation of decision-support AI is reported against
**DECIDE-AI** (Stage 1–2a, early clinical evaluation); full prospective trials against
**CONSORT-AI / SPIRIT-AI**. Route via `/check-reporting` (Phase 7). State which tier the
study reaches and scope the claim to it — a retrospective external study must not claim
deployment readiness, monitoring adequacy, or clinical-outcome benefit.

## 3. Comparator design

A standalone metric rarely answers the clinical question; decide what the model is measured
*against*, evaluated on the **same** test set. CLAIM 2024 and TRIPOD+AI both ask for comparison to
current practice / an existing model.

| Comparator | When | Hand-off |
|---|---|---|
| **Clinical / no-model baseline** | "does the model beat current standard of care?" | — |
| **Incremental value over an existing score** | model added on top of an established risk score / radiologist read | added-value statistics (NRI / IDI / decision curve) → `/analyze-stats` |
| **Reader comparison (standalone or AI-assisted)** | model vs / with radiologists | rubric, reader panel, inter-rater design → `/design-ai-benchmarking` |

Name whether the claim is **standalone** (model alone) or **assistive** (clinician + model); they
need different comparators and different reporting.

## 4. Single-run vs multi-seed variance

A single training run overstates precision: deep-model metrics move with the random seed
(initialisation, data order, augmentation), and some GPU ops are non-deterministic even with cuDNN
deterministic flags set (Varoquaux & Cheplygina, *npj Digit Med* 2022; reproducibility crisis,
Kapoor & Narayanan 2023). Require the headline metric as **mean ± SD over ≥ 3 seeds / runs**, or a
**single fixed reported seed with the determinism caveat stated**. A point estimate from one run,
presented as if exact, is a reporting defect.

## 5. Test-set sizing

Check **events per class in the test set**, not the cohort total. A metric computed on a sparse
positive set has a confidence interval spanning much of the usable range, so a headline AUROC /
sensitivity can be statistically uninformative even when the cohort is large.

- Size the test set for the **CI width** of the headline metric and for **per-subgroup** estimates
  you intend to report.
- **Calibration** in particular is data-hungry — prediction-model validation guidance uses a rule
  of thumb of roughly ≥ 100 events and ≥ 100 non-events before a reliability assessment is stable
  (treat as a rule of thumb, not a hard cutoff; confirm for the specific design).
- Hand the formal calculation (diagnostic-accuracy precision, AUC precision, agreement, calibration
  sample size) to `/calc-sample-size`.

Metric **selection** (Dice + boundary metric; AUROC + AUPRC under imbalance; FROC/mAP with the IoU
criterion) is owned by `/model-evaluation` (`references/metric_guide.md`, anchored to Metrics
Reloaded); this skill only checks that the chosen metric is task- and prevalence-correct.

## 6. Reporting-guideline fit

Map the study to its standard via `/check-reporting`, and **name both the base instrument and the
AI extension**, citing each at its actual maturity (published guideline vs protocol-stage), never
beyond it. The four standards below are cross-checked against the repository's `check-reporting`
verified checklists.

| Study framing | Primary standard (extension) | Base instrument | Risk of bias |
|---|---|---|---|
| Diagnostic / triage **imaging-AI** study (standalone or assistive) | **CLAIM 2024** update (Tejani et al., *Radiology: AI* 2024) | CLAIM 2020 (Mongan, Moy, Kahn, *Radiology: AI* 2020) | PROBAST+AI |
| **Prediction model** (diagnostic or prognostic; regression or ML) | **TRIPOD+AI** (Collins, Moons et al., *BMJ* 2024) | TRIPOD 2015 (Collins, Reitsma, Altman, Moons) | **PROBAST+AI** (Moons et al., *BMJ* 2025; replaces PROBAST-2019) on base PROBAST (Wolff et al., *Ann Intern Med* 2019) |
| **Diagnostic accuracy** study (index test vs reference standard; sens/spec) | **STARD-AI** (Sounderajah et al., *Nature Medicine* 2025) | STARD 2015 (Bossuyt et al., *BMJ* 2015) | QUADAS-2 / QUADAS-C |

Tie the partition, leakage controls, validation tier, comparator, run variance, and test-set sizing
above to the specific items these standards request (data partition, sample size, model evaluation,
comparison to current practice, reproducibility).

## Hand-offs
- Patient-disjointness proof → `scripts/check_split_leakage.py` (Phase 2, run first).
- Test-set / event sizing → `/calc-sample-size`.
- Reader-comparison rubric + inter-rater design → `/design-ai-benchmarking`.
- Per-case metric computation + reporting gate → `/model-evaluation` → `/analyze-stats`.
- Item-by-item compliance → `/check-reporting`; Methods write-up → `/write-paper`; reviewer-side
  audit of the finished draft → `/self-review` (MD0–MD8 `model_development.md` probe).

## Verification notes (what each claim is grounded on)
- **Leakage taxonomy / three categories, reproducibility crisis** — Kapoor & Narayanan, "Leakage and
  the reproducibility crisis in machine-learning-based science," *Patterns* 2023. Imaging-specific
  failure modes (patient-level split, preprocessing-before-split) — Varoquaux & Cheplygina,
  *npj Digital Medicine* 2022. Both already cited in `check_split_leakage.py`.
- **Site/scanner/shortcut leakage** — shortcut learning, Geirhos et al., *Nature Machine
  Intelligence* 2020; radiographic shortcut example, DeGrave et al., *Nature Machine Intelligence*
  2021; cross-site generalisation failure, Zech et al., *PLOS Medicine* 2018. Used as named
  examples of the "illegitimate features" / spectrum-bias rows, not as numeric claims.
- **Internal vs external, optimism correction, CV ≠ external** — TRIPOD 2015 (Collins, Reitsma,
  Altman, Moons) and TRIPOD+AI (*BMJ* 2024). The tier ladder mirrors the skill's Phase 3.
- **Metric selection deferral** — Metrics Reloaded (Maier-Hein & Reinke et al., *Nature Methods*
  2024); detail lives in `/model-evaluation`.
- **Reporting map** — CLAIM 2024 update (Tejani et al., *Radiology: AI* 2024) on base CLAIM 2020
  (Mongan, Moy, Kahn); TRIPOD+AI (*BMJ* 2024); STARD-AI (Sounderajah et al., *Nature Medicine*
  2025) on base STARD 2015 (Bossuyt et al., *BMJ* 2015); PROBAST+AI (Moons et al., *BMJ* 2025) on
  base PROBAST (Wolff et al., *Ann Intern Med* 2019). All four are cross-checked against this
  repository's `check-reporting` verified checklists (CLAIM 2024 = e240300; TRIPOD+AI = e078378;
  STARD-AI = DOI 10.1038/s41591-025-03953-8, PMID 40954311; PROBAST+AI = e082505).
- **Numbers deliberately not asserted**: the only quantitative figure is the ~100 events/non-events
  calibration rule of thumb, flagged as a rule of thumb to confirm per design — no dataset names,
  thresholds, or performance numbers are invented here. The reporting-standard DOIs/PMIDs above are
  carried from the repository's verified `check-reporting` checklists; still re-confirm the exact
  identifier via `/search-lit` before quoting any of them in a manuscript, and mark any uncertain
  item `[VERIFY]`.