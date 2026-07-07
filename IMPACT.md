# Adoption & Impact

This page tracks how MedSci Skills is used in the wild. It exists because GitHub
discards traffic data after 14 days and surfaces it to repo admins only — without
a durable record, the evidence of adoption disappears daily. Numbers here are
honest snapshots, not marketing. Empty sections mean *not yet observed*, and they
are expected to fill over time.

How the numbers are captured:

- **Automated**: a weekly workflow ([`.github/workflows/metrics.yml`](.github/workflows/metrics.yml))
  appends to [`metrics/traffic_log.csv`](metrics/traffic_log.csv) (stars, forks, release
  downloads, 14-day traffic, Zenodo views/downloads) and — so the *source* of each wave is not
  lost after GitHub's 14-day window — to [`metrics/referrers_log.csv`](metrics/referrers_log.csv)
  (top referring sites) and [`metrics/paths_log.csv`](metrics/paths_log.csv) (top viewed paths).
- **Manual**: academic citations and named downstream use are logged in
  [`docs/citations.md`](docs/citations.md) as they are discovered.

---

## Snapshot

*As of 2026-06-06 (repo created 2026-04-06 — roughly two months old):*

| Signal | Value | Source |
|---|---|---|
| GitHub stars | 134 | repo API |
| GitHub forks | 36 | repo API |
| Release asset downloads (cumulative) | 220 | releases API |
| Repo views (trailing 14 days) | 1,636 (560 unique) | traffic API |
| Repo clones (trailing 14 days) | 8,566 (791 unique) | traffic API |
| Zenodo archive | DOI [10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321) | Zenodo |

Trend over time lives in [`metrics/traffic_log.csv`](metrics/traffic_log.csv); a
star-history chart is available at
[star-history.com](https://star-history.com/#Aperivue/medsci-skills&Date). The
Snapshot block is a point-in-time capture; the live figures are in the traffic log.

## Interpretation of metrics

These numbers are read conservatively, because most of them measure *interest*, not
confirmed use:

- **Stars** indicate interest, not confirmed use.
- **Forks** may indicate experimentation or reuse — a somewhat stronger signal than a star.
- **Clones / downloads** are inflated by CI and mirroring traffic; the *unique* columns are more meaningful.
- **Confirmed use cases and academic citations** are the strongest evidence, and are scarcer than raw stars.
- **AI-mediated discovery** is a distinct and growing channel: the referrer log ([`metrics/referrers_log.csv`](metrics/referrers_log.csv)) captures visits arriving from LLM assistants such as ChatGPT and Claude. Because agent-recommended installs are often cloned or run via `npx` without ever loading the GitHub page, this channel — and the real usage behind it — is systematically undercounted by the star count.
- **Current status: early community interest for a niche biomedical-workflow repository — not widespread adoption.** This page never claims adoption that has not been observed; a thin section is a truthful section.

---

## Listings & ecosystem presence

- Conforms to the [Agent Skills](https://agentskills.io) standard (cross-host:
  Claude Code, Codex, Cursor, GitHub Copilot — see
  [`docs/host_compatibility.md`](docs/host_compatibility.md)).
- Published to the npm registry (`medsci-skills`) and the Claude Code plugin marketplace.
- Listed in the [Evidence Synthesis Tools](https://evidencesynthesis-tools.github.io/) directory
  (Workflow & Automation category; added via a maintainer-reviewed
  [PR](https://github.com/evidencesynthesis-tools/awesome-evidence-synthesis/pull/4), 2026-06-03).
- Included by independent maintainers in four third-party curated "awesome" lists:
  [awesome-medical-ai-skills](https://github.com/JuneYaooo/awesome-medical-ai-skills/blob/7e395fd600a64234dde74cb3be08710e300c8554/README.md#L424)
  and its [Chinese edition](https://github.com/JuneYaooo/awesome-medical-ai-skills-cn/blob/239471ad76d2d2f88bf1674bd4f3d09e8e06bb03/README.md#L227) (juneyaooo),
  [awesome-claude-skills](https://github.com/Chat2AnyLLM/awesome-claude-skills/blob/c2b12ff1a87c41045e28a7cc01863511f3654fcf/README.md#L127) (Chat2AnyLLM),
  and [awesome-research-agents](https://github.com/chrisliu298/awesome-research-agents/blob/fb32bf2ed19ed37c2ebd944c9bfdcd68d83e1411/README.md#L90) (chrisliu298).
  These are inclusion signals (a maintainer chose to list the toolkit), not independent reviews.
- Archived for citation on Zenodo with a concept DOI (always resolves to latest).

*(New listings are added here as they appear.)*

---

## Academic citations

Papers, preprints, theses, or protocols that cite the Zenodo DOI or describe
using MedSci Skills in their methods are logged in
[`docs/citations.md`](docs/citations.md).

If you used MedSci Skills in your research, please
[tell us](https://github.com/Aperivue/medsci-skills/issues/new?template=used-in-research.yml) —
it helps other researchers find the toolkit and helps us understand what to
improve.

---

## Downstream use

- **Forks**: 36 (a fork is the clearest signal that someone is building on or
  adapting the toolkit).
- **Named adopters**: collected via the
  ["Used in research" issue template](https://github.com/Aperivue/medsci-skills/issues/new?template=used-in-research.yml)
  and listed in [`docs/citations.md`](docs/citations.md) with permission.

---

## Notes on methodology

- All figures are point-in-time snapshots from public GitHub/Zenodo APIs. Clone
  counts include automated CI/mirroring traffic and overstate human use; the
  *unique* columns are the more meaningful adoption signal.
- This page never claims adoption that has not been observed. A thin section is a
  truthful section.
