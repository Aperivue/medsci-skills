# Publication Table Standards — Knowledge Base

> Reference document for medical journal table formatting.
> Source: YouTube tutorials, journal author guidelines, AMA Manual of Style, tool documentation.
> Last updated: 2026-04-11

---

## 1. Universal Rules (All Medical Journals)

1. **No vertical lines** — horizontal rules only (top, below header, bottom)
2. **Editable Word tables** — use Word Insert > Table. Never submit images, Excel, or PDF
3. **Sequential numbering** — Table 1, 2, 3... in order of first citation in text
4. **Define all abbreviations** — in footnotes, independently for each table
5. **Explanatory content in footnotes, not headings**
6. **Display item limit** — most journals: tables + figures combined 4-5
7. **Exact P values** — never just "significant/not significant"
8. **Variability measures required** — always state mean (SD) or median (IQR)
9. **Self-contained titles** — table title alone must convey content without reading text
10. **No duplication** — tables and figures must not repeat the same data

---

## 2. Journal-Specific Differences

### Footnote Markers

| Journal Family | Marker System | Order |
|---|---|---|
| AMA (Radiology, JAMA, AJR, Rad:AI) | Superscript lowercase letters | a, b, c, d... |
| NEJM | Symbols | *, †, ‡, §, ‖, ¶, **, ††... |
| Lancet | Symbols | *, †, ‡, §, ¶, ‖, **, ††... |
| European Radiology (Springer) | Superscript lowercase letters + asterisks for significance | a, b, c... and *, **, *** |

### P Value Formatting

| Journal | Case | Leading Zero | Examples |
|---|---|---|---|
| Radiology / JAMA / AJR / Rad:AI | Uppercase italic *P* | No | *P* = .03, *P* < .001 |
| NEJM | Uppercase *P* | No | *P* = .04, *P* < .001 |
| Lancet | Lowercase p | Yes | p = 0.03, p < 0.0001 |
| European Radiology | Lowercase p (Springer) | Varies | p = 0.03 |

### P Value Decimal Places

| Value Range | JAMA/Radiology | NEJM | Lancet |
|---|---|---|---|
| > .01 | 2 decimals (.04) | 2 decimals (.04) | 2 sig figs (0.04) |
| .01-.001 | 3 decimals (.003) | 3 decimals (.003) | Up to 4 decimals (0.0023) |
| < .001 | *P* < .001 | *P* < .001 | p < 0.0001 |

### Horizontal Lines

| Journal | Rule |
|---|---|
| AMA journals | Top, below header, bottom. Additional sparingly |
| NEJM | Minimize even internal horizontal lines |
| Lancet | Exactly 3: top, below header, bottom |

### 95% CI Format

| Journal | Format |
|---|---|
| Radiology | (XX, XX) — comma separator |
| JAMA | XX to XX — "to" separator |
| Lancet | XX to XX or XX-XX |
| NEJM | XX to XX |

### Table Title Format

| Journal | Format |
|---|---|
| AMA journals | **Table N.** Title in regular weight (bold "Table N." only) |
| NEJM | Table N. Title |
| Lancet | Table N: Title |

---

## 3. AMA Manual of Style (11th Ed) — Table Rules

### Structure
- **Column headers**: Bold
- **Row headers (stub)**: Regular weight, sentence case
- **Decking** (nested column headers): Maximum 3 levels
- **Alignment**: Text = left-aligned, Numbers = center or decimal-aligned
- **Units**: In column header parentheses, not repeated in cells
- **Maximum size**: ~40 rows x 6-8 columns, fit within 1 page

### Footnote System (AMA 11th)
- **Table footnotes**: Superscript lowercase letters (a, b, c...)
- **NOT symbols** — symbols (*, †, ‡) are for bottom-of-page text footnotes only
- **Assignment order**: Top-to-bottom, left-to-right through the table
- **Whole-table footnote**: Place superscript "a" at end of table title
- **Reference numbers + footnotes**: Reference first, comma, then footnote letter (e.g., 5,b)

### Footnote Placement Order
```
Below the table, in this sequence:

1. General note (no marker, applies to entire table)
   "Data are presented as median (IQR) unless otherwise noted."

2. Abbreviation note
   "ASA = American Society of Anesthesiologists, BMI = body mass index,
    CI = confidence interval."
   → Listed in order of appearance in table (left→right, top→bottom)
   → Some journals (JAMA) require alphabetical order — check guide

3. Specific notes (superscript letter markers)
   "a Excludes patients with missing follow-up data."
   "b Adjusted for age and sex."

4. Probability notes (asterisk markers, if used)
   "* P < .05; ** P < .01."
```

### P Value Rules
- Uppercase italic: *P*
- No leading zero: .05, not 0.05
- Thin space around operators: *P* = .03
- Only *P*, *α*, *β* omit leading zero; all other statistics keep it

---

## 4. Footnote System Specification

### When to Use Symbols vs Letters vs Numbers

| System | Markers | Use Case | Journals |
|---|---|---|---|
| Lowercase letters | a, b, c... | **Table footnotes (standard)** | AMA journals, EUR, most |
| Symbols | *, †, ‡, §, ‖, ¶ | Table footnotes (traditional) | NEJM, Lancet |
| Asterisks only | *, **, *** | **Probability notes only** | Springer journals |
| Uppercase letters | A, B, C... | Table footnotes | JCI |
| Numbers | 1, 2, 3... | Non-numeric tables only | Rarely used (confusion with references) |

### Caption vs Footnote — What Goes Where

