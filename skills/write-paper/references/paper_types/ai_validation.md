# AI Validation Study — Template for Radiology

## Overview

Template for studies that develop, validate, or compare AI/ML models for medical imaging tasks. Must follow at least one of STARD-AI, TRIPOD+AI, or CLAIM depending on the study type. This template extends the standard IMRAD structure with AI-specific requirements.

---

## Applicable Reporting Guidelines

Select based on study type (multiple may apply):

| Study Type | Primary Guideline | Also Consider |
|------------|------------------|---------------|
| Diagnostic accuracy of AI | STARD-AI | CLAIM |
| AI prediction model (development) | TRIPOD+AI (Type 1a/1b) | CLAIM |
| AI prediction model (validation) | TRIPOD+AI (Type 2a/2b/3) | CLAIM |
| Any AI study in medical imaging | CLAIM 2024 | STARD-AI or TRIPOD+AI |
| AI-assisted reader study | STARD-AI + reader study guidelines | CLAIM |
| LLM/MLLM evaluation | CLAIM + custom LLM reporting | -- |

---

## Title

- Include the AI/ML method, clinical task, and study type.
- Good: "Validation of a Deep Learning Model for Automated Detection of Intracranial Hemorrhage on Noncontrast CT: A Multicenter Study"
- Good: "Large Language Model Performance in Radiology Board-Style Questions: A Multi-Agent Validation Study"
- Avoid: vague terms like "novel," "state-of-the-art," or "revolutionary."

---

## Abstract (Structured, 250 words)

Follow the target journal's format. Include:
- **Purpose**: Clinical problem + study objective.
- **Materials and Methods**: Dataset size and source, model type, reference standard, primary metric.
- **Results**: Primary performance metric with 95% CI, key comparison result.
- **Conclusion**: Clinical implication, not just "the model performed well."

---

## Introduction (3-4 paragraphs)

### Paragraph 1: Clinical Problem
- The specific clinical task and its importance.
- Current diagnostic performance, error rates, or workflow bottlenecks.
- Why AI could help (workload, accuracy, speed, access).

### Paragraph 2: Current AI Landscape
- Prior AI approaches for this task (brief, cite key studies).
- Gaps: limited validation, single-center, no reader comparison, no generalizability data.
- For LLM studies: current evidence on LLM/MLLM performance in medical domains.

### Paragraph 3: Study Objective
- Precise aim with study design mentioned.
- Hypothesis if applicable.
- Template: "The purpose of this study was to {develop and validate / externally validate / compare} {model/system} for {task} using {dataset description}."

---

## Materials and Methods

### 4.1 Study Design
- Retrospective vs prospective.
- Single-center vs multicenter.
- Development vs validation vs both.
- Dates of data collection.
- If development+validation: describe the temporal or geographic separation.

### 4.2 Dataset

#### Source and Collection
- Institution(s), imaging modality, date range.
- How cases were identified (consecutive, sampled, queried).
- Inclusion and exclusion criteria (be specific).

#### Dataset Splitting (for development studies)
- Training / validation / test split ratios and method.
- **Critical**: confirm patient-level splitting (not image or exam level).
- Temporal split preferred over random split (state which was used).
- If external test set: describe source and independence.

#### Dataset Characteristics
- Total cases, positive/negative distribution.
- Demographics: age, sex, relevant clinical variables.
- Image characteristics: scanner models, protocols, acquisition parameters.
- Case complexity distribution if relevant.

### 4.3 Reference Standard
- How ground truth was established (pathology, follow-up, expert consensus, clinical diagnosis).
- Number of annotators, their experience level.
- Annotation process: independent reading, consensus, adjudication.
- Blinding: annotators blinded to model output and clinical information?
- Inter-annotator agreement reported (kappa, ICC).
- Timing between index test and reference standard.

### 4.4 AI Model

#### For Traditional DL Models
- Architecture (e.g., ResNet-50, U-Net, YOLO v8) with citation.
- Input: image size, preprocessing steps (normalization, augmentation).
- Training: optimizer, learning rate (schedule), batch size, epochs, early stopping criteria.
- Loss function.
- Hardware: GPU model, training time.
- Framework and version (PyTorch 2.x, TensorFlow 2.x).

#### For LLM/MLLM Studies
- Model name and version (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).
- API access date range (models change over time).
- Temperature and other generation parameters.
- Prompt design: system prompt, few-shot examples, chain-of-thought.
- Full prompts in supplement (or verbatim in methods if short).
- If multi-agent: agent roles, interaction protocol, consensus mechanism.
- Input format: text-only, image+text, structured data.

#### For Pipeline/System Studies
- End-to-end system description.
- Each stage: input, processing, output.
- Decision points and thresholds.
- Human-in-the-loop components.

### 4.5 Comparators (if applicable)
- Reader study design: number of readers, experience levels, subspecialty.
- Reading conditions: blinding, clinical information provided, time constraints.
- AI-assisted vs unassisted reading protocol.
- Washout period between reading sessions.

