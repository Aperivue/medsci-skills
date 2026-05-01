#!/usr/bin/env bash
# check_deps.sh — verify pandoc + xelatex + CJK font availability.
set -u

ok=0
fail=0

check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "[OK] $name"
    ok=$((ok + 1))
  else
    echo "[MISS] $name"
    fail=$((fail + 1))
  fi
}

check "pandoc" command -v pandoc
check "xelatex" command -v xelatex

if [[ "$(uname)" == "Darwin" ]]; then
  if /usr/bin/fc-list 2>/dev/null | grep -qi "Apple SD Gothic Neo" \
     || system_profiler SPFontsDataType 2>/dev/null | grep -qi "Apple SD Gothic Neo"; then
    echo "[OK] Apple SD Gothic Neo (macOS)"
    ok=$((ok + 1))
  else
    echo "[WARN] Apple SD Gothic Neo not detected — falling back to default fontconfig"
  fi
else
  if fc-list 2>/dev/null | grep -qi "Noto.*CJK.*KR"; then
    echo "[OK] Noto Sans/Serif CJK KR"
    ok=$((ok + 1))
  else
    echo "[MISS] Noto CJK KR — apt install fonts-noto-cjk"
    fail=$((fail + 1))
  fi
fi

echo
echo "Summary: $ok ok, $fail fail"
exit $fail
