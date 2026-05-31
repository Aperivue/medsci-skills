# Response-Letter Voice Reference (R2R / Rebuttal)

A reference for writing response-to-reviewers (R2R) letters and editor cover letters that
read as human-written scientific argument rather than machine-generated change-logs. Use
alongside the **Response-Letter Voice & AI-Tell Avoidance** section of the revise SKILL.md.

All examples below are **synthetic** (a fictional deep-learning lung-nodule CT study) and are
illustrative only. They contain no real study, author, or institution.

Sources:
- matsuikentaro1/humanizer_academic principles (general AI-writing patterns)
- Register calibrated from the conventions of published point-by-point response letters

---

## The core problem: the editing-mechanism register

Machine-drafted response letters narrate *how the text was edited* instead of the *science*.
The result reads like a diff log: which line changed, how many phrases were swapped, what a
verification pass returned. A careful reviewer reads this as auto-generated and as evidence
the authors are clearing a checklist rather than engaging with the critique.

The fix is one habit: **state what changed and why in plain prose, quote the new sentence,
name the section — and say nothing about the mechanism by which you found or made the edit.**

This targets the *editing* mechanism only. Narrating a **new analysis you ran** is the science
the reviewer asked for and is welcome — e.g., "we performed a sensitivity analysis restricted to
one observation per patient, and the primary findings held." The tell is describing the
text-editing operation ("we softened six phrases", "v2 adds a sentence"), not describing the
analysis or its result.

---

## Two acceptable formats (the structure is not the problem)

Real published response letters use any of several formats, and all read as human:

- **A. Free prose** — "We agree. We have added to the Methods: '...'."
- **B. Structured** — a `Response:` paragraph followed by a `Changes made:` (or `Action taken in
  the revised manuscript:`) block, often with `Original: '...'` → `Revised: '...'` before/after
  pairs and the section and revised-manuscript page/line.
- **C. Two-column table** — reviewer comment on the left, author response on the right.

Other normal conventions seen across real letters: restating the reviewer's comment before
responding, and numbering multiple changes within one response as (1), (2), (3).

The AI-tell is **not** the structure, the tables, or the before/after pairs — careful authors
write all of these. The tell is the **editing-mechanism narration** layered on top: version
prefixes ("v2 adds..."), internal draft line numbers, grep/verification language, internal FIX
codes, `§` markers, and bare "No further manuscript change" stubs. Keep whichever format you
like; strip the mechanism.

---

## Before / after gallery

### 1. Version-prefixed change narration + internal line numbers

> Reviewer: The causal language overstates an observational design.

**AI-tell (bad):**
"v2 Methods §Design (line 43) adds one sentence: 'The user/non-user contrast is reported
descriptively and is not interpreted as evidence of efficacy.' This is a short visible
clarification in the manuscript body rather than only in the Limitations."

**Natural (good):**
"We agree. The design is observational, so we have added a sentence to the Methods (Design
subsection) making the descriptive intent explicit: 'The user/non-user contrast is reported
descriptively and is not interpreted as evidence of efficacy.' The corresponding causal
phrasing in the Results has been removed."

Why: the natural version keeps the quoted new sentence and a section-name pointer but drops
the version prefix, the `§` marker, the internal line number, and the meta-commentary about
*where* the clarification sits.

### 2. Tooling / verification leak

> Reviewer: Several results are described as "numerical trends," which is speculative.

**AI-tell (bad):**
"A grep-and-soften pass replaced six phrases. Final grep verification across the manuscript
and the circulated supplementary tables returned zero occurrences of 'numerical trend',
'consistent direction', or 'possible relationship'."

**Natural (good):**
"We have rephrased these passages so that non-significant point estimates are no longer
presented as trends. For example, 'users showed a numerically larger reduction' now reads
'the point estimate favoured the user arm, but the 95% confidence interval crossed zero and
is uninformative for inference.'"

Why: the reviewer cares about the corrected wording and the principle behind it, not that the
authors ran a search to confirm the strings were gone.

### 3. Redundant "no change" stubs

> Reviewer: Retention was low.

**AI-tell (bad):**
"This was already reported in v1. No further manuscript change was applied."

**Natural (good):**
"We have kept the retention figure but moved it to the front of the Conclusions so it leads
the feasibility assessment rather than appearing as an aside: the final retention of 58%
fell short of the 80% target and is the binding constraint on the present pilot."

Why: even when little changes, reply with substance. A bare "no change" stub repeated across
comments is a hallmark of checklist-driven drafting.

### 4. Uniform openers

**AI-tell (bad):** every response begins "We thank the reviewer for this important suggestion."

**Natural (good):** vary by stance —
- "We agree, and have revised accordingly."
- "This is a fair concern about generalisability."
- "We see how the original wording invited this reading; we have corrected it."
- "We respectfully maintain the original analysis, for the reasons below."

### 5. Admitting an error

**AI-tell (bad):**
"v3 corrects the acquisition-time value at line 211 per the reviewer's observation."

