# stard Exemplars

This directory will hold 3–5 hand-curated stard flow/figure exemplars.
Use the extraction script to add one:

```bash
python skills/make-figures/scripts/extract_exemplar_from_pdf.py \
    --pdf "/path/to/paper.pdf" \
    --page N \
    --type stard \
    --label LastnameYEAR_STARD \
    --doi 10.xxxx/yyyy
```

See `../README.md` for curation guidelines.
