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
| `korean-journal-of-radiology.csl` | KJR | Independent. Parenthesised numbers `(1, 2)`, et-al after 6 (first 6 + et al) — **not** superscript |
| `american-medical-association.csl` | AMA Manual of Style 11th ed. — JAMA family, and any journal citing "AMA style" | Independent. Superscript, et-al after 6 (first 3 + et al), DOI kept |
| `liver-international.csl` | Liver International (Wiley) | AMA-style superscript: et-al after 6 (first 3 + et al), no PMID, DOI kept. Also a fallback for Wiley/AMA "first-3-et-al" superscript journals |
| `journal-of-cachexia-sarcopenia-and-muscle.csl` | JCSM | Independent. Superscript, et-al after 6 (first 6 + et al) |
| `nature.csl` | Nature portfolio | Independent. Superscript, et-al after 5 (first 1 + et al) |
| `journal-of-korean-medical-science.csl` | JKMS | Dependent on `nlm-citation-sequence.csl` (must be in same dir) |
| `journal-of-korean-medical-science-strict.csl` | JKMS, strict variant | Independent. Superscript NLM citation-sequence, et-al after 6 (first 6 + et al) |
| `vancouver.csl` | Generic Vancouver (brackets) | Fallback when journal CSL unavailable (e.g., JVIR, Radiology: AI) |
| `vancouver-superscript.csl` | Generic Vancouver (superscript) | Alternative fallback |
| `springer-basic-brackets.csl` | Parent of European Radiology | Do not use directly — keep co-located |
| `springer-vancouver-brackets.csl` | Parent of CVIR | Do not use directly — keep co-located |
| `nlm-citation-sequence.csl` | Parent of JKMS | Do not use directly — keep co-located |

## Missing — use fallback

- **Radiology: Artificial Intelligence (RYAI)**: no dedicated CSL on zotero/styles as of 2026-04. Use `radiology.csl` (parent journal, identical RSNA house style).
- **Journal of Vascular and Interventional Radiology (JVIR)**: no dedicated CSL. Use `vancouver.csl` and verify against latest author guidelines before submission.

## Updating

Only the files below are verbatim upstream styles, so only these may be refreshed by slug:

```bash
cd "$(dirname "$0")"
for s in european-radiology radiology american-journal-of-roentgenology \
         cardiovascular-and-interventional-radiology korean-journal-of-radiology \
         american-medical-association journal-of-cachexia-sarcopenia-and-muscle nature \
         journal-of-korean-medical-science nlm-citation-sequence \
         springer-basic-brackets springer-vancouver-brackets; do
  curl -fsSL -o "${s}.csl" "https://www.zotero.org/styles/${s}"
done
```

**Do not refresh these by filename** — they are locally renamed or locally modified copies whose
`<id>` does not match their filename, so fetching `zotero.org/styles/<filename>` would replace them
with a different style:

| File | Actual `<id>` slug | Caught by the check below? |
|------|--------------------|---------------------------|
| `vancouver.csl` | `nlm-citation-sequence` | yes |
| `vancouver-superscript.csl` | `nlm-citation-sequence-superscript` | yes |
| `liver-international.csl` | `nlm-citation-sequence-superscript` (locally retitled) | yes |
| `journal-of-korean-medical-science-strict.csl` | `journal-of-korean-medical-science-strict` | **no** — the slug matches the filename, but the style is locally authored (its `<title>` is a description, not a journal name). Confirm the slug resolves upstream before refreshing it |

Check which files are safe to refresh (filename must equal the `<id>` slug):
```bash
for f in *.csl; do
  slug=$(sed -n 's:.*<id>.*/\([^/<]*\)</id>.*:\1:p' "$f" | head -1)
  [ "$slug" = "${f%.csl}" ] || echo "LOCAL VARIANT: $f -> $slug"
done
```

Verify dependent-parent links if an upstream publisher reorganizes:
```bash
grep -H independent-parent *.csl
```
