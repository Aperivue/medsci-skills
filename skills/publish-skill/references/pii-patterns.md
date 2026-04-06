# PII Detection Patterns

Grep patterns for identifying personally identifiable information in Claude Code skills before open-source publication. All patterns are `grep -riE` compatible.

## How to Use

1. **Add your own identifiers** to the User-Specific section below before running
2. Run `audit_skill.sh <skill_directory>` or use these patterns manually with Grep
3. Every match must be resolved before publishing -- zero tolerance

---

## Universal Patterns

### Hardcoded Paths

```
/Users/[a-zA-Z]|/home/[a-zA-Z]|~/Documents|~/Desktop|~/Downloads|~/Projects
```

**Remediation**: Replace with `${CLAUDE_SKILL_DIR}` for bundled references, or use user-provided paths for output directories.

### Email Addresses

```
[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
```

**Remediation**: Remove entirely. If an email is needed for API registration, use a placeholder like `<your-email>`.

### IP Addresses and Internal URLs

```
\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|https?://[a-z]+\.(internal|local|corp)
```

**Remediation**: Remove or replace with `<your-server>`.

---

## Domain-Specific Patterns (Medical/Academic)

### Institutional References

```
SNUH|AMC|SMC|KAIST|SNU|ASAN|Mayo Clinic|Johns Hopkins|MGH|Charit
```

**Remediation**: Replace with "institution" or "medical center", or remove if not essential to the skill logic.

### Academic Roles with Names

```
professor\s+[A-Z][a-z]+|Prof\.\s+[A-Z]|Dr\.\s+[A-Z][a-z]+|PGY[0-9]|R[0-9]-[0-9]
```

**Remediation**: Replace with "researcher", "user", or "collaborator".

### Hospital-Specific Identifiers

```
IRB[- ]?\d|MRN[- ]?\d|patient[- ]?id|accession[- ]?number
```

**Remediation**: Use generic placeholders like `<IRB-number>`, `<patient-id>`.

---

## Language and Locale

### Hardcoded Language Preferences

```
in Korean|한국어로|Korean language|communicate in Korean|in Japanese|in Chinese|in English(?! for technical)
```

**Remediation**: Replace with "in the user's preferred language".

**Note**: Multilingual trigger keywords in the `triggers:` field are acceptable and encouraged for discoverability.

### Location-Specific References

```
Seoul|Busan|Tokyo|Beijing|서울|부산|울산|창원
```

**Remediation**: Remove or generalize to region/country level only if essential.

---

## User-Specific Patterns

**IMPORTANT**: Before each audit, add your personal identifiers below.

### Names (add yours)

```
# Example -- replace with your actual names:
# firstname|lastname|이름|성명|romanized_variants
```

### Institutional Affiliations (add yours)

```
# Example -- replace with your actual affiliations:
# university_name|hospital_name|lab_name|department
```

### Collaborator Names (add yours)

```
# Example -- replace with collaborator names that may appear:
# collaborator1|collaborator2|advisor_name
```

---

## False Positive Guidance

The following matches are typically safe to ignore:

| Pattern | Context Where It Is OK |
|---------|----------------------|
| `English` | "Use English for technical terms" -- this is a style guide, not locale hardcoding |
| `Korean` | In the `triggers:` field for discoverability |
| `professor` | Generic role description without a specific name attached |
| `/Users/` | In documentation explaining installation paths (not in skill logic) |
| `@` | In email-format examples clearly marked as placeholders |

When in doubt, flag the match for human review rather than auto-dismissing.
