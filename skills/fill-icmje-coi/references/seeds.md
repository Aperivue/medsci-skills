# Seeds — custom seeds and the shipped seed's provenance

Load-on-demand companion to `/fill-icmje-coi`. The Core Principles in SKILL.md (no SDT authoring,
no real-author seed in a public repo, the 13 items untouched) apply to every seed below.

## Custom seeds

For a custom seed (e.g., different default wording, items 2/3 pre-filled with a common grant),
generate it once:

1. Open `templates/icmje_coi_seed_synthetic.docx` in Word.
2. Edit the desired fields.
3. Save it under `{project}/submission/{journal}/` or a local private seeds directory (outside the
   medsci-skills repo).
4. Pass `--seed /path/to/custom.docx` to `scripts/fill_icmje_coi.py`, together with that seed's own
   values for `--seed-name`, `--seed-title` and `--seed-date`.

Do NOT commit a custom seed containing real author names to the public medsci-skills repo.

## How the shipped synthetic seed was created

`templates/icmje_coi_seed_synthetic.docx` was derived from the official ICMJE form:

1. Downloaded the official ICMJE template (`https://www.icmje.org/downloads/coi_disclosure.docx`).
2. Opened it in Word and typed placeholder values:
   - Date: `January 1, 2000`
   - Your Name: `Placeholder Author`
   - Manuscript Title: `Placeholder Manuscript Title`
3. Checked each of the 13 disclosure items' "None" option (14 checkboxes including the final
   certification).
4. Typed "None" in the "Name all entities" column for each item.
5. Scrubbed `docProps/core.xml` metadata: creator=`ICMJE`, lastModifiedBy=`Anonymous`,
   dates=`2000-01-01`.
6. Scrubbed `docProps/app.xml` Company/Manager fields.

No real author's disclosure data is embedded; the file is safe to redistribute.

ICMJE sources: Disclosure of Interest page <https://www.icmje.org/disclosure-of-interest/>;
FAQ on the disclosure forms
<https://www.icmje.org/about-icmje/faqs/conflict-of-interest-disclosure-forms/>.
