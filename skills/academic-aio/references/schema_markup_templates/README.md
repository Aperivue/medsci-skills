# Schema.org JSON-LD Templates

Embed-ready JSON-LD markup for academic-aio Section 5 (GitHub / CITATION.cff / Zenodo / Hugging Face) and Section 6 (author landing page). Schema.org markup is read by Google Scholar's structured-data parser, by AI overview engines, and by RAG systems that crawl repository pages.

## Files

- **`ScholarlyArticle.jsonld`** — embed in the paper landing page or repository README. Pairs each paper with DOI, PMID, abstract, license, OA flag, and citation graph anchors.
- **`CodeRepository.jsonld`** — embed in the repository README or as `.well-known/scholarly.jsonld`. Links code to its parent article via `isPartOf`.
- **`Dataset.jsonld`** — embed at the Zenodo or Hugging Face dataset landing page. Includes provenance, license, and variable-level metadata.
- **`Person.jsonld`** — embed at the author landing page or institutional profile. Cross-links ORCID, Scholar, Semantic Scholar, GitHub, Hugging Face, LinkedIn.

## How to embed

### In a Markdown README (GitHub renders the HTML script tag inside HTML blocks)

```html
<script type="application/ld+json">
{ ... contents of ScholarlyArticle.jsonld ... }
</script>
```

### In a personal landing page

Place the script tag in the `<head>` of the HTML page. For static-site generators (Hugo, Jekyll, Next.js), generate the JSON-LD at build time from frontmatter.

### Validation

Run `scripts/validate_schema.py path/to/file.jsonld` to verify syntactic validity and required-field presence before deploy.

```bash
python scripts/validate_schema.py references/schema_markup_templates/*.jsonld
```

## Anti-hallucination

- Do not auto-fill placeholder values (`<First Last>`, `0000-0000-0000-0000`, `10.xxxx/yyyy`). Mark unknown fields as `null` or remove the field — partial fabricated identifiers are worse than missing ones.
- Verify DOI format `10.{prefix}/{suffix}` and ORCID format before commit.

## Related

- `SKILL.md` Section 5 — README, CITATION.cff, Zenodo, Hugging Face
- `SKILL.md` Section 6 — Authority and E-E-A-T signals
- `SKILL.md` Section 7 — Citation-fabrication defense
