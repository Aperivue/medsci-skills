# Self-review — demo_paper.md (pre-post, reviewer perspective)

Deterministic pass (automated): 14/14 reported numbers match `results/results.json` (no fabrication);
em-dashes 11 (<25); AI-tell patterns 0; § 0; clinical-claim disclaimers present in title/abstract/
results/discussion. Gates dogfooded: split-leakage OK, training-hygiene OK, explainability-report OK.

## Anticipated Major comments
- **RM1 — References unverified (blocker for posting).** The reference list must pass `/verify-refs`
  (PubMed/CrossRef first-author + DOI cross-check) before upload. **Action (applied, 2026-07-31):**
  `/verify-refs --strict` run against `manuscript/refs.bib`; audit committed at
  `qc/reference_audit.json`. **8 of 9 OK, 0 fabricated, 0 duplicates, `submission_safe: true`.** The
  ninth (`paszke2019pytorch`, the PyTorch NeurIPS 2019 paper) is **UNVERIFIED and stays that way**:
  that proceedings year carries no CrossRef DOI and no PubMed record, so no registry can confirm it.
  UNVERIFIED is not FABRICATED — the entry is real and deliberately kept, with this note as its
  provenance. **RM1 is closed.**
- **RM2 — Missing AI-use disclosure.** The pipeline and the drafting were agent-orchestrated (the paper's
  subject); this must be disclosed explicitly. **Action (applied): added an "AI use" statement.**

## Anticipated Minor comments
- **Rm1 — Over-confidence not acted on.** ECE 0.127 is reported but no remedy shown. **Action (applied):**
  added a sentence noting temperature scaling as the standard recalibration step (a next step, not run).
- **Rm2 — Baseline comparison is vague** ("consistent with published baselines"). **Action (applied):**
  attributed to Yang et al. 2023 explicitly; kept qualitative (no unverified number quoted).
- **Rm3 — Author/affiliation are placeholders.** Editable by the author before posting. No change.
- **Rm4 — Single benchmark, image-level, small CNN.** Already disclosed in Limitations. No change.

## Scope-coherence check
Endpoint (benchmark classification) ↔ conclusion (a tooling/reproducibility claim) are aligned; no clinical
directive, no deployment claim. Consistent with the honest-framing requirement.

## Verdict
Ready to revise → v2 (RM2, Rm1, Rm2 applied). **RM1 closed 2026-07-31** (see above): the reference
audit is committed, nothing is fabricated, and the single UNVERIFIED entry is unverifiable by
construction rather than unchecked. Remaining before upload: author confirmation of the placeholder
author/affiliation (Rm3). No fabricated numbers; all metrics trace to the executed run.
