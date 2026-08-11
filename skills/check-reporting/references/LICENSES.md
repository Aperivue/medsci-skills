# Checklist Licenses

Attribution and licence status for the bundled reporting-guideline and risk-of-bias checklists.

**How the Licence column is established.** Each entry is resolved from the article's DOI through
the Crossref `license` field and, where Crossref carries only a text-and-data-mining policy, through
the PubMed Central record's `<license>` element. A row reads **verified** only when one of those two
returned an explicit Creative Commons or public-domain URL. Where neither did, the row says so — an
absent licence statement is **not** evidence of permissive licensing, and several publishers in this
table (ACP, JAMA Network) do not publish these instruments under an open licence at all.

This distinction is load-bearing. This repository is MIT-licensed and is redistributed through npm,
GitHub and a classroom ZIP without restriction. A checklist whose source is CC BY-**NC** cannot be
carried verbatim under those terms, and one with no open licence cannot be carried verbatim at all.

## Verified permissive

| File | Guideline | Reference | Licence | Verified via |
|------|-----------|-----------|---------|--------------|
| STROBE.md | STROBE 2007 | von Elm E et al. PLoS Med 2007 | CC BY 4.0 | PMC2020495 |
| STARD.md | STARD 2015 | Bossuyt PM et al. BMJ 2015;351:h5527 | CC BY 4.0 | PMC4623764 |
| TRIPOD_AI.md | TRIPOD+AI 2024 | Collins GS et al. BMJ 2024;385:e078378 | CC BY 4.0 | Crossref |
| PRISMA_2020.md | PRISMA 2020 | Page MJ et al. BMJ 2021;372:n71 | CC BY 4.0 | Crossref |
| PRISMA_2020_Abstracts.md | PRISMA 2020 for Abstracts | Page MJ et al. BMJ 2021;372:n71 | CC BY 4.0 | Crossref |
| CONSORT.md | CONSORT 2025 | Hopewell S et al. BMJ 2025;389:e081123 | CC BY 4.0 | Crossref |
| SPIRIT.md | SPIRIT 2025 | Chan AW et al. BMJ 2025;389:e081477 | CC BY 4.0 | Crossref |
| ARRIVE_2.md | ARRIVE 2.0 | Percie du Sert N et al. PLoS Biol 2020 | CC0 1.0 | Crossref |

## Non-commercial — NOT covered by this repository's MIT licence

Free to copy and redistribute **with attribution, for non-commercial purposes**. Commercial use
requires permission from the rights holder. These files must remain summaries of item *intent* in our
own words rather than reproductions.

| File | Guideline | Reference | Licence | Verified via |
|------|-----------|-----------|---------|--------------|
| ROBINS_I.md | ROBINS-I 2016 | Sterne JAC et al. BMJ 2016;355:i4919 | **CC BY-NC 3.0** | PMC5062054 |
| CARE.md | CARE 2013 | Gagnier JJ et al. J Clin Epidemiol 2014;67(1):46-51 | CC BY-NC 4.0 | publisher statement |
| MI_CLEAR_LLM.md | MI-CLEAR-LLM | Park SH et al. Korean J Radiol 2024;25(10):865-868; 2025 update KJR 2025;26(12):1123-1132 | CC BY-NC 4.0 | publisher statement |
| DECIDE_AI.md | DECIDE-AI 2022 | Vasey B et al. Nat Med 2022;28(5):924-933 | CC BY-NC 4.0 (DECIDE-AI materials) | publisher statement |

## No open licence found — summaries only, never reproductions

Neither Crossref nor PMC returned a Creative Commons or public-domain licence for these. The
publishers are subscription-access and do not place these instruments under an open licence. The
bundled files must express item *intent* in our own words, cite the source, and direct the reader to
complete the official instrument.

| File | Guideline | Reference | Status | Verified via |
|------|-----------|-----------|--------|--------------|
| QUADAS3.md | QUADAS-3 | Whiting PF et al. Ann Intern Med 2026;179(4):548-555 | © ACP — no open licence | Crossref (TDM policy only) |
| QUADAS2.md | QUADAS-2 | Whiting PF et al. Ann Intern Med 2011;155(8):529-536 | © ACP — no open licence | Crossref (TDM policy only) |
| PROBAST.md | PROBAST 2019 | Wolff RF et al. Ann Intern Med 2019;170(1):51-58 | © ACP — no open licence | Crossref (TDM policy only) |
| RoB2.md | RoB 2 2019 | Sterne JAC et al. BMJ 2019;366:l4898 | no CC licence found | Crossref (TDM policy only) |
| PRISMA_DTA.md | PRISMA-DTA 2018 | McInnes MDF et al. JAMA 2018;319(4):388-396 | © AMA — no open licence | Crossref (no licence field) |
| TRIPOD_LLM.md | TRIPOD-LLM 2025 | Gallifant J et al. Nat Med 2025;31(1):60-69 | published version subscription-access; author-accepted manuscript CC BY 4.0 via rights retention | publisher statement |
| CLAIM_2024.md | CLAIM 2024 Update | Tejani AS et al. Radiol Artif Intell 2024;6(4):e240300 | © RSNA, open access — consult RSNA for reuse terms | publisher statement |
| NOS.md | Newcastle-Ottawa Scale | Wells GA et al. Ottawa Hospital Research Institute | no formal licence published | — |

## Not yet resolved

Every other file under `checklists/` is not listed above because its licence has **not** been
resolved. That is a gap in this table, not a finding of permissiveness. Treat an unlisted file as
"unknown licence, summarise only" until it appears here.

## Corrections made to this table

Five rows previously claimed **CC BY** on no evidence: ROBINS-I (actually CC BY-**NC** 3.0),
RoB 2, QUADAS-2, PROBAST, and PRISMA-DTA (no open licence found for any of the four). The claim was
inherited rather than checked. It mattered: an NC restriction is incompatible with redistributing a
verbatim reproduction under this repository's MIT licence, and two of the instruments come from a
publisher that licenses none of this material openly.

---

All files here are educational summaries that cite their source; they do not relicense the
underlying guidelines. Any manuscript that uses one should cite the original instrument, and any
assessment that is reported should be completed against the official document.
