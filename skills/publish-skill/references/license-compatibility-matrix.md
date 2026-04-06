# License Compatibility Matrix

Reference for determining whether third-party content can be bundled in an open-source skill package. This matrix assumes the target package uses the **MIT License** as its primary license.

## Compatible for Bundling

These licenses allow bundling inside an MIT-licensed package:

| License | Requirements | Notes |
|---------|-------------|-------|
| **CC0 / Public Domain** | None | Ideal for bundled references |
| **CC BY 4.0** | Attribution in file header | Most open-access academic content |
| **CC BY 3.0** | Attribution in file header | Older open-access content |
| **MIT** | Include license notice | Standard for code |
| **BSD 2-Clause / 3-Clause** | Include license notice | Common for scientific libraries |
| **Apache 2.0** | Include license + NOTICE file | Patent grant included |
| **ISC** | Include license notice | Simplified MIT equivalent |

### Attribution Template

When bundling CC BY content, add this header to the file:

```
<!-- 
  Source: [Title] by [Author(s)]
  License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
  Original: [URL]
  Modifications: [describe any changes, or "None"]
-->
```

---

## NOT Compatible for Bundling

These licenses conflict with MIT distribution. Convert to **URL references**.

| License | Conflict | Remediation |
|---------|----------|-------------|
| **CC BY-NC 4.0 / 3.0** | Non-commercial restriction incompatible with MIT | URL reference only |
| **CC BY-NC-ND** | Non-commercial + no-derivatives | URL reference only |
| **CC BY-ND** | No-derivatives prevents modifications | URL reference only |
| **CC BY-SA 4.0** | Copyleft: would require entire package to be CC BY-SA | URL reference only |
| **GPL v2 / v3** | Copyleft: would require entire package to be GPL | Optional external dependency |
| **LGPL** | Linking requirements | Optional external dependency |
| **Proprietary / All Rights Reserved** | No distribution rights | Remove entirely |
| **Unknown** | Assume incompatible | Remove or contact author |

---

## URL Reference Pattern

When content cannot be bundled, replace the file with a reference document:

```markdown
# [Resource Name]

> Not bundled due to license restrictions ([License Type]).

## Official Source

- **URL**: [direct link to official source]
- **Publisher**: [organization name]
- **License**: [license name and URL]

## How to Use

1. Download the resource from the official source above
2. Place it in this skill's `references/` directory as `[filename]`
3. The skill will automatically detect and use the local copy

## What This Skill Does Without It

When the resource is not locally available, the skill will:
- Use knowledge-based assessment instead of checklist-driven assessment
- Note in its output that the assessment was performed without the official checklist
- Recommend the user obtain the official resource for more thorough analysis
```

---

## Optional External Dependency Pattern

For GPL-licensed tools that the skill can use but does not require:

```markdown
## Optional: [Tool Name]

This skill can optionally use [Tool Name] for [specific feature].

- **License**: GPL v3
- **Install**: `pip install [package]` or `install.packages("[package]")`
- **Without it**: The skill will [describe fallback behavior]
```

---

## Common Academic Content Licenses

Quick reference for frequently encountered academic content:

| Content Type | Typical License | Bundleable? |
|-------------|----------------|-------------|
| PubMed abstracts | Public domain (US gov) | Yes |
| Open-access journal articles | CC BY 4.0 | Yes (with attribution) |
| STROBE checklist | CC BY 4.0 | Yes |
| STARD checklist | CC BY 4.0 | Yes |
| PRISMA 2020 checklist | CC BY 4.0 | Yes |
| ARRIVE 2.0 checklist | CC BY 4.0 | Yes |
| TRIPOD+AI checklist | CC BY 4.0 | Yes |
| CONSORT checklist | CC BY-NC 4.0 | No -- URL reference |
| CARE checklist | Exclusive rights (Elsevier) | No -- URL reference |
| SPIRIT checklist | CC BY-NC-ND | No -- URL reference |
| CLAIM checklist | License unverified | No -- URL reference |
| R `metafor` package | GPL v2 | Optional dependency |
| Python `lifelines` | MIT | Yes |
| Python `python-pptx` | MIT | Yes |
| Python `statsmodels` | BSD | Yes |

---

## Decision Flowchart

```
Is the content original (written by you)?
  YES → Bundleable under MIT
  NO  → What is its license?
          CC0 / CC BY / MIT / BSD / Apache → Bundle with attribution
          CC BY-NC / CC BY-ND / CC BY-SA   → URL reference only
          GPL / LGPL                        → Optional external dependency
          Unknown / Proprietary             → Remove or contact author
```
