# Case-report anatomy — CARE narrative + 150-word abstract

A structure model for case reports, complementing `paper_types/case_report.md` and the CARE
checklist. Use it when `/write-paper` Phase 0 identifies the paper type as **case report**. This
is a synthetic anatomy model: it describes the required moves, failure modes, and cross-checks; it
is not prose to copy.

## Narrative spine

Strong case reports read as a clinically disciplined story, not as a miniature original article.
Build the manuscript around the sequence below, keeping each move tied to the patient's course.

1. **Why this case matters** — the rare presentation, diagnostic trap, management lesson, adverse
   event, or unexpected response. The reason must be specific enough that a reader understands why a
   single case deserves publication.
2. **Who the patient is, de-identified** — age range/sex and clinically relevant background only.
   Remove dates, institutions, initials, locations, unique occupations, and unnecessary demographic
   detail.
3. **What happened in time order** — symptoms, examination, tests, diagnostic reasoning,
   intervention, follow-up, and outcome. A timeline figure or table should let the reader reconstruct
   the course without rereading the prose.
4. **How the diagnosis was reasoned through** — include alternatives considered, why they were less
   likely, key imaging/laboratory/pathology findings, and any diagnostic limitation.
5. **What was done and what changed** — treatment, dose/procedure/device details if load-bearing,
   response, adverse events, adherence/tolerability, and follow-up duration.
6. **What the reader should learn** — a narrowly scoped teaching point, anchored to the literature
   and the evidence level of a single case.

## 150-word structured abstract

Most short case reports need a compact abstract with **Introduction / Case Presentation /
Conclusion** headings. Allocate words deliberately; do not import the IMRAD abstract model.

### Introduction
- One sentence naming the condition/presentation and the precise reason the case is reportable.
- Avoid broad disease background. The abstract's first sentence should already point to the novelty
  or teaching value.

### Case Presentation
- Two to four sentences covering the patient's de-identified presentation, key findings, diagnostic
  reasoning, intervention, and follow-up outcome.
- Include the decisive imaging/laboratory/pathology finding if it is the reason the case matters.
- Keep chronology clear; do not compress the case into an unexplained list of diagnoses and tests.

### Conclusion
- One sentence stating the teaching point, scoped to a single case.
- Use cautious verbs: "may", "should prompt consideration", "is consistent with", or "highlights".
  Do not claim incidence, efficacy, safety, causality, or practice-changing proof.

## Case Presentation section

### Patient information
- De-identified demographics and relevant clinical background.
- Main concern/symptom in the patient's sequence, not as a retrospective diagnosis.
- Past medical, family, psychosocial, medication, and exposure history only when they affect the
  differential, intervention, or interpretation.

### Clinical findings
- Physical examination and bedside findings that altered diagnostic reasoning.
- State relevant negatives when they narrow the differential; omit routine normal findings that do
  not move the case.

### Timeline
- Use a compact figure or table when the course has more than two clinically meaningful time points.
- Include onset, presentation, key tests, diagnosis, intervention changes, complications, and final
  follow-up/outcome.
- Use relative time (`Day 0`, `Week 6`, `Month 3`) unless exact dates are essential and approved for
  publication.

### Diagnostic assessment
- Name the test modality and the load-bearing finding, then the interpretation.
- For imaging cases, describe the finding and impression separately: modality/sequence, lesion or
  anatomical location, discriminating feature, and how it affected the differential.
- Document diagnostic challenges: atypical presentation, unavailable tests, delayed diagnosis,
  discordant results, or uncertainty that remained.

### Therapeutic intervention
- State what was done, why, and when it changed.
- Include dose, route, procedure, device, duration, or surgical detail only when needed for
  reproducibility or interpretation.

### Follow-up and outcomes
- Report the follow-up interval, patient- or clinician-assessed outcome, objective response where
  available, adverse events, and residual deficits.
- Avoid "the patient improved" unless the text specifies how improvement was assessed.

## Discussion

- Open with the one-sentence lesson, not a second case summary.
- Compare against the nearest reported cases or mechanisms. If five or more similar cases are found,
  use a brief comparison table; if fewer, state the search boundary and avoid implying a definitive
  global count.
- Separate temporal association from causality. A single case can raise a hypothesis or illustrate a
  diagnostic clue; it cannot estimate treatment effect or risk.
- State what is uncertain: alternative explanations, incomplete testing, short follow-up, missing
  patient perspective, or limited generalizability.