**Natural (good):**
"The reviewer is correct. During revision we found an error in the reported acquisition time;
the correct value is 15 s per phase. We have corrected this in the Methods and apologise for
the oversight."

### 6. Tempering an over-claim (the most common revision task)

> Reviewer: Several results are described as "significantly outperformed," but the confidence
> intervals overlap; this overstates the evidence.

**AI-tell (bad):**
"v2 grep-and-soften pass replaced 'significantly outperformed' at lines 14, 88, and 203. Final
grep verification across the circulated manuscript returned zero occurrences of
'significantly', 'consistent direction', or 'numerical superiority' (§Results, §Discussion).
FIX-2 vocabulary cascade applied."

**Natural (good):**
"We fully agree. Given the overlapping 95% confidence intervals, 'significantly outperformed'
overstated the evidence. We have tempered this language in the Abstract, Results, and
Discussion to describe the difference as a modest, consistent improvement rather than a
statistically significant one. For example, in the Results:
*Original:* 'the 2.5D model significantly outperformed the 2D model.'
*Revised:* 'the 2.5D model achieved a modestly higher C-index (0.71 vs 0.68); the confidence
intervals overlap, so this is a consistent but not statistically significant difference.'"

Why: the natural version makes the same correction the reviewer asked for, shows the exact
before/after wording, and names the affected sections — without the grep narration, the
internal line numbers, the `§` markers, or the internal FIX label.

---

## Succinctness & non-defensiveness (R2+)

Items 1-6 strip the *editing-mechanism* tell. These strip the *defensive over-elaboration* tell,
which dominates later (R2+) rounds: pre-emptive lobbying, manufactured paragraphs for satisfied
reviewers, and disclosure piled into a front section. The fix is always to say less and let the
point-by-point carry the work. (Examples remain synthetic — a fictional imaging deep-learning study.)

### 7. Pre-emptive hand-holding / cross-reviewer lobbying

**AI-tell (bad):**
"We respectfully note that Reviewers 1 and 3 found this analysis appropriate, and we left the
primary endpoint unchanged on that basis. We hope Reviewer 2 will agree that the consensus of
the panel supports our approach."

**Natural (good):**
"We retained the primary endpoint as pre-registered. Our reasoning is [one-sentence scientific
justification]; we have added it to the Methods: '[new sentence].'"

Why: answer the reviewer in front of you on the merits. Citing what other reviewers thought is
lobbying, not science, and reads as defensive.

### 8. Defensive meta-comment about an unchanged passage

**AI-tell (bad):**
"We confirm that this statement is unchanged and has not been softened or weakened in any way,
and we emphasise that it already fully conveys the intended claim."

**Natural (good):**
"This is already stated in the Discussion: '[existing sentence].'"

Why: point to where the matter is handled and stop. Insisting that nothing was weakened invites
the suspicion that something was.

### 9. Over-elaborated response to a satisfied reviewer

> Reviewer: The revised manuscript is much improved and I have no further concerns.

**AI-tell (bad):**
"We are deeply grateful to the reviewer for this generous assessment. It has been a privilege to
benefit from such careful and constructive guidance throughout, and we are delighted that the
substantial revisions across the Methods, Results, and Discussion have fully addressed the
concerns raised in the previous round."

**Natural (good):**
"Thank you."

Why: a satisfied reviewer needs one sentence. A paragraph of gratitude is padding and reads as
machine-generated filler.

### 10. Methodology disclosure as a separate front section

**AI-tell (bad):**
A standalone "Statistical Note" at the top of the letter: "Before responding to individual
comments, we wish to disclose that the subgroup analyses were not adjusted for multiplicity..."

**Natural (good):** inside the response to the comment that raised it —
"The reviewer is right to ask about multiplicity. These subgroup analyses were exploratory and
are not adjusted for multiple comparisons; we now state this in the Methods and label them as
exploratory in Table 3."

Why: keep the disclosure (never hide a deviation) but put it where the reviewer raised it. A
front-loaded "note" separates the admission from the question and reads as pre-emptive defence.

### 11. Bundling a multi-point paragraph into one block reply

> Reviewer: The introduction is too long, the cohort definition is unclear, and Figure 2 is
> hard to read.

**AI-tell (bad):**
"We thank the reviewer for these helpful comments. We have shortened the introduction, clarified
the cohort, and improved Figure 2 accordingly."

**Natural (good):** split into three —
"**Comment 1.** *'The introduction is too long.'* We have cut the introduction by roughly a
third, removing [what]. …
**Comment 2.** *'The cohort definition is unclear.'* We have added to the Methods: '[new
sentence].' …
**Comment 3.** *'Figure 2 is hard to read.'* We have remade Figure 2 with [change]. …"

Why: each sub-point gets a quoted comment and a specific response. A single block reply hides
which point you actually addressed and which you skipped. Succinct means short answers, not
fewer comments.

---

## Three response skeletons

Pick the skeleton that matches the comment's substance; do not force every reply into one shape.

### A. Full agreement (most common)

> [quote the reviewer comment]

