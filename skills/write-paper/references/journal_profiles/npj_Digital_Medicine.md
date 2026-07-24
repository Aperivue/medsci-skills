# npj Digital Medicine

## Journal Identity

- **Full name**: npj Digital Medicine
- **Abbreviation**: npj Digit. Med.
- **Publisher**: Nature Portfolio (Springer Nature)
- **ISSN**: 2398-6352 (online)
- **Frequency**: Continuous (online only)
- **Impact Factor**: High-impact digital health journal
- **Open Access**: Yes (CC BY 4.0 or CC BY-NC-ND 4.0)
- **APC**: ~EUR 2,490 (check current rates)

## Manuscript Types and Word Limits

| Type | Abstract | Manuscript Body | References | Notes |
|------|----------|----------------|------------|-------|
| Article | Structured | No strict limit (concise recommended) | No cap | Primary research |
| Review | Structured | No strict limit | No cap | |
| Brief Communication | Unstructured | Shorter than Article | No cap | |
| Perspective | Unstructured | ~3,000 | No cap | |
| Comment | Unstructured | ~1,500 | No cap | |
| Matters Arising | Brief summary | ≤ 1,200 | 15 | No APC; on npj Digit. Med. papers only |

## Abstract Format

Structured with three headings:
1. **Background**
2. **Methods**
3. **Results**

Typical length 250-350 words (no explicit cap stated).

## Keywords

Not explicitly required in guidelines.

## Required Sections

Nature-style order (Methods after Discussion):
1. **Introduction**
2. **Results**
3. **Discussion**
4. **Methods** (placed after Discussion)
5. **Data Availability Statement**
6. **Code Availability Statement** (if custom code used)
7. **Acknowledgements** (including funding)
8. **Author Contributions** (CRediT recommended)
9. **Competing Interests** (mandatory, even if none)
10. **References**
11. **Figure Legends** (after References)
12. **Tables** (at end)

## Citation Style

- Nature referencing style (numbered, square brackets)
- Numbered sequentially in order of appearance
- More than 5 authors: first author only, then "et al."
- Journal names: italicized, abbreviated with full stops
- Volume numbers: **bold**
- URLs: cited parenthetically in text, not in reference list
- Example: `Schott, D. H., Collins, R. N. & Bretscher, A. Secretory vesicle transport velocity... *J. Cell Biol.* **156**, 35-39 (2002).`

## Reporting Guidelines

| Study Type | Required Checklist |
|------------|-------------------|
| Randomized trials | CONSORT |
| Systematic reviews | PRISMA |
| Observational studies | STROBE |
| Diagnostic/prognostic | STARD, TRIPOD |
| AI diagnostic accuracy | STARD-AI |
| AI intervention trial | CONSORT-AI |
| AI prediction model | TRIPOD+AI |
| Qualitative research | COREQ or SRQR |
| Case reports | CARE |

Nature Portfolio Reporting Summary required with revised manuscript.

## Portal Mechanics

Facts about the submission system itself, recorded at first submission. These are not author
guidelines — they are what the portal does, and several of them are stated only on the
submission form. Read by `/sync-submission` `check_portal_mirror.py`.

- **Submission system**: SNAPP (Springer Nature Article Processing Platform)
- **Fields that REPLACE the manuscript**: Author Contributions · Competing Interests · Data Availability · Acknowledgements

  The form says so at each of them: *"This replaces any statement written within the manuscript
  and is the one that we will publish."* The manuscript file is the copy reviewers read; the
  portal box is the copy the world gets. Paste the manuscript section verbatim — do not
  re-compose it, which is how a co-first-authorship sentence and a "the funder had no role"
  sentence each came one click from vanishing.
- **No equal-contribution checkbox**: co-first authorship survives only if it is typed into the
  Author Contributions box. A † footnote on the title page does not reach the published record.
- **Code Availability has no dedicated field**: append it to the Data Availability text.
- **Research funding is structured** (funder + grant ID) with nowhere for a role disclaimer, so
  "The funder had no role in study design…" must live in the Acknowledgements box.
- **Accepted figure formats**: `.jpeg`, `.tiff`, `.eps` — **`.png` is not offered**. Line art and
  text-bearing figures should go as TIFF + LZW, flattened onto white (a surviving alpha channel
  prints black).
- **Cover letter is a file upload** (PDF), not a paste field.
- **Figure embedding**: figures are uploaded separately; embedding them in the manuscript file
  as well produces a compiled review PDF with every figure twice.
- **Known auto-extraction losses**: title and abstract come through exactly, but the affiliation
  parser silently drops intermediate levels (e.g. a college inside a university). Check author
  affiliations against the manuscript one by one; do not trust the extracted values.

## Special Notes

- **Initial submission formatting is relaxed**; strict formatting required only at acceptance.
- **Methods section after Discussion** (Nature family convention, not standard IMRAD).
- **No Supplementary Methods allowed**: all methods must be in main manuscript.
- **Single-blind peer review**; typical first decision ~4-6 weeks; desk reject rate ~50%+.
- **ORCID required** for corresponding author before final submission.
- **Data Availability and Code Availability** statements mandatory.
- **LLM/AI policy**: LLMs cannot be authors; document use in Methods section.
- **Figures**: 300 dpi minimum; panel labels lowercase bold (a, b, c); colorblind-accessible palettes required (avoid red/green).
- **Supplementary Information**: single merged PDF; large tables as separate "Supplementary Data" files.
- **Preprints** encouraged and do not compromise novelty.
- **Manuscript transfer service**: rejected papers can transfer to other Nature Portfolio journals with referee reports.
- **Statistics section mandatory**: must include test name, n, alpha level, one-tailed vs two-tailed, exact P values.

- **AI-use disclosure placement**: Methods
  <!-- machine-read by /self-review check_classical_style.py --profile; source: the profile's own AI policy line: "document use in Methods section" -->
