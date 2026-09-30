# Challenge — the normaliser that was right for the data it was fit on, and wrong for the data it met

A segmentation model is trained on CT. Its training plan records a normalisation contract: clip to
the CT foreground window, then z-score by the CT mean and standard deviation. That contract travels
with the checkpoint into inference, and the inference command has **no argument that declares the
modality of the incoming images**.

The model is then applied to an MR cohort. Every case returns a file. The job exits 0.

## The question

Given a dataset profile with per-case intensity summaries and the trained contract, decide whether
the cohort about to be predicted is in the intensity domain that contract assumes.

## What makes it hard

The tempting check is the destructive one — "how much of each volume does the clip discard?" — and
it is wrong. A CT volume's 99th percentile is bone, and clipping bone above a soft-tissue window is
what the contract is *for*. That check fires on 100% of the cohort the plan was fit on. A detector
that rejects its own training domain is worse than no detector, and a five-number summary cannot
tell "the window is working" from "the window is destroying the image".

The check that survives is narrower and decisive: **Hounsfield units are defined by an air floor
near −1000.** A cohort in which no case contains a voxel below −500 is not in Hounsfield units,
whatever any metadata field claims — and a CT contract applied to it is applying a window that means
nothing there.

## What the fixtures encode

- A cohort that IS in the contract's domain must come back clean. This is the false-positive guard,
  and it is the half most detectors of this kind fail.
- A cohort with no air floor anywhere must raise a Major.
- A split where some cases bottom out near air and some do not cannot be served by one contract, and
  is flagged.
- A contract the loader cannot parse must **refuse**, not score as "assumes arbitrary" and pass.

## Provenance

Derived from `demo/05_msd_amos_spleen`, where this exact mismatch cost a measured **~0.28 Dice** —
established by two independent counterfactual arms, neither of which retrained the model. The
toolkit's own profiler had already recorded the underlying property before training, as a **Minor**,
in a directory no later step reads. The gap this card closes is routing and severity, not detection.
