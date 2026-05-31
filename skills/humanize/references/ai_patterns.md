# AI Writing Pattern Reference for Medical/Radiology Manuscripts

Detailed reference for the 24 AI writing patterns, with expanded examples and suggested
rewrites specifically tailored for medical imaging and radiology research. Patterns 1-18 are
the general set; 19-21 are senior-MA-reviewer red flags; 22-24 are response-to-reviewers (R2R)
letter patterns.

Sources:
- matsuikentaro1/humanizer_academic (English 18 patterns)
- Wikipedia: Signs of AI writing
- Adapted for radiology/medical imaging context

---

## Content Patterns

### Pattern 1: Significance Inflation

AI inflates importance with vague claims about "broader impact" instead of stating specific
clinical or scientific significance.

**Watch words:** pivotal, evolving landscape, underscores, highlights its importance, setting
the stage for, deeply rooted, focal point, indelible mark, paradigm shift, unprecedented

| # | BAD (AI-generated) | GOOD (Human-written) |
|---|-------------------|---------------------|
| 1 | "CT plays a pivotal role in the evolving landscape of oncologic imaging" | "CT is the primary imaging modality for cancer staging" |
| 2 | "This underscores the critical importance of early detection in improving patient outcomes" | "Early detection reduced mortality by 20% in the NLST trial" |
| 3 | "AI represents a paradigm shift in radiology practice" | "AI-assisted detection increased sensitivity from 0.78 to 0.91" |
| 4 | "Deep learning has made an indelible mark on medical image analysis" | "Deep learning models have achieved diagnostic accuracy comparable to radiologists in several tasks" |
| 5 | "Setting the stage for transformative advances in precision radiology" | "These methods may improve lesion detection in low-dose protocols" |

**Radiology-specific note:** Radiology papers are particularly susceptible to this pattern
in introductions discussing AI/deep learning. State the specific performance metric or
clinical outcome instead.

---

### Pattern 2: Notability Claims

AI labels studies, institutions, or researchers with unearned superlatives.

**Watch words:** landmark, renowned, prestigious, groundbreaking, impressive, seminal,
pioneering, state-of-the-art

| # | BAD | GOOD |
|---|-----|------|
| 1 | "This groundbreaking study from a prestigious institution" | "In a multicenter study of 12,000 patients (Smith et al., 2024)" |
| 2 | "The landmark NLST trial" | "The National Lung Screening Trial (NLST)" |
| 3 | "Using a state-of-the-art deep learning architecture" | "Using a ResNet-50 model pretrained on ImageNet" |
| 4 | "These impressive results demonstrate" | "The AUC was 0.94 (95% CI: 0.91-0.97)" |

**Radiology-specific note:** "State-of-the-art" is especially overused in AI radiology papers.
Name the specific architecture and training approach instead.

---

### Pattern 3: Superficial -ing Analyses

AI appends "-ing" participial phrases to sentences, creating fake analytical depth without
adding information.

**Watch words (at end of sentence):** highlighting, underscoring, emphasizing, showcasing,
fostering, reflecting, contributing to, demonstrating, suggesting, indicating

| # | BAD | GOOD |
|---|-----|------|
| 1 | "The AUC was 0.93 (95% CI: 0.90-0.96), highlighting the strong diagnostic performance of the model" | "The AUC was 0.93 (95% CI: 0.90-0.96)." |
| 2 | "Sensitivity improved from 78% to 91%, underscoring the value of AI-assisted detection" | "Sensitivity improved from 78% to 91%. This improvement corresponded to detection of 13 additional malignant nodules per 1000 screens." |
| 3 | "Inter-reader agreement was excellent (ICC = 0.92), demonstrating the reproducibility of the measurement technique" | "Inter-reader agreement was excellent (ICC = 0.92; 95% CI: 0.88-0.95)." |
| 4 | "Processing time decreased by 40%, showcasing the efficiency gains" | "Processing time decreased by 40% (from 5.2 to 3.1 minutes per case)." |
| 5 | "The false-positive rate decreased to 3.2%, reflecting improved specificity" | "The false-positive rate decreased to 3.2%." |

**Fix strategy:** End the sentence at the data. If interpretation is needed, start a new
sentence with a specific claim supported by the numbers.

---

### Pattern 4: Promotional Language

AI uses adjectives and adverbs that promote rather than describe.

