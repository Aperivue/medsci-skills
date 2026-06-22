# Updating — privacy & data notice

The self-updater exists so physician-researchers can stay current without using GitHub, git,
or a terminal. It is intentionally minimal about data.

## What it connects to

- **`api.github.com`** — a single public, read-only GitHub REST call to look up the latest
  release of `Aperivue/medsci-skills` (tag + the release asset's name and SHA-256 digest).
- **GitHub's release-asset host** (`*.githubusercontent.com`) — to download the classroom ZIP
  for your operating system over HTTPS.

No other servers are contacted.

## What is (and is not) sent

- The only thing sent is an ordinary HTTPS GET request (with a generic `User-Agent:
  medsci-skills-updater`). GitHub, like any web host, sees your IP address and the request.
- **Nothing about your machine or work is collected or transmitted.** The updater does **not**
  read or send your working directory, file contents, transcripts, session data, or skill usage.
  There is **no telemetry, no analytics, and no unique install identifier**.
- Because GitHub is a US-based service, the network request may be processed outside your country.

## What is stored locally

Everything the updater writes stays on your computer under `~/.medsci-skills/`:

- `targets/<target>/` — what version is installed where (an installed-manifest + small state file).
- `backups/<timestamp>/<target>/` — snapshots of any skill you had modified, kept before an update
  overwrites it. **These are never deleted automatically** — remove them yourself when you no longer
  need them.
- `updater/` — the one-click updater itself.
- `update_check.json` — a small cache so the update check runs at most once a day.

Install logs are written next to the installer and **mask your home directory as `~`**.

## Opt-in session-start notice (Claude Code)

`python3 installers/install.py --enable-update-notify` registers a Claude Code **SessionStart** hook
that prints a one-line *"update available"* notice and nothing else. It is **off by default** and is
the only thing that writes to `~/.claude/settings.json` (it merges one hook entry and preserves your
existing settings).

The hook is built to be safe:

- It **does not read the SessionStart input** — your working directory, transcript path, and session
  id are never read or transmitted. There is no telemetry, no analytics, and no unique id.
- Its only network call is the same single GitHub version GET described above, made **at most once a
  day** (a 24-hour cache), with a short timeout. On any error or timeout it stays silent, so it never
  delays or blocks a session.
- It honors `MEDSCI_NO_UPDATE_CHECK=1` and installs nothing — it only *tells* you an update exists.

Remove it any time with `python3 installers/install.py --disable-update-notify` (which removes only
that hook and leaves the rest of `settings.json` intact).

## Checking, opting out, and uninstalling

- **Check only:** `python3 installers/install.py --check-update` reports whether a newer version
  exists and installs nothing.
- **Turn off the opt-in session-start notice:** `python3 installers/install.py --disable-update-notify`,
  or set `MEDSCI_NO_UPDATE_CHECK=1` to silence it without removing it.
- **Uninstall the updater / state:** delete the `~/.medsci-skills/` folder (and any Desktop
  "Update MedSci Skills" launcher you chose to create). The installed skills under
  `~/.claude/skills` / `~/.agents/skills` are separate and remain until you remove them.

## Security note (honest scope)

Downloading a release and running its bundled installer is, by nature, **running code from
GitHub**. The updater verifies the download's SHA-256 against the digest GitHub's API reports for
that release asset, which **detects a corrupted or tampered-in-transit download** — it does **not**
protect against a compromised GitHub account or a malicious official release. Treat updates with the
same trust you place in this GitHub repository.
