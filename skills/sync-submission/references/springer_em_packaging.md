# Springer Editorial Manager packaging (no title-page slot)

Some Springer Editorial Manager journals offer only **Manuscript / Figure / Table / Supplementary / LaTeX** upload item types — no separate Title Page or Cover Letter slot, and sometimes no Graphical Abstract slot. Common for observational / cohort submissions.

- **Title page → page 1 of the Manuscript file.** Build via pandoc: title-page markdown (strip internal-only blocks such as a "Manuscript Metrics" QC block, plus any Funding / Author Contributions / Keywords that also appear later) + a real docx page break (raw OpenXML `<w:br w:type="page"/>`; a bare `\newpage` is silently dropped in docx output) + the manuscript body **with its byline / affiliations / corresponding-author footnote removed** so the title page is not duplicated.
  - Verify: at least one page break; the affiliation block appears once; the article title is followed directly by the Abstract (no repeated byline); no internal QC strings leak.
- **Cover letter → paste into the "comments to the publication office" free-text field.**
- **Graphical Abstract (no dedicated slot) → upload as a Figure with Description = "Graphical Abstract".**
- **Declarations completeness (portal hard checkbox).** The manuscript "Statements and Declarations" must carry all seven Springer subheadings: Funding; Competing Interests; Ethics Approval; Consent to Participate; Consent for Publication; Author Contributions; Data Availability. For de-identified observational / registry studies, Consent to Participate = waived (existing de-identified records) and Consent for Publication = "Not applicable; only de-identified data, no individual person's identifying details, images, or videos".

```bash
for s in Funding "Competing Interests" "Ethics Approval" "Consent to Participate" "Consent for Publication" "Author Contributions" "Data Availability"; do
  unzip -p manuscript.docx word/document.xml | sed 's/<[^>]*>//g' | grep -q "$s" && echo "OK $s" || echo "MISSING $s"; done
```

- **Ethics approval / exemption number (observational or exempt cohort).** State the IRB approval or exemption reference number in the ethics statement. Institutional exemption notices carry the reference in the document body; filename digits are usually a receipt number, not the approval number — open the notice before writing the ethics block.
- **Word limit "including references".** When the limit counts references, the binding constraint is body+references words, not the reference-count ceiling. Measure body+refs on the rendered docx before adding references; each Vancouver reference is roughly 25–33 rendered words.
- **Submitting via a co-author's account.** Editorial Manager auto-adds the account holder at the top of the author list, tagged first/corresponding. De-duplicate, reorder to the intended position, reassign the first-author tag to the true first author, and fill missing co-author email/ORCID.
- **Re-read the EM-compiled submission PDF before Approve** — author order, degrees, ethics number, references, declarations, and figures.
