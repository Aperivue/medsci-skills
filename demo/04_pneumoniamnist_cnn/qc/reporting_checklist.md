# Reporting checklist — CLAIM 2024

**Manuscript**: `manuscript/writeup.md` (+ `manuscript/title_page.md`)
**Guideline**: CLAIM 2024 Update — Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH,
Kahn CE Jr. *Radiol Artif Intell* 2024;6(4):e240300. doi:10.1148/ryai.240300
**Checklist source**: vendored `skills/check-reporting/references/checklists/CLAIM_2024.md` (44 items)
**Assessed**: 2026-07-31

This is a binary classification study on a public benchmark, so CLAIM maps onto it more directly
than onto Demo 5. The items that fail here fail for one of two reasons: the benchmark does not carry
the information (patient identity, demographics, lesion masks), or the study is a tooling
demonstration and never intended to make the claim the item asks about.

## Summary

| Status | Count |
|---|---:|
| PRESENT | 27 |
| PARTIAL | 6 |
| MISSING | 7 |
| N/A | 4 |

**Compliance among applicable items: 27 / 40 fully present (67.5 %), 33 / 40 at least partial
(82.5 %).** N/A items are excluded from the denominator rather than counted as satisfied.

## The one finding worth acting on

**Item 23 (Software) — the manuscript states package versions that no shipped artifact records, and
two other shipped documents say they were never captured.** `manuscript/writeup.md` gives "torch
2.12.1, medmnist 3.0.2, scikit-learn 1.9.0, captum 0.9.0, Python 3.13"; `pipeline/REPRODUCIBILITY.md`
says "Package versions: not captured at run time. This is the one gap in the record";
`pipeline/requirements.txt` says "no exact version set was captured for the published run, and
inventing pins would be a claim never tested"; and `results/results.json` has no environment block.
The Reproducibility section then asserted that package versions "are given in Methods" alongside
"none are hand-entered".

**Action (applied 2026-07-31)**: the versions are **kept but flagged in place** — they may well be
correct, and deleting a possibly-true fact is not more honest than labelling it. The manuscript now
states that this line is the single number in the note that cannot be re-derived from the
repository, and the Reproducibility section no longer claims otherwise. Closing this properly needs
the author to paste a real `pip freeze`, which is what `REPRODUCIBILITY.md` already asks reproducers
to do.

## Item-by-item

