<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Self-Improving / Self-Evaluating System probes (SI1–SI7)

For any manuscript whose claimed mechanism of improvement is the system judging or revising **itself**:
an agent that iteratively critiques and rewrites its own output, a pipeline trained on data it generated,
an LLM used as the judge that selects or scores the training signal, a "self-evolving" clinical agent.
This class is growing fast in medical AI and is reviewed badly, because the loop *looks* like a method
while the thing that decides whether it worked is often the system itself.

Co-apply with `mllm_evaluation.md` (when an LLM is the evaluator), `ai_overclaiming.md` (when the claim
outruns the evidence), and `model_development.md` (when the loop produces training data).

**The organizing question is not "did it improve?" but "what said so?"** Every improvement loop is a
claim that some signal can substitute for human judgment, and signals are not interchangeable. Order
them (Chen, Wang & Qu 2026, arXiv:2607.07663, §5.2):

| Rung | Signal | What it buys |
|------|--------|--------------|
| 1 | **Formal verifier** — proof checker, type system, schema validator | Sound by construction; cannot accept a false improvement |
| 2 | **Execution feedback** — a test suite, a recomputation, an independent measurement, a held-out labelled set | Reliable but incomplete |
| 3 | **Learned judge** — reward model, LLM-as-judge | Bounded by the judge's own competence; is itself an optimization target |
| 4 | **Intrinsic signal** — the model's own confidence, self-consistency, likelihood | Cheapest, most gameable |

Demonstrated self-improvement strength tracks that order. A paper claiming a rung-1 result on a rung-3
signal is the single most common failure in this literature, and it is a MAJOR.

**SI1 — Name the rung.** Which signal decided that an iteration was an improvement? If the answer is
"the model judged its own output better," the paper has a rung-3 or rung-4 signal and must not report a
rung-1/2 conclusion (e.g., "the agent autonomously improves diagnostic accuracy"). If the signal is
never named at all — the loop simply ran N times and the final output is presented as better — that is a
MAJOR: no evidence of improvement has been offered, only evidence of change.

**SI2 — The self-confirming loop (generator == evaluator).** When the generator and the evaluator share
weights, their biases correlate: the loop preferentially reinforces the errors the model is **most
confident about**, and a self-critique "inherits the blind spots that produce confident fabrication."
- Is the judge the same model (or the same family / the same provider's checkpoint) as the system being
  judged? Disclosed?
- Is the judge validated **against an external standard** — human expert ratings, a held-out labelled
  set, a task with checkable ground truth — and is the agreement reported?
- Unvalidated same-model judge → **MAJOR**. The reported gain may be the judge and the generator agreeing
  with each other, which is not evidence about the world.
- Reward hacking is the special case where the gamed judge is explicit; the self-confirming loop is the
  general case, and **needs no adversary** — do not accept "we had no incentive to game it" as an answer.

**SI3 — Reformulation vs progress.** Ungrounded self-critique converges to rewording. Ten rounds of
self-critique across three model providers and four task families produced a **55% decline in
informational change** across iterations — the loop circles — while a *single* verification step restored
forward movement (DeVilling 2025, arXiv:2510.21861).
- Does the paper report the **trajectory** across iterations, or only the final output vs the first?
- Is there a plateau/decline analysis, or a stopping rule that is anything other than a fixed N?
- Is any of the measured gain attributable to the output getting *longer* or *more hedged* rather than
  more correct?
- Improvement claimed from an ungrounded loop with no per-iteration external measurement → **MAJOR**.

**SI4 — Training on self-generated data (collapse).** If the system trains on its own outputs:
- What fraction of the training signal is **exogenous** (real, externally grounded) data, and is it held
  constant across rounds? If the exogenous fraction goes to zero, degenerative dynamics follow — loss of
  distribution tails, entropy decay, variance amplification (Shumailov et al., *Nature* 2024).
- Is filtering/gating of the generated data described, and is the filter itself rung-3 (an LLM) or
  rung-2 (a checkable criterion)?
- Are rare classes / tail findings — the ones that matter clinically — checked for erosion across rounds,
  or is only aggregate accuracy reported?
- Self-training with no real-data mixing and no tail analysis → **MAJOR**.

**SI5 — Diversity collapse.** Distinct from data collapse: in co-evolutionary or curriculum loops the
*task* distribution narrows, because the proposer drifts toward the band of problems that satisfy the
reward.
- Is the diversity of generated cases/questions measured over rounds, or only their quantity?
- For synthetic clinical cases: are they still covering the presentations that were rare at round 0?
- "Novelty is a consumable resource that closed loops deplete" — a paper reporting rising performance on
  a distribution its own loop is narrowing has measured the wrong thing → **MAJOR** if the curriculum is
  the contribution, MINOR if incidental.

**SI6 — Result-level vs process-level evidence.** Does the evaluator judge the **answer** or the
**procedure**? Outcome-only filtering admits lucky guesses with wrong reasoning — a serious matter in a
clinical pipeline, where the reasoning is what a clinician must audit.
- Is any process-level check reported (step correctness, the retrieved evidence actually supporting the
  claim, the derivation), or only final-answer agreement?
- If the paper's claim is that the system's *method* improved, but its evidence is that its *answers*
  scored higher on N cases, the claim outruns the evidence → MAJOR (see `ai_overclaiming.md`).

**SI7 — Human-in-the-loop honesty and clinical deployment.** Where in the loop does a human remain, and
does the paper say so plainly?
- Direction-setting — deciding *what to improve* — is the paradigm case of a non-verifiable task, and it
  is where humans remain. A paper describing a "fully autonomous" clinical improvement loop that in fact
  had a human choosing the objective, the prompts, the stopping point, and the failure cases should say
  so; "autonomous" as a headline over a human-steered loop is an overclaim → MAJOR.
- Deployment framing: an improvement loop that runs **after** deployment changes the device. Is there any
  account of how the improved system is re-validated, monitored, or rolled back? A self-modifying system
  in a clinical setting with no re-validation path is a regulatory as well as scientific gap → MAJOR when
  deployment is claimed.

## Deterministic support

`skills/peer-review/scripts/check_self_improvement_claims.py` (also runnable from `/self-review`) reads
the manuscript text and reports:

- `SELF_CONFIRMING_EVALUATOR` (major) — the same model is named as both the system and the judge, and no
  external validation of the judge (human expert / ground truth / held-out labels) appears anywhere.
- `UNGROUNDED_SELF_LOOP` (major) — an explicit self-refinement / self-critique / self-training claim with
  no external verification vocabulary anywhere in the text.
- `SELF_TRAINING_NO_REAL_DATA` (minor) — training on model-generated data with no mention of real-data
  mixing or an exogenous fraction.

The script narrows SI2 / SI3 / SI4 to what can be decided by reading; the remaining probes are judgment
and stay judgment.