| Content | Caption (above table) | Footnote (below table) |
|---|---|---|
| Table title | Yes | No |
| Study period/setting | Yes (brief) | No |
| Abbreviation definitions | No | **Yes** (first footnote) |
| Statistical test descriptions | No | **Yes** |
| P value thresholds | No | **Yes** (probability note) |
| Data source | No | **Yes** (source note) |
| Missing data explanation | No | **Yes** (specific note) |
| Sample size (N) | Column header or caption | Footnote (supplementary) |

### Statistical Test Footnote Patterns

**Pattern A — Individual markers (preferred when tests vary by row):**
```
Age, y                    65.3 (12.1)    62.1 (11.8)    .04ᵃ
Sex, male                 53 (52)        48 (47)        .41ᵇ

ᵃ Wilcoxon rank-sum test.
ᵇ Fisher exact test.
```

**Pattern B — General note (preferred when same test for all rows of a type):**
```
P values were calculated using the Wilcoxon rank-sum test for continuous
variables and the Fisher exact test for categorical variables.
```

---

## 5. Common Mistakes Checklist

### Structure
- [ ] Binary variables: show only one level (Male 53%, not Male 53% / Female 47%)
- [ ] Remove derivable columns (Total column when groups are shown)
- [ ] Keep tables under 50 rows (excess → supplementary)
- [ ] No sub-part numbering (Table 3A/3B → Table 3, Table 4)
- [ ] Do not repeat all table data in Results text

### Formatting
- [ ] Consistent decimal places within each column
- [ ] Units in column headers, not in cells
- [ ] No vertical lines, minimal horizontal lines
- [ ] Numbers right-aligned or center-aligned (not left)
- [ ] Specify variability: "Mean (SD)" or "Median (IQR)" in header or footnote

### Statistics
- [ ] RCTs: P values in Table 1 are usually unnecessary (randomization)
- [ ] Always name the statistical test (in footnote or general note)
- [ ] Report effect sizes per clinically meaningful unit (OR per 10-year, not per 1-year)
- [ ] CI notation consistent throughout (parentheses vs "to" — match journal style)
- [ ] Never use "NS" — report exact P values

### Submission
- [ ] Editable Word table (not image/screenshot)
- [ ] No color as sole information carrier (use bold/italic/symbols instead)
- [ ] All abbreviations defined in footnotes
- [ ] Each table's footnotes are self-contained (no "see Table 1 footnote")

---

## 6. Tool Recommendations

### Primary Pipeline: R {gtsummary}

**Why gtsummary:**
- Built-in journal themes: JAMA, Lancet, NEJM
- Auto-selects statistical tests (Wilcoxon, Fisher, Chi-square)
- Auto-generates footnotes (test names, summary statistics)
- Outputs to Word (via flextable), LaTeX (via huxtable), HTML (via gt)

**Core API:**
```r
library(gtsummary)

# Set journal theme FIRST
theme_gtsummary_journal("jama")  # or "lancet", "nejm"
theme_gtsummary_compact()

# Table 1
tbl <- df %>%
  tbl_summary(
    by = group,
    type = list(age ~ "continuous2"),
    statistic = list(
      all_continuous() ~ c("{mean} ({sd})", "{median} ({p25}, {p75})"),
      all_categorical() ~ "{n} ({p}%)"
    ),
    digits = list(all_continuous() ~ 1),
    missing = "ifany"
  ) %>%
  add_p() %>%
  add_overall() %>%
  add_stat_label() %>%
  bold_labels() %>%
  modify_footnote(all_stat_cols() ~ "Mean (SD); Median (Q1, Q3); n (%)")

# Export
tbl %>% as_flex_table() %>% flextable::save_as_docx(path = "table1.docx")
tbl %>% as_hux_table() %>% huxtable::to_latex() %>% writeLines("table1.tex")
```

**Regression table:**
```r
model <- glm(outcome ~ age + sex + bmi, data = df, family = binomial)

tbl_regression(model, exponentiate = TRUE) %>%
  add_global_p() %>%
  bold_p(t = 0.05) %>%
  bold_labels()
```

### Supporting Tools

| Tool | Role | When to Use |
|---|---|---|
| gt | Fine-grained styling | Cell-level colors, custom footnote marks, heatmaps |
| flextable | Word output engine | Final DOCX formatting, autofit, borders |
| huxtable | LaTeX output engine | LaTeX code extraction |
| tableone (R/Python) | Quick exploratory Table 1 | Early drafts, data exploration |
| python-docx | Python Word tables | When pipeline is Python-only |
| great_tables | Python gt port | Growing but immature for medical use |

### Python Limitation
Python has no equivalent to gtsummary's journal themes or automatic statistical test selection. For publication tables, R is strongly recommended. Python-only pipelines should use tableone for generation + python-docx for Word formatting, accepting manual style adjustments.

---

## 7. Format-Specific Notes

### Word (DOCX) Submission
- Use Word's Insert > Table function (never tab-separated)
- Font: Times New Roman 10-12pt (table body can be 9-10pt)
- Single spacing within cells
- Remove all vertical borders; keep 3 horizontal lines
- Bold headers, regular body text
- Each table on a separate page, after References

### LaTeX Submission
- Use `booktabs` package (`\toprule`, `\midrule`, `\bottomrule`)
- Never use `\hline` or `|` vertical separators
- `\siunitx` for decimal alignment
- `\multirow` / `\multicolumn` for merged cells
- Generate via gtsummary → huxtable → to_latex() for consistency

### HTML (Review/Proofing)
- gt produces the highest quality HTML tables
- Useful for co-author review before final Word/LaTeX export
- Can include interactive features (sorting, filtering) for supplementary materials