**Watch words:** remarkable, dramatic, stunning, profound, extraordinary, exceptional,
breathtaking, robust (unless describing a statistical method), comprehensive, innovative,
novel (overused)

| # | BAD | GOOD |
|---|-----|------|
| 1 | "Our model achieved remarkable diagnostic accuracy" | "Our model achieved an AUC of 0.95" |
| 2 | "A dramatic reduction in false-positive rates was observed" | "The false-positive rate decreased from 12.3% to 4.1%" |
| 3 | "This comprehensive framework provides a robust solution" | "This framework reduced processing time by 60% while maintaining accuracy" |
| 4 | "The novel deep learning approach demonstrated exceptional performance" | "The proposed approach outperformed the baseline by 0.08 AUC points (p = 0.003)" |
| 5 | "A robust and comprehensive evaluation was conducted" | "We evaluated the model on three external datasets" |

**Radiology-specific note:** "Robust" is acceptable when describing a statistical method
(e.g., "robust standard errors") but not as a general-purpose adjective for frameworks,
pipelines, or results.

---

### Pattern 5: Vague Attributions

AI attributes claims to unnamed sources instead of citing specific studies.

**Watch words:** Studies have shown, Experts argue, Some researchers, It is widely accepted,
Several publications, The literature suggests, It has been reported, Research indicates

| # | BAD | GOOD |
|---|-----|------|
| 1 | "Studies have shown that AI can improve diagnostic accuracy" | "In a meta-analysis of 82 studies, AI systems achieved pooled sensitivity of 87% (Liu et al., 2019)" |
| 2 | "It is widely accepted that MRI is superior for soft tissue contrast" | "MRI provides superior soft tissue contrast resolution compared with CT (reference)" |
| 3 | "Several studies have demonstrated the utility of radiomics" | "Aerts et al. (2014) demonstrated that radiomic features predicted outcomes in lung and head-and-neck cancer" |
| 4 | "Research indicates that prompt engineering affects LLM output quality" | "Prompt structure affected diagnostic accuracy by up to 15 percentage points in GPT-4V evaluations (Wu et al., 2024)" |
| 5 | "It has been reported that CAD systems reduce reading time" | "Park et al. (2023) reported a 25% reduction in reading time with AI-assisted detection" |

**Fix strategy:** Replace every vague attribution with a specific citation. If you do not
know the specific reference, flag it for the user to fill in with `[CITE NEEDED]`.

---

### Pattern 6: Formulaic Challenges Sections

AI produces template limitation/future-work sections that could apply to any paper.

**Watch words:** Despite these limitations, Future outlook, Continues to provide valuable
insights, Further research is warranted, More studies are needed

| # | BAD | GOOD |
|---|-----|------|
| 1 | "Despite these limitations, our study provides valuable insights into AI-assisted diagnosis" | "The single-center design limits generalizability to community practice settings where case mix and image quality differ" |
| 2 | "Further research is warranted to validate these findings" | "External validation on a multi-institutional dataset with variable scanner protocols is needed before clinical deployment" |
| 3 | "More studies are needed to fully understand the potential of this approach" | "Prospective evaluation comparing AI-assisted and conventional reading in a screening population would quantify the clinical impact" |
| 4 | "Despite challenges, the future of AI in radiology is promising" | "Integration into the clinical PACS workflow remains an engineering challenge requiring vendor collaboration" |

**Fix strategy:** State the specific limitation, its consequence, and the specific study
design that would address it.

---

## Language Patterns

### Pattern 7: AI Vocabulary Words

Words whose frequency increased markedly in post-2023 AI-generated text. Their presence
at high density signals AI authorship.

**High-signal words to eliminate or replace:**

| AI Word | Replacement |
|---------|-------------|
| Additionally | (delete, or use "In addition," sparingly) |
| Furthermore | (delete, or restructure the sentence) |
| Moreover | (delete) |
| Crucial | Important (or delete) |
| Delve | Examine, analyze, investigate |
| Enhance | Improve |
| Fostering | Promoting, supporting (or delete) |
| Garner | Receive, attract |
| Highlight (verb) | Show, demonstrate (or delete) |
| Interplay | Interaction, relationship |
| Intricate | Complex (or delete if unnecessary) |
| Key (adjective, overused) | Important, main, primary |
| Landscape (abstract) | Field, domain (or delete) |
| Leverage | Use, apply |
| Multifaceted | (delete; describe the specific facets) |
| Pivotal | Important, central |
| Showcase | Show, demonstrate |
| Tapestry | (delete entirely) |
| Testament | Evidence, indication |
| Underscore (verb) | (delete; state the point directly) |
| Utilize | Use |
| Valuable | Useful (or delete) |

