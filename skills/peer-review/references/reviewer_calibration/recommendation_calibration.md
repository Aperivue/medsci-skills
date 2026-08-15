<!-- peer-review only. Not a domain probe: this is about the journal RECOMMENDATION,
     which /self-review does not produce. Do not vendor it into self-review. -->

# Recommendation Calibration for AI/Method and Review Papers

Before finalizing **Major Revision** (or, for AJR-style forms, a Reconsider tier) for an original AI, LLM,
or methodology paper **— or for a Review / narrative / primer article —** explicitly run this calibration
gate. It prevents a valid issue list from under-weighting contribution and priority.

1. **Design/validity flaw**: Is there a central design, leakage, reference-standard, baseline, or workflow
   mismatch that threatens the main claim?
2. **Speculative value**: Is the clinical or research-use pathway weak, with no clear decision-impact,
   workflow-change, downstream-validation, or actionability argument?
3. **Weak novelty**: Is the work hard to distinguish from close prior AI/LLM extraction or validation
   papers, or does it omit the baseline needed to show that the proposed adaptation adds value?

If 2 and 3 both hold, do not default to Major Revision simply because the review is constructive. In the
confidential comments, state that the manuscript has a priority/contribution problem in addition to the
fixable technical issues, and calibrate the recommendation toward the journal's stronger option (for
example, reject/resubmission where that tier exists). If only 1 holds and the value/novelty case is strong,
Major Revision remains appropriate.

## The three questions take evidence, not opinions

Answering "no" to 2 or 3 is a claim about the literature and about the artifact. Answered from the
manuscript's own framing, it is the manuscript grading itself — and it fails in one direction only,
toward the revision tier.

**Condition 3 ("weak novelty") may not be answered *no* without naming what was checked.** At minimum:

- **Per component.** A study assembling two or more established parts — an off-the-shelf model, a
  standard pipeline, a published score — must be assessed component by component. *Composition of
  individually validated components is engineering, not a finding*, unless the composition itself
  yields something neither component gives. Where every component is separately established, the
  burden shifts: the manuscript must show what the combination produces that its parts do not.
- **Existing products.** Name the tools or commercial systems already delivering the claimed output,
  or state that a search for them found none. "I am not aware of one" is not that search.

**Condition 2 ("speculative value") may not be answered *no* by asserting the clinical need.** That the
problem matters is a fact about the world; condition 2 asks about *this artifact's* pathway to a
decision, a workflow change, or a downstream validation. A strong need with no pathway is exactly the
case the condition exists to catch.

**Wiring: a task-formulation mismatch feeds condition 3.** If the task-formulation audit found that the
*claimed* task and the *measured* task differ, then the contribution as claimed has not been
demonstrated — so **condition 3 defaults to YES (weak novelty) unless separately evidenced against the
prior art.** Without this, an audit finding and a "the contribution is real" answer sit in the same QC
log four lines apart and nothing notices.

**Why this is here.** This is a lived failure, not a hypothetical. A QC log recorded, four lines
apart, a task-formulation audit finding that the claimed task and the measured task differed — and,
below it, condition 3 answered *no* on the grounds that the contribution was real. Condition 3 had
been answered by citing the very claim the audit had just invalidated; condition 2 from the clinical
need rather than the artifact. Neither answer cited anything. The recommendation that followed
landed well below its tier. The review was strong on execution and still came out in the wrong
place, because the gate that was supposed to price contribution accepted an unsourced answer.

*(Written from the reviewer's own QC log. A review is confidential in three directions — the
manuscript, any co-reviewer's report, and the editor's decision — so none of the three is described
here. The failure is in the gate, and the gate is what this file is for.)*

**Fixable vs unfixable tier-domination**: separate defects that a revision can repair (extraction errors,
missing supplementary, a mislabeled table, an over-claiming sentence) from defects that cannot be repaired
within the current submission (poolability of incommensurable studies, a broken construct, an invalid
evaluation instrument). When both classes are present, the **unfixable** class governs the recommendation —
do not let a long list of fixable items reframe an unfixable core as "addressable in revision."

**Salvage-reframe that shrinks the contribution is NOT a fixable major revision.** When your proposed fix
for a construct/validity flaw is to *narrow the claim* (a clinical claim reframed as a weaker technical
signal, a full study reframed as a proof-of-concept), check whether that narrower framing survives
the novelty/importance bar. If novelty/importance is ALREADY weak — your own scorecard, or a second
opinion, puts Originality or Reader-interest at or below mid — then the reframe *reduces* the
contribution and makes the importance problem worse, not better. A contribution shrunk to survive a
validity flaw is a **Reject-leaning** outcome (the contribution is the product, not
addressable-in-revision), not an encourage-major-revision. Deterministic trigger to self-audit: if
your confidential note calls the claim narrower or more modest than the manuscript claims AND your
recommendation is Reject-family-adjacent, do not upgrade it to major revision on the reframe.

**Review/narrative/primer escalation** *(the contribution IS the product)*: for a review article there is no
data to re-analyze; the distinct contribution — novelty, integrative synthesis, domain-specificity — is the
deliverable itself. Therefore **weak novelty / no distinct contribution / not domain-specific is
unfixable-in-current-form**: "add a distinct contribution" asks for a substantially different paper, so each
gap looking individually "addressable in revision" is a trap. When RV1 (novelty) is a Major in a saturated
space and no distinct contribution exists, escalate the recommendation one tier toward Reject (e.g.,
Reconsider → Reject) rather than defaulting to the revision tier.

**Confidential-note Reject-grade self-grep**: before committing the recommendation, re-read your own
Confidential Comments to the Editor. If they contain Reject-grade language — "hard to distinguish from work
it already cites," "cannot be resolved by minor editing," or **deferring the value/priority judgment to the
editorial board** ("whether the incremental value clears the bar is a scope judgment I leave to the
board") — that deferral is itself a Reject-grade tell, not a neutral hand-off. Re-examine plain Reject so the
confidential note and the recommendation are consistent.
