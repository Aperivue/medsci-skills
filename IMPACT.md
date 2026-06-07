# Adoption & Impact

This page tracks how MedSci Skills is used in the wild. It exists because GitHub
discards traffic data after 14 days and surfaces it to repo admins only — without
a durable record, the evidence of adoption disappears daily. Numbers here are
honest snapshots, not marketing. Empty sections mean *not yet observed*, and they
are expected to fill over time.

How the numbers are captured:

- **Automated**: a weekly workflow ([`.github/workflows/metrics.yml`](.github/workflows/metrics.yml))
  appends a row to [`metrics/traffic_log.csv`](metrics/traffic_log.csv) — stars,
  forks, release downloads, 14-day traffic, and Zenodo views/downloads.
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
[star-history.com](https://star-history.com/#Aperivue/medsci-skills&Date).

---

## Listings & ecosystem presence

- Conforms to the [Agent Skills](https://agentskills.io) standard (cross-host:
  Claude Code, Codex, Cursor, GitHub Copilot — see
  [`docs/host_compatibility.md`](docs/host_compatibility.md)).
- Indexed in community "awesome" lists for the agent-skills ecosystem.
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
