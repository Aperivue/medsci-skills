# OA + open-review sources by domain

Venues that reliably offer open-access full text or published peer reviews, grouped by
the medical domains the suite must serve. These are sourcing *starting points* — confirm
the license of each specific record at acquire time. No specific DOIs are listed here on
purpose (they are added to `queue.txt` only after verification).

## Published peer reviews (best for review-skill work)

- **F1000Research** — peer-review reports published CC-BY (strongest license footing).
- **eLife** — public reviews / assessments alongside Reviewed Preprints (confirm per record).
- **PeerJ** — optional open review histories (confirm per record).
- **BMJ Open** — pre-publication histories on many articles (license varies per record).

## OA articles by domain

- **Radiology / imaging** — Radiology and European Radiology OA articles; RSNA OA.
- **Medical AI / informatics** — Lancet Digital Health (OA), npj Digital Medicine (OA),
  Radiology: Artificial Intelligence OA articles.
- **Medical education** — BMC Medical Education (OA).
- **Clinical specialties / general medicine** — PLOS Medicine (OA), BMJ Open (OA).
- **Medical statistics / methods** — OA articles in BMC Medical Research Methodology;
  selected OA statistics-in-medicine methods papers.
- **ML/DL for medicine (CS venues)** — open proceedings (e.g., MICCAI/MELBA open content)
  and arXiv/medRxiv preprints (preprint license varies — confirm).

## Reviewer guidance / reporting standards (background, not corpus records)

EQUATOR Network reporting guidelines and their explanation-and-elaboration documents,
and publishers' public reviewer guides, inform the probes/rubrics directly. They are
reference material, not `_corpus/` records, and are cited where used.

## Linked artifacts (supplementary / code / data) — harvest with the article

Prefer papers that ship a **Data/Code availability** statement. Their supplementary files,
**GitHub/GitLab** repos, **Zenodo / OSF / Figshare** deposits, and **HuggingFace** model/
dataset cards carry the highest-value, most checkable detail (the real threshold, the actual
split, the calibration plot, the dataset provenance, the plotting code's true figure anatomy).
Record each under the manifest record's `linked_artifacts[]` with its **own** verified license
(a code repo's software license and a Zenodo deposit's per-deposit license are not the
article's — see `LICENSING.md`). These are especially valuable for the `make-figures` lane,
where the repo's plotting code or a supplementary figure shows what a strong chart contains.

## Figure-rich sources (for the make-figures lane)

For figure-type exemplars, prefer venues whose articles reliably contain the target chart:
**meta-analyses** (Systematic Reviews, Cochrane-style) for forest/funnel; **survival cohorts /
oncology trials** for Kaplan–Meier; **diagnostic-accuracy** studies for ROC / precision-recall;
**prediction-model** papers (TRIPOD+AI) for calibration and decision curves; **imaging-AI**
papers (CLAIM) for model-architecture, dataset-flow, and per-subgroup panels.
