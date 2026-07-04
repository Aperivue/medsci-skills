# Self-review — demo_paper.md (pre-post, reviewer perspective)

Deterministic pass (automated): 14/14 reported numbers match `results/results.json` (no fabrication);
em-dashes 11 (<25); AI-tell patterns 0; § 0; clinical-claim disclaimers present in title/abstract/
results/discussion. Gates dogfooded: split-leakage OK, training-hygiene OK, explainability-report OK.

## Anticipated Major comments
- **RM1 — References unverified (blocker for posting).** The reference list must pass `/verify-refs`
  (PubMed/CrossRef first-author + DOI cross-check) before upload. Canonical items are low-risk, but exact
  pages / IDs (CLAIM 2024 e-locator, captum arXiv id, TRIPOD+AI, NeurIPS/ICCV proceedings) must be
  confirmed. **Action: run `/verify-refs --strict` before posting; do not upload with the placeholder note.**
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
Ready to revise → v2 (RM2, Rm1, Rm2 applied). Remaining hard gate before upload: **RM1 (/verify-refs)** and
author confirmation. No fabricated numbers; all metrics trace to the executed run.
