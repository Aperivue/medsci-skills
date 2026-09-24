#!/usr/bin/env bash
# Install this repository's local git hooks.
#
# WHY A HOOK AT ALL
#   CI can refuse three things deterministically — a co-reviewer's report, an editor's decision, a
#   submission ID — because nothing legitimate in this repository does them. It cannot judge the
#   rest, because "does this paragraph identify someone" is a reading task and no threshold over a
#   fetch date or a rounded statistic separates the two. That judgement has to happen where the
#   prose is written, by something that can read.
#
#   The 2026-08 audit is a case study in why it cannot be a step people remember to run: every leak
#   it found was written by someone who would have said yes if asked, and nobody was asked.
#
# WHAT THE HOOK DOES
#   pre-push: sends the ADDED lines of the push to `claude -p` and asks whether any of them would
#   let a reader identify a real person, manuscript, review, submission or dataset. Blocks on
#   IDENTIFIES. Added LINES, not just paragraphs, because two of the six findings that motivated
#   this were a table row and a bullet list, and the paragraph-level router cannot see either.
#
#   No `claude` on PATH → prints and exits 0. Most contributors do not have it, and a checklist
#   typo must never be blocked by a tool nobody has.
#
#   Escape hatch: `git push --no-verify`, or MEDSCI_SKIP_PII_HOOK=1. Both are legitimate — a hook
#   you cannot get past is a hook people uninstall. It is logged so the skip is visible later.
#
# Usage:  bash scripts/install_git_hooks.sh [--uninstall]
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_DIR="$(git -C "$REPO_ROOT" rev-parse --git-path hooks 2>/dev/null)"
[ -d "$HOOK_DIR" ] || HOOK_DIR="$REPO_ROOT/.git/hooks"
HOOK="$HOOK_DIR/pre-push"

if [ "${1:-}" = "--uninstall" ]; then
  if [ -f "$HOOK" ] && grep -q 'medsci-pii-hook' "$HOOK" 2>/dev/null; then
    rm -f "$HOOK"; echo "removed $HOOK"
  else
    echo "no medsci pre-push hook installed at $HOOK"
  fi
  exit 0
fi

if [ -f "$HOOK" ] && ! grep -q 'medsci-pii-hook' "$HOOK" 2>/dev/null; then
  echo "refusing to overwrite an existing pre-push hook that is not ours:"
  echo "  $HOOK"
  echo "Merge it by hand, or move it aside and re-run."
  exit 1
fi

mkdir -p "$HOOK_DIR"
cat > "$HOOK" <<'HOOK_BODY'
#!/usr/bin/env bash
# medsci-pii-hook — ask a model whether anything about to be pushed identifies a real case.
# Installed by scripts/install_git_hooks.sh. Skip with --no-verify or MEDSCI_SKIP_PII_HOOK=1.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"
LOG="${HOME}/.local/log/medsci-pii-hook.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null

if [ "${MEDSCI_SKIP_PII_HOOK:-0}" = "1" ]; then
  echo "[medsci-pii-hook] skipped via MEDSCI_SKIP_PII_HOOK=1"
  echo "$(date -u +%FT%TZ) skipped-env $(git rev-parse --short HEAD)" >> "$LOG" 2>/dev/null
  exit 0
fi

[ -x "$ROOT/scripts/llm_provenance_review.sh" ] || exit 0

echo "[medsci-pii-hook] reviewing added lines before push..."
if bash "$ROOT/scripts/llm_provenance_review.sh" --diff --strict; then
  echo "$(date -u +%FT%TZ) pass $(git rev-parse --short HEAD)" >> "$LOG" 2>/dev/null
  exit 0
fi

echo ""
echo "[medsci-pii-hook] push blocked: a model judged an added line identifying."
echo "  Keep the lesson, drop the identifying half — docs/grounding_without_identifying.md"
echo "  A model's verdict is an opinion. If it is wrong, push with --no-verify and say so in the PR."
echo "$(date -u +%FT%TZ) blocked $(git rev-parse --short HEAD)" >> "$LOG" 2>/dev/null
exit 1
HOOK_BODY

chmod +x "$HOOK"
echo "installed $HOOK"
if command -v claude >/dev/null 2>&1; then
  echo "  \`claude\` found — the hook will ask a model on every push."
else
  echo "  \`claude\` NOT on PATH — the hook will report and let the push through (by design)."
fi
echo "  skip once:  git push --no-verify      log: ~/.local/log/medsci-pii-hook.log"
