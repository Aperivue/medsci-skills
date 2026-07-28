# Challenge — figure portal readiness (size + accepted format)

A figure bounces at the upload button after a long submission session, for one of two
deterministic reasons the author could have caught beforehand:

1. **Size cap** — JACC: Asia rejects a figure over **25 MB**, which a raw uncompressed
   600-dpi RGBA TIFF sails straight past.
2. **Format allowlist** — Springer Nature's SNAPP accepts only `.tiff` / `.jpeg` / `.eps`
   and **rejects the `.png`** a figure was rendered as.

Both are decidable from the file on disk — a byte size and an extension — so
`figure_portal_readiness_check.py` catches them at pre-flight. (The *fix* is to regenerate
with `/make-figures export_portal_tiff.py`: LZW + RGBA→RGB flatten.)

## What `verify.sh` asserts (network-free, stdlib, no committed binaries)

Fixtures are generated at runtime as byte files with figure extensions — the check reads
size and extension, never image content, so no real images are needed.

- **Format**: with `--accept tiff jpeg eps` (SNAPP), a `.png` is `FIGURE_FORMAT_REJECTED`
  while a `.tiff` is accepted; a non-image `.txt` in the same directory is ignored.
- **Size**: with a cap below a figure's size, that figure is `FIGURE_OVERSIZE`.
- **Clean** (no false positive): accepting `png`+`tiff` under the 25 MB default leaves every
  figure silent (exit 0).
- **Skip semantics** (via the pre-flight gate): with no figures directory the `figure_readiness`
  check is recorded `skipped`, never an error; it warns (P1) by default and only halts under
  `--strict`.
