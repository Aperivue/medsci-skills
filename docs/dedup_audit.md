# Code-Duplication Audit (`_shared/` extraction question)

Audit of repeated utility code across skill scripts, and the decision on whether
to extract a shared module. **Conclusion: do not create a runtime `_shared/`
module — the small duplication is the deliberate price of skill portability.**

## What was audited

`skills/*/scripts/*.py` were scanned for repeated helpers.

| Pattern | Sites | Notes |
|---|---|---|
| Open `.docx` zip → read `word/document.xml` | `fill-icmje-coi`, `manage-refs/check_xref`, `verify-refs` | ~3-line idiom, then **diverges**: fill-icmje does literal-string *replacement* (write), check_xref reads the raw XML string, verify-refs extracts paragraph text. Not a single reusable function. |
| DOI regex (`10.\d{4,9}/…`) | `academic-aio/validate_schema`, `verify-refs` | One-line constant. |
| File SHA-256 | `sync-submission`, `version-dataset` | ~6-line helper. |
| `http_json` + PubMed/CrossRef calls | `verify-refs`, `meta-analysis/cohort_overlap_check` | ~8-line urllib wrapper + endpoint URLs. |
| pandas tabular reader | `generate-codebook`, `version-dataset` | Format-dispatch read; the two have different needs (profiling vs canonical-string hashing). |

The overlaps are small (3–8 line idioms), and several diverge in purpose after the
shared first step.

## Why not extract to a runtime `_shared/`

Skills in this repo are **strictly self-contained by design**:

- Every script is invoked as `python "${CLAUDE_SKILL_DIR}/scripts/X.py"` — relative
  to its *own* skill directory.
- There are **zero** cross-skill imports today (no `../`, no `sys.path` surgery,
  no `from skills…`). Verified by grep across `skills/*/scripts/*.py`.
- Skills are distributed and copied **individually** (see `/publish-skill`). A
  skill folder is expected to work when lifted out of the repo.

A runtime `_shared/` imported by skill scripts (`from ...._shared import read_docx`)
would be the *first* cross-skill coupling. A skill copied out of the repo — the
normal distribution path — would then fail to import. That trades a few lines of
duplication for a portability break, which is a bad bargain for a skills
marketplace.

## Recommendation

1. **Accept the current small duplication.** It is the cost of each skill being a
   portable, self-contained unit. The idioms are short and stable.
2. **If consolidation is ever wanted**, use a *build-time vendoring* pattern (a
   single canonical source copied into each skill's own `scripts/` by a sync
   script), not a runtime import — mirroring the established `citation_writer.py`
   vendoring approach. The skill stays self-contained; the source of truth stays
   single. This is only worth it if a helper grows large or correctness-critical.
3. **Do not** add a top-level `_shared/` Python package that skill scripts import
   at runtime.

## Status

No extraction performed. This audit is the deliverable; the duplication is a
documented, intentional trade-off. Revisit only if a shared helper grows large
enough that drift between copies becomes a correctness risk (then prefer
vendoring over runtime import).
