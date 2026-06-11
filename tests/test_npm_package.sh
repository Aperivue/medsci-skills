#!/usr/bin/env bash
# Self-test for the npm/npx distribution baseline (PR0).
# Verifies the CLI shim, executable bit, version sync, and the pack-content audit.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "  ok: $1"; }

echo "== test_npm_package =="

# 1. CLI is executable (required #2).
[ -x bin/medsci-skills.js ] || fail "bin/medsci-skills.js is not executable (chmod +x)"
pass "bin/medsci-skills.js is executable"

# 2. Shebang present.
head -1 bin/medsci-skills.js | grep -q '^#!/usr/bin/env node' || fail "missing '#!/usr/bin/env node' shebang"
pass "node shebang present"

# 3. --help exits 0 and mentions install.
node bin/medsci-skills.js --help >/tmp/msk_help.txt 2>&1 || fail "--help exited non-zero"
grep -qi 'install' /tmp/msk_help.txt || fail "--help did not mention install"
pass "--help works"

# 4. --version matches package.json.
PKG_VER="$(node -e "process.stdout.write(require('./package.json').version)")"
CLI_VER="$(node bin/medsci-skills.js --version | tr -d '[:space:]')"
[ "$PKG_VER" = "$CLI_VER" ] || fail "version mismatch: package.json=$PKG_VER cli=$CLI_VER"
pass "--version matches package.json ($PKG_VER)"

# 5. list reads the catalog and prints the skill count.
node bin/medsci-skills.js list >/tmp/msk_list.txt 2>&1 || fail "list exited non-zero"
grep -qiE 'MedSci Skills .* [0-9]+ skills' /tmp/msk_list.txt || fail "list did not print a skill count"
pass "list works"

# 6. doctor runs (python3 present in CI -> exit 0; tolerate absence locally).
if node bin/medsci-skills.js doctor >/tmp/msk_doctor.txt 2>&1; then
  pass "doctor ran (exit 0)"
else
  echo "  note: doctor exited non-zero (python3 likely absent) — tolerated"
fi
grep -qi 'setup-medsci' /tmp/msk_doctor.txt || fail "doctor did not point to setup-medsci"
pass "doctor points to setup-medsci"

# 7. pack-content audit passes (no denied paths, required present).
python3 scripts/check_npm_package_contents.py || fail "npm pack content audit failed"
pass "npm pack content audit clean"

echo "PASS: test_npm_package"
