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

# Windows/Git Bash: MiKTeX's bin directory is frequently absent from the Git Bash
# PATH, so xelatex reads as [MISS] even after `winget install MiKTeX.MiKTeX`.
# Best-effort: prepend the known MiKTeX bin locations when xelatex is not resolvable.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if ! command -v xelatex >/dev/null 2>&1; then
      _la="$(cygpath -u "${LOCALAPPDATA:-}" 2>/dev/null || printf '%s' "${LOCALAPPDATA:-}")"
      _pf="$(cygpath -u "${PROGRAMFILES:-}" 2>/dev/null || printf '%s' "${PROGRAMFILES:-}")"
      for _d in \
        "$_la/Programs/MiKTeX/miktex/bin/x64" \
        "$_la/Programs/MiKTeX/miktex/bin" \
        "$_pf/MiKTeX/miktex/bin/x64"; do
        if [[ -x "$_d/xelatex.exe" ]]; then PATH="$_d:$PATH"; break; fi
      done
    fi
    ;;
esac

check "pandoc" command -v pandoc
check "xelatex" command -v xelatex

case "$(uname -s)" in
  Darwin)
    if /usr/bin/fc-list 2>/dev/null | grep -qi "Apple SD Gothic Neo" \
       || system_profiler SPFontsDataType 2>/dev/null | grep -qi "Apple SD Gothic Neo"; then
      echo "[OK] Apple SD Gothic Neo (macOS)"
      ok=$((ok + 1))
    else
      echo "[WARN] Apple SD Gothic Neo not detected — falling back to default fontconfig"
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    _win="$(cygpath -u "${WINDIR:-}" 2>/dev/null || printf '%s' "${WINDIR:-}")"
    [[ -z "$_win" ]] && _win="/c/Windows"
    if [[ -f "$_win/Fonts/malgun.ttf" ]]; then
      echo "[OK] Malgun Gothic (Windows)"
      ok=$((ok + 1))
    else
      echo "[WARN] Malgun Gothic not detected — it ships with Windows 7+; see C:\\Windows\\Fonts"
    fi
    ;;
  *)
    if fc-list 2>/dev/null | grep -qi "Noto.*CJK.*KR"; then
      echo "[OK] Noto Sans/Serif CJK KR"
      ok=$((ok + 1))
    else
      echo "[MISS] Noto CJK KR — apt install fonts-noto-cjk"
      fail=$((fail + 1))
    fi
    ;;
esac

echo
echo "Summary: $ok ok, $fail fail"
exit $fail
