#!/usr/bin/env bash
# Regression test for /lit-sync Phase 2.5 mtime-polling logic.
#
# Four synthetic scenarios (origin: ~/.local/cache/phase1b_b_dryrun/ dry-run,
# 2026-04-24). Runs in an isolated tmpdir; does not touch any real Zotero or
# project files. macOS (stat -f) and Linux (stat -c) compatible.
#
# Usage: bash skills/lit-sync/tests/test_poll_logic.sh
# Exit:  0 all pass, 1 any scenario fails.

set -u

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Inline poll script — same logic shipped with lit-sync Phase 2.5 guidance.
POLL="$TMP/poll.sh"
cat > "$POLL" <<'POLL_EOF'
#!/usr/bin/env bash
TARGET="$1"
TIMEOUT="${2:-10}"
if stat -f "%m" /dev/null >/dev/null 2>&1; then
    STAT_CMD='stat -f %m'
else
    STAT_CMD='stat -c %Y'
fi
BEFORE=$($STAT_CMD "$TARGET")
START=$(date +%s)
while true; do
    NOW=$($STAT_CMD "$TARGET")
    if [[ "$NOW" != "$BEFORE" ]]; then
        ELAPSED=$(( $(date +%s) - START ))
        echo "DETECTED mtime change after ${ELAPSED}s"
        exit 0
    fi
    if (( $(date +%s) - START >= TIMEOUT )); then
        echo "TIMEOUT after ${TIMEOUT}s"
        exit 1
    fi
    sleep 0.5
done
POLL_EOF
chmod +x "$POLL"

PASS=0
FAIL=0

run_scenario() {
    local name="$1" window="$2" write_at="$3" expected_exit="$4"
    local bib="$TMP/refs_${name//[^a-z0-9]/_}.bib"
    echo "@misc{test, title={x}}" > "$bib"
    # Age the file so mtime isn't "now" (macOS second-granularity could cause
    # the initial BEFORE to match a sub-second later write).
    touch -t 202001010000 "$bib"

    if [[ "$write_at" != "none" ]]; then
        ( sleep "$write_at" && echo "@misc{test, title={y}}" > "$bib" ) &
        WRITER_PID=$!
    else
        WRITER_PID=""
    fi

    "$POLL" "$bib" "$window" >/dev/null
    local actual=$?

    [[ -n "$WRITER_PID" ]] && wait "$WRITER_PID" 2>/dev/null

    if [[ "$actual" == "$expected_exit" ]]; then
        echo "  PASS  [$name] exit=$actual (expected $expected_exit)"
        PASS=$((PASS+1))
    else
        echo "  FAIL  [$name] exit=$actual (expected $expected_exit)"
        FAIL=$((FAIL+1))
    fi
}

echo "Phase 2.5 polling regression (4 scenarios)"
echo "  Tmpdir: $TMP"
echo

# Timing slack. The poller reads `date +%s`, so both START and the `>= TIMEOUT`
# comparison are whole seconds: the deadline can fire up to ~1s early on top of any
# sleep overshoot. Each scenario therefore needs its write and its deadline several
# seconds apart, not one or two.
#
# Widening a DETECT scenario's window costs no runtime — it exits the moment it sees
# the mtime change, so the window is only a deadline. Narrowing a TIMEOUT scenario's
# window shortens it. The slack column is the gap these margins buy.
#
#                                              window  write_at   slack
# 1. BBT write within window → detect
run_scenario "detect-within-window" 10 3 0   #     10         3      7s
# 2. No write, short window → timeout
run_scenario "timeout-silent" 3 none 1       #      3      none     n/a
# 3. BBT debounce, late-but-within write → detect
run_scenario "debounce-late" 14 8 0          #     14         8      6s
# 4. Slow BBT, write outside window → timeout (Phase 2.5 fallback prompt)
run_scenario "slow-bbt-timeout" 2 8 1        #      2         8      6s

echo
echo "Summary: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]]
