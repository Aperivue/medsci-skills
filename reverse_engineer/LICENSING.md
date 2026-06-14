# Reverse-engineering: learn-then-synthesize licensing policy

This directory holds the tooling for a long-running program that studies open-access
(OA) papers and published peer reviews to improve the MedSci Skills suite (better
review probes, exemplars, rubrics, and detectors). This document is the **copyright
firewall** for that program. It is binding on every commit produced by the program.

## The one rule

**Learn from sources privately; publish only synthesis.**

- **Private (never committed):** raw OA PDFs, full-text article prose, full peer-review
  reports, figures/tables copied from papers, and any per-paper analysis that quotes
  source text. These live only under `_corpus/`, which is gitignored.
- **Public (committed to this repo):** distilled *ideas, structure, and facts* (which
  are not copyrightable expression) and *freshly authored synthetic prose/exemplars*
  written in the style of — never copied from — the originals.

If a candidate public artifact cannot be produced without copying source expression,
it does not get committed. Capture the *pattern*, author a *new* example.

## What "synthesis" may contain

| Allowed in public commits | Not allowed in public commits |
|---|---|
| Abstracted descriptions ("excellent Methods sections state the reference standard, its timing, and reader blinding in the first paragraph") | Verbatim or lightly-paraphrased sentences from a paper |
| Reviewer-concern *patterns* ("reviewers flag single-center external validation when authors claim generalizability") | A copied peer-review report, even excerpted |
| New synthetic exemplars authored from scratch | Cropped figures/tables from non-CC sources |
| Facts and numbers that are not creative expression (e.g., a guideline item exists) | A figure anchor from any source not verified CC-BY / CC0 |
| Figure anchors **only** from CC-BY / CC0 sources, with attribution | |

## The manifest gate

Every source that informs a public artifact must have a record in the corpus manifest
(`_corpus/manifest.json`, schema: `source_manifest.schema.json`). Each record carries:

- `license` / `license_url` — the source's actual license (verified per record).
- `verbatim_allowed` — default **false**.
- `public_reuse_policy` — default **`synthetic_only`**. `paraphrase_ok` and
  `cc_by_attribution` require a verified permissive license on that record.

`scripts/distill.py` refuses to emit a public artifact for a source whose manifest
record is missing or whose policy does not permit the intended reuse. A source with an
unverified or unknown license is **learn-only**: it may inform the maintainers' reading
but must not appear in any committed artifact.

## Source license notes (verify per record — do not assume)

- **F1000Research** peer-review reports are published CC-BY — `paraphrase_ok` /
  `cc_by_attribution` is defensible *after* confirming the specific report.
- **eLife / PeerJ / BMJ Open** publish reviews, but the licence varies by record and
  venue — confirm each before raising the policy above `synthetic_only`.
- **OA articles** range from CC-BY to CC-BY-NC-ND — the licence governs figure anchors
  and any quotation; the *ideas* are free to learn from regardless.

When in doubt, keep the record at the default (`verbatim_allowed: false`,
`public_reuse_policy: synthetic_only`) and publish synthesis only.

## Linked artifacts have their own licenses (verify each independently)

A paper's supplementary files, code repository, and data deposit are **separate works with
separate licenses** — the article's CC license does not extend to them. Record each under the
record's `linked_artifacts[]` with its own verified license; `distill.py` validates and
authorizes each separately (`--authorize id#N`).

| Linked artifact | Where its license lives | Reuse notes |
|---|---|---|
| **Supplementary files** | Usually the article's license (verify — some are separate) | Same rules as the article; learn the patterns, publish synthesis. |
| **Code repository** (GitHub/GitLab) | The repo's `LICENSE` file — a *software* license (MIT / Apache-2.0 / BSD / GPL / none) | Permissive software licenses (MIT/Apache/BSD/ISC/CC0) permit code reuse *with attribution*; **no LICENSE file = all-rights-reserved**, learn-only. GPL/AGPL impose copyleft — do not vendor into this MIT-licensed repo; learn the approach, author fresh. The *ideas/algorithms* are free to learn from regardless. |
| **Data deposit** (Zenodo / OSF / Figshare) | The deposit page — a *per-deposit* license (often CC0 or CC-BY, sometimes restricted) | CC0/CC-BY data and figures may anchor a committed figure with attribution; restricted/unknown = learn-only. |
| **Model / dataset card** (HuggingFace) | The card's stated license (model weights and dataset often differ) | Treat weights and data licenses separately; many are non-commercial or gated — learn-only by default. |

The firewall is the same in spirit: **learn from any artifact privately; publish only
synthesis**, unless that specific artifact's license is verified-permissive for the reuse you
intend. A linked artifact with an unknown/empty license authorizes nothing.

## Distribution note

`reverse_engineer/` is maintainer tooling. It is excluded from the npm tarball
(not in the `package.json` `files` allowlist) and `_corpus/` is gitignored, so neither
raw sources nor this tooling ship to end users.
