# Why this exemplar is good — Nam2025_KJR_Fig01 (pipeline)

Hierarchy / structure: A clean left-to-right pipeline — paired inputs (CXR image on top, clinical text on bottom) merge into a single downstream processor (MLLM) and terminate in a single output box. The two parallel encoder boxes are aligned horizontally, which communicates multimodal symmetry at a glance.

Whitespace & balance: Generous horizontal whitespace around the central MLLM chip icon makes it the visual anchor. Input column and output column carry roughly equal ink weight, avoiding a lopsided read.

Typography (font size, weight, alignment): Box labels (Image encoder / Text encoder) are bolded sans-serif; patient demographics use a smaller mono-like face to read as tabular data rather than prose. Illustrative "clinical question" is italicized and color-accented to flag that it is an example, not a label.

Emphasis (which elements are visually strongest, why): Pink-tinted inputs and green output speech bubble draw attention to the clinically meaningful endpoints (question in → answer out), while the technical processing blocks sit in neutral gray.

Color usage: Two saturated tints (pink for input, green for output) plus neutral gray for machinery. Colorblind-safe if converted — the saturation contrast survives grayscale.

Weaknesses (if any — nothing is perfect): The MLLM "chip" icon is decorative rather than structural; could confuse readers expecting an architectural diagram. CXR thumbnail is small relative to the clinical-info panel, slightly under-weighting the image modality.
