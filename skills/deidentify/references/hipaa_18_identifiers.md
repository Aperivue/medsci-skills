# HIPAA Safe Harbor: 18 Identifiers

Reference for the `deidentify` skill.  Based on HIPAA Privacy Rule 164.514(b)(2).

## Identifier List

| # | Identifier | Script action | Manual review needed |
|---|-----------|--------------|---------------------|
| 1 | Names | Pseudonymize (P0001, P0002...) in columns named as names | Yes — names inside free text or comments are not found |
| 2 | Geographic data (< state) | Suppress addresses/postcodes the locale pack matches | Yes — ZIP codes are not truncated to 3 digits |
| 3 | Dates (except year) | Date shift (per-patient offset); day and month remain | Yes — Safe Harbor keeps the year only |
| 4 | Ages > 89 | **Not done** — ages are kept as they are | Yes — group ages 90 and over yourself |
| 5 | Telephone numbers | Suppress | No |
| 6 | Fax numbers | Suppress, only where they match the phone patterns | Yes |
| 7 | Email addresses | Suppress | No |
| 8 | Social Security numbers | Suppress | No |
| 9 | Medical record numbers | Replace (ID0001, ID0002...) | Yes — unnamed numeric ID columns are REVIEW_NEEDED |
| 10 | Health plan beneficiary numbers | Suppress, only in columns named as insurance numbers | Yes |
| 11 | Account numbers | **Not detected** | Yes |
| 12 | Certificate/license numbers | **Not detected** | Yes |
| 13 | Vehicle identifiers | **Not detected** | Yes |
| 14 | Device identifiers | **Not detected** | Yes |
| 15 | Web URLs | **Not detected** | Yes |
| 16 | IP addresses | **Not detected** | Yes |
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
- The script detects items 1-3, 5, 7-9 via column names and value patterns, item 10 via
  column names only, and item 6 only where a fax number looks like a phone number. It does
  not detect items 11-16 and does not generalize ages (item 4); the researcher handles these
  before the dataset is described as Safe Harbor de-identified.
- Safe Harbor also covers "any other unique identifying number, characteristic, or code".
  The script flags unnamed columns of unique numbers as REVIEW_NEEDED; other codes are not
  recognized.
