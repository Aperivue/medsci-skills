# Adoption metrics (data branch)

Weekly snapshots appended by `.github/workflows/metrics.yml` on `main`. This branch holds
data only, has no code, and is never merged.

- `traffic_log.csv`: stars, forks, release downloads, 14-day views and clones, Zenodo views and downloads
- `referrers_log.csv`: top referring sites per run
- `paths_log.csv`: top viewed paths per run

Rows before 2026-10 were also committed to `metrics/` on `main`, which still has that history.