**Radiology examples:**

| BAD | GOOD |
|-----|------|
| "Additionally, we utilized a novel architecture to enhance detection" | "We used a ResNet-50 to improve detection" |
| "This crucial finding underscores the pivotal role of AI" | "This finding supports the use of AI" |
| "We delved into the intricate interplay between image quality and model performance" | "We examined how image quality affected model performance" |

**Rule:** If more than 3 of these words appear in a single page, the section needs revision.

---

### Pattern 8: Copula Avoidance (Avoiding "is")

AI substitutes elaborate verb constructions for simple "is/are."

**Watch words:** serves as, stands as, marks, represents [a], boasts, features, offers [a],
constitutes, functions as

| # | BAD | GOOD |
|---|-----|------|
| 1 | "CT serves as the primary imaging modality for lung cancer screening" | "CT is the primary imaging modality for lung cancer screening" |
| 2 | "This metric represents a significant improvement" | "This metric is a significant improvement" |
| 3 | "The dataset features 12,000 annotated images" | "The dataset contains 12,000 annotated images" |
| 4 | "DWI stands as the most sensitive sequence for acute stroke detection" | "DWI is the most sensitive sequence for acute stroke detection" |
| 5 | "This architecture constitutes a major advance" | "This architecture is a major advance" |

---

### Pattern 9: Negative Parallelisms

AI overuses "Not only X but also Y" constructions.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "The model not only improved sensitivity but also reduced false positives" | "The model improved sensitivity and reduced false positives" |
| 2 | "This approach not only streamlines workflow but also enhances diagnostic confidence" | "This approach reduces reading time by 30% and improves diagnostic confidence" |
| 3 | "AI not only assists in detection but also aids in characterization" | "AI assists in both detection and characterization" |

**Threshold:** More than 1 per section is a red flag.

---

### Pattern 10: Rule of Three Overuse

AI forces ideas into groups of exactly three.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "accuracy, efficiency, and reproducibility" (repeated across 4 paragraphs) | Vary: sometimes mention two, sometimes four, as the content demands |
| 2 | "detection, segmentation, and classification" | "detection and segmentation" (if classification is not relevant to the point) |
| 3 | "clinical, technical, and educational implications" | Group naturally: state the specific implications rather than labeling categories |
| 4 | "sensitivity, specificity, and accuracy" repeated 5 times | Report each metric where relevant; do not always bundle all three |

**Detection method:** Search for the pattern `X, Y, and Z` -- if it appears more than 3 times
in a section, the author (or AI) is forcing triples.

---

### Pattern 11: Synonym Cycling (Elegant Variation)

AI avoids repeating the same word by cycling through synonyms, which creates inconsistency
in medical writing where precision matters.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "patients... participants... subjects... individuals" | "patients" (consistent throughout, matching IRB language) |
| 2 | "lesions... abnormalities... findings... pathology" | "lesions" (if referring to the same thing) |
| 3 | "radiologists... readers... interpreters... physicians" | "radiologists" or "readers" (pick one per context) |
| 4 | "images... scans... examinations... studies" | "examinations" for the procedure, "images" for the pictures |
| 5 | "model... algorithm... system... tool... framework" | "model" (if it is a model) |

**Radiology-specific note:** Inconsistent terminology is a real problem in radiology
manuscripts. "Lesion" and "finding" have different meanings; "examination" and "image"
are not interchangeable. Pick the most precise term and use it consistently.

---

### Pattern 12: False Ranges

AI uses "from X to Y" where X and Y are not on a meaningful continuum.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "from improved detection to enhanced workflow efficiency" | "improved detection and workflow efficiency" |
| 2 | "ranging from data augmentation to transfer learning" | "including data augmentation and transfer learning" |
| 3 | "from clinical practice to research applications" | "in clinical practice and research" |

---

## Style Patterns

### Pattern 13: Em Dash Overuse

AI uses em dashes far more frequently than human academic writers.

