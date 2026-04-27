# Official Reporting Guideline Templates

This directory ships canonical flow diagram and figure templates for the four
most commonly required reporting guidelines in clinical research:

| Guideline | Source | What we ship | Why |
|-----------|--------|--------------|-----|
| PRISMA 2020 | prismastatement.org (CC-BY 4.0) | Locally built `.pptx` (4 variants: new/updated × v1/v2) | Site uses Squarespace JS-fingerprint redirect that blocks programmatic download. We reproduce the published layout (Page MJ et al. *BMJ* 2021;372:n71, Fig 1) and supply a `fill_prisma_template.py` to populate counts. |
| CONSORT 2025 | consort-spirit.org | Official `.docx` (flow diagram + editable checklist) | Direct fetch works; supersedes CONSORT 2010 per the SPIRIT-CONSORT 2025 update. |
| STARD 2015 | equator-network.org | Official `.pdf` flow diagram + `.docx` checklist | Flow diagram is published as PDF only; no Word source exists upstream. |
| SPIRIT 2025 | consort-spirit.org | Official `.docx` (participant timeline + editable checklist) | Direct fetch works; supersedes SPIRIT 2013 per the 2025 update. |

## Refresh / verify

```bash
bash scripts/fetch_official_templates.sh           # all targets
bash scripts/fetch_official_templates.sh consort2010
FORCE=1 bash scripts/fetch_official_templates.sh   # ignore cache
```

The fetcher reports per-target OK/SKIP/FAIL. URLs are versioned in the script
header — if a target rotates, update `TARGETS=` and rerun.

## PRISMA 2020 build/fill workflow

```bash
# (one-time) generate template variants
python3 scripts/build_prisma2020_template.py --variant new \
    --out templates/official/prisma2020/PRISMA_2020_flow_new_v1.pptx
python3 scripts/build_prisma2020_template.py --variant new --include-other-sources \
    --out templates/official/prisma2020/PRISMA_2020_flow_new_v2.pptx

# fill with study counts (positional 10-tuple)
python3 scripts/fill_prisma_template.py \
    --template templates/official/prisma2020/PRISMA_2020_flow_new_v1.pptx \
    --counts "315,122,186,7,111,204,102,84,3,15" \
    --out fig1_prisma_filled.pptx

# or with a JSON file giving every key
python3 scripts/fill_prisma_template.py \
    --template templates/official/prisma2020/PRISMA_2020_flow_new_v1.pptx \
    --counts-file my_counts.json \
    --out fig1_prisma_filled.pptx
```

Render to PDF/PNG via LibreOffice headless:

```bash
soffice --headless --convert-to pdf fig1_prisma_filled.pptx
soffice --headless --convert-to png fig1_prisma_filled.pptx
```

## Attribution

PRISMA layout: Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020
statement: an updated guideline for reporting systematic reviews. *BMJ*
2021;372:n71. doi:10.1136/bmj.n71. CC-BY 4.0.

CONSORT 2025 / SPIRIT 2025: see https://www.consort-spirit.org/.

STARD 2015: Bossuyt PM, Reitsma JB, Bruns DE, et al. STARD 2015. *BMJ*
2015;351:h5527.
