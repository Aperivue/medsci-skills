<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# AI / ML overclaiming probes (AO0–AO4)

A 4-probe checklist for medical-AI/ML primary studies (diagnostic, prognostic, triage, detection) where the **conclusion's reach exceeds the evidence**. These probes complement (do not replace) the generic Phase 2 issue checklist and the signature "Overclaiming vs evidence level" check. The aim is to keep a framing-level over-reach from passing as a wording nitpick: a paper can report sound metrics yet draw a clinical claim — generalizable, outperforms clinicians, deployment-ready — that the design does not support, and that claim is what a reader carries away. Run AO0 first.

**AO0 — Locate the strongest claim, then its support (run before AO1; gates any over-reach finding)**:
- Identify the load-bearing claims in the Title, Abstract, and Conclusion (the sentences a reader quotes). For each, find the specific evidence cited (which dataset, which comparison, which metric + uncertainty).
- An over-reach finding is a **lead until the claim and its support are read together against the manuscript** — do not strawman a stray adjective. Escalate only when a headline claim genuinely outruns the cited evidence.
- If the claim is already appropriately hedged to the evidence, record "claim matched to evidence" and move on.

**AO1 — Generalizability claimed from limited external validation**:
- Does the Abstract/Conclusion assert the model "generalizes," is "transferable/robust across settings," or is suitable for broad populations, while external validation is a single site / single scanner-vendor / single source (or absent)?
- Sub-check: is the external set demographically narrow (single ethnicity, single sex-dominant, narrow age) relative to the population the claim names?
- If the generalizability claim outruns the external evidence → recommend softening to the evidence ("validated at one external site") and moving multi-setting generalizability to a stated limitation + next step. MAJOR candidate when it is a headline claim; MINOR when it is a single qualifier in the Discussion.

**AO2 — Superiority language against overlapping or under-powered comparison**:
- Flag "outperforms", "superior to", "beats", "can replace [clinician/radiologist]" when (a) the model vs comparator 95% CIs overlap, (b) no test of the *difference* is reported (two separate AUCs are not a comparison), or (c) the comparison rests on a small test set / few readers.
- Ask for the difference in the metric with its CI and a paired test of that difference, not two standalone estimates.
- If the difference is not statistically supported → recommend reframing from "outperforms" to "comparable to" (still a meaningful result). MAJOR when a superiority/replacement claim is the headline; otherwise MINOR.

**AO3 — Comparison-frame mismatch (model task ≠ human task)**:
- When a model-vs-clinician comparison drives a claim, verify the two performed the **same task on the same inputs under the same constraints**: same images/inputs available, same time budget, same question asked, same decision point.
- Common mismatches: the model sees a curated single view while readers see the full study; readers are timed or work from a different modality; the "reader" benchmark is a literature value on a different cohort.
- A mismatch makes "outperforms clinicians" non-interpretable as a clinical claim → ask the authors to state exactly which task the comparison establishes, or to align the conditions. MAJOR candidate when it underpins a headline.

**AO4 — Deployment / clinical-readiness claim from retrospective internal evidence**:
- Flag "ready for clinical deployment", "can be used to triage/guide treatment", "will reduce workload/cost", or a recommended decision threshold, when the evidence is a retrospective, internally-split (or even external but observational) accuracy study with no prospective, silent-trial, or decision-impact data and (often) no calibration or decision-curve analysis.
- Discrimination on retrospective data does not establish that acting on the model helps patients; a probability that drives a decision must also be calibrated, and net benefit must be shown.
- Recommend reframing deployment/utility language to "supports further prospective evaluation", and (where a threshold is proposed) adding calibration + decision-curve evidence. MAJOR when a deployment/care-directive claim is made; MINOR when only a hedged "potential utility" sentence.

**Output template (AO1 example)**:
> "The Conclusion states the model 'generalizes across institutions,' but external validation appears limited to a single site ([Methods, External validation]). I'd suggest softening this to the evidence — e.g., 'validated at one external site' — and framing multi-institution generalizability as a stated limitation and a next step. If a broader claim is intended, an external set spanning multiple sites/vendors would be needed to support it."

**Output template (AO2 / AO3 example)**:
> "The 'outperforms radiologists' claim rests on a comparison whose 95% CIs for model and reader [metric] overlap ([Figure/Table]), and no test of the difference is reported; the reader task also differs from the model's in [inputs/time] ([Methods/Table]). I'd suggest (a) reporting the difference in [metric] with its CI and a paired test rather than two separate estimates, and (b) stating explicitly which clinical task the comparison establishes. If the difference is not statistically supported, reframing from 'outperforms' to 'comparable to' would be both defensible and still a meaningful result."

**Discipline — leads vs findings (applies to AO0–AO4)**:
- A claim-vs-evidence mismatch surfaced by a quick scan is a **lead, not a finding, until the claim sentence and its cited support are read together** against the manuscript. Do not escalate a hedged Discussion qualifier as if it were a headline.
- Anchor every over-reach comment to the exact claim location and the exact evidence (dataset, comparison, metric + CI). A comment that names the location and the gap is actionable; "the authors overclaim" is not.
- Keep severity tied to *where* the claim sits and *what it drives*: a headline/clinical-action claim that outruns the design is design-/framing-level (MAJOR, often Major #1); a stray adjective is MINOR.
