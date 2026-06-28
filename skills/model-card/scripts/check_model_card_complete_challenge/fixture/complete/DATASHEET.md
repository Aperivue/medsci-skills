# Datasheet: HepaSeg multiphase-CT dataset v1.0 (synthetic example)

## Motivation
- **Purpose and creators**: created to train and evaluate liver-lesion segmentation; assembled by the imaging-AI group at a tertiary-care hospital, funded by an internal research grant.

## Composition
- **Instance**: one instance is a single patient's portal-venous-phase CT volume with a lesion mask.
- **Size and split**: 600 patients, split at the patient level into 384 train / 96 validation / 120 test.
- **Label / target**: a binary lesion mask, derived from manual radiologist segmentation (reference standard).
- **Modalities / acquisition**: multiphase abdominal CT from two scanner vendors, standard institutional protocol.
- **Known imbalance / missingness / errors**: small lesions (under 1 cm) are under-represented; 4 studies excluded for motion artefact.

## Collection Process
- **Acquisition**: consecutive eligible patients undergoing multiphase abdominal CT in the period.
- **Time frame**: 2018-2024.
- **Consent / IRB / governance**: IRB-approved retrospective study with a waiver of consent.

## Preprocessing / Cleaning / Labeling
- **Preprocessing and order vs split**: resampling to 1 mm isotropic and intensity normalisation, with normalisation statistics fit on the training fold only.
- **Annotation protocol**: two abdominal radiologists annotated independently; disagreements adjudicated by a third; inter-reader Dice 0.86.
- **De-identification**: DICOM headers stripped of identifiers; pixel data checked for burned-in PHI.

## Uses
- **Appropriate and inappropriate uses**: appropriate for liver-lesion segmentation research; must not be used to claim performance on non-contrast CT or other organs.
- **Risks**: single-centre composition limits generalisability; re-identification risk considered low after de-identification.

## Distribution
- **Availability and licence**: available to collaborators on request under a data-use agreement; not public; licence CC BY-NC 4.0.

## Maintenance
- **Maintainer and versioning**: maintained by the imaging-AI group; contact data-steward@example.org; versioned, with errata communicated to data-use-agreement holders.