"We agree. We have [substantive change] in the [section]. The revised text reads:
'[new sentence verbatim].'"

Keep it to 2-5 sentences. Quote the new text; name the section; stop.

### B. Partial agreement with a bounded clarification

> [quote the reviewer comment]

"The reviewer raises a valid point about [aspect]. We have [the part you accept] in the
[section]. We have not [the part you decline] because [specific scientific reason]; instead,
we [the bounded alternative], which addresses the underlying concern without [the cost of the
full request]."

### C. Polite, evidence-backed rebuttal

> [quote the reviewer comment]

"We understand the concern that [restate the reviewer's point fairly]. We respectfully
maintain [your position] because [reasoning grounded in the data or design]. [If literature
supports you: 'This is consistent with (Author, Year), who showed ...'] To make this clearer
to readers, we have added a sentence to the [section]: '[new sentence].'"

Never open a rebuttal combatively, and never write "the reviewer is wrong." Frame disagreement
as a shared interest in getting the interpretation right.

### Graceful defer (when you decline an addition but want to leave the door open)

"We considered [the requested addition], but believe [the change already made] adequately
addresses the underlying concern without [the cost]. If the reviewer prefers, we are happy to
add [the requested item] in a subsequent revision."

This is a common, courteous move: it shows you took the request seriously, gives a reason, and
defers rather than flatly refusing.

### Response-letter head (R2+)

On R1 the editor gets a separate cover letter; on **R2+ there is no separate cover letter** — its
content becomes the head of the response letter. Keep the head to a short greeting, a
one-paragraph "in brief" summary of the principal changes, an optional one-sentence
companion/verification note, the single line stating that all quotations are from the revised
manuscript, and the signature. Then go straight to the point-by-point.

"Dear Dr. [Editor], thank you for the opportunity to revise our manuscript once more. In brief,
this revision [1-2 sentence change summary]. All quotations below are from the revised
manuscript; a point-by-point response follows. Sincerely, [First Author], on behalf of all
authors."

Reuse this head verbatim in any portal "cover letter" field rather than writing a second document.

---

## Meta-phrase to natural-expression conversion

| Editing-mechanism phrase | Natural reviewer-facing phrasing |
|---|---|
| "v2 adds one sentence at line 88" | "we have added to the [section]: '...'" |
| "softened six over-interpretive phrases" | "we have rephrased the over-interpretive passages so that ..." |
| "grep verification returned zero occurrences" | (delete entirely — describe the corrected wording instead) |
| "No further manuscript change" | "the existing text in the [section] already addresses this; the relevant statement is ..." |
| "the FIX-1 vocabulary cascade" | (delete — name the actual wording change) |
| "(Methods §X)" / "see §Discussion" | "in the Methods" / "in the Discussion" |
| "the internal supplementary index (not in the circulated bundle)" | (delete — never reference internal scaffolding) |
| "demoted the term throughout at all 13 locations" | "we have replaced [old term] with [new term] throughout the manuscript" |

---

## Location-pointer rule

- Point to changes by **section name** ("in the Methods, Statistical analysis subsection").
- A **revised-manuscript page and/or line number is acceptable and common** ("Methods, page 7,
  lines 177-178") *when those numbers refer to the revised manuscript the reviewer is reading*
  (state once at the top: "all page and line numbers refer to the revised manuscript"). This
  is a normal human convention, not an AI-tell.
- What is banned is the **internal markdown/draft line number** ("line 43" pointing into your
  working file) — it will not match the reviewer's PDF and reads as a diff log. If you cannot
  guarantee the line number matches the reviewer's manuscript, use the section name only.
- When the change is a sentence or two, **quote the new text** in quotation marks. This is
  concrete, verifiable, and reads as the work of an author who knows their own manuscript.
- For larger changes (a new paragraph, a restructured subsection), summarise the change in
  one sentence and point to the section; do not transcribe the whole block.

---

## Pre-submission checklist (response letter + cover letter)

- [ ] `grep -c "§"` = 0
- [ ] No internal line-number references ("(line NN)", "at lines N, M, ...")
- [ ] No version-prefixed change narration ("v2 adds...", "the v3 revision demotes...")
- [ ] No tooling/verification leak ("grep", "softened N phrases", "circulated bundle", internal FIX labels)
- [ ] No bare "No further manuscript change" stubs — each reply carries substance
- [ ] Openers varied across responses
- [ ] New manuscript text quoted verbatim where a sentence-level change was made
- [ ] Em dashes below threshold (see humanize Pattern 13)
- [ ] Ran `/humanize` on both documents; triage hits reviewed, confirmed patterns 22-24 instances = 0 (`§` = 0 hard)
- [ ] (R2+) No separate cover letter; its summary is folded into the response-letter head
- [ ] Satisfied reviewers answered in 1-2 sentences; no cross-reviewer lobbying or defensive meta-comments
- [ ] Multi-point reviewer paragraphs split into discrete, individually quoted comments
- [ ] Methodology disclosures folded into the relevant response, not a separate front section
