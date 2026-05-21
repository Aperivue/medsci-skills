# Update intake — from CK-07 e2e session (2026-05-20 → 2026-05-21)

**Source session**: CK-07 CKM Syndrome Mortality manuscript v1.0 → v1.5 (JACC: Advances submission format)
**Triage status**: ✅ harvested 2026-05-21 (this intake plus session 1 + session 3 feedback consolidated into plan `~/.claude/plans/e2e-dapper-cerf.md`)
**OSS PII guard applied**: yes — no manuscript IDs, no mentor names, no project-internal codes leaked in this file

This file lists candidate updates discovered during a single end-to-end manuscript build cycle.

## Absorption status (2026-05-21 harvesting session)

- [x] §1 Profile promotions (JACC_Advances / EJPC / NMCD / JCEM / Korean_Circulation_Journal) — harvested from `~/.claude/private-journal-profiles/` and written to public `skills/{find-journal,write-paper}/references/journal_profiles/` (Phase 3)
- [x] §2 `lit-sync` DOI-dedup (already implemented at SKILL.md line 109–116, verified)
- [x] §3 `journal-profile-creation.md` global rule — created at `~/.claude/rules/` (Phase 5A)
- [x] §3 `numerical-safety.md` prose-level recompute — boost added (Phase 5B)
- [DEFERRED] §2 `write-paper` journal-format automation, `sync-submission` v_N branching, `check-reporting` regenerate — recorded as Phase 4 deferred PR candidates
- [DEFERRED] §4 `manuscript-version-bump-guard.sh` hook — defer until incident
- [PENDING USER] §5 Cardiovascular Diabetology + Circulation: Cardiovascular Quality and Outcomes — user fallback data needed

---

## 1. Journal profiles added (private tier)

8 files newly created under `~/.claude/private-journal-profiles/`. POLICY (private→public) requires user verification before promotion. Recommended promotion candidates marked ★.

### Compact profiles — `~/.claude/private-journal-profiles/find-journal/`

| File | Promotion candidate | Verification needed |
|------|---------------------|---------------------|
| `JACC_Advances.md` (33 lines) | ★ public (high — JACC family) | Homepage + GfA fetched OK; AI policy = Elsevier publisher-level (transcribed from publisher policy page, not journal page) |
| `EJPC.md` (31 lines) | ★ public (high — ESC/EAPC flagship; AI policy verbatim from journal Author Guidelines) | OUP GfA fetched OK; verbatim AI policy quoted |
| `NMCD.md` (31 lines) | ★ public (Elsevier, cardio-metabolic) | ScienceDirect GfA fetched OK |
| `JCEM.md` (32 lines) | public candidate (OUP/Endocrine Society) | OUP Author Guidelines fetched OK; AI policy verbatim |
| `Korean_Circulation_Journal.md` (30 lines) | public candidate (KSC flagship) | e-kcj.org fetched OK; AI policy not on instructions page (refer to journal editorial office) |
| `Korean_Journal_of_Internal_Medicine.md` (29 lines) | public candidate (KAIM, IF 2.4) | kjim.org Authors page fetched OK; AI policy verbatim |

### Detailed profiles — `~/.claude/private-journal-profiles/write-paper/`

| File | Promotion candidate |
|------|---------------------|
| `JACC_Advances.md` (197 lines) | ★ public — full positioning table vs JACC main / JACC Asia / EJPC; submission portal verified |
| `EJPC.md` (192 lines) | ★ public — full positioning table vs JACC: Advances / JAHA / NMCD |

### Two journals deferred (auth-gated; user fallback needed)

- **Cardiovascular Diabetology** (Springer auth-gate `idp.springer.com`) — needs user-supplied submission guidelines text
- **Circulation: Cardiovascular Quality and Outcomes** (AHA Journals 403) — AHA family-wide WebFetch failure; user-supplied scope + Author Instructions needed

### Already-registered journals (work not needed; reuse existing)

- `Atherosclerosis.md` (private find-journal) — high-quality profile already exists
- `JAHA.md` (private find-journal) — full populated profile already exists
- AHA family (Circulation main, JAMA Cardiology, JACC main, JACC: CV Imaging, European Heart Journal) — already in private library

### Promotion checklist before public push

Per `skills/find-journal/POLICY.md`, before `git mv private → public`, the next session should:

