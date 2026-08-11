---
title: "Synthetic Example: Reader-Study Evaluation of an Assistive Triage Model"
authors: [Placeholder A, Placeholder B, Placeholder C]
journal: "arXiv:0000.00000"
date_published: 2026-01-15
tags:
  - 📝Paper
  - 🤖AI/LLM
  - 🏥ClinicalReasoning
  - 📊HeadToHead
status: 🟢Completed
aliases:
  - Synthetic-triage-reader-study
---

# Synthetic Example: Reader-Study Evaluation of an Assistive Triage Model

> **This note is a formatting example, not a real paper.** Every value below is invented to
> show the shape of a completed note. Nothing here should be cited.

📎 **Open the PDF inside Obsidian**: ![[synthetic_triage_reader_study.pdf]]

## 📌 One-line summary
In a synthetic 20-case reader study, an assistive model raised median reader accuracy from 7
to 9 of 10 while leaving the rate of confidently wrong calls unchanged.

## 🎯 Background and aim
* Earlier work reported end-point accuracy but not how readers behaved with the tool in hand
* The paper asks whether assistance changes the reasoning path or only the final answer
* Stated hypothesis: assistance improves accuracy without reducing overconfident errors

## 🔑 Methods and results
1. **Design**: cross-sectional reader study, 20 vignettes, 12 readers, blinded to arm
2. **Main results**: median score 9 of 10 assisted versus 7 unassisted (p = 0.004);
   confidently-wrong rate 15% versus 14% (not significant)
3. **Comparison**: against unassisted readers only; no second tool was evaluated
4. **Limitations**: authors note the vignettes were curated, the reader pool was single-site,
   and no downstream patient outcome was measured

## 💡 My reading
* The accuracy gain and the flat error rate point the same way — assistance helps the cases
  readers were already close on, not the ones they were confidently wrong about
* Worth checking whether our own evaluation would even detect that split, or only report the
  headline accuracy

---
## Related notes
* [[MOC]]
* [[Sequential decision-making]]
* [[LLM co-pilot in medicine]]
* [[Reader study design]]
