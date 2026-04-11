# HIPAA Safe Harbor: 18 Identifiers

Reference for the `deidentify` skill.  Based on HIPAA Privacy Rule 164.514(b)(2).

## Identifier List

| # | Identifier | Script action | Manual review needed |
|---|-----------|--------------|---------------------|
| 1 | Names | Pseudonymize (P001, P002...) | No |
| 2 | Geographic data (< state) | Suppress | Yes — ZIP first 3 digits may be kept if population >= 20,000 |
| 3 | Dates (except year) | Date shift (per-patient offset) | No |
| 4 | Ages > 89 | Generalize to "90+" | No |
| 5 | Telephone numbers | Suppress | No |
| 6 | Fax numbers | Suppress | No |
| 7 | Email addresses | Suppress | No |
| 8 | Social Security numbers | Suppress | No |
| 9 | Medical record numbers | Replace (ID001, ID002...) | No |
| 10 | Health plan beneficiary numbers | Suppress | No |
| 11 | Account numbers | Suppress | Yes — rare in research data |
| 12 | Certificate/license numbers | Suppress | Yes — rare in research data |
| 13 | Vehicle identifiers | Suppress | Yes — only in trauma data |
| 14 | Device identifiers | Suppress | Yes — only in device studies |
| 15 | Web URLs | Suppress | No |
| 16 | IP addresses | Suppress | No |
| 17 | Biometric identifiers | N/A (not in tabular data) | N/A |
| 18 | Full-face photographs | N/A (not in tabular data) | N/A |

## Korean Equivalents

| HIPAA identifier | Korean equivalent | 한국 개인정보보호법 분류 |
|-----------------|-------------------|----------------------|
| Names | 성명 | 고유식별정보 |
| SSN | 주민등록번호 | 고유식별정보 |
| MRN | 차트번호/의무기록번호 | 개인정보 |
| Phone | 전화번호/연락처 | 개인정보 |
| Address | 주소 | 개인정보 |
| DOB | 생년월일 | 개인정보 |
| Email | 이메일 | 개인정보 |
| Insurance no. | 건강보험증 번호 | 고유식별정보 |

## Notes

- Items 17-18 (biometrics, photos) are outside the scope of this tool (tabular data only).
- Items 11-14 (accounts, certificates, vehicles, devices) are rare in clinical research datasets
  but should be flagged if column names suggest their presence.
- For Korean data, 주민등록번호 is the most critical direct identifier (combines birthdate + gender).
- The script detects items 1-10 and 15-16 via column names and regex patterns.
  Items 11-14 rely on column-name heuristics only.
