# Marked (tracked-changes) manuscript — verdicts, probes, upload failures

Companion to SKILL.md Phase 10. The build (`build_marked_manuscript.py`) and the round-trip gate
(`check_marked_manuscript.py`) commands live there.

## Verdicts

`MARKED_ACCEPT_MISMATCH`, `MARKED_REJECT_MISMATCH` (content dropped, duplicated, or invented), `MARKED_NO_REVISIONS` (Compare produced a clean copy), `MARKED_AUTHOR_MIXED`, `MARKED_TABLE_LOSS`, `MARKED_BASE_TRACKED` (a baseline still carrying live tracked changes, which makes the comparison ill-defined — accept or reject them first).

## A move is not an insert plus a delete

Word encodes relocated content as `w:moveFrom` / `w:moveTo`, and a verifier that knows only `w:ins` / `w:del` reconstructs the original with the moved paragraph in it *twice* — reporting a perfectly good file as corrupt. The gate resolves `revised = unchanged + w:ins + w:moveTo` and `original = unchanged + w:delText + w:moveFrom`. Any docx probe written here must walk exact `w:t` / `w:delText` elements, because the regex `<w:t[^>]*>` also matches `<w:tbl>`, `<w:tc>` and `<w:tr>`, silently swallowing table markup as prose.

## Upload failure on a large marked file

The marked file carries the baseline's embedded images as deleted content, so it can exceed a portal's size cap even when the clean file is small. First rule out the ordinary causes: the file is still open in Word (a `~$…docx` lock), the portal session expired, or the upload is transient — retry. If it is genuinely too large, downsample only `word/media/*` and repackage; tracked changes live in `word/document.xml` and are untouched. Re-run the gate afterwards and keep the full-resolution original as `*.full.docx`.