**Threshold:** More than 2 em dashes per 1000 words.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "The model -- trained on 50,000 images -- achieved an AUC of 0.94" | "The model, trained on 50,000 images, achieved an AUC of 0.94" |
| 2 | "Three features -- size, shape, and margin -- were selected" | "Three features (size, shape, and margin) were selected" |
| 3 | "CT -- the most widely used modality -- remains essential" | "CT, the most widely used modality, remains essential" |

---

### Pattern 14: Title Case in Headings

AI capitalizes all major words in section headings. Most medical journals use sentence case.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "Statistical Analysis And Primary Endpoints" | "Statistical analysis and primary endpoints" |
| 2 | "Deep Learning Model Architecture" | "Deep learning model architecture" |
| 3 | "Inter-Reader Agreement Assessment" | "Inter-reader agreement assessment" |

**Note:** Follow the target journal's style guide. Most radiology journals (Radiology, AJR,
European Radiology) use sentence case for section headings.

---

### Pattern 15: Curly Quotation Marks

ChatGPT and similar tools produce curly (smart) quotes. Many journal submission systems
and LaTeX workflows expect straight quotes.

| BAD | GOOD |
|-----|------|
| \u201csensitivity\u201d | "sensitivity" |
| \u2018specificity\u2019 | 'specificity' |

**Fix:** Find-and-replace all curly quotes with straight quotes before submission.

---

## Filler and Hedging Patterns

### Pattern 16: Filler Phrases

Empty phrases that add words without adding meaning.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "It is important to note that the AUC exceeded 0.90" | "The AUC exceeded 0.90" |
| 2 | "It is worth noting that sensitivity decreased in smaller lesions" | "Sensitivity decreased in smaller lesions" |
| 3 | "In order to evaluate diagnostic performance" | "To evaluate diagnostic performance" |
| 4 | "Due to the fact that the dataset was imbalanced" | "Because the dataset was imbalanced" |
| 5 | "At the present time, no consensus exists" | "No consensus exists" |
| 6 | "With respect to image quality" | "For image quality" |
| 7 | "The model has the ability to detect" | "The model can detect" |
| 8 | "In the context of emergency radiology" | "In emergency radiology" |

**Detection method:** Search for "It is" at sentence start, "In order to," "Due to the fact,"
"With respect to," "has the ability to," "In the context of."

---

### Pattern 17: Excessive Hedging

AI stacks multiple hedging words, making claims weaker than the evidence supports.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "may potentially suggest the possibility of improved outcomes" | "improved outcomes" (if the data clearly shows it) or "suggests improved outcomes" (if uncertain) |
| 2 | "It could be argued that this might have some impact" | "This may affect diagnostic accuracy" |
| 3 | "These findings seem to indicate that AI may perhaps assist" | "These findings indicate that AI assists" (if the data supports it) |

**Calibration guide for radiology manuscripts:**
- Strong evidence (p < 0.001, large effect, prospective design): State as fact. "AI improved detection."
- Moderate evidence (p < 0.05, moderate effect, retrospective): Single hedge. "AI may improve detection."
- Weak evidence (trend, small sample, pilot, single-center): Measured hedge. "These preliminary results suggest AI may improve detection."
- Exploratory (secondary analysis, post hoc): Explicit qualifier. "In exploratory analysis, AI-assisted reading was associated with higher sensitivity."

---

### Pattern 18: Generic Positive Conclusions

AI ends papers with content-free optimistic statements.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "The future looks bright for AI-assisted radiology" | (delete) |
| 2 | "This paves the way for transformative advances in diagnostic imaging" | "Prospective validation in a screening population is the next step before clinical implementation" |
| 3 | "AI continues to reshape the landscape of medical imaging" | "AI-assisted detection reduced missed cancers by 12% in this retrospective analysis" |
| 4 | "These findings open new avenues for research" | "Future work should evaluate the model on external datasets with heterogeneous scanner protocols" |
| 5 | "This work lays the foundation for future innovations" | "The trained model and evaluation code are publicly available at [URL]" |

**Fix strategy:** Replace with the single most specific implication or the concrete next step.

---

## Senior MA Reviewer Patterns

### Pattern 19: § (Section-Sign) Marker

