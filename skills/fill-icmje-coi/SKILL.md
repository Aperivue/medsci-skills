---
name: fill-icmje-coi
description: Use when each author needs an ICMJE Conflict of Interest disclosure form (coi_disclosure.docx) for submission. Clones a pre-filled synthetic seed with every item marked None and replaces only date, name and manuscript title, so most authors just confirm or amend.
triggers: ICMJE, COI form, conflict of interest form, disclosure form, coi_disclosure.docx, 이해상충, 이해상충 폼, icmje 폼, 저자 동의서, submission forms
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Fill-ICMJE-COI Skill

The official ICMJE `coi_disclosure.docx` keeps every field inside Word Content Controls (SDTs),
which `python-docx` `cell.text` silently ignores. The script therefore does literal-string
replacement in `word/document.xml`, which only works when the target strings already exist — hence
the shipped pre-filled synthetic seed.

## Core Principles (Do Not Violate)

1. **Never author SDT XML from scratch.** Only replace existing strings in an already-populated
   seed, because programmatic Content Controls are fragile and Word-version-dependent. If an error
   seems to require altering the seed structure, stop and escalate to the user.
2. **Never use or commit a seed that contains a real author's data.** The shipped
   `templates/icmje_coi_seed_synthetic.docx` is PII-scrubbed (synthetic name, title, date; metadata
   `ICMJE` / `Anonymous`); real-person seeds leak PII through both `document.xml` and `docProps`.
   Keep custom seeds with real names in private per-project directories, and before promoting any
   seed check `unzip -p seed.docx docProps/core.xml` for real names.
3. **Never modify the 13 disclosure items or the certification checkbox.** The script replaces only
   Date, Name and Title; the ☒ None entries come from the seed unchanged. Never say the script
   "handled the disclosures": it cloned the seed, and no author-specific disclosure reasoning
   happened. An author with a real disclosure edits their own form in Word.
4. **The seed must be pre-filled** (all-None ☒ + text). The script does not work on a blank ICMJE
   template.

Skip this skill when the target journal uses its own declaration form (Elsevier Declaration of
Interest, a BMJ ICMJE derivative, etc.) rather than the canonical ICMJE form — check the author
guidelines first.

## Execution

### Phase 1 — Intake

Ask the user (or extract from the conversation):
1. **Manuscript title** (exact, as on the title page)
2. **Submission date** (e.g., "April 20, 2026")
3. **Author list** — ordered, one name per slot: `[(1, "Author One"), (2, "Author Two"), ...]`,
   taken verbatim from the manuscript title page or the user's list
4. **Output directory** — typically `submission/{journal}/icmje_forms/`

**Gate 1 — user approval.** Present the intake back before generating anything. Name which authors
will get all-None forms and remind the user that anyone with a real disclosure must fill their own
form in Word instead.

### Phase 2 — Generate

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/fill_icmje_coi.py \
  --seed ${CLAUDE_SKILL_DIR}/templates/icmje_coi_seed_synthetic.docx \
  --seed-name "Placeholder Author" \
  --seed-title "Placeholder Manuscript Title" \
  --seed-date "January 1, 2000" \
  --new-title "{exact manuscript title}" \
  --new-date "{submission date}" \
  --out-dir {out_dir} \
  --authors '[[1,"Author One"],[2,"Author Two"],...]'
```

It writes one `ICMJE_COI_{NN}_{Name}.docx` per author and exits nonzero if any seed string is not
found, so a mismatch never fails silently.

### Phase 3 — Verify

For each generated docx confirm: ☒ count = 14 (13 disclosure items + final certification);
"None" disclosures = 13; the correct name after "Your Name:" and title after "Manuscript Title:";
no seed placeholder strings left (`Placeholder Author`, `Placeholder Manuscript Title`,
`January 1, 2000`).

```bash
python3 - {out_dir}/*.docx <<'PY'
import sys, zipfile
for f in sys.argv[1:]:
    xml = zipfile.ZipFile(f).read("word/document.xml").decode("utf-8")
    assert xml.count("☒") == 14, f"{f}: bad ☒ count"
    assert xml.count(">None<") + xml.count(">None ") == 13, f"{f}: bad None count"
    for ph in ("Placeholder Author", "Placeholder Manuscript Title", "January 1, 2000"):
        assert ph not in xml, f"{f}: seed leak {ph!r}"
    print("✓", f)
PY
```

**Gate 2 — user review.** Present the verification results before handing off the files.

### Phase 4 — Circulation Guidance

Give the user this copy to send with each personalized form, written in the co-authors' language:

> Please review the attached ICMJE COI form.
> - If the contents are correct, sign and reply with a PDF.
> - If a change is needed, edit/check the relevant item, sign, and reply.
> - If there are no changes at all, reply "no changes" and return the signed PDF separately.

All authors can be emailed in one draft batch (e.g., `gws gmail draft`). **Gate 3 — the user
approves the batch** before anything is sent.

## Custom Seeds and Seed Provenance

Read `${CLAUDE_SKILL_DIR}/references/seeds.md` when the user wants a custom seed (different default wording, a common
grant pre-filled in items 2/3) or asks how the shipped seed was made.
