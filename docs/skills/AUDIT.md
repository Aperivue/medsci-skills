# How MedSci Skills Are Validated

This page describes what is actually checked in this repository, what is reviewed by hand, and what is deliberately **not** claimed. It is a trust surface grounded in the repo's CI and demos, not a marketing claim. Every check below runs in `.github/workflows/validate.yml` on each push and pull request, or is reproducible locally.

## Static gates (run in CI on every change)

| Gate | What it enforces |
|---|---|
| `scripts/validate_skills.sh` | Per-skill structure (required frontmatter, anti-hallucination section), size tiers, and a public-surface PII / precedent scan (personal paths, names, document EXIF). Also runs the contract validator. |
| `scripts/validate_skill_contracts.py` | Every skill ships a `skill.yml` (v2); schema correctness; the optional v2.1 quality-card fields (non-empty lists, strict `evidence_surface` enum). Missing contract → **FAIL**. |
| `scripts/validate_catalog_consistency.py` | Catalog counts (skills, reporting guidelines, journal profiles) recomputed from disk and asserted equal across `metadata/catalog_counts.json` and the public docs. |
| `scripts/validate_routing_assets.py --strict` | Every `${CLAUDE_SKILL_DIR}` asset reference in a `SKILL.md` resolves to a file that exists. |
| `scripts/gen_skill_docs.py --check` | The generated per-skill pages under `docs/skills/` are in sync with each `SKILL.md` + `skill.yml` (no drift). |
| `scripts/version_dataset.py verify --strict` | The three demo projects' `manifest.lock.json` (input + output SHA-256) still reproduce. |

## Dynamic evidence (reproducible demos)

Three end-to-end demos exercise the core pipeline on public data, each pinned by a `manifest.lock.json` that CI verifies:

- [`demo/01_wisconsin_bc/`](../../demo/01_wisconsin_bc/) — diagnostic accuracy (STARD 2015).
- [`demo/02_metafor_bcg/`](../../demo/02_metafor_bcg/) — meta-analysis (PRISMA 2020).
- [`demo/03_nhanes_obesity/`](../../demo/03_nhanes_obesity/) — survey epidemiology (STROBE).

## Evidence surface (per-skill)

Each skill's Quality Card carries an `evidence_surface` label — the strongest validation it has. Labels are assigned conservatively:

| Label | Meaning |
|---|---|
| `ci_validator` | A CI gate exercises the skill's behavior or output. |
| `demo` | The skill is exercised end-to-end by one of the demos above. |
| `bundled_script` | The skill ships a deterministic script that produces its output. |
| `manual_workflow` | LLM/MCP-driven; no standalone automated check (often needs a Claude MCP server). |
| `not_yet_demonstrated` | No demo or deterministic check yet. |

## Trust boundaries

**What these gates establish:** structural validity, absence of known PII patterns, citation/asset/count integrity, generated-doc sync, and reproducibility of the demo outputs.

**What is reviewed by hand, not automated:** clinical correctness, statistical appropriateness for a given dataset, and writing quality. The skills enforce *process* (verified references, reporting-guideline items, drift checks); they do not certify that a study's design or conclusions are correct. Several skills are `manual_workflow` and depend on a connected Claude MCP server (PubMed, CrossRef, Zotero); off-Claude they degrade to manual steps (see [`host_compatibility.md`](../host_compatibility.md)).

**What is deliberately not claimed:** there is no external security scan, no skill signing, and no third-party audit in this repository at this time. Cross-agent host support is asserted only where install and discovery have been verified against official documentation; OpenClaw and Hermes remain unverified roadmap items.

## Reproduce locally

```bash
bash scripts/validate_skills.sh
python3 scripts/validate_skill_contracts.py
python3 scripts/validate_catalog_consistency.py
python3 scripts/validate_routing_assets.py --strict
python3 scripts/gen_skill_docs.py --check
```

---

*Part of [MedSci Skills](../../README.md). Per-skill pages: [skill reference index](README.md).*