| # | Item | Status | Location / note |
|---|---|---|---|
| 1 | Title | PRESENT | Names the pipeline and the technology ("medical-imaging CNN studies", "worked example"). |
| 2 | Abstract | PRESENT | Structured; states design, benchmark, split protocol, seeds, gates, metrics with CIs, calibration, interpretability, and the honest framing. |
| 3 | Background | PRESENT | Introduction names the documented failure modes the work targets and the intended use (tooling). |
| 4 | Objectives | PRESENT | "The question this note addresses is narrow and practical…". |
| 5 | Study design | PRESENT | Retrospective secondary use of a public benchmark; stated. |
| 6 | Study goal | PRESENT | Model creation + internal testing, framed as a tooling demonstration. |
| 7 | Data sources | PRESENT | PneumoniaMNIST (MedMNIST v2, CC BY 4.0), auto-downloaded, with the source-archive SHA-256. |
| 8 | Eligibility | PARTIAL | The official benchmark split is used wholesale; no eligibility criteria are applied or reportable beyond the benchmark's own. |
| 9 | Preprocessing | PRESENT | Methods + `pipeline/dataset.py`; the benchmark ships pre-normalised 28×28 arrays. |
| 10 | Subset selection | PRESENT | MedMNIST's predefined train/validation/test split, with the disjointness proof in `qc/split_leakage.json`. |
| 11 | De-identification | MISSING | Not stated. The source is a de-identified public release; closable in one sentence. |
| 12 | Missing data | N/A | The benchmark has no missing values. |
| 13 | Acquisition protocol | MISSING | **Not available** — MedMNIST distributes 28×28 arrays with no acquisition metadata. The original Kermany cohort's parameters are not restated. |
| 14 | Reference standard definition | PARTIAL | The benchmark's own binary labels are used; their derivation is in the source dataset, cited but not described. |
| 15 | Reference standard rationale | MISSING | No argument for the benchmark labels against alternatives. |
| 16 | Annotators | MISSING | Not restated from the source dataset. |
| 17 | Annotation procedures | MISSING | Same. No annotation was performed here. |
| 18 | Annotation variability | MISSING | **Not available** for the released labels. |
| 19 | Partition assignment | PRESENT | Official image-level split; test n = 624, prevalence 0.625; class imbalance addressed by reporting AUPRC alongside AUROC. |
| 20 | Partition disjointness | PRESENT | **Sample level, proved by set arithmetic** (`qc/split_leakage.json`), and the manuscript states plainly that a real patient dataset would require the same gate at patient level — the honest disclosure of a benchmark limitation rather than a claim of patient-level rigour. |
| 21 | Test set size | MISSING | No power or precision calculation; the test set is the benchmark's own. The bootstrap CIs make the resulting precision visible. |
| 22 | Model architecture | PRESENT | Three conv blocks + global pooling + linear head; full definition in `pipeline/model.py`. |
| 23 | Software | **PARTIAL** | See the finding above: named but unsupported by any artifact, now flagged in the manuscript. |
| 24 | Initialization | PARTIAL | Training is from scratch (no transfer learning); implied by the scaffold and stated in `requirements.txt` as an optional swap, not stated in the manuscript body. |
| 25 | Training procedures | PRESENT | Adam lr 1e-3, cross-entropy, batch 128, 20 epochs, best checkpoint on validation, seeds 42/43/44; convergence shown in Figure 1. |
| 26 | Model selection | PRESENT | Best checkpoint on the validation split, stated. |
| 27 | Ensembling | PRESENT | Three-seed probability ensemble, with its own CIs. |
| 28 | Performance metrics | PRESENT | AUROC + AUPRC (imbalance-aware) and accuracy at 0.5; compared qualitatively to published baselines without quoting an unverified number. |
| 29 | Uncertainty | PRESENT | Mean ± SD over three seeds **and** bootstrap 95 % CIs (2000 replicates) on the ensemble. |
| 30 | Robustness | PARTIAL | Three seeds capture run-to-run variance; no perturbation, subgroup or external robustness analysis. |
| 31 | Explainability | PRESENT | Grad-CAM with **both Adebayo sanity checks** quantified (r −0.07, −0.03) and passed through the explainability-reporting gate; explicitly reported as attribution, not localisation, because the benchmark has no masks. |
| 32 | Internal testing | PRESENT | Test split touched once, by the evaluation script; per-seed and ensemble results reported. |
| 33 | External testing | **MISSING, and disclosed** | No external cohort. Limitations names it as required for a clinical dataset. Demo 5 in this repository is the external-validation counterpart. |
| 34 | Trial registration | N/A | Not a clinical trial. |
| 35 | Inclusion/exclusion numbers | PARTIAL | n = 624 test with prevalence is given; there is no flowchart, because the benchmark's split has no exclusion cascade to draw. |
| 36 | Demographics | MISSING | **Not available** — MedMNIST distributes no demographic fields. |
| 37 | Performance reporting | PRESENT | Per seed, over seeds, and ensemble, all against the reference standard. |
| 38 | Accuracy estimates | PRESENT | 95 % CIs, ROC analysis (Figure 2), AUPRC for imbalance. |
| 39 | Failure analysis | PARTIAL | Calibration error is surfaced and interpreted (ECE 0.127, over-confident), which is a failure-mode finding; there is no confusion matrix in the write-up and no examples of misclassified cases in clinical context. |
| 40 | Limitations | PRESENT | Benchmark resolution, image-level splitting, MPS non-determinism, default architecture, and the absence of external validation. |
| 41 | Implications | PRESENT | Discussion + Conclusion, scoped to tooling with clinical use explicitly out of scope. |
| 42 | Full protocol | PRESENT | `pipeline/REPRODUCIBILITY.md` and the runnable repository. |
| 43 | Availability | PRESENT | Dataset public; code, results manifest, gate outputs and figures all shipped; toolkit archived on Zenodo. |
| 44 | Funding | MISSING | No funding statement. |

## What a submitting author would fix first

1. **Item 23** — paste a real `pip freeze`, or delete the version line. It is the only place in this
   note where a stated fact contradicts another shipped document.
2. **Items 11, 24, 44** — one sentence each.
3. **Items 13, 16, 17, 18, 36** cannot be closed from MedMNIST; cite the source dataset for
   annotation provenance and state the gap.
4. **Item 33** is deliberately open and is answered by Demo 5 rather than by this note.

Nothing here was auto-scored. Each row was assessed against the manuscript text, and where an item is
satisfied outside the manuscript the file that satisfies it is named.
