# consort Exemplars

This directory will hold 3–5 hand-curated consort flow/figure exemplars.
Use the extraction script to add one:

```bash
python skills/make-figures/scripts/extract_exemplar_from_pdf.py \
    --pdf "/path/to/paper.pdf" \
    --page N \
    --type consort \
    --label LastnameYEAR_CONSORT \
    --doi 10.xxxx/yyyy
```

See `../README.md` for curation guidelines.
