# Repository, CITATION.cff, Zenodo, and Hugging Face Rules

Load from `SKILL.md` Section 5 when the artifact is a GitHub README, `CITATION.cff`, Zenodo record,
or Hugging Face model/dataset card. Rule numbers match `checklists/AIO_GENERAL.md` items 5.1–5.6.
JSON-LD markup and its validator, and the rule against auto-completing author metadata, are in
`SKILL.md` Section 5.

## 5.1 README canonical 10-slot order

1. Title + one-line description + badges (license, DOI, arXiv, Hugging Face, paper link).
2. Paper reference block — BibTeX + APA + two-sentence abstract.
3. TL;DR — at most 5 bullets: problem, approach, key result, intended users.
4. Quickstart — `pip install` or `git clone && make demo`. Should work in under 5 minutes.
5. Reproducibility — exact commands that regenerate every figure and table. Pin package versions.
6. Project structure — a tree with one-line folder descriptions.
7. Data access — license, download scripts, DUA notes.
8. FAQ — "How is this different from X?", "Can this be used clinically?", "How do I cite this?".
   High-value retrieval content.
9. Acknowledgements, funding, and COI.
10. License (prefer Apache-2.0 for research code).

## 5.2 CITATION.cff

Add a `CITATION.cff` file at repository root. GitHub renders it as a "Cite this repository"
button, and AI agents treat it as the primary citation hint. Include authors with ORCID, title,
version, DOI (post-Zenodo-archive), repository URL, and license.

## 5.3 Zenodo DOI

Enable GitHub–Zenodo integration for each release. Cite the version-specific DOI in the paper's
Data/Code Availability section. Zenodo deposits appear in Google Scholar and OpenAlex, creating an
independent citable artifact.

## 5.4 Hugging Face model card YAML

Required keys: `license`, `library_name`, `tags`, `datasets`, `base_model` (when fine-tuning),
`pipeline_tag`. Required prose sections: Intended use, Training data, Evaluation, Limitations,
Ethical considerations, and a clinical-use disclaimer ("This model is not approved for clinical
diagnostic use; it is provided for research purposes only").

## 5.5 Hugging Face dataset card

Required prose: license, PHI and re-identification risk, task, language, splits, annotation
process, known biases, ethical review status. Flag PHI leakage in the dataset samples.

## 5.6 Web-crawler-friendly formatting

- Markdown headings are declarative claims.
- Code blocks are fenced and language-tagged.
- Tables are plain Markdown, not HTML (survive Markdown-to-vector chunking).
- Images have descriptive alt text (vision-LLMs read alt text when image retrieval fails).
- Each README section is under about 300 words to survive fixed-size chunking.
- Use question-style subheadings when natural ("Why another benchmark?", "How fast is
  inference?").
