<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Image-Synthesis / Cross-Modality Generation probes (IS1–IS4)

A 4-probe checklist for studies that synthesize one imaging modality from another (MRI→PET, MRI→CT, CT→MRI, non-contrast→contrast, low-dose→full-dose) and then claim the synthetic image carries clinically usable **functional/molecular** information. These probes complement (do not replace) the generic Phase 2 issue checklist. Their purpose is to keep three structurally distinct failure modes — which a single review tends to split or miss — under one reviewer's coverage, because each looks individually "addressable by reframing" while together they govern whether the central claim survives.

Trigger: the manuscript trains a generative model (GAN/PatchGAN, diffusion, U-Net/Swin-UNet, CycleGAN) to produce a target modality from a source modality **and** frames the output as providing metabolic / receptor / perfusion / metabolic-uptake information, or as a substitute for the real target modality when it is unavailable.

**IS1 — Determinism / information ceiling (synthetic-vs-source value claim)**:
- The synthetic image is a deterministic function of the input source image(s). For the **same reader on the same case**, "source + synthetic" cannot carry patient-specific information beyond "source alone" — any reader AUC gain is most consistent with a representation/presentation/interpretability effect, not new diagnostic information.
- Does a direct source→label baseline (e.g., MRI-only model on the same split) exist to separate *information* from *presentation*? Absent → the incremental-value claim is unsupported as written.
- An interpretability/accessibility gain can still be clinically useful — recommend reframing the Abstract/Discussion to that, not to "added diagnostic value." MAJOR candidate when the Abstract/Conclusion reads the gain as new information.

**IS2 — Target-derived preprocessing / label leakage (circularity)**:
- Was any mask, ROI, lesion segmentation, slice-selection rule, intensity normalization, or registration target derived from the **target modality** or the **outcome label** rather than from the input source alone?
- The decisive case: if a tumour/lesion mask (drawn on the target modality or from the diagnosis) guided slice selection or training, then the central claim — "functional information is *inferred from source structure*" — is circular and not supported by the design.
- Is the slice-selection / sampling strategy described at all? Silence here is itself a MAJOR candidate: the reviewer cannot exclude leakage, so the claim cannot be granted. Request the exact provenance of every preprocessing input and a leakage-free re-analysis.

**IS3 — Lesion/target-level vs global validation**:
- Quantitative agreement (SUVR/SUV correlation, Bland–Altman, PSNR/SSIM) reported on a **global or whole-organ** metric (e.g., whole-brain-to-reference-region SUVR) does not establish that the synthetic image reproduces the **lesion-level** quantity that actually drives grading/differentiation. Tumour uptake is heterogeneous; global agreement can be high while lesion uptake is wrong.
- Is target-level agreement reported (tumour ROI / target-to-background ratio)? Absent → the quantitative-fidelity claim must be tempered, or lesion-level agreement added. MAJOR candidate when the manuscript states lesion-level usability from a global metric.

**IS4 — Mechanistic / proxy-signal plausibility**:
- Name the physical quantity the source measures versus the target measures (e.g., MRI structure / blood–brain-barrier disruption vs PET tracer amino-acid transport & protein synthesis). When the manuscript labels the synthetic signal with the target's biology ("metabolic information"), is the source→target signal link **validated**, or merely assumed because the outputs look like the target?
- High image similarity is not evidence that an unmeasured biological signal was recovered. An unvalidated proxy claim is over-interpretation regardless of PSNR/SSIM. Watch for tracer-mechanism mislabeling carried through the whole manuscript (e.g., calling amino-acid-transport PET a "metabolism" readout).
- Absent validation of the structure→function link → temper the biological-information claim to image-resemblance. MAJOR candidate when the title/Abstract/Conclusion assert recovered functional/molecular information.

**Output template (IS1 example)**:
> "Because the synthetic PET is a deterministic function of the input MRI, for the same reader on the same case it cannot add patient-specific information beyond the MRI; the MRI-alone vs MRI+synthetic-PET gain is therefore more consistent with a representation/interpretability effect than with new diagnostic information, and no direct MRI→label baseline is provided to separate the two. I'd suggest reframing the Abstract and Discussion as an interpretability/accessibility gain rather than added diagnostic value, and (optionally) reporting a same-split MRI→label baseline to quantify how much of the gain is information versus presentation."

**Output template (IS2 example)**:
> "The slice-selection strategy is not described. If a tumour mask (drawn on the reference PET or from the diagnosis) guided which slices were preprocessed or trained on, then the central claim — that functional information is inferred from MRI structure — would be circular, and I could not exclude this from the manuscript as submitted. Please state the exact provenance of every preprocessing input (masks, ROIs, slice selection, normalization, registration target) and, if any was derived from the target modality or the label, provide a leakage-free re-analysis."
