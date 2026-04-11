# Publication Table Tools — Comparison

## R Packages

| Feature | gtsummary | gt | flextable | tableone | kableExtra | huxtable |
|---|---|---|---|---|---|---|
| **Primary Use** | Table 1 + regression | Fine styling | Word output | Quick Table 1 | LaTeX/PDF | Multi-format |
| **Auto Statistics** | Yes (test selection) | No | No | Yes (p, SMD) | No | huxreg() only |
| **Journal Themes** | JAMA, Lancet, NEJM | No | Custom | No | No | No |
| **Footnotes** | Via gt engine | Native (excellent) | Native | Manual | Native | Native |
| **Word Output** | Via flextable | Limited | **Best** | Via knitr | Limited | Yes |
| **LaTeX Output** | Via huxtable | Native | Limited | Via knitr | **Best** | Native |
| **HTML Output** | Via gt | **Best** | Yes | Via knitr | Yes | Yes |
| **Maintenance** | Active (MSKCC) | Active (Posit) | Active | Maintenance | Maintenance | Maintenance |

## Python Libraries

| Feature | great_tables | tableone (py) | python-docx | pandas Styler |
|---|---|---|---|---|
| **Primary Use** | gt port | Quick Table 1 | Word tables | HTML/LaTeX |
| **Auto Statistics** | No | Yes (p, SMD) | No | No |
| **Journal Themes** | No | No | No | No |
| **Footnotes** | tab_footnote() | No | Manual | No |
| **Word Output** | No | No | **Native** | No |
| **LaTeX Output** | No | Via export | No | to_latex() |
| **Maturity** | Growing | Stable | Stable | Built-in |

## Recommended Pipelines

### Best: R gtsummary → Word
```r
theme_gtsummary_journal("jama")
theme_gtsummary_compact()
tbl %>% as_flex_table() %>% flextable::save_as_docx(path = "table.docx")
```

### Best: R gtsummary → LaTeX
```r
tbl %>% as_hux_table() %>% huxtable::to_latex()
# OR
tbl %>% as_gt() %>% gt::gtsave("table.tex")
```

### Python-only (acceptable, not ideal)
```python
# Generation
from tableone import TableOne
table1 = TableOne(df, columns=cols, categorical=cats, groupby='group', pval=True)
# Export to CSV, then format with python-docx
```

## Key Insight
> **Python lacks gtsummary-equivalent journal themes and auto-statistics.**
> For publication tables in medical journals, R is strongly preferred.
> Python pipelines require manual style adjustments that R handles automatically.

## Tool Selection Decision Tree

```
Need Table 1 or regression table?
  → gtsummary (+ journal theme)

Need pixel-perfect custom styling?
  → gt (HTML) or flextable (Word)

Submitting to Word-only journal?
  → gtsummary → as_flex_table() → save_as_docx()

Submitting LaTeX?
  → gtsummary → as_hux_table() → to_latex()
  → OR kableExtra for direct LaTeX control

Python-only constraint?
  → tableone (generation) + python-docx (formatting)
  → Accept manual style work

Quick exploratory table?
  → tableone (R or Python) — fastest setup
```
