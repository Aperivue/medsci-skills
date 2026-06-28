# Evaluation plan
We evaluate GPT-X (version 2026-03) on a held-out, post-cutoff internal set for report generation.
The reference standard is set by two radiologists, with disagreements adjudicated by a third.
Quality is measured with RadGraph-F1 and CheXbert-F1 alongside BLEU-4, all with 95% CIs.
Faithfulness is assessed via atomic-fact checking and a false-premise probe (hallucination rate).
We disclose the exact prompt, temperature 0.2 with a fixed seed, and report mean +/- SD across 3 runs
with two prompt phrasings. A blinded clinical reader study with an omission/fabrication error taxonomy
supports the deployment claim. Where the SLAKE benchmark is used, we report a contamination check
(training cutoff versus benchmark release date). Answer matching uses normalised exact match.
