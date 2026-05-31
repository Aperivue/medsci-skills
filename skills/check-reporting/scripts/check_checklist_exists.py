#!/usr/bin/env python3
"""Fail-fast guard for /check-reporting checklist routing.

The /check-reporting skill assesses a manuscript against a vendored reporting
guideline checklist (references/checklists/*.md). Historically, when a routed
checklist file was absent the skill silently fell back to constructing the
checklist "from its knowledge of the guideline" — a fabrication path that is
exactly what the rest of the skill exists to prevent. This guard makes that
case loud:

  - The requested guideline resolves to a vendored file that exists  -> exit 0.
  - It resolves to a known guideline whose file is ABSENT            -> exit 1,
    prints MISSING_CHECKLIST_CONTRACT_VIOLATION.
  - The name is not a recognised guideline                           -> exit 2,
    prints UNKNOWN_GUIDELINE.

`--allow-from-memory` is the single explicit opt-in escape hatch: it downgrades
exit 1/2 to exit 0 but always emits a NON-AUTHORITATIVE warning, so a
construct-from-memory assessment can never happen silently.

Source of truth for "what is vendored" is the checklists directory on disk, not
this file — the alias map only translates display names to filename stems.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Display/guideline name (normalised) -> checklist filename stem.
# Keys are normalised by _norm(): lowercased, with spaces/hyphens/dots/plus/
# underscores and a trailing 4-digit year stripped. The stem is the expected
# file under references/checklists/<stem>.md. A stem whose file is absent is a
# contract violation, surfaced loudly rather than silently fabricated.
ALIAS_TO_STEM = {
    "strobe": "STROBE",
    "consort": "CONSORT",
    "consortai": "CONSORT_AI",
    "stard": "STARD",
    "stardai": "STARD_AI",
    "tripod": "TRIPOD",
    "tripodai": "TRIPOD_AI",
    "prisma": "PRISMA_2020",
    "prismadta": "PRISMA_DTA",
    "prismap": "PRISMA_P",
    "arrive": "ARRIVE_2",
    "care": "CARE",
    "spirit": "SPIRIT",
    "spiritai": "SPIRIT_AI",
    "claim": "CLAIM_2024",
    "miclearllm": "MI_CLEAR_LLM",
    "squire": "SQUIRE_2",
    "clear": "CLEAR",
    "moose": "MOOSE",
    "grras": "GRRAS",
    "swim": "SWiM",
    "amstar": "AMSTAR2",
    "amstar2": "AMSTAR2",
    "quadas": "QUADAS2",
    "quadas2": "QUADAS2",
    "quadasc": "QUADAS_C",
    "rob2": "RoB2",
    "robinsi": "ROBINS_I",
    "robinse": "ROBINS_E",
    "robis": "ROBIS",
    "robme": "ROB_ME",
    "robnma": "RoB_NMA",
    "probast": "PROBAST",
    "probastai": "PROBAST_AI",
    "nos": "NOS",
    "cosmin": "COSMIN_RoB",
    "cosminrob": "COSMIN_RoB",
}

EXIT_OK = 0
EXIT_MISSING = 1
EXIT_UNKNOWN = 2


def _norm(name: str) -> str:
    """Normalise a guideline name to an alias key.

    Lowercase, drop a trailing 4-digit year, then strip spaces/hyphens/dots/
    plus/underscores. "STARD-AI" -> "stardai"; "AMSTAR 2" -> "amstar2";
    "CONSORT 2010" -> "consort"; "TRIPOD+AI" -> "tripodai".
    """
    n = name.strip().lower()
    n = re.sub(r"\b(19|20)\d{2}\b", "", n)          # drop version year
    n = re.sub(r"[\s\-_.+]", "", n)                 # strip spaces/-/_/./+
    return n


def checklist_dir(skill_dir: Path) -> Path:
    return skill_dir / "references" / "checklists"


def resolve_stem(guideline: str) -> str | None:
    return ALIAS_TO_STEM.get(_norm(guideline))


def available_stems(cdir: Path) -> list[str]:
    if not cdir.is_dir():
        return []
    return sorted(p.stem for p in cdir.glob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-fast guard: confirm a routed reporting-guideline checklist is vendored."
    )
    parser.add_argument("--guideline", help="Guideline name, e.g. 'STROBE', 'STARD-AI', 'CONSORT 2010'.")
    parser.add_argument(
        "--skill-dir",
        default=str(Path(__file__).resolve().parent.parent),
        help="check-reporting skill root (default: inferred from this script).",
    )
    parser.add_argument(
        "--allow-from-memory",
        action="store_true",
        help="Explicit opt-in: downgrade a missing/unknown checklist to exit 0 with a "
             "NON-AUTHORITATIVE warning instead of failing. Never silent.",
    )
    parser.add_argument(
        "--simulate-missing-checklist",
        action="store_true",
        help="Force the missing-file path (for contract tests).",
    )
    parser.add_argument("--list", action="store_true", help="List vendored checklist files and exit.")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    cdir = checklist_dir(skill_dir)

    if args.list:
        stems = available_stems(cdir)
        print(f"{len(stems)} vendored checklists in {cdir}:")
        for s in stems:
            print(f"  {s}")
        return EXIT_OK

    if args.simulate_missing_checklist:
        print("MISSING_CHECKLIST_CONTRACT_VIOLATION: simulated missing checklist "
              "(guideline routed but no vendored file).", file=sys.stderr)
        if args.allow_from_memory:
            print("WARNING: --allow-from-memory set; a from-memory (NON-AUTHORITATIVE) "
                  "assessment would proceed. The report MUST be marked non-vendored.")
            return EXIT_OK
        return EXIT_MISSING

    if not args.guideline:
        parser.error("--guideline is required (or use --list / --simulate-missing-checklist)")

    stem = resolve_stem(args.guideline)
    if stem is None:
        print(f"UNKNOWN_GUIDELINE: '{args.guideline}' is not a recognised reporting guideline.",
              file=sys.stderr)
        if args.allow_from_memory:
            print("WARNING: --allow-from-memory set; proceeding from memory for an unrecognised "
                  "guideline (NON-AUTHORITATIVE). The report MUST be marked non-vendored.")
            return EXIT_OK
        return EXIT_UNKNOWN

    path = cdir / f"{stem}.md"
    if path.is_file():
        print(f"OK: {args.guideline} -> references/checklists/{stem}.md")
        return EXIT_OK

    print(f"MISSING_CHECKLIST_CONTRACT_VIOLATION: '{args.guideline}' resolves to "
          f"'{stem}.md' which is not vendored under {cdir}.", file=sys.stderr)
    if args.allow_from_memory:
        print(f"WARNING: --allow-from-memory set; proceeding from memory for '{args.guideline}' "
              f"(NON-AUTHORITATIVE). The report MUST be marked non-vendored.")
        return EXIT_OK
    return EXIT_MISSING


if __name__ == "__main__":
    sys.exit(main())
