# Radiology: Artificial Intelligence (RYAI)

## Journal Identity

- **Full name**: Radiology: Artificial Intelligence
- **Abbreviation**: Radiol Artif Intell
- **Publisher**: Radiological Society of North America (RSNA)
- **ISSN**: 2638-6100
- **Frequency**: Bimonthly
- **Impact Factor**: ~8.1 (2024)

## Manuscript Types and Word Limits

| Type | Abstract | Manuscript Body | Figures | Tables |
|------|----------|----------------|---------|--------|
| Original Research | 250 | 3500 | 7 | 5 |
| Technical Note | 250 | 1500 | 4 | 3 |
| Review Article | 250 | 5000 | 10 | 5 |
| Letter to Editor | none | 500 | 1 | 1 |

Word counts exclude abstract, references, figure legends, and tables.

## Abstract Format

Structured with four headings:
1. **Purpose**
2. **Materials and Methods**
3. **Results**
4. **Conclusion**

Maximum 250 words. Must be self-contained.

## Citation Style

- Vancouver (numbered) style.
- Numbered sequentially in order of first appearance in text.
- Use superscript numbers in the manuscript body.
- Format: Author(s). Title. Journal Abbreviation. Year;Vol(Issue):Pages.
- List all authors if 6 or fewer; if 7+, list first 3 followed by "et al."

## Keywords

- 3-5 keywords required.
- MeSH terms preferred.
- Listed alphabetically.

## Required Elements

### For All Manuscripts
- **Title page**: title, short title (50 chars), authors with affiliations, corresponding author, word count, number of figures/tables/references.
- **Key Points**: Not required (unlike AJR).
- **Data Availability Statement**: Required. Must specify whether data and code are available and under what conditions.
- **Author Contributions**: CRediT taxonomy required.
- **Conflict of Interest Disclosures**: Required for all authors.
- **Funding**: Grant numbers and funding sources.

### For AI Studies (Mandatory)
- **CLAIM Checklist**: Must be completed and submitted as supplemental material for any study involving AI/ML in medical imaging.
- **AI Disclosure in Methods**: Must describe any use of AI tools in the research process (data collection, analysis, writing assistance). Specific tools and versions must be named.
- **AI Disclosure in Acknowledgments**: Must acknowledge AI writing assistance if used, specifying the tool and its role.
- **Code Availability**: Strongly encouraged. GitHub repository or equivalent.
- **Model Card**: Encouraged for studies introducing new AI models.

## Reporting Guidelines

Match study type to required checklist:

| Study Type | Required Checklist |
|------------|-------------------|
| Diagnostic accuracy (AI) | STARD-AI |
| Prediction model | TRIPOD+AI |
| Any AI study in imaging | CLAIM 2024 |
| Randomized trial with AI | CONSORT-AI |
| Systematic review of AI | PRISMA 2020 |

Multiple checklists may apply (e.g., CLAIM + STARD-AI for a diagnostic AI study).

## Supplemental Materials

- Strongly encouraged.
- Can include additional tables, figures, methods details, code.
- Supplemental material is peer-reviewed.
- Common supplements: expanded methods, additional performance metrics, subgroup analyses, CLAIM checklist.

## Formatting Notes

- Double-spaced, 12-point font.
- Line numbers required on the manuscript.
- Pages numbered consecutively.
- Abbreviations defined at first use in both abstract and body (independently).
- SI units preferred; conventional units acceptable with SI in parentheses.

## Statistical Reporting

- Report exact p-values (e.g., P = .034); use P < .001 only when value is below that threshold. Never report only "P < .05".
- 95% CI required for all primary performance metrics (AUC, sensitivity, specificity, accuracy).
- For AI model comparisons: use DeLong test for AUC comparison; McNemar test for paired sensitivity/specificity.
- Calibration must accompany discrimination for prediction models: calibration plot + Hosmer-Lemeshow or calibration slope/intercept.
- Subgroup performance metrics required for fairness assessment (CLAIM requirement).
- Effect sizes with units; avoid "significant" without accompanying statistics.
- Statistical software and version must be named in Methods.
- Statistical review for all accepted manuscripts.

## Review Process

- Single-blind peer review.
- Typical first decision: 4-6 weeks.
- Revisions usually due within 60 days.

## Special Considerations for Education-Research Manuscripts

- Paper 1 (S5 Multi-agent Validation) and Paper 2 (MLLM Image Reliability) are strong fits for RYAI.
- CLAIM checklist is mandatory for both.
- Emphasis on reproducibility: pipeline code, prompt templates, and evaluation criteria should be described in detail or provided as supplements.
- For LLM/MLLM studies: model version, API date, temperature settings, prompt text (or reference to supplement) must be reported in Methods.

---

## AI Writing Disclosure Policy
- **Requirement level:** Required
- **Permitted scope:** Language editing only — AI/LLM tools may assist with language editing and manuscript preparation but cannot be listed as authors; must not generate scientific content, interpret data, or draw conclusions
- **Disclosure location:** Methods + Acknowledgments — must describe the AI tool name, version, and specific role in both the Methods section (under "AI Disclosure in Methods") and Acknowledgments (under "AI Disclosure in Acknowledgments"); this is distinct from AI used as the research subject
- **AI-generated images:** Banned — AI-generated or AI-manipulated images in figures are not permitted; AI models studied as research subjects must follow CLAIM checklist reporting
- **Policy URL:** https://pubs.rsna.org/page/ai-policy
