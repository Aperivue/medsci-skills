# Why this exemplar is good — Nam2025_KJR_Fig07 (pipeline / MAIRA-Seg)

Hierarchy / structure: A horizontal pipeline with input row (CXRs, pseudo-masks, task instruction, textual context) on top, processing row (image encoder, segmentation model, tokenizer/embedding) in the middle, and convergence on a single LLM block at the bottom. The vertical progression communicates "modalities in → unified tokens → one model out" without ambiguity.

Whitespace & balance: The LLM block spans almost full width as a visual foundation. Upper row inputs are grouped by modality with clear gaps, avoiding the "everything dumps in" look.

Typography (font size, weight, alignment): Small but uniform sans-serif labels; auxiliary labels ("Only in multi", "Pseudo-labels") are italic to mark them as conditional annotations without adding a legend.

Emphasis (which elements are visually strongest, why): The LLM base block is the largest uniform colored rectangle — visually grounding the whole system as one model. Fire icons on trainable components again let the figure double as a training-recipe specification.

Color usage: Warm pinks for segmentation/prompt-side modules; cool blues for vision/LLM modules. Dashed borders denote optional paths ("Only in multi"). Consistent with the color code used in other architecture figures in the paper.

Weaknesses (if any — nothing is perfect): The dense upper input row competes for attention; a subtle grouping box or lane separator would help. The segmentation-tokens-extractor sits off the main flow axis, which introduces a jog in the layout that briefly interrupts the top-down read.
