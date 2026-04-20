---
name: fill-icmje-coi
description: >
  Batch-generate per-author ICMJE Conflict of Interest Disclosure Forms
  (`coi_disclosure.docx`) for manuscript submission. Pre-fills all 13 disclosure
  items as "☒ None" + final certification ☒ using a synthetic seed template
  shipped with the skill, then clones the seed per author with Date, Name, and
  Manuscript Title replaced. Designed for the common case of hospital-based
  observational research where no author has real financial conflicts; the
  circulated forms become "reply 변경 없음 + sign" for most authors and only
  flag those who need to amend.
triggers: ICMJE, COI form, conflict of interest form, disclosure form, coi_disclosure.docx, 이해상충, 이해상충 폼, icmje 폼, 저자 동의서, submission forms
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Fill-ICMJE-COI Skill

You are helping a researcher prepare ICMJE Conflict of Interest Disclosure Forms
for every co-author on a manuscript about to be submitted to an ICMJE member
journal (CHEST, NEJM, JAMA, Lancet, Radiology, etc.). This skill batch-generates
one personalized `.docx` per author from a synthetic all-None seed shipped with
the skill, avoiding 10–20 minutes of repetitive Word clicking per author.

## Why This Skill Exists

The official ICMJE `coi_disclosure.docx` puts every field inside Word Content
Controls (Structured Document Tags, a.k.a. SDTs). Naive `python-docx`
manipulation of `cell.text` silently ignores SDT content, so the straightforward
programmatic approach does not work. The historical workaround was to open the
template in Word and manually fill each author's form (21 authors × 13
checkboxes × 2 clicks = ~500 clicks). This skill replaces that by operating
directly on `word/document.xml` inside the docx zip and doing literal-string
replacement — but that requires the target strings to already exist in the
seed, so the skill ships a pre-filled synthetic seed.

**Precedent:** CK-5 Emphysema → Mortality cohort (2026-04-20) — 6 authors
auto-filled in ~5 seconds from the synthetic seed with zero Word clicks.

## Core Principles (Do Not Violate)

1. **Never author SDT XML from scratch.** Only replace existing strings in an
   already-populated seed. Creating Content Controls programmatically is
   fragile and Word-version-dependent.
2. **Never ship a real author's filled form as the seed.** The template
   directory contains `icmje_coi_seed_synthetic.docx` with all PII scrubbed
   (synthetic name, title, date; metadata reset to `ICMJE` / `Anonymous`).
   Real-person seeds leak PII through both document.xml and docProps.
3. **Never modify the 13 disclosure items or certification checkbox.** The
   script only replaces Date/Name/Title. If any author has a real disclosure,
   they must edit in Word manually — the skill's purpose is the common
   all-None case.
4. **Always verify before circulation.** Each output must have 14 × ☒ and
   13 × "None" in document.xml. The script runs this check implicitly by
   preserving the seed structure; a post-generation grep is cheap insurance.

## When to Use This Skill

- Manuscript accepted for submission to an ICMJE member journal
- 3+ co-authors with no real financial conflicts
- Editorial Manager / submission portal requires per-author ICMJE disclosure docx
- About to hand-fill the same form 6–21 times

Skip this skill when:
- Any author has a real financial disclosure to list (they fill their own form
  in Word; this skill does not help)
- Target journal uses its own declaration form (not ICMJE) — check author
  guidelines first
- Only 1 author (not worth the setup)

## Execution

### Phase 1 — Intake

Ask the user (or extract from conversation):
1. **Manuscript title** (exact, as it will appear on title page)
2. **Submission date** (e.g., "April 20, 2026")
3. **Author list** — ordered, one name per slot: `[(1, "Yoojin Nam"), (2, "Hye Ree Cho"), ...]`
4. **Output directory** — typically `submission/{journal}/icmje_forms/`

Present the intake back to the user for confirmation (**Gate 1 — user approval**)
before generating anything. Explicitly name which authors will get all-None
forms and remind that anyone with a real disclosure must instead fill their own
form in Word.

### Phase 2 — Generate

Invoke the script with the synthetic seed that ships with this skill:

```bash
python3 ${SKILL_DIR}/scripts/fill_icmje_coi.py \
  --seed ${SKILL_DIR}/templates/icmje_coi_seed_synthetic.docx \
  --seed-name "Placeholder Author" \
  --seed-title "Placeholder Manuscript Title" \
  --seed-date "January 1, 2000" \
  --new-title "{exact manuscript title}" \
  --new-date "{submission date}" \
  --out-dir {out_dir} \
  --authors '[[1,"Author One"],[2,"Author Two"],...]'
```

The script exits nonzero if any seed string is not found, preventing silent
failures.

### Phase 3 — Verify

For each generated docx, confirm:
- ☒ count = 14 (13 disclosure items + 1 final certification)
- "None" count = 13
- Correct name appears after "Your Name:"
- Correct title appears after "Manuscript Title:"
- No leakage of seed placeholder strings (`Placeholder Author`, `Placeholder Manuscript Title`, `January 1, 2000`)

