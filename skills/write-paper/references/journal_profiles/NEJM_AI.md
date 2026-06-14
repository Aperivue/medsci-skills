# NEJM AI

## Journal Identity

- **Full name**: NEJM AI
- **Abbreviation**: NEJM AI
- **Publisher**: NEJM Group (owned and published by the Massachusetts Medical Society)
- **ISSN**: 2836-9386 (digital-only)
- **Frequency**: Monthly (12 issues/year) with continuous publication
- **Impact Factor**: None yet (journal launched January 2024; no Journal Citation Reports JIF assigned as of mid-2026 — verify Clarivate JCR / Scopus CiteScore at submission time)
- **Open Access**: No author-pays model; **no submission or publication fees**. Author Accepted Manuscript may be deposited in a noncommercial repository at acceptance (CC BY-NC-ND default; CC BY-ND or CC BY for Coalition S / NIH / NIHR / UKRI / Wellcome). **Datasets, Benchmarks, and Protocols are freely available immediately on publication.**
- **Editor-in-Chief**: Isaac (Zak) Kohane (Harvard Medical School, Biomedical Informatics)
- **Relevant imaging/eval editors**: Xiaoxuan Liu (SPIRIT-AI/CONSORT-AI), Judy Wawira Gichoya (radiology informatics), Venkatesh Murthy (radiology/cardiac imaging), Pranav Rajpurkar (medical imaging AI), Roxana Daneshjou, David Ouyang
- **Submission**: NEJM AI online submission system; contact editorial.ai@nejm.org. **No presubmission inquiries** (full manuscripts only).

## Aims and Scope

Interdisciplinary journal facilitating dialogue among stakeholders using AI to transform medicine; **intentionally pairs "pre-clinical" and clinical articles**. Covers AI methodologies and data science applied to biomedical informatics, connected health, telemedicine, **medical images and imaging**, personalized medicine, policy and regulation, and ethical/medicolegal implications. AI "must meet the same bar for clinical evidence as other clinical interventions." Rigorous NEJM-Group peer review plus dedicated statistical review.

## Manuscript Types and Word Limits

Word-count limits include introduction through conclusion/discussion; **exclude** abstract, figure legends, and table notes.

| Type | Abstract | Body (max) | Tables + Figures | Notes |
|------|----------|-----------|------------------|-------|
| **Original Article** | Structured (B/M/R/C) ≤300 w | **3,000** | up to 5 | Clinical trials of AI, AI-assisted dx/tx, breakthrough pre-clinical, rigorous evaluations of medical AI |
| **Datasets, Benchmarks, and Protocols** | Structured (B/M/R/C) ≤300 w | **3,000** | up to 5 | New datasets, shared benchmarks, **reproducible/novel protocols or study designs adaptable to other trials**; immediately full OA |
| Case Study | Unstructured | 2,000 | up to 5 | First-person deployment lessons |
| Review | Unstructured | 3,000 | up to 5 | Usually solicited |
| Perspective | Unstructured | 1,200 | 1 central | Usually solicited |
| Policy Corner | Unstructured | 2,000 | 2 central | Multi-stakeholder policy |
| Editorial | Unstructured | 1,000 | none | Solicited; ≥1 reference |
| Letter | none | 400 | 1 | ≤5 refs; first ref = article discussed |

All original-research article types require a **1–2 sentence short description** in addition to the abstract.

## Abstract Format

**Structured: Background, Methods, Results, Conclusions** (4 headings), **≤300 words**, for all original research. Report key findings as **key data, not unsupported statements**. (Note: this differs from npj DM's 3-heading and Lancet DH's 5-heading abstracts — NEJM AI needs its own 4-heading variant.)

## Required Sections / Submission Elements

1. Title page (single corresponding author; ORCID for corresponding at submission, all authors at acceptance)
2. Structured abstract (B/M/R/C ≤300 w) + 1–2 sentence short description
3. Introduction → Methods → Results → Discussion/Conclusion (standard IMRAD; not Nature Methods-last)
4. Funding/support statement (mandatory if funded)
5. **Data-sharing statement** (ICMJE-compliant)
6. Code availability / reproducibility (ML reporting — see below)
7. **Author contributions** including who wrote the first draft (and any paid writing assistance)
8. **AI-use disclosure** (in both cover letter and manuscript)
9. Ethics/consent statement: IRB approval, **how informed consent was obtained and which body approved the consent document**, Declaration of Helsinki adherence
10. **Diversity/representativeness supplementary table** (clinical research studies)
11. Tables embedded in manuscript; **figures uploaded as separate files**
12. COI disclosure for every author via **Convey** (published with article)

