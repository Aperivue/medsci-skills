---
name: deidentify
description: Use when clinical data may contain PHI and must be de-identified before any LLM-assisted analysis. A local Python script (no network or AI calls) detects identifiers with regex and heuristics in 11 country locale packs, with interactive terminal review.
metadata:
  triggers: "deidentify, de-identify, anonymize, 비식별화, 익명화, remove PHI, remove PII, strip patient info"
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
3. **You may read** the scan and reviewed reports (column classifications; no cell values)
   and the audit log (keyed hashes; no original values). Read the de-identified output only
   after the researcher has run the review and confirmed it; it has the identifiers they
   chose to anonymize removed, and nothing more (see "What the tool does not do").
4. **Always communicate in the user's preferred language** about the process, but use
   English for technical terms (PHI, HIPAA, Safe Harbor, etc.).
5. **The researcher runs the script in their own terminal**, not through you (no `!` prefix,
   no Bash tool call): the review prints sample values of every column.

## Reference Files

- `${CLAUDE_SKILL_DIR}/references/hipaa_18_identifiers.md` — HIPAA Safe Harbor checklist
- `${CLAUDE_SKILL_DIR}/references/korean_phi_patterns.md` — Korean-specific regex patterns
- `${CLAUDE_SKILL_DIR}/references/date_shift_guide.md` — Date shifting best practices

Read relevant references before advising the researcher.

## Prerequisites

- Python 3.9+
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
- Full pipeline (most common): `python3 deidentify.py full <file> --locale <code>`
- Step-by-step (cautious): `python3 deidentify.py scan <file> --locale <code>` first

Available locale codes: `kr` (Korea), `us` (USA), `jp` (Japan), `cn` (China), `de` (Germany),
`uk` (United Kingdom), `fr` (France), `ca` (Canada), `au` (Australia), `in` (India), `it` (Italy).
If `--locale` is omitted, the script shows an interactive country selection menu.
Users can provide a custom locale file via `--locale-file custom.json`.

### Phase 2: Script Execution

Guide the researcher to run the script. The script is located at:
```
${CLAUDE_SKILL_DIR}/deidentify.py
```

**Full pipeline** (recommended for most users):
```bash
python3 ${CLAUDE_SKILL_DIR}/deidentify.py full data.xlsx \
    --locale kr \
    --output-dir ./deidentified/
```

**Step-by-step** (for careful review):
```bash
# Step 1: Scan
python3 ${CLAUDE_SKILL_DIR}/deidentify.py scan data.xlsx --locale kr --output-dir ./deidentified/

# Step 2: Review (interactive)
python3 ${CLAUDE_SKILL_DIR}/deidentify.py review ./deidentified/scan_report.json

# Step 3: Apply (refuses a report that was not reviewed, has a column without a decision,
# or was made from data that has changed since: edit the file, then scan and review again)
python3 ${CLAUDE_SKILL_DIR}/deidentify.py apply ./deidentified/reviewed_report.json
```

**Options:**
- `--locale CODE`: Country locale for PHI patterns (kr, us, jp, cn, de, uk, fr, ca, au, in, it)
- `--locale-file PATH`: Custom locale JSON file (copy `locales/_template.json` to create one)
- `--auto-accept-safe`: Keep SAFE columns without showing them. Not recommended: SAFE means
  no pattern matched, not that the column holds no identifiers (a name typed into a short
  comment matches no pattern), and this option means nobody looks at those columns
- `--hash-mapping`: Store unkeyed SHA-256 hashes instead of original names/IDs in the mapping
  file. Dates and numeric IDs can be recovered from such hashes by trying every candidate, so
  mapping.json stays restricted either way
- `--output-dir`: Where to save de-identified file, mapping, and audit log
- `-v/--verbose`: Enable debug logging

### Phase 3: Interactive Review Guidance

The script's terminal review has three passes:

1. **Pass 1 — Column Classification**: Each column is shown as PHI / REVIEW_NEEDED / SAFE,
   with sample values. The researcher confirms or overrides each classification.