- End with a practical teaching point that a clinician can use at the bedside.

## Subtype: adverse drug / device / contrast reaction (pharmacovigilance)

When the case *is* the adverse event (drug reaction, contrast-agent extravasation, device
complication), the attribution is the contribution — make it rigorous, not narrative.

- **Apply a named causality instrument, do not just assert it**: the Naranjo Adverse Drug Reaction
  Probability Scale or WHO-UMC categories for drugs; report the score and the resulting tier
  (doubtful / possible / probable / definite). State the inputs that drove it.
- **Dechallenge and (only if ethical) rechallenge**: document that withdrawal was followed by
  resolution, and note the temporal latency from exposure to onset. Rechallenge is usually withheld
  on safety grounds — say so rather than leaving it unexplained.
- **Severity and preventability** where instruments exist (e.g., Modified Hartwig–Siegel severity;
  Schumock–Thornton preventability) — these turn an anecdote into a structured safety report.
- **Locate the event against a denominator**: an institutional rate (events / total procedures) or a
  pharmacovigilance database count (e.g., prior reports in a spontaneous-reporting system) anchors
  rarity without overclaiming incidence from n=1.
- **Separate the index event from downstream confounders**: if patient self-management or a
  comorbidity worsened the course, attribute each step rather than blaming the agent for the whole
  trajectory.
- **Close the safety loop**: state that the reaction was (or should be) reported to the relevant
  pharmacovigilance programme.
- A compact **instrument table** (tool | criteria applied | result | interpretation) is the clearest
  way to present causality/severity/preventability.

## Subtype: diagnostic pitfall / mimic

When the lesson is "this entity was mistaken for another," the differential is the spine.

- **Name the trap explicitly** in the framing ("X masquerading as Y") and state why the
  misclassification was plausible (overlapping imaging/clinical features, an obscured primary site).
- **Structured differential**: list the realistic competitors and, for each, the feature that argued
  for or against it (morphology, immunohistochemistry, virology, distribution). A differential that
  only names alternatives without adjudicating them is incomplete.
- **Trace the resolving pathway**: which test finally settled origin vs extent (e.g., inconclusive
  cross-sectional imaging → tissue diagnosis → functional imaging for staging), and acknowledge where
  a modality was limited or omitted and why.
- **Diagnostic-delay framing** (optional but strong): when delay shaped the outcome, separate
  patient-level from healthcare-pathway-level contributors rather than a single "late presentation."
- **Self-critical mechanism reasoning**: when proposing a mechanism, test it against this case's own
  data and reject candidates the case does not support (e.g., a hyperperfusion mechanism is unlikely
  when the recorded blood pressure stayed below the autoregulatory threshold).

## Required cross-checks

- **Consent / anonymization**: confirm written consent or the applicable waiver statement before
  drafting submission-ready text; image panels must be stripped of identifiers.
- **CARE coverage**: Title, Keywords, Abstract, Patient Information, Clinical Findings, Timeline,
  Diagnostic Assessment, Therapeutic Intervention, Follow-up/Outcomes, Discussion, Patient
  Perspective (if available), and Informed Consent.
- **Literature boundary**: search strategy, number of similar cases found, and whether a comparison
  table is warranted.
- **Figure anatomy**: for complex courses, pair the text with `/make-figures`
  `exemplar_plots/clinical_timeline.md`.

## Common failure modes

- **Rarity without justification** — the Introduction says "rare" but gives no clinical reason,
  epidemiologic anchor, or teaching value.
- **Consent or de-identification gap** — no consent statement, identifiable dates/institutions, or
  unmasked imaging metadata.
- **Chronology collapse** — the diagnosis, intervention, and outcome are present but not in a
  reconstructable sequence.
- **Diagnostic reasoning missing** — tests are listed, but alternatives and why the final diagnosis
  was favored are absent.
- **Causal overclaim** — the Discussion treats a temporal association as proof of treatment effect,
  adverse-event causality, or mechanism.
- **Literature absence mishandled** — "first case" or "only case" is asserted without a transparent
  search boundary.
- **Teaching point too broad** — the conclusion asks clinicians to change practice rather than
  recognize a clue, consider a diagnosis, or report similar cases.
- **Causality by assertion** — an adverse-event case calls the agent "causative" without a named
  instrument (Naranjo/WHO-UMC), documented dechallenge, or exclusion of alternatives.
- **Differential without adjudication** — a mimic/pitfall case lists competing diagnoses but never
  says which feature ruled each in or out.