## Citation Style

NEJM/Vancouver-style numbered references (verify exact NEJM AI formatting in the Formatting Guide for Authors PDF). AI-generated material **cannot be cited as a primary source**; all quoted material fully attributed.

## Reporting Guidelines

- **Machine-learning methodology** must be reported in detail: problem statement + clinical relevance; dataset source/size/characteristics + collection + preprocessing; **written permission for any datasets/databases**; algorithms/models with hyperparameters and configurations; evaluation metrics + validation strategy (cross-validation or separate test set); comprehensive results + comparisons + statistics; limitations + data biases + clinical implications; ethics (consent, data privacy); **reproducibility (code availability + implementation steps)**.
- Recommended checklist: **TRIPOD-AI or MI-CLAIM**.
- Trials: CONSORT flow diagram + checklist.

## Statistics (statistical-review desk — strict)

- Methods must state **sample-size/power** considerations and primary/secondary analysis methods.
- **Missing-data** handling described; complete-case generally not acceptable as primary unless missingness is rare.
- Significance tests accompanied by **confidence intervals**; CIs adjusted to match any significance-level adjustment.
- **Two-sided P values unless the design requires one-sided** (e.g., non-inferiority / TOST). P formatting: >0.01 → 2 decimals; 0.01–0.001 → 3 decimals; <0.001 → "P<0.001."
- Results to no more precision than meaningful (e.g., odds ratios to 2 significant digits).
- **Observational studies**: signed/dated prespecified SAP encouraged (deposit in a repository); prespecified FWER/FDR control or **limit secondary/exploratory analyses to point estimates + 95% CI with no P values** and a note that intervals are unadjusted for multiplicity; show confounder distribution stratified by exposure; sensitivity to unmeasured confounding; **encourage retesting findings in an independent study**.
- Prefer absolute counts/rates before relative risks; **avoid odds ratios** where they overestimate risk.

## Trial Registration

AI-intervention **trials** enrolling patients after 2025-01-01 must register in a **WHO ICTRP-compliant** database. (A diagnostic/evaluation reader study that does not prospectively assign subjects to intervention vs comparison groups for a health outcome is generally **not** a "clinical trial" requiring ICTRP registration — confirm at submission; an OSF prospective registration is a strength but is not an ICTRP registry.)

## Authorship & Corresponding-Author Policy

- ICMJE authorship criteria; **no author limit** (Commentary types prefer <10).
- **Only ONE corresponding author** during submission and revision; that author is the manuscript guarantor. After acceptance, additional reader-contact authors may be designated, but the original corresponding author remains the corresponding author of record.
- **Co-first / co-senior allowed**: "Drs. A and B contributed equally to this manuscript" at the end of the author list.

## Prior Publication

Not published nor under consideration elsewhere, EXCEPT: research presented at scientific meetings; results released to government agencies for statutory/urgent public-health needs; **articles posted on a preprint server** (allowed). Cascaded NEJM manuscripts accepted.

## Peer Review

Single-blind; ≥2 outside reviewers for original research + dedicated **statistical/methodological review**; reviews requested within ~2 weeks (NEJM-family fast triage). Editors screen and only send suitable manuscripts to review. Optional **invitation/request-based accelerated review** (≈7-day decision) for urgent public-health / immediate-practice-change / meeting-timed work — request via editorial.ai@nejm.org (not guaranteed).

## Special Notes

- **3,000-word hard limit** for Original Article / Datasets-Benchmarks-Protocols is the dominant constraint — manuscripts written for Lancet DH (~3,500–5,000) or npj DM must be compressed heavily.
- **Datasets, Benchmarks, and Protocols** is a distinct, less-crowded lane for a pre-registered, reusable evaluation **protocol / study design + locked benchmark dataset**, with immediate full OA.
- Single corresponding author requirement conflicts with co-corresponding setups → designate one submitting/guarantor author up front.
- COI is collected via **Convey**, not ICMJE PDF forms generated elsewhere.
- Diversity/representativeness supplementary table is a hard requirement for clinical research.
- Archived via Portico; published under MMS copyright with Publishing Agreement + Authorship Statement at acceptance.

## Verification
- Source: NEJM AI Author Center / Editorial Policies / Article Types / Peer Review & Publication Process (author-guide text, verified 2026-06-14).
- Re-verify before submission: exact reference formatting (Formatting Guide PDF), current JCR/CiteScore status, and whether the study is classified as a "clinical trial" for registration.
