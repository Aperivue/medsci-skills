# Korean PHI Patterns

Regex patterns and column-name dictionaries used by `deidentify.py`.
This file serves as documentation; the actual patterns are in the Python script.

## Value-Level Regex Patterns

### 주민등록번호 (Resident Registration Number)

```
\d{6}-[1-4]\d{6}
```

- Format: `YYMMDD-GNNNNNN`
- First 6 digits: birthdate (YYMMDD)
- 7th digit (G): gender + birth century (1=1900s male, 2=1900s female, 3=2000s male, 4=2000s female)
- Remaining 6: region code + serial + check digit
- Example: `850315-1234567`

### 외국인등록번호 (Alien Registration Number)

```
\d{6}-[5-8]\d{6}
```

- Same format as 주민번호 but 7th digit is 5-8
- Covered by the same regex when expanded to `[1-8]`

### 전화번호 — 휴대전화 (Mobile Phone)

```
01[016789]-?\d{3,4}-?\d{4}
```

- Prefixes: 010, 011, 016, 017, 018, 019
- Dashes optional
- Examples: `010-1234-5678`, `01012345678`, `011-234-5678`

### 전화번호 — 유선전화 (Landline)

```
0[2-6][0-9]{0,2}-?\d{3,4}-?\d{4}
```

- Area codes: 02 (Seoul), 031-033 (Gyeonggi), 041-044 (Chungcheong), 051-055 (Gyeongsang), 061-064 (Jeolla/Jeju)
- Examples: `02-555-1234`, `031-765-4321`, `051-234-5678`

### 이메일 (Email)

```
[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}
```

- Standard email pattern
- Common Korean domains: naver.com, daum.net, hanmail.net, kakao.com

### 날짜 (Date)

ISO format:
```
(19|20)\d{2}[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])
```

Korean format:
```
(19|20)\d{2}년\s*(0?[1-9]|1[0-2])월\s*(0?[1-9]|[12]\d|3[01])일
```

Short (YYMMDD):
```
([5-9]\d|0[0-4])(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])
```

### 주소 (Address)

Korean address suffix pattern:
```
(특별시|광역시|특별자치시|특별자치도|도\s|시\s|군\s|구\s|읍\s|면\s|동\s|리\s|로\s|길\s)
```

- Matches administrative divisions that appear in Korean addresses
- Detection threshold: >30% of values in a column contain these patterns

### 한국인 이름 (Korean Name)

```
[\uAC00-\uD7AF]{2,4}
```

- 2 to 4 Hangul syllable characters
- **CRITICAL**: Only applied to columns identified as name-type by column name
- Common Korean words (정상, 양성, 음성, etc.) also match this pattern
- False positive mitigation: match against column name hints only

## Column Name Dictionary

### Name-type columns
`환자명`, `성명`, `이름`, `성함`, `patient_name`, `patientname`, `pt_name`, `name`,
`first_name`, `last_name`

### RRN-type columns
`주민번호`, `주민등록번호`, `ssn`, `social_security`

### Date-type columns
`생년월일`, `생년`, `출생일`, `dob`, `date_of_birth`, `birth_date`, `birthdate`

### Phone-type columns
`전화번호`, `연락처`, `핸드폰`, `휴대폰`, `휴대전화`, `자택전화`,
`phone`, `telephone`, `mobile`, `phone_number`, `cell`

### Address-type columns
`주소`, `자택주소`, `거주지`, `address`, `home_address`, `street`,
`zip`, `zipcode`, `zip_code`

### Email-type columns
`이메일`, `email`, `email_address`

### ID-type columns
`차트번호`, `등록번호`, `환자번호`, `의무기록번호`, `원무번호`,
`mrn`, `medical_record`, `chart_no`, `patient_id`, `patientid`,
`chart_number`, `record_number`, `hospital_id`

### Insurance-type columns
`보험번호`, `insurance_no`, `insurance_number`

## High-Cardinality Numeric Detection

Columns not matching any name pattern but containing:
- >90% pure numeric values (digits only)
- Length >= 5 digits
- >80% unique values

These are flagged as potential MRN/chart numbers for researcher review.
