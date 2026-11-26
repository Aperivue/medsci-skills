# Zotero + Better BibTeX Policy

**Status**: Frozen (Phase 0.5.6, 2026-04-24, per D-2 + v1.1.1 F4)
**Scope**: Reference management for all medsci-skills projects.

## Policy summary

Project owner (usually the primary author) maintains the Zotero library with Better BibTeX auto-export. Collaborators work from the committed `refs.bib` snapshot. No collaborator is required to install Zotero.

`SSOT.yaml` records the policy per project:

```yaml
reference_manager:
  type: zotero
  required_for: project_owner              # key field
  fallback_for_collaborator: snapshot_only
```

## Roles

### Project owner (required_for = project_owner)

**Must have installed**:
- Zotero desktop 7 or later (Zotero 10 or later to write through the local API without a web API key)
- Better BibTeX plugin ([retorque.re/zotero-better-bibtex/](https://retorque.re/zotero-better-bibtex/))

**Must configure**:
1. Create a Zotero collection for the project. Record its key in `SSOT.yaml` `reference_manager.collection_key`.
2. Pin citekeys (Better BibTeX → right-click collection → "Pin BibTeX key"). Ensures stable `[@citekey]` across sessions.
3. Configure auto-export to `<project>/manuscript/_src/refs.bib`:
   - File → Export Library → Better BibTeX → "Keep updated"
   - Export path = `SSOT.truth.refs_bib`
4. Commit `refs.bib` to git. This is the canonical snapshot collaborators consume.

**Runs `/lit-sync`**: owner-only operation. Pulls verified references from `/search-lit` output into Zotero, then Better BibTeX re-exports `refs.bib`.

### Collaborator (fallback_for_collaborator = snapshot_only)

**Not required**:
- Zotero installation
- Better BibTeX
- Access to the owner's Zotero library

**Works with**:
- Committed `refs.bib` snapshot (read-only)
- `[@citekey]` references in `manuscript/index.qmd` or `manuscript.md`
- `/verify-refs` consumes `refs.bib` directly

**When collaborator needs a new reference**:
1. Flag it in manuscript as `[@NEW:topic]` placeholder (see `/write-paper` citekey-only gate).
2. Notify owner to add it via Zotero.
3. Owner runs `/lit-sync`, re-exports `refs.bib`, commits.
4. Collaborator pulls, replaces `[@NEW:topic]` with the real citekey.

## Citekey policy

`citekey_policy: pinned_or_stable` means:

- **Pinned**: Better BibTeX pin explicitly set. Preferred for all cited entries.
- **Stable**: Better BibTeX generated key per the owner's citekey formula (e.g., `authorYear`), but not yet pinned. Acceptable during drafting.

`/verify-refs` tolerates both but warns on unpinned keys in submission-stage manuscripts.

Forbidden:
- Hand-written BibTeX citekeys that do not exist in the Zotero library.
- Generating `refs.bib` entries from LLM memory.
- Editing `refs.bib` directly (violates `artifact_contract.md` — only `/lit-sync` may write).

## Artifact contract

| Artifact | Sole Writer | Readers |
|---|---|---|
| `manuscript/_src/refs.bib` | `/lit-sync` (owner) | `/write-paper`, `/verify-refs`, `/render` |

Collaborator checkouts treat `refs.bib` as read-only. Any hand edit is considered drift and must be reverted.

## Setup checklist (project owner)

- [ ] Zotero 7 or later installed (10 or later for local-API writes)
- [ ] Better BibTeX plugin installed
- [ ] Project collection created; `collection_key` recorded in `SSOT.yaml`
- [ ] Better BibTeX "Keep updated" auto-export configured to `manuscript/_src/refs.bib`
- [ ] `citekey_policy` in `SSOT.yaml` set to `pinned_or_stable`
- [ ] Initial `refs.bib` committed
- [ ] First `/lit-sync` run succeeds

## Fallback: required_for = none

Projects with no Zotero at all (discouraged, legacy). `refs.bib` is hand-maintained. `/verify-refs` still runs. Use only when migrating very old projects; do not start new projects this way.

## Fallback: required_for = all_contributors

Multi-institution SR/MA where every contributor must have Zotero access (shared screening, distributed extraction). Each contributor installs Zotero + Better BibTeX and joins the group library. Rare.

## Change log

- **2026-04-24** Policy frozen. D-2 + F4: owner/collaborator split; collaborator Zotero not required.
