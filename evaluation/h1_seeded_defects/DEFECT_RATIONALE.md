# Seeded-defect rationale and completeness argument (E1 / E2)

This document records **why each seeded defect was chosen, what real-world manuscript-error
class it represents, and how far the set can claim to be necessary-and-sufficient.** It
accompanies the defect registry (`registry.py`) and injectors (`inject.py`) and is the
evidentiary basis for the Tool Validation section of the methods paper. It is referenced when
a reader asks: *how were defects injected, on what grounds, and how do you know the set is
adequate?*

It also records the **clean-baseline provenance and false-negative scope** for the benchmark.

## 1. Design in one paragraph

The benchmark injects **one known defect at a time** into a temporary copy of a clean input,
runs the **single detector that targets that defect class**, and records whether the detector
emitted the specific code for the injected defect (recall), plus whether the same detector
raised that code on the *uninjected* input (clean false positive). Injection is deterministic
(first-match-in-document-order, no RNG); attribution is unambiguous (one defect, one judged
detector per temporary copy). Because fault injection has **no defined defect prevalence**, the
benchmark reports **recall and the clean false-positive rate, not precision or sensitivity** — it
is a *triggering* check, not a population estimate. Across the 27 offline injection instances
(19 distinct specs, 17 of them offline; 2 citation defects require a live PubMed/CrossRef lookup
and are recorded NOT_RUN offline) the detectors recovered every injected defect and raised none
of the corresponding signals on clean inputs.

## 2. Grounding: where the defect classes come from

The defect classes are **not invented for the benchmark.** Each maps to (a) a deterministic
detector that already shipped in the toolkit and (b) a documented, recurring failure mode in
LLM-assisted or human medical-research writing. The detector set itself was distilled
empirically: a **13-project panel self-review reduced 158 cross-project review traces into 12
recurring defect patterns**, which became the deterministic gate families (see `CHANGELOG.md`,
[3.6.0]/[3.7.0]). The benchmark injects a representative defect for each family.

| Defect class | Detector (`detector_id`) | Real-world error it represents | Grounding |
|---|---|---|---|
| **Citation & reference integrity** | `verify_refs`, `citation_keys` | Fabricated/duplicate/placeholder citations, undefined keys — the canonical LLM failure mode | LLM bibliography fabrication quantified in medicine and in general bibliographies; pagination/placeholder and undefined-key checks are standard reference-manager hygiene |
| **Numerical / cohort arithmetic** | `cohort_arithmetic` | Exclusion-cascade sums that do not balance; incidence rates that do not back-calculate from numerator/denominator | Source-to-prose numerical drift; STROBE flow-count balance; rate = events / person-time identity |
| **Confounding / scope / estimand** | `scope_coherence` | A cross-sectional / single-time-point design licensing a prognostic or surveillance claim | Endpoint↔conclusion scope coherence; a design cannot support a longitudinal claim it did not measure |
| **Reporting compliance** | `framework_naming` | Naming a reporting-guideline AI extension without its base instrument; mixing `+AI` / `-AI` hyphenation | Reporting-framework naming discipline; base instrument must be named alongside any extension |
| **Style / review-process integrity** | `classical_style` | Section-symbol (§) usage, in-body AI-disclosure sentences, em-dash overuse — markers a classical reviewer reads as machine-written | Classical manuscript-style conventions; these are the highest-frequency "AI tell" signals |
| **Generated-code quality** | `generated_code` | Missing random seed, hard-coded absolute paths, in-place source-file overwrite in emitted analysis scripts | Reproducibility hygiene (fixed seed; portable paths; never overwrite source data) |

## 3. The 19 defects, mechanism by mechanism

Each row: the injector's deterministic transform and the specific error class it instantiates.
Codes in parentheses are the detector signal the benchmark scores.

### Citation & reference integrity (`verify_refs`, `citation_keys`)
- **CIT_PAGINATION** (`PAGINATION_PLACEHOLDER`) — rewrites the first entry's `pages` field to
  `e000--e000`. Represents a publication-stage placeholder left in a "finished" reference, a
  load-bearing-citation hazard when it backs a method or headline claim.
- **CIT_DUPLICATE** (`DUPLICATE`) — duplicates the first entry under a new citekey with the same
  DOI. Represents the same source cited twice under two keys (reference-list inflation / drift).
- **CIT_UNDEFINED_KEY** (`UNDEFINED`) — adds an in-text `[@ghost_missing_key]` not present in the
  bibliography. Represents a prose citation pointing at a non-existent reference.
- **CIT_FAKE_DOI** (`FABRICATED`, *network*) — corrupts the first entry's DOI to a non-resolving
  string. Represents a hallucinated DOI — detectable only against a live resolver, hence NOT_RUN
  offline.
- **CIT_WRONG_AUTHOR** (`MISMATCH`, *network*) — replaces the first entry's authors with
  fabricated names while keeping a real DOI. Represents the first-author-hallucination case (a
  real DOI whose author list does not match), detectable only against the authority record.

### Numerical / cohort arithmetic (`cohort_arithmetic`)
- **COH_CASCADE_SUM** (`CASCADE_SUM`) — states "Of 5,010 participants, 1,000 had missing data,
  leaving 4,500" (5,010 − 1,000 ≠ 4,500). Represents an exclusion/complete-case cascade that does
  not balance.
- **COH_RATE_BACKCALC** (`RATE_BACKCALC`) — states "5.0 per 1,000 person-years (250 events over
  100,000 person-years)" (250 / 100,000 × 1,000 = 2.5, not 5.0). Represents a reported rate that
  does not back-calculate from its own numerator and denominator.

