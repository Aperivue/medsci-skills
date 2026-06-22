#!/usr/bin/env python3
"""Opt-in Claude Code SessionStart notifier for MedSci Skills.

Prints a single `{"systemMessage": ...}` line when a newer release exists, or nothing. It is OFF by
default — registered into ~/.claude/settings.json only on explicit opt-in
(`install.py --enable-update-notify`) and removed by `install.py --disable-update-notify`.

Privacy & safety, by construction:
  * Does NOT read the SessionStart stdin — your cwd, transcript path, and session id are never read
    or transmitted. No telemetry, no analytics, no unique install id.
  * The only network call is a single GitHub version GET, and only when the shared 24h cache is
    stale. It uses a short timeout and exits SILENTLY on any error/timeout, so it never delays or
    blocks a session.
  * Honors `MEDSCI_NO_UPDATE_CHECK=1` (silent, no network).
  * Surfaces via `systemMessage` (shown to you), not stdout context — it adds nothing to the model's
    context.

Lives next to update.py / medsci_txn.py in ~/.medsci-skills/updater/ and reuses their cached,
clock-sane version check.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medsci_txn  # noqa: E402
import update  # noqa: E402

HOOK_HTTP_TIMEOUT = 4  # keep SessionStart snappy; only the rare cache-miss path waits at all


def main() -> int:
    # Never read stdin (privacy). Never raise. Worst case: print nothing.
    if os.environ.get("MEDSCI_NO_UPDATE_CHECK"):
        return 0
    try:
        home = medsci_txn.state_home()
        inst = update.installed_version(home)
        inst_v = update.parse_semver(inst)
        if inst_v is None:
            return 0  # not installed via the transactional installer -> say nothing

        tag = update._cache_fresh(home)  # clock-sane 24h cache (shared with --check-update)
        if tag is None:
            try:
                tag = update.resolve_latest_tag(
                    lambda u: update._real_get_json(u, timeout=HOOK_HTTP_TIMEOUT)
                )
                update._cache_store(home, tag)
            except Exception:  # noqa: BLE001 - offline / slow / API error -> stay silent, never block
                return 0

        latest_v = update.parse_semver(tag[1:] if tag.startswith("v") else tag)
        if latest_v and latest_v > inst_v:
            msg = (
                f"MedSci Skills update available — installed {inst}, latest {tag}. "
                f"Run the updater in ~/.medsci-skills/updater/ (or the 'Update MedSci Skills' Desktop "
                f"launcher) to update. Set MEDSCI_NO_UPDATE_CHECK=1 to silence this notice."
            )
            print(json.dumps({"systemMessage": msg, "suppressOutput": True}))
    except Exception:  # noqa: BLE001 - a notifier must never disrupt a session
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
