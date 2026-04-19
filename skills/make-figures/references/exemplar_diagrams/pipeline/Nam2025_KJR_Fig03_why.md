# Why this exemplar is good — Nam2025_KJR_Fig03 (pipeline)

Hierarchy / structure: Two-panel layout (A and B) separated by a thin vertical rule, with each panel self-contained. A shows contrastive pre-training: text encoder (top) and image encoder (bottom) converge on a similarity matrix. B shows a VQA inference pipeline flowing left → right. Panel labels sit in the top-left corner of each panel at a consistent position.

Whitespace & balance: Margins around the similarity matrix give it room to read as a data object rather than decoration. The two panels carry roughly equal visual mass so neither dominates.

Typography (font size, weight, alignment): Box labels use uniform sans-serif at one size; the similarity matrix cells use a mono face so Tᵢ·Iⱼ products align as a grid. The CXR/report thumbnails carry subscripts (T₁, T₂, I₁, I₂) in the same font as the matrix cells — visually tying the inputs to the matrix rows/columns.

Emphasis (which elements are visually strongest, why): The diagonal of the similarity matrix is shaded darker, pulling the eye to the positive pairs — this is the pedagogical point of contrastive learning and the figure lets design carry the explanation.

Color usage: Pink for text-side components, blue for image-side components. This two-channel color coding is consistent across both panels and makes the multimodal symmetry self-evident.

Weaknesses (if any — nothing is perfect): Panel B's projection matrix W and token boxes are compressed; readers unfamiliar with contrastive-language-image architecture may need to read the caption closely. The "language instruction" box on the far right of B is visually detached from the main flow.