### Confounding / scope / estimand (`scope_coherence`)
- **SCO_PROGNOSTIC** (`CROSS_SECTIONAL_PROGNOSTIC`) — appends a surveillance/longitudinal-progression
  conclusion to a manuscript whose design is cross-sectional. Represents a conclusion that
  overreaches the study design. (Injected only into the cross-sectional demo, where it is
  genuinely incoherent; SKIPPED where there is no cross-sectional design statement.)

### Reporting compliance (`framework_naming`)
- **FRM_BASE_MISSING** (`BASE_MISSING`) — names `PROBAST-AI` without naming base `PROBAST`.
  Represents citing an AI extension as if it were a finished standalone instrument.
- **FRM_HYPHEN_MIX** (`HYPHEN_MIX`) — names base `TRIPOD` then mixes `TRIPOD+AI` and `TRIPOD-AI`.
  Represents inconsistent extension hyphenation that signals a fabricated/garbled framework name.

### Style / review-process integrity (`classical_style`)
- **STY_SECTION_SYMBOL** (`SECTION_SYMBOL`) — appends a sentence using "§2 of the protocol".
- **STY_AI_DISCLOSURE** (`INBODY_AI_DISCLOSURE`) — appends an in-body "Generative AI was not
  used…" sentence (belongs in the cover letter / disclosure form, not the body).
- **STY_EM_DASH** (`EM_DASH_OVERUSE`) — appends many "clause — clause" pairs (overuse threshold).
  These three are the highest-frequency machine-written "tells" a classical reviewer flags.

### Generated-code quality (`generated_code`)
- **GEN_MISSING_SEED_PY / _R** (`MISSING_SEED`) — strips `set.seed()` / `np.random.seed()` and
  adds an unseeded random operation. Represents non-reproducible randomness in analysis code.
- **GEN_ABS_PATH_PY / _R** (`HARDCODED_ABS_PATH`) — appends a hard-coded `/Users/...` data path
  (generic placeholder username, no PII). Represents a non-portable absolute path.
- **GEN_INPLACE_OVERWRITE_PY** (`INPLACE_SOURCE_OVERWRITE`) — reads and writes the same CSV path.
  Represents an analysis step that overwrites its own source data.

## 4. Necessary-and-sufficient: what is and is not claimed

**What the set IS:**
- **Family-complete.** Every deterministic gate family is exercised by at least one injector, so
  no detector family is left unbenchmarked.
- **Grounded, not invented.** Each defect instantiates a documented recurring failure mode (the
  12-pattern lineage above) or a published LLM/medical-writing error class — not an artificial
  target chosen to flatter a detector.
- **Attributable.** One defect per temporary copy and one judged detector per defect, so a pass
  or fail is unambiguous.

**What the set is NOT (stated plainly):**
- **Not exhaustive.** A fault-injection benchmark cannot prove a defect catalog is *complete*;
  the space of possible manuscript errors is open-ended. The benchmark demonstrates that each
  detector **fires on its target defect**, not that the detectors cover every defect a real
  manuscript could carry.
- **Not a difficulty/sensitivity estimate.** Several families are exercised by a single injector;
  recall here measures detector **triggering**, not population **sensitivity**, because injection
  has no defined prevalence. Estimating precision or sensitivity would require a corpus of real
  manuscripts carrying a known, naturally-occurring error distribution — explicitly future work.

This honest scoping is the correct answer to "how do you know you injected necessary-and-sufficient
defects?": the set is **sufficient to validate that each shipped detector triggers on the error it
targets**, and **necessary in that it covers every detector family**, but it is **not** a complete
census of manuscript defects and is not presented as one.

## 5. Clean baseline and false negatives

**Who performed the pre-injection integrity check, and how.** The clean baseline is established
**deterministically, not by human judgment**: before any injection, each detector is run on the
*uninjected* input (the demonstration manuscript or the synthetic fixture), and the codes it emits
are recorded. A defect signal is only counted as a clean false positive if the detector raises the
**target code on clean input**. In the committed canonical run, the clean false-positive count is
**0 across all clean inputs** — i.e. no detector raised a target signal in the absence of the
defect. This check is re-runnable by any reader from the release.

The demonstration manuscripts were themselves produced by the pipeline and passed the gates
**organically** before being used as clean inputs: the few gate firings encountered during
generation (a non-portable path, a prognostic-wording flag, a formatting inconsistency) were
corrected and re-verified clean, and that trail is reported in the manuscript. The single author
(Y.N.) executed the harness; because the clean check is deterministic, the "0 target signals on
clean input" result does not depend on the operator.

**False negatives.** The benchmark measures **recall on known injected defects** — for the offline
set, every injected defect was recovered (false negatives on the injected set = 0). It does **not**
measure false negatives on *real* manuscripts with an unknown natural error distribution: a
detector that never sees a class of error it was not built for would not register here. Quantifying
that real-world false-negative rate requires a corpus of real manuscripts with independently
adjudicated ground-truth errors, which this controlled injection does not provide and which a
separate study would assemble. This boundary is stated in the manuscript's Limitations.

## 6. Cross-references
- `registry.py` — the 19 `DefectSpec` rows (defect_id, class, detector, expected codes, demos).
- `inject.py` — the 17 deterministic injectors.
- `run_h1.py` — the harness (clean-baseline run + one-defect-per-temp-copy injection).
- `CHANGELOG.md` [3.6.0]/[3.7.0] — the 13-project-panel → 12-recurring-pattern → gate lineage.
- E2 (`../h2_llm_baseline/`) reuses the same 19 specs to compare the deterministic detectors
  against a generic single-prompt LLM reviewer on identical defects (ablation).