AI 모델이 본문에서 섹션을 가리킬 때 `§` 기호를 자주 사용. Senior MA reviewer가 즉시 "AI 패턴"으로 인지. 한국·미국 의학지 manuscript에서는 거의 사용되지 않는 LaTeX 풍 표기.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "as described in §2.3" | "as described in the Methods" |
| 2 | "(see §Discussion)" | "(see Discussion)" |
| 3 | "§Results" | "Results" |

**Detection:** `grep -c "§" manuscript.md` → 반드시 0.
**Fix strategy:** § 전부 삭제 또는 섹션명(`Methods`, `Results`, `Discussion`)으로 대체.

---

### Pattern 20: Methods/Results Self-Reference Parenthetical

`(Methods §X)`, `(Results §Y)`, `(Methods, Section 2.3)` 형태의 self-reference 괄호. Pattern 19(§)와 함께 자주 등장. Reviewer는 "굳이 섹션을 자기 인용할 필요 없다"고 판단.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "We applied bootstrap resampling (Methods §2.3) to..." | "We applied bootstrap resampling (described in Methods) to..." 또는 단순 삭제 |
| 2 | "The pooled estimate (Results §3.1) was..." | "The pooled estimate was..." |
| 3 | "As shown in Table 1 (Methods)..." | "As shown in Table 1..." |

**Detection:** `grep -inE "\((Methods|Results|Discussion|Introduction)\s*§" manuscript.md` → 0줄.
**Fix strategy:** 본문 흐름이 자명하면 괄호 삭제. 명시 필요 시 "(Methods)" 또는 "(see Methods)"로 단축.

---

### Pattern 21: AI Disclosure Boilerplate (Body)

"Artificial Intelligence Disclosure" / "Generative AI was not used to create..." / "AI Acknowledgement" 류 boilerplate 단락이 manuscript 본문에 등장. Submission 양식·cover letter에는 필요하지만 본문에 두면 reviewer에게 "AI로 썼다"는 선언 + AI-generated 시그널.

| # | BAD | GOOD |
|---|-----|------|
| 1 | 본문 끝에 "## Artificial Intelligence Disclosure" 단락 | 단락 통째 삭제 → cover letter 또는 submission form에만 기재 |
| 2 | "Generative AI was not used to create, modify, or alter any images, figures, or tables in this manuscript." (본문 Methods) | (삭제) — `~/.claude/rules/journal-ai-image-policies.md` boilerplate는 cover letter에만 |
| 3 | Acknowledgments 섹션에 "We acknowledge the use of ChatGPT for language editing" | 저널 정책에 따라 cover letter로 이동 또는 단순 "Language editing was performed" |

**Detection:** `grep -inE "artificial intelligence disclosure|generative ai was not used|ai acknowledg(e)?ment" manuscript.md` → 0줄 (본문).
**Fix strategy:** 단락 본문에서 제거 → submission form / cover letter에만. 저널이 본문 명시를 요구할 때만 예외.

---

## Response-Letter Patterns (R2R)

These three patterns are specific to response-to-reviewers (R2R) letters and editor cover
letters. They rarely appear in manuscript bodies but dominate machine-drafted rebuttals,
where the model narrates the editing process instead of the science. Apply them whenever the
text under review is a response letter or cover letter. See the revise skill's
`references/r2r_voice.md` for full before/after skeletons. Examples below are synthetic
(a fictional deep-learning lung-nodule CT study).

