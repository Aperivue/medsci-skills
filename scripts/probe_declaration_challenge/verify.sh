#!/usr/bin/env bash
# Challenge card for check_probe_declaration.py.
#
# A green gate proves it RAN. These fixtures are built at runtime and each carries exactly
# one defect the gate claims to catch, so a green run against a broken module is reported
# here rather than discovered in a review.
#
# The last case is the one that bit the gate's own first draft: the repository numbers a
# gate probe zero and excludes it from the "N-probe checklist" count. A checker that only
# accepts its own preferred spelling is this repository's most common detector defect, and
# this card pins that convention so a later edit cannot quietly drop it.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="${1:-$HERE/../check_probe_declaration.py}"
[ -f "$GATE" ] || { echo "cannot find check_probe_declaration.py at $GATE"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0; FAIL=0
check() { if [ "$2" = "$3" ]; then printf '  PASS  %s\n' "$1"; PASS=$((PASS+1));
          else printf '  FAIL  %s (expected %s, got %s)\n' "$1" "$2" "$3"; FAIL=$((FAIL+1)); fi }

run() { # run <dir> -> exit code of the gate in --strict mode
  python3 "$GATE" --dir "$1" --strict > /dev/null 2>&1; echo $?
}

mk() { # mk <dir> <file> <body>
  mkdir -p "$1"; printf '%s\n' "$3" > "$1/$2"
}

CLEAN='# Example probes (EX1–EX3)

A 3-probe checklist for the thing.

**EX1 — first**: body.

**EX2 — second**: body.

**EX3 — third**: body.'

# ------------------------------------------------------------------ the happy path
mk "$WORK/clean" ex.md "$CLEAN"
check "a self-consistent module passes" 0 "$(run "$WORK/clean")"

# ------------------------------------------------- title under-declares its contents
mk "$WORK/under" ex.md "${CLEAN/EX1–EX3/EX1–EX2}"
check "title declaring fewer probes than exist fails" 1 "$(run "$WORK/under")"

# -------------------------------------------------- title over-declares its contents
mk "$WORK/over" ex.md "${CLEAN/EX1–EX3/EX1–EX9}"
check "title declaring more probes than exist fails" 1 "$(run "$WORK/over")"

# ------------------------------------------------------------ stale body count
mk "$WORK/count" ex.md "${CLEAN/A 3-probe/A 5-probe}"
check "stale \"N-probe checklist\" count fails" 1 "$(run "$WORK/count")"

# ------------------------------------------------------------ numbering gap
mk "$WORK/gap" ex.md "$(printf '%s' "$CLEAN" | grep -v 'EX2 — second')"
check "a numbering gap is reported" 1 "$(run "$WORK/gap")"

# ------------------------------------------ probes present but no declared range
mk "$WORK/notitle" ex.md '# Example probes

**EX1 — first**: body.'
check "probe definitions with no declared range fail" 1 "$(run "$WORK/notitle")"

# --------------------------------- hyphen and prefix-less range must both parse
mk "$WORK/hyphen" ex.md "${CLEAN/EX1–EX3/EX1-EX3}"
check "a hyphen range parses (not only an en dash)" 0 "$(run "$WORK/hyphen")"
mk "$WORK/short" ex.md "${CLEAN/EX1–EX3/EX1–3}"
check "a prefix-less range parses (EX1–3)" 0 "$(run "$WORK/short")"

# ------------------------- the repo's gate-probe convention must NOT be flagged
mk "$WORK/gateprobe" ex.md '# Example probes (EX0–EX3)

A 3-probe checklist (EX1–EX3, with EX0 as a gate) for the thing.

**EX0 — gate**: body.

**EX1 — first**: body.

**EX2 — second**: body.

**EX3 — third**: body.'
check "gate probe excluded from the count is accepted" 0 "$(run "$WORK/gateprobe")"

# ------------------------------------------------------------ input guards
mkdir -p "$WORK/empty"
check "an empty directory exits 2, not 0" 2 "$(run "$WORK/empty")"
check "a missing directory exits 2" 2 "$(run "$WORK/does-not-exist")"

# --------------------------------- without --strict a violation still exits 0
python3 "$GATE" --dir "$WORK/under" > /dev/null 2>&1
check "without --strict a violation exits 0 (repo convention)" 0 "$?"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
