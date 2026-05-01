# Citation Styles (CSL)

Journal-specific Citation Style Language files for pandoc citeproc rendering.
Source: https://github.com/citation-style-language/styles (zotero/styles).

## Bundled CSLs

| File | Use for | Notes |
|------|---------|-------|
| `european-radiology.csl` | European Radiology, EURE | Dependent on `springer-basic-brackets.csl` (must be in same dir) |
| `cardiovascular-and-interventional-radiology.csl` | CVIR | Dependent on `springer-vancouver-brackets.csl` |
| `radiology.csl` | Radiology (RSNA) | Independent. Also acceptable fallback for Radiology: AI when no dedicated CSL exists |
| `american-journal-of-roentgenology.csl` | AJR | Independent |
| `korean-journal-of-radiology.csl` | KJR | Vancouver-superscript variant |
| `vancouver.csl` | Generic Vancouver (brackets) | Fallback when journal CSL unavailable (e.g., JVIR, Radiology: AI) |
| `vancouver-superscript.csl` | Generic Vancouver (superscript) | Alternative fallback |
| `springer-basic-brackets.csl` | Parent of European Radiology | Do not use directly — keep co-located |
| `springer-vancouver-brackets.csl` | Parent of CVIR | Do not use directly — keep co-located |

## Missing — use fallback

- **Radiology: Artificial Intelligence (RYAI)**: no dedicated CSL on zotero/styles as of 2026-04. Use `radiology.csl` (parent journal, identical RSNA house style).
- **Journal of Vascular and Interventional Radiology (JVIR)**: no dedicated CSL. Use `vancouver.csl` and verify against latest author guidelines before submission.

## Updating

```bash
cd "$(dirname "$0")"
for s in european-radiology radiology american-journal-of-roentgenology \
         cardiovascular-and-interventional-radiology korean-journal-of-radiology \
         vancouver vancouver-superscript \
         springer-basic-brackets springer-vancouver-brackets; do
  curl -fsSL -o "${s}.csl" "https://www.zotero.org/styles/${s}"
done
```

Verify dependent-parent links if Springer reorganizes:
```bash
grep -H independent-parent *.csl
```
