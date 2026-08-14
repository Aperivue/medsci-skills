<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Radiomics / Feature-Reproducibility probes (R1–R4)

A 4-probe checklist for radiomic feature reliability/reproducibility, acquisition–reconstruction parameter sweeps, and reliability/harmonization-based feature filtering claims. These probes complement (do not replace) the generic Phase 2 issue checklist. Their purpose is to keep design-level structural validity from being under-weighted: a review can correctly flag the reporting-layer issues (an over-claiming Abstract, a small external cohort) yet still miss whether the central contribution holds, which softens the assessment by one notch.

**R1 — Design-grid circularity (in-domain "prediction" tautology)**:
- Is an outcome (e.g., feature reliability) predicted from the very grid parameters that were systematically/exhaustively varied to construct the dataset?
- If so, a high in-domain R² / accuracy is structurally guaranteed by the design ("predicting the construction recipe"), not a discovered relationship — do the predictors simply index the axes of the design grid?
- Does the manuscript frame in-domain performance as a finding/success and lead the Abstract/Key Points with it?
- If yes → do **not** endorse the in-domain success. Recommend reframing so the substantive finding is the cross-domain transportability (and, where present, its failure). MAJOR candidate.

**R2 — Construct validity / proxy-target gap**:
- The clinical rationale typically assumes that features which are reliable/stable/robust in the phantom are also better predictors of a biological/clinical target. A feature can be perfectly stable and biologically uninformative — this link is not logically guaranteed.
- Is any post-filter performance gain shown to be signal recovery, rather than a by-product of removing a degraded/misaligned baseline feature space?
- Does the manuscript acknowledge and test the orthogonality of the proxy (reliability) and the target (outcome)? Absent → MAJOR candidate.

**R3 — Transportability framing vs reporting issue**:
- When cross-phantom / cross-scanner / cross-center failure (negative R² on the target domain, low Jaccard overlap of selected features, calibration slope < 1) is the substantive result, is it nonetheless framed as a generalization success in the Abstract/Key Points/Conclusion?
- Does the Results text state explicitly that a negative R² on the target domain means the model performs worse than predicting the mean (i.e., the mapping does not transport), rather than reading it as a weak continuous performance metric?
- **Calibration link**: if in-domain "success" is partly a design artifact and the cross-domain result is a failure, reframing the Abstract will not rescue the central contribution. This is a design-level finding, not a reporting fix — keep its severity at the design level and do not soften it to a reporting issue.

**R4 — Multiplicity (model × threshold / model × cohort grid)**:
- Are multiple classifiers × multiple reliability thresholds (or cohorts) compared with one-sided tests, with a few reaching p < 0.05?
- Is multiple-testing correction applied, and is the expected number of false positives by chance named explicitly (e.g., "5 models × 3 thresholds = 15 tests, ≈1 expected false positive")? Do not defer this to a generic "statistical review needed."
- For a small external cohort (n ≤ ~30), do bootstrap ΔAUC intervals cross zero? If so, restrict any headline-gain claim accordingly (e.g., to a single classifier family in a small cohort).

**Output template (R1 example)**:
> "Because the acquisition parameters were varied as a systematic factorial grid, a model that predicts feature reliability from those same parameters is largely recovering the grid by construction; the in-domain R² ≈ 1.0 therefore reflects design structure rather than a discovered relationship. I'd suggest reframing the Abstract and Key Points so the substantive finding is the cross-phantom/cross-scanner transportability (and its failure), and stating explicitly in the Results that a negative R² on the target domain means the model performs worse than predicting the mean — i.e., the reliability mapping does not transport."

**Output template (R4 example)**:
> "The reported gains come from a grid of [N models] × [M thresholds] one-sided comparisons; with [N×M] tests, roughly one positive is expected by chance alone, and the external cohort (n = [k]) yields bootstrap ΔAUC intervals that cross zero for several thresholds. I'd suggest reporting a multiplicity-adjusted analysis (or stating the expected false-positive count), restricting the headline claim to the classifier family that survives, and marking the ΔAUC intervals that cross zero in the figure."

## When this module does not apply

These probes are out of scope for:

- Single fixed-protocol radiomic model with no parameter sweep and no reliability-filtering claim
- Pure deep-learning end-to-end imaging model (handcrafted feature reproducibility not at issue)
- Replication of a documented prior radiomic pipeline with no new reliability/transportability claim

Moved here from the consuming skill so the scope travels with the probes.
