---
title: "Sequential decision-making"
type: concept
tags:
  - 🧠Concept
  - 🏥ClinicalReasoning
aliases:
  - Sequential diagnosis
related_papers:
  - "[[Synthetic Example: Reader-Study Evaluation of an Assistive Triage Model]]"
  - "[[Synthetic Example: Cost-Aware Diagnostic Agent]]"
  - "[[Synthetic Example: Simulated Clinic Benchmark]]"
status: 🌱Seedling
---

# Sequential decision-making

> **This note is a formatting example.** The papers it links are synthetic. It shows what a
> seedling concept note looks like before the reader has rewritten the definition.

## 📖 Definition, in my own words
> 🌱 *Placeholder — drafted by the skill, awaiting the reader's own wording.*

Deciding what to do next when the picture is still incomplete: order a test, ask a question,
or commit. What separates it from one-shot diagnosis is that each step changes what the next
step should be, so the quality of a path cannot be read off its endpoint.

## 🌐 Why it matters
Benchmarks that score only the final answer cannot distinguish a good path from a lucky one.
Any evaluation meant to say something about clinical use has to score the sequence.

## 📚 How different papers treat it
- **[[Synthetic Example: Reader-Study Evaluation of an Assistive Triage Model]]**: treats the
  path as an outcome in its own right; reports where readers diverged from the model
- **[[Synthetic Example: Cost-Aware Diagnostic Agent]]**: prices each step, so the metric is
  accuracy per unit of cost rather than accuracy alone
- **[[Synthetic Example: Simulated Clinic Benchmark]]**: holds the environment fixed and lets
  the agent choose the order, treating step count as the difficulty axis

## 🔗 Related concepts
- [[LLM co-pilot in medicine]] — the same question from the human side: who chooses the next step
- [[Evaluation beyond endpoint accuracy]] (not yet written) — the measurement problem this creates

## ❓ Open questions
- Is there a scoring rule for a diagnostic path that does not collapse back to its endpoint?
- When a model and a reader take different paths to the same answer, which one should the
  evaluation reward?

## 📝 Update log
- 2026-01-20: drafted from 3 papers
