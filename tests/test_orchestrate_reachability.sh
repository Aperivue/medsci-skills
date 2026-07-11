#!/usr/bin/env bash
# Self-test for scripts/check_orchestrate_reachability.py:
#  - the live repo must pass (every skill reachable from /orchestrate)
#  - a synthetic fixture that omits one skill's table row must fail (exit 1)
#  - a synthetic fixture routing to a non-existent skill (ghost) must fail
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DET="$ROOT/scripts/check_orchestrate_reachability.py"

# 1) live repo passes
python3 "$DET" --strict >/dev/null || { echo "FAIL: live repo should be fully reachable" >&2; exit 1; }

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/skills/alpha" "$tmp/skills/beta" "$tmp/skills/orchestrate"
: > "$tmp/skills/alpha/SKILL.md"; : > "$tmp/skills/beta/SKILL.md"; : > "$tmp/skills/orchestrate/SKILL.md"

# 2) omit 'beta' from the table -> must fail
cat > "$tmp/md_missing.md" <<'MD'
## Available Skills
| Skill | Domain | When to Route |
|---|---|---|
| **alpha** | X | route alpha |
## Classification Logic
MD
if python3 "$DET" --skill-md "$tmp/md_missing.md" --skills-dir "$tmp/skills" --strict >/dev/null 2>&1; then
  echo "FAIL: a missing skill row should exit 1" >&2; exit 1
fi

# 3) full table -> passes
cat > "$tmp/md_full.md" <<'MD'
## Available Skills
| Skill | Domain | When to Route |
|---|---|---|
| **alpha** | X | route alpha |
| **beta** | X | route beta |
## Classification Logic
MD
python3 "$DET" --skill-md "$tmp/md_full.md" --skills-dir "$tmp/skills" --strict >/dev/null \
  || { echo "FAIL: a complete table should exit 0" >&2; exit 1; }

# 4) ghost route (table names a non-existent skill) -> must fail
cat > "$tmp/md_ghost.md" <<'MD'
## Available Skills
| Skill | Domain | When to Route |
|---|---|---|
| **alpha** | X | route alpha |
| **beta** | X | route beta |
| **gamma** | X | route a skill that does not exist |
## Classification Logic
MD
if python3 "$DET" --skill-md "$tmp/md_ghost.md" --skills-dir "$tmp/skills" --strict >/dev/null 2>&1; then
  echo "FAIL: a ghost route should exit 1" >&2; exit 1
fi

echo "PASS: orchestrate reachability gate — live repo reachable, missing-row and ghost-route both fail."