### 4.6 Statistical Analysis
- **Primary metric**: AUC, sensitivity, specificity, accuracy, F1 -- state which and why.
- **Confidence intervals**: 95% CIs for all primary metrics (bootstrap or exact binomial).
- **Comparison tests**: DeLong test for AUC comparison, McNemar for sensitivity/specificity.
- **Calibration**: calibration plot, Brier score, calibration slope/intercept (for prediction models).
- **Subgroup analyses**: pre-specified subgroups with rationale.
- **Multiple comparisons**: correction method if applicable.
- **Sample size**: justification or power analysis if prospective.
- **Software**: version numbers for all statistical packages.

### 4.7 Ethics
- IRB approval with protocol number.
- Informed consent status.
- Data de-identification method.

---

## Results

> **Results = facts and numbers only.** No interpretation, no "why," no prior study
> comparisons. See SKILL.md Phase 4 anti-interpretation guardrails.

### 5.1 Dataset Characteristics
- Flow diagram (Figure 1): screening, exclusions, final cohorts.
- Table 1: demographics and baseline characteristics by split (train/val/test) or group.
- Class distribution: positive/negative cases per split.

### 5.2 Model Performance (Primary Endpoint)
- Table 2: Primary performance metrics with 95% CIs.
- ROC curve (Figure 2) with AUC and CI.
- At the chosen operating point: sensitivity, specificity, PPV, NPV.
- How the operating point was selected (Youden, clinical threshold, fixed sensitivity).

### 5.3 Reader Comparison (if applicable)
- Table 3: Reader performance vs AI performance.
- Statistical comparison (DeLong, McNemar).
- AI-assisted vs unassisted reader performance.
- Reading time comparison if measured.

### 5.4 Subgroup Analysis
- Performance by key subgroups (age, sex, scanner, pathology subtype, difficulty).
- Present as table or forest plot.
- State the numbers; do NOT interpret why subgroups differ (save for Discussion).

### 5.5 Error Analysis
- Types of errors (false positives and false negatives).
- Representative examples (Figure 3+): correctly classified, false positive, false negative.
- Describe error patterns factually; do NOT speculate on causes (save for Discussion).

### 5.6 Calibration (for prediction models)
- Calibration plot (Figure).
- Brier score, calibration slope, intercept.
- Hosmer-Lemeshow or similar test.

---

## Discussion

> **Before writing:** Collect anchor papers and user input via SKILL.md Phase 5a
> interactive planning gate.

### Paragraph 1: Summary
- Restate key findings without repeating exact numbers.
- Frame in context of the study aim.

### Paragraphs 2-3: Performance in Context (anchor paper driven)
- Organize around anchor papers provided by the user.
- For each anchor paper: state their result → compare with ours → explain discrepancy.
- Compare to prior models on the same task (cite specific AUC/accuracy from prior studies).
- Compare to human reader performance (if applicable).
- Explain performance differences: data, methodology, population.

### Paragraph 4: Clinical Deployment Implications
- Where in the workflow would this fit? (triage, second reader, standalone, quality assurance)
- What is the intended use case?
- Implementation considerations: speed, hardware, integration.
- Regulatory pathway considerations (if relevant).

### Paragraph 5: Limitations
Typical AI study limitations to address honestly:
1. Retrospective design and selection bias.
2. Single-center / limited generalizability.
3. Reference standard limitations (imperfect ground truth).
4. Dataset size and class imbalance.
5. Temporal/geographic bias (training and test from same distribution).
6. For LLMs: model version changes, non-reproducibility, API dependency.
7. No prospective clinical validation.
8. No assessment of clinical outcome impact.
For each: (a) what it is, (b) how mitigated, (c) direction of residual bias.

### Conclusion
- One to two sentences: main finding and primary clinical implication.
- Must be a citable statement — memorable and specific.

---

## Special Required Sections

### Data Availability Statement
- Template: "The datasets generated and/or analyzed during the current study are {available in the [repository name] repository, [URL] / not publicly available due to [reason] but are available from the corresponding author on reasonable request}."

### Code Availability
- Template: "The code for {model training / analysis / evaluation} is available at {URL}."
- If not available: "Code is available from the corresponding author on reasonable request."

### AI Disclosure
- In Methods: "Large language model {name, version} was used for {specific task}. The model was accessed via {API/interface} between {dates}. Generation parameters were set to {temperature, etc.}."
- In Acknowledgments: "{Tool name} was used for {writing assistance / code generation / data analysis}. All AI-generated content was reviewed and verified by the authors."

---

## Common Pitfalls to Avoid

1. **Data leakage**: Preprocessing (normalization statistics) computed on full dataset before splitting.
2. **Image-level splitting**: Splitting by image rather than by patient allows the same patient in train and test.
3. **Missing CIs**: Reporting AUC = 0.95 without confidence interval is incomplete.
4. **No calibration**: AUC measures discrimination only; calibration is essential for prediction models.
5. **Overclaiming**: "Our model outperformed radiologists" when CIs overlap or test set is small.
6. **Missing error analysis**: Knowing where the model fails is as important as overall metrics.
7. **Vague prompts**: For LLM studies, not providing the exact prompts used.
8. **No intended use**: Not specifying where in the clinical workflow the model would be deployed.
9. **Cherry-picked operating point**: Choosing the threshold that looks best on the test set.
10. **Ignoring prevalence**: Reporting PPV/NPV without discussing the study prevalence vs real-world prevalence.
