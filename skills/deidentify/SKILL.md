---
name: deidentify
description: >
  De-identify clinical research data before LLM-assisted analysis. Standalone Python CLI
  detects PHI (Korean SSN, phone, names, dates, addresses) via regex + heuristics.
  Interactive terminal review. No LLM touches raw data — the script runs locally
  without any network or AI calls.
triggers: deidentify, de-identify, anonymize, 비식별화, 익명화, remove PHI, remove PII, strip patient info
tools: Read, Bash, Glob
model: inherit
---

# De-identification Skill

You are guiding a medical researcher through data de-identification. The actual
de-identification is performed by a **standalone Python script** that runs WITHOUT
any LLM. Your role is to explain, guide, and verify — not to see or process raw
PHI data.

## Critical Safety Rules

1. **NEVER ask the user to paste, show, or upload raw data containing PHI.**
   The script processes data locally. You never need to see patient-level data.
2. **NEVER read or display the mapping file contents.** It contains original PHI values.
3. **You may read** the scan report (column classifications, no raw values), audit log
   (SHA-256 hashes only), and de-identified output (PHI already removed).
4. **Always communicate in the user's preferred language** about the process, but use
   English for technical terms (PHI, HIPAA, Safe Harbor, etc.).

## Reference Files

- `${CLAUDE_SKILL_DIR}/references/hipaa_18_identifiers.md` — HIPAA Safe Harbor checklist
- `${CLAUDE_SKILL_DIR}/references/korean_phi_patterns.md` — Korean-specific regex patterns
- `${CLAUDE_SKILL_DIR}/references/date_shift_guide.md` — Date shifting best practices

Read relevant references before advising the researcher.

## Prerequisites

- Python 3.10+
- `openpyxl` (for .xlsx files): `pip install openpyxl`
- Supported formats: CSV, TSV, Excel (.xlsx)

## Five-Phase Workflow

### Phase 1: Assessment

Ask the researcher:
1. What file format is the data? (CSV, Excel, etc.)
2. What PHI do you expect in the data? (names, dates, IDs, etc.)
3. Does your IRB require specific de-identification documentation?
4. Do you need to re-identify later? (affects mapping file choice)

Based on answers, recommend the appropriate command:
- Full pipeline (most common): `python deidentify.py full <file>`
- Step-by-step (cautious): `python deidentify.py scan <file>` first

### Phase 2: Script Execution

Guide the researcher to run the script. The script is located at:
```
${CLAUDE_SKILL_DIR}/deidentify.py
```

**Full pipeline** (recommended for most users):
```bash
python ${CLAUDE_SKILL_DIR}/deidentify.py full data.xlsx \
    --output-dir ./deidentified/ \
    --auto-accept-safe
```

**Step-by-step** (for careful review):
```bash
# Step 1: Scan
python ${CLAUDE_SKILL_DIR}/deidentify.py scan data.xlsx --output-dir ./deidentified/

# Step 2: Review (interactive)
python ${CLAUDE_SKILL_DIR}/deidentify.py review ./deidentified/scan_report.json

# Step 3: Apply
python ${CLAUDE_SKILL_DIR}/deidentify.py apply ./deidentified/reviewed_report.json
```

**Options:**
- `--auto-accept-safe`: Skip confirmation for columns classified as SAFE (faster for large datasets)
- `--hash-mapping`: Store SHA-256 hashes instead of original values in mapping file (one-way, more secure)
- `--output-dir`: Where to save de-identified file, mapping, and audit log
- `-v/--verbose`: Enable debug logging

### Phase 3: Interactive Review Guidance

The script's terminal review has three passes:

1. **Pass 1 — Column Classification**: Each column is shown as PHI / REVIEW_NEEDED / SAFE.
   The researcher confirms or overrides each classification.
2. **Pass 2 — Undecided Items**: Columns that weren't resolved in Pass 1 get a second look
   with more sample values displayed.
3. **Pass 3 — Final Summary**: A table of all planned actions. The researcher can edit
   individual decisions before confirming.

Coach the researcher:
- "PHI로 분류된 컬럼은 기본적으로 익명화됩니다. 아닌 경우 'k'를 입력하세요."
- "REVIEW_NEEDED는 스크립트가 판단하기 어려운 컬럼입니다. 샘플 값을 확인하고 결정하세요."
- "SAFE는 PHI가 없는 컬럼입니다. 혹시 의심되면 'r'로 재검토 요청할 수 있습니다."

### Phase 4: Verify and Document

After the script completes, help the researcher verify:

1. **Read the audit log** (safe — contains only hashes):
   ```bash
   cat ./deidentified/audit_log.csv | head -20
   ```
   Verify the number of changes, affected columns, and PHI types.

2. **Spot-check the de-identified file** (safe — PHI already removed):
   Read a few rows to confirm pseudonyms (P0001, etc.), date shifts, and [REDACTED] markers
   appear where expected.

3. **Check that sensitive columns are actually removed**:
   Verify no original names, phone numbers, or RRN values remain.

4. **Mapping file security**:
   - Remind: "mapping.json에는 원본 환자정보가 포함되어 있습니다."
   - Recommend storing it separately from the de-identified data
   - File permissions are automatically set to 0600 (owner-only)

### Phase 5: Documentation

Generate a de-identification methods paragraph for the manuscript or IRB:

Template:
> Protected health information was removed from the dataset prior to analysis using
> a rule-based de-identification tool (deidentify.py, medsci-skills). The tool scanned
> column names and cell values using regex patterns for Korean resident registration
> numbers, phone numbers, email addresses, dates, and addresses. Each column classification
> was reviewed by the researcher in an interactive terminal session. Names were replaced
> with pseudonyms (P0001, P0002, ...), dates were shifted by a random per-patient offset
> (±365 days) preserving relative temporal intervals, and direct identifiers (phone numbers,
> email addresses, registration numbers) were suppressed. A total of [N] cells across
> [M] columns were de-identified. The de-identification mapping file was stored separately
> under restricted access (file permissions 0600).

Customize based on the actual audit log statistics.

## Cross-Skill Integration

- **deidentify** sits BEFORE `clean-data` in the research pipeline
- After de-identification, hand off to `/clean-data` for data quality profiling
- `/analyze-stats` can safely process the de-identified output
- `/write-paper` Methods section should reference the de-identification process
- `/write-protocol` can use the HIPAA/PIPA reference files for protocol documentation

## Output Files

| File | Contains PHI? | Safe for Claude? | Purpose |
|------|:------------:|:----------------:|---------|
| `*_deidentified.xlsx/csv` | No | Yes | De-identified data for analysis |
| `mapping.json` | **YES** | **No** | Original ↔ pseudonym mapping |
| `audit_log.csv` | No (hashes only) | Yes | What was changed and where |
| `scan_report.json` | No | Yes | Column classification results |
| `reviewed_report.json` | No | Yes | Researcher-reviewed classifications |

## Scope and Limitations

**Supported (v1)**:
- Structured tabular data: CSV, TSV, Excel (.xlsx)
- Korean PHI patterns: 주민번호, 전화번호, 이메일, 주소, 이름, 날짜, 차트번호
- English PHI column names (SSN, MRN, DOB, phone, address, email, etc.)
- Pseudonymization, date shifting, ID replacement, suppression

**NOT supported (planned for v2)**:
- DICOM image metadata (PS3.15 Annex E) — requires pydicom
- Clinical free-text NER (clinical notes, radiology reports)
- Automated k-anonymity / l-diversity assessment
- SPSS (.sav), SAS (.sas7bdat), or other statistical formats
