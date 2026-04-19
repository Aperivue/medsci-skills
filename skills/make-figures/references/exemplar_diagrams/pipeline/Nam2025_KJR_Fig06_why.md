# Why this exemplar is good — Nam2025_KJR_Fig06 (pipeline / M3D architecture)

Hierarchy / structure: Strict top-to-bottom flow. Volumetric CT input (single modality box with three anatomical sub-panels) feeds a 3D image encoder; parallel text-side question templates feed the text tokenizer. Both streams converge on a single LLM-with-LoRA block, then split into two downstream heads (report generation, VQA). The shape (funnel in → funnel out) mirrors the dual-task architecture.

Whitespace & balance: Equal space allocated to image-side and text-side inputs; the LLM block spans the full width to signal it is the shared backbone. Tight but not cramped.

Typography (font size, weight, alignment): Bolded section headers (Report Generation / VQA) for the prompt boxes; prompt contents in a slightly smaller, clearly italic-or-lighter weight. The special tokens (<|eot_id|>, <|start_header_id|>) use a monospace face — the right choice for communicating that they are literal code strings.

Emphasis (which elements are visually strongest, why): The fire/snow icons (trainable/frozen) are placed on individual components, making the training-recipe claim visually inspectable. This is a small but high-value design choice — readers can audit the method by looking at the figure.

Color usage: Cool blues for vision modules, warm pinks for language/prompt modules. Two-tone palette scales well to grayscale (luminance differs).

Weaknesses (if any — nothing is perfect): The "trainable/frozen" legend sits in the upper right and may be missed by readers who scan left-to-right top-down. The three CT sub-views (chest/abdomen/pelvis) are small enough that anatomy is only suggested.