**Related (triage, not a fixed-string pattern):** *defensive over-elaboration* — pre-emptive
cross-reviewer lobbying ("Reviewers 2 and 3 also accepted this"), defensive meta-comments ("we
confirm this is unchanged and not softened"), manufactured paragraphs answering a satisfied
reviewer, or a separate cover letter on an R2+ round when its content belongs in the
response-letter head — is a succinctness / round-discipline issue, not a regex pattern, and is
most common on R2+ rounds. The normative guidance lives in the revise skill (Step 5 +
Response-Letter Voice), its `references/r2r_voice.md`, and the `rebuttal-letter-style` rule;
humanize only cross-references it (no hard fail, no detection regex added here).

### Pattern 22: Editing-Mechanism / Change-Log Narration

The response prose narrates *how the text was edited* — what was added, where, how many phrases
were swapped, which pass produced it — instead of stating what changed and why. The reviewer
reads this as auto-generated and as checklist-clearing rather than scientific engagement.

**Scope — this targets editing-mechanism narration only (avoid over-flagging):** narrating a
*new analysis you ran* ("we performed a sensitivity analysis restricted to one eye per patient,
and the result held") is the science the reviewer asked for — never flag it. Likewise "we added
a sentence to the Methods: '...'", structured `Response:` / `Changes made:` blocks, and
`Original → Revised` before/after pairs are normal human conventions. The tell is the *editing
mechanism* layered on top, not the act of describing, quoting, or locating a change.

**Watch phrases (the tell):** version-prefixed edits ("v2 Methods adds one sentence"), "we
softened six phrases", "demoted the term at all N locations", "a grep-and-soften pass", "the v2
revision changes", bare "No further manuscript change" stubs, "reframed via the vocabulary cascade".

| # | BAD (editing-mechanism) | GOOD (substantive / science) |
|---|---|---|
| 1 | "v2 Methods adds one sentence: '...'. This is a short visible clarification rather than only in the Limitations." | "We agree the design is observational; we have added to the Methods: '...'" |
| 2 | "We softened six over-interpretive phrases in Results and Discussion." | "We have rephrased the over-interpretive passages; for example, '...' now reads '...'." |
| 3 | "No further manuscript change was applied." | "The existing Discussion text already addresses this; the relevant statement is '...'." |

**Detection (triage, not auto-fail):** `grep -inE "v[0-9]+ .*(add|demote|soften|reframe)|softened [0-9a-z]+ phrases|no further (manuscript )?change|grep-and-soften|vocabulary cascade|demoted .* at all [0-9]+" response_to_reviewers.md` — review each hit and flag only genuine editing-mechanism narration, never analysis narration or quoted additions.
**Fix strategy:** Delete the mechanism narration. State the substantive change and quote the new sentence; omit how it was found or made.

### Pattern 23: Internal Line-Number Reference Tone

Pointing reviewers to internal draft/markdown line numbers ("(line 43)", "at lines 43, 49,
58, 60, 77–79"). These never match the reviewer's view of the revised manuscript and read as
a diff log. Section names are what authors actually use.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "We clarified this at line 43." | "We clarified this in the Methods (Design subsection)." |
| 2 | "Single-sentence clarifications were added at lines 43, 49, 58, 60, and 77–79." | "We added short clarifications to the Methods covering the design, the intervention, and the outcome definitions." |
| 3 | "v2 line 127 retains this sentence and adds the adjustment after it." | "In the Results (Between-group comparison) we retained the original sentence and added the adjustment immediately after." |

**Not a tell:** a **revised-manuscript** page/line ("page 7, lines 177-178") when the letter
states once that all page/line numbers refer to the revised manuscript the reviewer is reading.
The tell is the *internal draft* line number that will not match the reviewer's PDF.

**Detection:** `grep -inE "\(line [0-9]+|at lines? [0-9]+|line [0-9]+(–|-)[0-9]+" response_to_reviewers.md` → review each hit; keep only those that demonstrably point to the revised manuscript.
**Fix strategy:** Replace internal/draft line numbers with a section name; keep revised-manuscript page/line only if it matches what the reviewer sees.

### Pattern 24: Tooling / Scaffolding Leak

Exposing internal tooling, verification mechanics, or draft scaffolding to the reviewer:
grep counts, internal FIX/category codes, references to "the circulated bundle" or "the
internal supplementary index", or `§` self-references carried into the response letter.

| # | BAD | GOOD |
|---|-----|------|
| 1 | "Final grep verification returned zero occurrences across the circulated bundle." | (delete — describe the corrected wording instead) |
| 2 | "Addressed via the FIX-1 vocabulary cascade." | "We replaced [old term] with [new term] throughout the manuscript." |
| 3 | "These strings remain only in the internal supplementary index, which is not part of the circulated bundle." | (delete — never reference internal scaffolding to a reviewer) |
| 4 | "as reframed in §Discussion" | "as reframed in the Discussion" |

**Detection (triage, except `§`):** `grep -inE "grep verification|grep-and-soften|circulated bundle|internal (supplementary )?index|FIX-[0-9]|vocabulary cascade|§" response_to_reviewers.md cover_letter.md` — only `§` is a hard 0 (always a tell). The other terms can rarely be legitimate (e.g., "a cascade detector", "we grep-checked our own data pipeline"), so confirm each hit is an internal-tooling reference before flagging.
**Fix strategy:** Strip confirmed references to internal tooling, verification passes, and draft scaffolding. The reviewer should see only the science and the substantive changes.

---

## Section-Specific Application Guide

### Abstract (ALL patterns)

The abstract is the most visible section and the most likely to be checked for AI writing.
Apply all applicable patterns (1-21) with zero tolerance.

**Common abstract issues:**
- Pattern 1 in the Background sentence.
- Pattern 4 in the Results sentence ("demonstrated remarkable performance").
- Pattern 18 in the Conclusion sentence ("paves the way").

### Introduction (Patterns 1, 2, 5, 7, 12)

- Opening paragraph: Check for significance inflation (Pattern 1) and AI vocabulary (Pattern 7).
- Literature review paragraph: Check for vague attributions (Pattern 5).
- Gap statement: Check for notability claims (Pattern 2).

### Methods (Patterns 8, 16)

- Methods should be the most straightforward section. Watch for copula avoidance ("serves as
  the reference standard" instead of "is the reference standard") and filler phrases.

### Results (Patterns 3, 4, 6, 10, 11)

- After every statistical result, check for appended -ing clauses (Pattern 3).
- Check for promotional adjectives before numbers (Pattern 4).
- Check for synonym cycling of key terms (Pattern 11).

### Discussion (Patterns 1, 5, 6, 17, 18)

- First paragraph: Check for significance inflation (Pattern 1).
- Comparison paragraphs: Check for vague attributions (Pattern 5).
- Limitations: Check for formulaic language (Pattern 6).
- Final paragraph: Check for generic conclusions (Pattern 18) and excessive hedging (Pattern 17).

### Conclusion (Patterns 1, 18)

- The conclusion should be 1-3 sentences stating the main finding and its specific implication.
- No significance inflation, no generic optimism.

### Response to Reviewers / Cover letter (Patterns 22, 23, 24 — plus 13, 16, 19)

- Response letters and cover letters are reviewer-facing argument, not change-logs. The
  dominant AI-tell here is the editing-mechanism register (Pattern 22), internal draft
  line-number pointers (Pattern 23), and tooling/scaffolding leaks (Pattern 24).
- Also sweep for em dashes (13), filler phrases (16), and `§` markers (19).
- Patterns 1-18 still apply where relevant, but 22-24 are the highest-yield checks for this
  document type.

---

## Quick Checklist (Pre-Submission)

Run this checklist on the final manuscript before submission:

- [ ] No "Additionally" / "Furthermore" / "Moreover" at sentence start (allow max 1 total)
- [ ] No "pivotal" / "crucial" / "landscape" / "delve" / "utilize" / "leverage"
- [ ] No "-ing" participial phrases appended to statistical results
- [ ] No "serves as" / "stands as" / "represents a" (use "is")
- [ ] No vague "Studies have shown" without a specific citation
- [ ] No "not only X but also Y" (allow max 1 total)
- [ ] No generic positive conclusions ("paves the way," "the future looks bright")
- [ ] Consistent terminology throughout (no synonym cycling)
- [ ] Em dashes: fewer than 2 per 1000 words
- [ ] Hedging calibrated to evidence level (no stacked hedges)
- [ ] Filler phrases eliminated ("It is important to note that," "In order to")
- [ ] Straight quotation marks (not curly)
- [ ] Sentence case in headings (unless journal requires title case)
- [ ] AI pattern density < 2.0 per 1000 words
- [ ] § (section sign) 0건 (Pattern 19) — `grep -c "§"` = 0
- [ ] (Methods §X) / (Results §Y) self-reference 0건 (Pattern 20)
- [ ] AI Disclosure boilerplate 본문 0건 (Pattern 21) — cover letter / submission form 전용

### Response letters / cover letters only (Patterns 22-24)

- [ ] No editing-mechanism narration (Pattern 22) — "v2 adds one sentence", "softened N phrases", "No further manuscript change" (analysis narration and quoted additions are fine)
- [ ] No internal draft line-number pointers (Pattern 23) — "(line NN)", "at lines N, M" (revised-manuscript page/line is fine)
- [ ] No tooling/scaffolding leak (Pattern 24) — "grep", "FIX-N", "circulated bundle", "internal index", `§`
