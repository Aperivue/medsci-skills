<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# LLM / MLLM clinical-evaluation probes (ME0–ME8)

For the evaluation of a **large language model or multimodal LLM on a clinical task** — radiology
report generation, visual question answering (VQA), or clinical text extraction / classification —
whether the model is a **closed API or open weights**. This probe owns the *evaluation* mechanics
(reference standard, faithfulness, contamination, prompt sensitivity, reader study); it extends, and
cross-links, `ai_overclaiming.md` (the claim) and the self-review input-contamination / fine-tuning
checks. Author-side harness design is `/mllm-eval`; this module is the reviewer-side audit. (For
image-to-image generative models use `image_synthesis.md`; this is for text / VQA output.)

**ME0 — Pin the task, the model + version, the comparator, and the decoding settings (gate; run first)**:
- State the task (report generation / VQA / extraction-classification), the **exact model and
  version/date** (closed API or open-weights id), the **decoding settings** (temperature, max tokens),
  and **what the outputs are scored against**. Model-agnostic by construction — every probe applies to a
  closed API and to open weights.
- A finding is a **lead** until the eval protocol is read in full; do not escalate before the reference
  standard and metrics are located.

**ME1 — Reference standard for generated text (not a noisy proxy)**:
- For report generation or open-ended answers, the comparator must be an **adjudicated expert reference**,
  not a single unverified clinical report or a model-generated label treated as truth. State who set the
  reference, the adjudication rule, and the agreement among reference-setters (cross-link MI-CLEAR-LLM;
  the diagnostic-accuracy D-probes).
- Benchmark labels mined from raw reports without adjudication carry the report's own errors into the
  "ground truth." An undefined or single-rater unadjudicated reference for a generation claim → MAJOR.

**ME2 — Clinical-efficacy metrics beyond n-gram overlap**:
- BLEU / ROUGE / METEOR measure surface word overlap and are **weakly correlated with clinical
  correctness** — a report can score high while inverting laterality or missing a pneumothorax (Yu et
  al., *Patterns* 2023, RadCliQ). Require a **factual / clinical-efficacy metric**: **RadGraph-F1**
  (entity-relation overlap; Jain et al., NeurIPS Datasets & Benchmarks 2021), **CheXbert-F1**
  (finding-label agreement; Smit et al., 2020 — or the rule-based CheXpert labeler, Irvin et al.,
  2019), or a composite (RadCliQ), reported **alongside** any n-gram score.
- A headline resting on BLEU / ROUGE as if it were correctness → MAJOR; a clinical metric present but
  without CIs or a per-finding breakdown → MINOR.

**ME3 — Faithfulness / hallucination, measured not assumed**:
- A fluent answer is not a faithful one. For generated text require an **atomic-fact faithfulness**
  measure — decompose the output into atomic claims and check each against the image / source — and a
  **false-premise / abstention** robustness probe (does the model fabricate a finding when asked a
  leading or unanswerable question? — MedVH, Med-HALT). Report a **hallucination / fabrication rate**,
  not just an accuracy.
- A generation or VQA claim with no faithfulness or false-premise evaluation → MAJOR (the central MLLM
  gap); present but only spot-checked → MINOR.

**ME4 — Test-set contamination of the model's pretraining**:
- Public clinical benchmarks (VQA-RAD, SLAKE, MIMIC-CXR-derived, MedQA) may sit inside the model's
  pretraining corpus, so a high score can be **memorisation, not capability** — and for closed APIs the
  corpus is unknowable. Require an explicit contamination statement: the model's training cutoff vs the
  benchmark release date, a **held-out / private or post-cutoff** evaluation set, or a contamination
  probe (canary strings, perturbed-duplicate gap, membership test).
- "We evaluated model X on benchmark Y" with no contamination handling, where Y predates the cutoff →
  MAJOR; acknowledged as a limitation but not mitigated → MINOR (escalate if it carries the headline).

**ME5 — Prompt sensitivity, determinism, and run variance**:
- LLM outputs move with **prompt phrasing / format, temperature, and run-to-run sampling** (closed APIs
  are non-deterministic even at temperature 0). A single-prompt single-run number overstates stability.
  Require: the **exact prompt(s)** (MI-CLEAR-LLM transparency), temperature / seed, **≥ 3 runs** with
  variance, and a **prompt-robustness** check (≥ 2 phrasings / formats) for the headline.
- Single prompt, single run, temperature / seed undisclosed → MAJOR; prompt disclosed but variance
  unreported → MINOR.

**ME6 — Task-metric discipline for VQA / classification**:
- Apply the imbalance and operating-point discipline (cross-link `ai_overclaiming.md` and the
  model-development MD6 metric checks): report accuracy **at the real clinical prevalence**, not on a
  balanced QA set; specify **how free-text answers were matched** to the key (exact / normalised /
  LLM-judge — and if an LLM judges, validate it on controls, cross-link `/design-ai-benchmarking`); and
  state how **refusals / abstentions** are scored.
- Balanced-set accuracy generalised to deployment, or an unspecified answer-matching rule → MAJOR;
  refusal handling unstated → MINOR.

**ME7 — Reader study for generated reports**:
- Automated metrics do not establish clinical acceptability. A report-generation deployment claim needs a
  **blinded clinical reader study** with a pre-defined **error taxonomy** (clinically significant vs
  insignificant, omission vs fabrication), a severity scale, and **inter-reader agreement** (route the
  rubric / IRR to `/design-ai-benchmarking`, the ICC/κ to `/analyze-stats`, and reader / case sizing to
  `/calc-sample-size`).
- A deployment / utility claim from automated metrics alone, with no reader evaluation → MAJOR.

**ME8 — Calibration, abstention, and safety**:
- A clinical LLM that is confidently wrong is dangerous. Check whether the study reports **confidence
  calibration / appropriate abstention** (does the model express uncertainty or refuse when it should?),
  a **fabricated-citation / evidence** rate, **harmful-output** screening, and **subgroup robustness**
  (defer fairness depth to `equity_fairness.md`).
- For a deployment-flavoured claim, the absence of any safety / abstention evaluation → MAJOR; for an
  exploratory benchmark, → MINOR with a stated limitation.

**Output template (ME2 / ME3 example)**:
> "Report quality is reported as BLEU-4 and ROUGE-L, which track word overlap rather than clinical
> correctness — a report can score well while reversing laterality. I would add a factual metric
> (RadGraph-F1 or CheXbert-F1) reported with confidence intervals alongside the n-gram scores, and —
> because fluency is not faithfulness — an atomic-fact faithfulness rate plus a false-premise probe (does
> the model assert a finding when asked about an absent one?). Without these, the evaluation cannot
> distinguish a fluent confabulation from an accurate report."
