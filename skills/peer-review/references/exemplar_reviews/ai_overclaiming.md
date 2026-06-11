# Exemplar — AI overclaiming relative to the evidence

**Finding class:** the conclusion's reach (generalizable / outperforms / can replace)
exceeds what a single-center, single-reader, or internally-validated result supports.
**Typical severity:** design-/framing-level → **Major #1** when the headline claim depends
on it; Minor when it is only a stray adjective in the Discussion.

## What the reviewer noticed

The Abstract and Conclusion state the model "generalizes across institutions" and
"outperforms radiologists," but the external test set is one site (Methods, "External
validation"), the reader comparison used two readers on a different task tempo than the
model (Table 3), and the confidence intervals for model vs reader AUC overlap (Figure 2).

## Weak phrasing (avoid)

> The authors overclaim. Saying the model generalizes and beats radiologists is not
> justified and should be removed.

(Verdict without an anchor, no path forward, gatekeeper tone.)

## Strong phrasing (model this)

> The Conclusion states the model "generalizes across institutions," but external
> validation appears limited to a single site (Methods, *External validation*). I'd
> suggest softening this to the evidence — e.g., "validated at one external site" — and
> framing multi-institution generalizability as a stated limitation and next step.
>
> Relatedly, the "outperforms radiologists" claim rests on a comparison whose 95% CIs for
> model and reader AUC overlap (Figure 2), and the reader task differs from the model's in
> [tempo/inputs] (Table 3). It would strengthen the paper to (a) report the difference in
> AUC with its CI and a test of that difference rather than two separate AUCs, and (b)
> state explicitly which clinical task the comparison establishes. If the difference is
> not statistically supported, I'd recommend reframing from "outperforms" to
> "comparable to," which is still a meaningful and more defensible result.

## Why this is Major #1 here

The over-reach is in the Abstract and Conclusion and is the paper's headline, so a reader
takes away a claim the data do not support. Anchoring it to the single-site external set
and the overlapping CIs makes the fix concrete and keeps the contribution intact.

## Related checks

Signature check "Overclaiming vs evidence level"; self-review category D
(endpoint↔conclusion scope); `check_scope_coherence.py` for surrogate→care-directive and
cross-sectional→prognostic variants.