2. **Pass 2 — Undecided Items**: Columns that weren't resolved in Pass 1 get a second look
   with more sample values displayed.
3. **Pass 3 — Final Summary**: A table of all planned actions. The researcher can edit
   individual decisions before confirming.
4. **Patient key** (only when dates will be shifted): the researcher picks the column that
   identifies the patient, or `row` if every row is a different patient. Each patient gets
   their own offset; without a key the tool does not shift dates.

Coach the researcher. Deliver these prompts in the researcher's preferred language:
- "Columns classified as PHI are anonymized by default. Press 'k' to keep the original value."
- "REVIEW_NEEDED are columns the script could not vouch for: free text, a PHI word inside a
  longer column name, ID-like numbers, a rare address. Read the sample values and type 'a'
  or 'k' — Enter alone is not accepted for these."
- "SAFE means no pattern matched, not that the column is free of identifiers. Read its sample
  values too, and press 'r' if a column holds names or anything else identifying."
- For free-text columns, 'a' replaces each whole text with `[REDACTED]`: the script cannot
  find a name inside a sentence, so it does not try to keep the rest of the text.

### Phase 4: Verify and Document

After the script completes, help the researcher verify:

1. **Read the audit log** (no original values; `before_hash` is an HMAC-SHA256 under a
   per-run key that is kept only in mapping.json):
   ```bash
   cat ./deidentified/audit_log.csv | head -20
   ```
   Verify the number of changes, affected columns, and PHI types.

2. **Ask the researcher to spot-check the de-identified file first**, in their own terminal:
   pseudonyms (P0001, etc.), shifted dates and [REDACTED] markers where expected, and no
   names in the columns they kept. Read it yourself only after they confirm.

3. **Check that sensitive columns are actually removed**:
   Verify no original names, phone numbers, or RRN values remain.

4. **Mapping file security**:
   - Remind the researcher: "mapping.json contains original patient identifiers — treat it as restricted."
   - Recommend storing it separately from the de-identified data
   - File permissions are automatically set to 0600 (owner-only)

### Phase 5: Documentation

Generate a de-identification methods paragraph for the manuscript or IRB:

Template:
> Direct identifiers were removed from the dataset prior to analysis using
> a rule-based de-identification tool (deidentify.py, medsci-skills) with the [COUNTRY]
> locale pattern pack. The tool scanned column names and cell values using regex patterns
> for country-specific identifiers (e.g., national ID numbers, phone numbers), email
> addresses, dates, and addresses. Each column classification was reviewed by the
> researcher in an interactive terminal session. Names were replaced with pseudonyms
> (P0001, P0002, ...), dates were shifted by a random per-patient offset (1-365 days, either direction)
> preserving relative temporal intervals, and direct identifiers (phone numbers, email
> addresses, national ID numbers) were suppressed. A total of [N] cells across [M]
> columns were de-identified. The de-identification mapping file was stored separately
> under restricted access (file permissions 0600).

Customize based on the actual audit log statistics. Do not call the dataset "de-identified
under HIPAA Safe Harbor" (or anonymised under another law) unless the gaps listed in
"What the tool does not do" were closed as well, or an expert determination covers them.

## Cross-Skill Integration

- **deidentify** sits BEFORE `clean-data` in the research pipeline
- After de-identification, hand off to `/clean-data` for data quality profiling
- `/analyze-stats` can safely process the de-identified output
- `/write-paper` Methods section should reference the de-identification process
- `/write-protocol` can use the HIPAA/PIPA reference files for protocol documentation

## Output Files

| File | Contains PHI? | Safe for Claude? | Purpose |
|------|:------------:|:----------------:|---------|
| `*_deidentified.xlsx/csv` | Only what the researcher kept, and what the tool cannot detect (see below) | After the researcher confirms it | Data for analysis |
| `mapping.json` | **YES** | **No** | Original ↔ pseudonym mapping, per-patient date offsets, audit hash key |
| `audit_log.csv` | No original values (keyed hashes) | Yes | What was changed and where |
| `scan_report.json` | No cell values | Yes | Column classification results |
| `reviewed_report.json` | No cell values | Yes | Researcher-reviewed classifications and patient key column |

