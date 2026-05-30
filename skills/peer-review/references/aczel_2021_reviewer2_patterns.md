# Anti–"Reviewer 2" Tone Patterns

Source: Aczel B, Szaszi B, Holcombe AO. *Don't be reviewer 2! Reflections on writing effective peer review comments.* Research Integrity and Peer Review. 2021;6:13. PMC8505560.

This reference codifies the linguistic patterns to avoid (and the partner-voice patterns to use) when drafting peer reviews. Apply during Phase 3 drafting and Phase 4 Self-QC.

## Avoid (the "Reviewer 2" signals)

| Category | Examples | Why |
|---|---|---|
| **Attitude markers** | "reject," "absurdly," "illogical," "naive" | Reads as verdict, not feedback |
| **Boosters** | "utterly ridiculous," "completely fails to," "totally inadequate" | Amplifies negativity, no information added |
| **Self-mention as gatekeeper** | "I cannot possibly imagine," "I refuse to believe" | Centers reviewer ego over the work |
| **Personal attacks on authors** | "The authors seem oblivious to...," "The authors do not understand..." | Critiques the people, not the work |
| **Vague dismissals** | "There is a vast literature the authors have ignored," "This is well-known" | Not actionable; offers no path forward |
| **Third-person accusatory framing** | "The authors do not sufficiently explain..." | Distancing register feels like a verdict |
| **Nitpicking every typo** | Listing 10 grammar errors as separate Minor items | Signals reviewer hostility, not care for the manuscript |
| **Requesting non-existent studies** | "The authors should have done a multi-center RCT" | Asks for impossible work to justify rejection |
| **Self-citation pressure** | "The authors should cite [reviewer's papers]" unless directly relevant | Ego-driven, recognizable to editors |
| **Over-length reviews** | Multi-hour reviews with 20+ comments | Signals desire to overwhelm rather than help |

## Prefer (the partner-voice signals)

| Category | Examples | Why |
|---|---|---|
| **First/second person rapport** | "I appreciate the thoroughness," "I stumbled over some jargon," "I look forward to the next version" | Builds collaboration, not hierarchy |
| **Hedged suggestions** | "I'd suggest," "It would help if," "Consider whether," "could be clarified" | Leaves authorial judgment intact |
| **Critique the work, not the people** | "The paper's claim to originality is weakened by..." (not "The authors seem oblivious to...") | Protects the relationship while making the same point |
| **Specific, actionable feedback** | Name the page/table/line/cell. Specify the missing citation. State the exact change requested. | Authors can act in one editorial pass |
| **Balanced framing** | Acknowledge the work's strengths in General Comments before listing concerns | Reviewer credibility ↑; authors more receptive |
| **Distinguish reflection from request** | Numbered Minor items = actionable; Closing Remark = reflection. Do not blur. | Authors know what to do |
| **Calibrate length to severity** | Minor Revision → 1-2 sentences per comment. Major Revision → 3-5 sentences with suggested fixes. | Length signals difficulty; mismatched length confuses authors |

## Worked transformations (Aczel verbatim examples + skill-specific)

### From the paper

| Problematic | Improved |
|---|---|
| "The authors seem oblivious to the extensive existing literature on this subject in the field of higher education, and thus claim their discoveries as original when they are not" | "The paper's claim to originality is weakened by its lack of reference to similar work done in the field of higher education" |
| "The authors do not sufficiently explain themselves in the Methods section, which is jargon-filled" | "I stumbled over some of the jargon in your Methods section; I'd suggest that you adopt more plain-language explanations" |

### Skill-specific transformations (medical imaging context)

| Problematic | Improved |
|---|---|
| "Please harmonize this label." | "I'd suggest harmonizing this label across the table." |
| "The authors must clarify..." | "It would help future readers if [X] were clarified." |
| "The Conclusion is overstated." | "The Conclusion could be tempered to match the single-unit scope of the data." |
| "Please cite the formula." | "Citing the specific formula (e.g., Graybill 1976) would make the calculation unambiguously reproducible." |
| "The methods section is unclear." | "I found myself wondering which environment was used for which analysis — a one-line breakdown would aid reproducibility." |

## Phase 4 Self-QC additions

Add to the existing Pre-Submission QC checklist:

- [ ] **Attitude marker scan**: 0 instances of "reject," "absurd," "ridiculous," "naive," "oblivious," "fail," "wrong"
- [ ] **Personal attack scan**: No "the authors seem...," "the authors do not understand," "the authors are unaware"
- [ ] **First-person rapport present**: At least 2 instances of "I" in General Comments / Closing Remark (not in attitude-marker contexts)
- [ ] **Hedged language ratio**: At least 50% of Minor Comment requests use hedged forms ("I'd suggest," "could," "would help") rather than imperative ("must," "Please [verb]")
- [ ] **Balance check**: General Comments names ≥2 specific strengths before listing concerns
- [ ] **Length proportionality**: Minor Revision ≤ 600 words total; Major Revision ≤ 1000 words total
- [ ] **Typo nitpicking limit**: At most 1 grammar/typo Minor Comment, only if in formal section (Acknowledgements, Declarations) or repeated systematically

## When to escalate tone (override partner voice)

Aczel's framework assumes the manuscript is fundamentally sound but needs revision. Escalate to firmer (still professional) language only when:

- Patient safety concern (dose, drug error, PHI leak)
- Severe data leakage (training-test contamination, label leakage)
- Reference standard fundamentally invalid (no ground truth)
- Citation fabrication or plagiarism suspected
- Author conflict of interest undeclared

Even at escalation, retain:
- Specific evidence (page/line)
- Hedged accusation form ("the data appear to suggest...")
- Confidential Comments to Editor for the gravest concerns

## Cross-references

- Skill: `peer-review/SKILL.md` Phase 3 (Draft) and Phase 4 (Self-QC)
- Companion: `peer-review/references/reviewer_profiles/{JOURNAL}.md` for journal-specific scorecard
- Related: `~/.claude/rules/writing-style.md` (active voice, no "we believe/think")

## Citation

Aczel B, Szaszi B, Holcombe AO. Don't be reviewer 2! Reflections on writing effective peer review comments. *Research Integrity and Peer Review.* 2021 Oct 11;6(1):13. doi:10.1186/s41073-021-00117-3. PMCID: PMC8505560.