- [ ] User opens each journal homepage + author guidelines and attests
- [ ] ISSN cross-checked against portal.issn.org for the exact journal name (currently transcribed from journal's own masthead/about pages)
- [ ] AI policy wording double-checked against the journal's or publisher's own policy page (for JACC: Advances specifically — confirm Elsevier publisher-level policy applies, since the JACC: Advances GfA page does not show a journal-specific AI policy)
- [ ] Commit message records which pages were opened and on what date

---

## 2. Skill improvement candidates

### `/verify-refs` — works as designed; one usability note

**Validated**: this session reproduced the v1.1.2 first-author cross-check value. A bib entry with correct DOI but wrong first author (CK-07 case: `Lee, Seon Mee` vs actual `Kim, Mee Kyoung`, DOI `10.3803/EnM.2014.29.4.405`) was caught as MISMATCH with `note: "first-author hallucination suspected"`. The rule pays off — no change needed to the detection.

**Usability nit**: when verify-refs flags a MISMATCH, the report does not trace which manuscript paragraph cites the offending bibkey. A future enhancement could add a "cited from manuscript.md line N" pointer for faster remediation. Defer until 2+ similar cases recur.

### `/lit-sync` — three improvement candidates

**a) Collection auto-create on first sync.** This session found that for a project with no `references/` folder, lit-sync needed manual prep (Zotero collection creation, `references/zotero_collection.json` scaffolding). Recommended: lit-sync detects missing collection by project_id and auto-creates `<ProjectID>` Zotero collection on Phase 1.

**b) DOI-based dedup before add.** `zotero_add_by_doi` does not check if the DOI is already in the library. This session triggered Inker 2021 → 4 duplicates (one new add + 3 prior from CK-01/08/13). Recommended: lit-sync should search by DOI first, and only call `add_by_doi` when no existing item matches. Then assign existing item to the new collection rather than re-adding.

**c) After-sync cleanup: report duplicates within current collection only.** Current `zotero_find_duplicates` returns all library-wide duplicates (11 groups in this session, only 1 actually CK-07-related). Recommended: lit-sync filters duplicates to those whose any-member is in the just-synced collection.

### `/write-paper` — journal-format automation candidate

**Observation**: this session manually adjusted v1.4 → v1.5 for JACC: Advances format:
- Abstract 4-heading → 5-heading (Background / Objectives / Methods / Results / Conclusions)
- Highlights 3-5 bullets added
- Central Illustration legend added
- AI Declaration section moved to immediately above references (Elsevier publisher policy)
- 5,000-word cap aggressive trim (text + refs + figure legends combined)

**Recommended enhancement**: write-paper Phase 7 (journal-format adjustment) reads the find-journal compact profile's "Special Notes" + "Article Types Accepted" + detailed profile's "Required Journal-Specific Elements", and proposes format transformations as a checklist. Currently this step is implicit; making it explicit would shorten the v_N → v_(N+1) cascade when switching journals.

### `/sync-submission` — v_N → v_(N+1) branching automation

**Pattern observed**: this session executed 6 versions (v1 → v1.1 → v1.2 → v1.3 → v1.4 → v1.5), each triggered by audit results. Each branch followed:

1. Freeze v_N (`manuscript/archive/v{N}_frozen/`)
2. Update SSOT (`manuscript.md` in place with `manuscript_version` bumped)
3. Rebuild DOCX (`submission/<journal>/v{N+1}/manuscript_v{N+1}.docx`)
4. Re-run QC gates (`xref_audit_v{N+1}.json`, `reference_audit.json`)
5. Update `STATUS.md` Stream table
6. Sync into `reviews/circulation_R1/` if circulating

**Recommended**: sync-submission could add a `branch v{N+1}` subcommand that automates steps 1-5 given a trigger ("Codex audit yielded N items", "critic R0 cycle 2", "senior PI revision", "cascade to new journal"). Currently this is manual cp + Edit + bash, error-prone for the version-counting.

### `/check-reporting` — usability nit (no functional change)

Manuscript v1.5 was prepared without re-running check-reporting on STROBE checklist. The skill is solid but its output (`qc/reporting_checklist.md`) ages quickly as the manuscript changes. Recommended: add a "regenerate if manuscript.md mtime > checklist mtime" automation pattern in the skill's preamble.

---

## 3. Cross-cutting global-rule candidates

### Candidate new rule: `journal-profile-creation.md`

Pattern observed this session for adding 10 candidate journals to medsci-skills:

1. **WebFetch attempt first** — Elsevier ScienceDirect, OUP, Wiley typically OK
2. **403 / auth-gate detection** — AHA Journals family (Circulation, JAHA, Hypertension), Springer journals (BMC Cardiovascular Diabetology) typically blocked
3. **User-fallback request** — paste page text or PDF path; do not infer
4. **Private tier default** — POLICY's verification bar is strict; promote later

This pattern is documented inline in `find-journal/POLICY.md` but a separate global rule (`~/.claude/rules/journal-profile-creation.md`) would make it discoverable from outside the skill. Defer until 2-3 sessions repeat the pattern.