## What the tool does not do

The tool removes or replaces the identifiers the researcher marked for anonymization. It does
not by itself make a dataset HIPAA Safe Harbor de-identified, or anonymous under other laws:

- **Ages over 89 are kept as they are.** Safe Harbor requires ages 90 and over to be grouped
  (e.g. "90+"); do it before sharing.
- **Shifted dates keep a day and a month.** Safe Harbor removes every date element except the
  year; date shifting is a different method (typically justified by an expert determination
  or used within a limited data set). Dates the script cannot parse become `[DATE_SHIFTED]`.
- **Names in text are not found.** Free-text columns are REVIEW_NEEDED and, if anonymized,
  replaced as a whole. A name in a short comment column can still be classified SAFE: the
  review shows every column's sample values so the researcher can catch it.
- **Rare combinations are not assessed.** Small cells, rare diagnoses, or quasi-identifiers
  (age + sex + ZIP + admission month) can identify a patient; no k-anonymity check is run.
- **Geography is only as fine as the patterns.** Addresses and postcodes are detected per
  locale; truncating ZIP codes to three digits (Safe Harbor) is not done.
- **Known limits — bare 5-digit US ZIP codes:** a ZIP column is caught by its name (`zip`,
  `zipcode`, `zip_code`) or by the ZIP+4 form (`94110-1234`). A bare 5-digit value cannot be
  told apart from other 5-digit codes (e.g. procedure codes), so a ZIP column under another
  name can be classified SAFE: check the sample values in review.
- **Known limits — dates:** these spellings are still classified SAFE: month-first with a
  dash (`Mar-15-2024`), year-first with a month word (`2024-Mar-15`), month and year only
  (`March 2024`), non-English month words (`15 mars 2024`, `15. März 2024`), and two-digit-year
  day/month dates outside the `us` locale (`15/03/24` under `uk`). Under `us`, any
  `M/D/YY`-shaped value (e.g. `1/2/10`) is treated as a date, so a column of such
  three-part numbers is flagged PHI/date.
- **Not detected:** URLs, IP addresses, account, licence, vehicle and device numbers (fax
  numbers only where they look like the locale's phone numbers), and identifiers written in
  column names or file names. Only the first sheet of an Excel file is processed (the other
  sheets are not written to the output).

## Scope and Limitations

**Supported (v1)**:
- Structured tabular data: CSV, TSV, Excel (.xlsx)
- 11 country locales with country-specific PHI patterns:
  - Korea (kr): RRN (주민번호), phone, email, address, Hangul names, dates
  - USA (us): SSN, US phone, US address, zip codes
  - Japan (jp): マイナンバー, Japanese phone, 都道府県 address, Kanji names
  - China (cn): 身份证号, Chinese phone, 省市区 address, Chinese names
  - Germany (de): Steuer-ID, German phone, Straße address
  - UK (uk): NHS Number, NI Number, UK phone, postcodes
  - France (fr): NIR/INSEE, French phone, Rue address
  - Canada (ca): SIN, Canadian phone, postal codes
  - Australia (au): TFN, Medicare number, AU phone
  - India (in): Aadhaar, PAN, Indian phone, pin codes
  - Italy (it): Codice Fiscale, Italian phone, Via address
- Universal patterns (all locales): email, ISO dates, high-cardinality numeric IDs (MRN)
- English column names recognized across all locales
- Custom locale support via `--locale-file` with template
- Pseudonymization, date shifting, ID replacement, suppression

**NOT supported (planned for v2)**:
- DICOM image metadata (PS3.15 Annex E) — requires pydicom
- Clinical free-text NER (clinical notes, radiology reports)
- Automated k-anonymity / l-diversity assessment
- SPSS (.sav), SAS (.sas7bdat), or other statistical formats

## Anti-Hallucination

- **Never fabricate file paths, URLs, DOIs, or package names.** Verify existence before recommending.
- **Never invent journal metadata, impact factors, or submission policies** without verification at the journal's website.
- If a tool, package, or resource does not exist or you are unsure, say so explicitly rather than guessing.
