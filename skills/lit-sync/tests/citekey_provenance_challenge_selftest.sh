#!/usr/bin/env bash
# Self-test for the citekey-provenance challenge card.
#
# A card that passes proves it RAN. It proves nothing about whether it would catch a
# defect. So: mutate the detector five ways, each removing a behaviour the card claims to
# assert, and require the card to FAIL every time. If any mutation slips through green,
# the card is blind on that axis and this exits 1.
#
# The five mutations are the mistakes this detector is actually exposed to:
#   1. --strict fails on UNRESOLVED too      (a paper never added != a composed citekey)
#   2. the empty-library guard is dropped    (an empty .bib condemns every note, saying nothing)
#   3. the notetype filter is dropped        (concept notes get judged as literature notes)
#   4. the DOI suggestion is disabled        (INVENTED silently degrades to UNRESOLVED)
#   5. the filename check is dropped         (a note whose filename disagrees reads as OK)
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CARD="$HERE/citekey_provenance_challenge.sh"
SRC="$HERE/../scripts/check_citekey_provenance.py"
[ -f "$CARD" ] || { echo "missing card: $CARD"; exit 2; }
[ -f "$SRC" ]  || { echo "missing detector: $SRC"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

python3 - "$SRC" "$CARD" "$WORK" <<'PY'
import pathlib, subprocess, sys

src_path, card, work = sys.argv[1], sys.argv[2], sys.argv[3]
src = pathlib.Path(src_path).read_text(encoding="utf-8")

MUTATIONS = {
    "--strict fires on UNRESOLVED too": (
        'if args.strict and counts["INVENTED"]:',
        'if args.strict and (counts["INVENTED"] or counts["UNRESOLVED"]):',
    ),
    "empty-library guard removed": (
        "        return 2\n\n    rows = []",
        "        pass\n\n    rows = []",
    ),
    "notetype filter removed": (
        'if field(fm, "notetype") != "literature":\n            continue',
        "if False:\n            continue",
    ),
    "DOI suggestion disabled": (
        'suggestion = doi_to_key.get(doi, "") if doi else ""',
        'suggestion = ""',
    ),
    "filename check removed": (
        'verdict = "OK" if path.stem == citekey else "FILENAME"',
        'verdict = "OK"',
    ),
}

# The card must pass against the real detector, or the mutations below prove nothing.
real = subprocess.run(["bash", card, src_path], capture_output=True, text=True)
if real.returncode != 0:
    print("FAIL: the card does not pass against the unmutated detector")
    print(real.stdout[-2000:])
    sys.exit(1)
print("  PASS  card is green against the real detector")

blind = []
for label, (old, new) in MUTATIONS.items():
    n = src.count(old)
    if n != 1:
        print(f"  FAIL  {label}: anchor matched {n} time(s) — the detector changed, "
              "so this self-test no longer tests what it claims")
        blind.append(label)
        continue
    mutant = pathlib.Path(work) / "mutant.py"
    mutant.write_text(src.replace(old, new), encoding="utf-8")
    r = subprocess.run(["bash", card, str(mutant)], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  FAIL  {label}: the card stayed GREEN — it is blind on this axis")
        blind.append(label)
    else:
        fired = sum(1 for l in r.stdout.splitlines() if l.strip().startswith("FAIL"))
        print(f"  PASS  {label}: card failed as it must ({fired} assertion(s) fired)")

if blind:
    print(f"\n{len(blind)} mutation(s) went undetected: {', '.join(blind)}")
    sys.exit(1)
print(f"\nall {len(MUTATIONS)} mutations caught")
PY