### Existing rules validated (no change needed)

- `~/.claude/rules/manuscript-style-classical.md` — § = 0, em-dash < 25, classical heading style; all enforced cleanly
- `~/.claude/rules/citation-safety.md` v1.1.2 — first-author cross-check caught the Lee→Kim KSSO case
- `~/.claude/rules/manuscript-references.md` — Phase 1 (pandoc citeproc) + Phase 2 (Zotero CWYW preparation) hybrid worked
- `~/.claude/rules/manuscript-versioning.md` — v_N freeze + v_(N+1) branch pattern executed 6 times this session without drift
- `~/.claude/rules/senior-mentor-circulation.md` — circulation_R1/ folder structure preserved through 6 version bumps
- `~/.claude/rules/zotero-workflow.md` — MCP user-scope + BBT auto-export pattern (auto-export still requires user GUI step)
- `~/.claude/rules/oss-publication-pii-guard.md` — applied to this intake file itself

### Existing rule that needs a small clarification: `numerical-safety.md`

This session caught a stale hand-typed number in Limitations §7 ("21,679 single-visit subjects" from v1.1 cohort 30,700) that survived v1.2 → v1.3 because the cohort denominator changed under it. Current `numerical-safety.md` says "never hand-type CSV data into scripts." Recommended: add a parallel rule "never hand-type aggregate counts into manuscript prose; recompute from parquet/CSV on every revision." Currently this is implicit in the skill's audit checklist, not in the global rule.

---

## 4. Harness setting candidates

### No `settings.json` changes proposed

The harness already permits the tools used in this session (Bash, WebFetch, Zotero MCP, Skill tool). No `update-config` changes needed.

### Hook candidate (low priority): `manuscript-version-bump-guard.sh`

Triggered on `Edit` to any `manuscript/manuscript.md` whose YAML front-matter `manuscript_version` field changes — automatically `cp` to `manuscript/archive/v{old}_frozen/` before allowing the edit. This would enforce `manuscript-versioning.md` mechanically. Defer until a v_N drift incident occurs.

---

## 5. Two journal profiles still owed (user-supplied data needed)

Tracked separately so another session can pick up when user provides the data:

### Cardiovascular Diabetology
- Springer auth-gate blocked WebFetch on both homepage and submission-guidelines
- Need from user: (1) journal scope statement, (2) submission guidelines body (article types, word limits, abstract structure, references, AI policy), (3) APC amount
- Filename target: `~/.claude/private-journal-profiles/find-journal/Cardiovascular_Diabetology.md`

### Circulation: Cardiovascular Quality and Outcomes
- AHA Journals 403 (family-wide block)
- Need from user: (1) journal scope statement, (2) Author Instructions body — article types and word limits + abstract structure (typically 4-heading)
- AI policy can inherit from existing `JAHA.md` profile (AHA family-wide AI policy)
- Filename target: `~/.claude/private-journal-profiles/find-journal/Circulation_Cardiovascular_Quality_and_Outcomes.md`

---

## 6. Verification artifacts (for reproducibility)

Intake claims here are anchored to source files in the originating project workspace (paths redacted to OSS-safe placeholders per `oss-publication-pii-guard.md`):

- v1.4 → v1.5 word count + Highlights / 5-heading abstract changes: `<project>/submission/jacc_advances/v1.5/manifest.md`
- 6-version cascade log: `<project>/STATUS.md` (Stream table)
- Zotero collection map: `<project>/references/zotero_collection.json` (19 items, 1:1 mapped)
- First-author hallucination case (cross-cohort surname swap): `<project>/qc/reference_audit.json` (counter-validated by re-run after fix)
- Stale-number P1-a discovery + fix: `<project>/qc/critic_review_R0_v1.2.md` (item P1-a)
- POSIXct/Date mismatch W-1 case: `<project>/qc/audit_R0_cycle3_v1.4.md` (item W-1)

---

## Suggested processing order for the harvesting session

1. **Profile promotions** (lowest risk, immediate value): JACC: Advances + EJPC compact + detailed → public (after POLICY checklist). NMCD + JCEM + KCJ + KJIM compact → public consideration.
2. **lit-sync DOI-dedup enhancement** (small, high-value): prevents future Inker-like 4-duplicate incidents across CK projects.
3. **journal-profile-creation.md global rule** (defer until 2-3 more sessions repeat the WebFetch → user-fallback pattern).
4. **write-paper journal-format automation** (medium, defer — current manual process worked).
5. **sync-submission v_N branching automation** (medium, defer — current manual cascade worked, 6 versions in 2 days).
6. **manuscript-version-bump-guard.sh hook** (low priority; defer until incident).