Verification one-liner:
```bash
for f in {out_dir}/*.docx; do
  python3 -c "
import zipfile, sys
xml = zipfile.ZipFile('$f').read('word/document.xml').decode()
assert xml.count('☒') == 14, 'bad ☒ count'
assert xml.count('None') == 13, 'bad None count'
assert 'Placeholder' not in xml, 'seed leak'
print('✓ $f')
"
done
```

Present verification results to user (**Gate 2 — user review**) before handing
off files.

### Phase 4 — Circulation Guidance

Provide the user with circulation copy to send with each personalized form:

> 첨부된 ICMJE COI 폼을 검토 부탁드립니다.
> - 내용이 맞으면 서명 후 PDF로 회신
> - 수정이 필요하면 해당 항목을 고쳐서 체크 + 서명 후 회신
> - 전체가 변경 없음이면 "변경 없음" 회신 + 서명본 PDF 별도 회신

All 6–21 authors can be emailed in one `gws gmail draft` batch (**Gate 3 — user
approves batch send** before actually dispatching).

## Custom Seeds

If the user wants a custom seed (e.g., different default wording, pre-filled
items 2/3 with a common grant), generate it once as follows:

1. Open `templates/icmje_coi_seed_synthetic.docx` in Word
2. Edit the desired fields
3. Save as a new file under `{project}/submission/{journal}/` or
   `~/.claude/private-seeds/`
4. Pass `--seed /path/to/custom.docx` to the script along with the new seed
   values for `--seed-name`, `--seed-title`, `--seed-date`

Do NOT commit custom seeds that contain real author names to the public
medsci-skills repo. Keep them in private per-project directories or under
`~/.claude/private-seeds/`.

## Seed Provenance (how the shipped synthetic seed was created)

The shipped `templates/icmje_coi_seed_synthetic.docx` was derived from the
official ICMJE `coi_disclosure.docx` through the following steps:

1. Downloaded the official ICMJE template (`https://www.icmje.org/downloads/coi_disclosure.docx`)
2. Opened in Word, typed placeholder values:
   - Date: `January 1, 2000`
   - Your Name: `Placeholder Author`
   - Manuscript Title: `Placeholder Manuscript Title`
3. Checked each of the 13 disclosure items' "None" option (14 checkboxes total including final certification)
4. Typed "None" in the "Name all entities" column for each item
5. Scrubbed `docProps/core.xml` metadata: creator=`ICMJE`, lastModifiedBy=`Anonymous`, dates=`2000-01-01`
6. Scrubbed `docProps/app.xml` Company/Manager fields

No real author's disclosure data is embedded. The file is safe to redistribute.

## Anti-Hallucination

- **Never invent author names, email addresses, or ORCIDs.** Pull them
  verbatim from the manuscript's title page or the user's author list.
- **Never claim to have filled the 13 disclosure items** — they come from the
  seed unchanged. If the user asks whether the script "handled the
  disclosures," the honest answer is "it cloned the seed's ☒ None entries;
  no author-specific disclosure reasoning happened."
- **Never promise the script works on a blank ICMJE template.** It does not —
  the seed must be pre-filled with all-None ☒ + text.
- **Never edit seed XML by authoring new SDT elements.** If an error requires
  altering the seed structure, stop and escalate to the user; Word-generated
  SDT XML is the ground truth.
- **Never push private seed files to public repos.** If the user asks to
  promote a custom seed, verify by `unzip -p seed.docx docProps/core.xml` that
  no real names remain in metadata before committing.

## References

- ICMJE Disclosure of Interest page: https://www.icmje.org/disclosure-of-interest/
- ICMJE COI form download: https://www.icmje.org/downloads/coi_disclosure.docx
- ICMJE FAQ on disclosure forms: https://www.icmje.org/about-icmje/faqs/conflict-of-interest-disclosure-forms/
- ${SKILL_DIR}/scripts/fill_icmje_coi.py — generator CLI + Python API
- ${SKILL_DIR}/templates/icmje_coi_seed_synthetic.docx — shipped synthetic seed (PII-free)

## Related Skills

| Skill | Relationship |
|---|---|
| `write-paper` | Completes the manuscript whose title is used as input |
| `find-journal` | Identifies whether the target journal requires ICMJE form |
| `add-journal` | Journal profile records whether ICMJE form is required |
| `revise` | After revision, updated title may require re-generating forms |

## Non-Goals

- Filling journal-specific disclosure forms (Elsevier Declaration of Interest,
  BMJ ICMJE derivative, etc.) — only the canonical ICMJE form
- Handling authors with real disclosures — those authors fill their own forms
- Signing the forms — authors sign manually after receiving their personalized docx
- Uploading to Editorial Manager — that remains manual, post-signature
