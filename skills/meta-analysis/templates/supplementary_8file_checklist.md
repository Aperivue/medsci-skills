# SR-MA Supplementary Package — 8-File Standard

**Motivation**: Recent SR-MA peer reviews surfaced supplementary packages that contained only figure captions (≈90 lines), missing PRISMA checklist, exclusion list, extraction table, per-study RoB — despite Methods citing "Supplementary Table S1". Below is the minimum package to avoid this pattern.

**Apply to**: every SR-MA submission. Radiology / Radiology-AI / European Radiology / JCSM / Lancet family / JAMA family / BMJ family all expect this level of supplementary.

## 8 mandatory files

### S1 — PRISMA / PRISMA-DTA / PRISMA-S checklist

- 27-item PRISMA 2020 (general) or PRISMA-DTA (diagnostic accuracy SR-MA)
- Each item filled with main-manuscript page reference (`p.3, lines 45-48`)
- Use checklist template from your institutional checklist store
- For pure search reporting: PRISMA-S 16-item additional

### S2 — PROSPERO protocol PDF (snapshot + amendments)

- Download from prospero.york.ac.uk at registration AND at submission
- Include all amendments with date + rationale
- **If subgroup analyses changed post-registration**: explicit amendment record with date

### S3 — Full search strategy verbatim (per database)

- Each database (PubMed / Embase / Cochrane / Scopus / Web of Science) with:
  - Search date (YYYY-MM-DD)
  - Final string verbatim (copy-paste from interface)
  - Filter use (date, language, study type)
  - Number of records retrieved per database

### S4 — Full-text exclusion list with reasons (PRISMA item 16b)

- Every full-text article excluded with:
  - First author, year, title
  - PMID / DOI
  - Exclusion reason (one of pre-specified categories)
- Use Rayyan export or equivalent

### S5 — Per-study data extraction table

- One row per included study × all extracted variables (use `extraction_form_v2.md` schema)
- Include `source_page_ref` + `source_verbatim_quote` for outcome cells (DTA 2×2 or AUC)
- Locked read-only file (CSV + PDF snapshot)

### S6 — Per-study × per-domain risk-of-bias table

- For DTA: QUADAS-AI (4 domains × N_diagnostic studies) + applicability concerns
- For prognostic: PROBAST-AI (4 domains × N_prognostic studies)
- Per-cell: Low / High / Unclear + 1-line justification
- Optionally: METRICS framework parallel column
- Include pre-adjudication Cohen's κ per domain

### S7 — Subgroup forest plots (all pre-specified + clearly labeled exploratory)

- Each forest plot with:
  - Subgroup label
  - "Pre-specified in PROSPERO" or "Exploratory (post-hoc)" tag
  - Heterogeneity (I², τ²) per stratum
  - **k=1 strata excluded from formal test OR flagged as descriptive only**

### S8 — Sensitivity analyses + publication bias

- Leave-one-out for primary outcome (forest plot or table)
- Cohort overlap sensitivity analysis (exclude one of HIGH-confidence overlap pair)
- Deeks' funnel asymmetry test for DTA studies (mada::funnel)
- Funnel plot + Egger / Begg for prognostic AUC pooling
- Trim-and-fill if asymmetry detected

## Submission gate check

Before submitting, verify:

```bash
ls -la submission/supplementary/
# Expected: at minimum 8 files (S1-S8)

# Each file size > 5 KB (figure caption only is ~3 KB)
for f in submission/supplementary/S*.{md,pdf,csv,docx}; do
  size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
  echo "$f: $size bytes"
done
```

If any S-file is missing or only contains figure captions → **NOT READY for submission**.

## Cross-link to AI Disclosure (`/sync-submission` gate)

The supplementary checklist should be combined with the AI Disclosure presence check. Most major imaging journals require an affirmative or negative disclosure statement either in manuscript text or in S-file metadata.

## Related

- `templates/extraction_form_v2.md`
- `scripts/dta_extraction_qc.py`
- `scripts/cohort_overlap_check.py`
- `/peer-review` Phase 2A P5 (supplementary completeness probe)
