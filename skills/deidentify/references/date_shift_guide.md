# Date Shifting Guide

## What is Date Shifting?

Date shifting replaces actual dates with shifted dates, preserving the relative time
intervals between events for the same patient.  This maintains temporal relationships
(e.g., "surgery was 3 days after admission") while removing the absolute dates that
could identify individuals.

## SANT Method (Shift and Truncate)

The recommended approach, used by PCORI Clinical Data Research Networks:

1. **Generate offset**: For each patient, draw a random integer from [-365, +365] days
2. **Apply uniformly**: Shift ALL dates for that patient by the same offset
3. **Truncate edges**: Remove records near dataset boundaries where shifting would
   push dates outside the study period

### Why per-patient offset?

- Preserves relative intervals between events for the same patient
- "Admission → Surgery → Discharge" intervals remain exact
- Different patients get different offsets (prevents cross-patient inference)

## Implementation Details

### Seed Management

- A random seed is generated once per run and stored in `mapping.json`
- This makes the shifting deterministic and reproducible
- Re-running with the same seed on the same data produces identical results
- The seed should be kept as securely as the mapping file itself

### Entity Identification

The script looks for a patient/entity ID column to group dates:
1. Columns classified as `id` type (차트번호, MRN, patient_id, etc.)
2. If no ID column exists, all dates are shifted by the same global offset

### Supported Date Formats

| Format | Example | Preserved |
|--------|---------|-----------|
| ISO | 2024-03-15 | Yes |
| Dot-separated | 2024.03.15 | Yes |
| Slash-separated | 2024/03/15 | Yes |
| Compact | 20240315 | Yes |
| Korean | 2024년 3월 15일 | Yes |

### Unparseable Dates

If a date string cannot be parsed by any known format, it is replaced with
`[DATE_SHIFTED]` rather than left unchanged (fail-safe).

## When NOT to Date Shift

- **Study-level dates** that are already public (e.g., "data collected 2020-2023")
- **Seasonal analyses** where month or season is a study variable
- **Age at event**: Calculate age before shifting, then shift the dates

## Edge Cases

- **Impossible dates after shift**: Feb 30 → script uses Python datetime which
  handles month-end overflow (raises ValueError → caught and adjusted)
- **Leap years**: Feb 29 shifted to a non-leap year → becomes Feb 28
- **Cross-year boundaries**: Handled correctly by timedelta arithmetic
- **Negative ages**: If birth date is shifted forward past an event date,
  the relative interval (age at event) is still preserved

## Re-identification Risk

Even with date shifting, be aware:
- Rare diseases + approximate date range can still narrow candidates
- If attacker knows the shift range (±365), they have a 730-day window
- For very small populations, consider larger shift ranges or year-only dates

## References

- Hripcsak G, et al. "Bias Associated with Mining Electronic Health Records."
  J Biomed Inform. 2011;44(6):1120-1126. (Temporal relationship preservation)
- Meystre SM, et al. "Automatic De-identification of Textual Documents in the
  Electronic Health Record." BMC Med Res Methodol. 2010;10:70.
