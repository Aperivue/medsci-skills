#!/usr/bin/env python3
"""Validate skill contract files (dual-schema v1.1.1).

schema_version policy:
  - 1 (legacy)  -> WARN during 3-month transition (2026-04-24 -> 2026-07-24),
                   FAIL thereafter
  - 2           -> ENFORCE strict requirements (layer, when_to_use, etc.)

Missing skill.yml -> WARN (migration in progress).
Malformed skill.yml -> FAIL.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path


V1_SUNSET = "2026-07-24"

REQUIRED_V1 = {
    "schema_version",
    "name",
    "owner_domain",
    "inputs",
    "outputs",
    "deterministic_scripts",
    "side_effects",
    "downstream_consumers",
    "forbidden_actions",
}

REQUIRED_V2 = {
    "schema_version",
    "name",
    "layer",
    "owner_domain",
    "when_to_use",
    "when_NOT_to_use",
    "inputs",
    "outputs",
    "side_effects",
    "downstream_consumers",
    "forbidden_actions",
}

VALID_LAYERS = {"A", "B", "C", "D"}

LIST_FIELDS = {
    "inputs",
    "outputs",
    "deterministic_scripts",
    "deterministic_steps",
    "side_effects",
    "downstream_consumers",
    "forbidden_actions",
    "exclusive_with",
    "sequence_after",
    "aliases",
}


def parse_top_level_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t", "-")):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if match:
            keys.add(match.group(1))
    return keys


def extract_scalar(text: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.M)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")


def list_has_item(text: str, key: str) -> bool:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"^{re.escape(key)}:\s*(.*)$", line):
            same_line = line.split(":", 1)[1].strip()
            if same_line and same_line not in {"[]", "null", "{}"}:
                return True
            for nxt in lines[i + 1:]:
                if nxt and not nxt.startswith((" ", "\t", "-")):
                    return False
                if re.match(r"^\s*-\s+\S+", nxt):
                    return True
            return False
    return False


def past_v1_sunset() -> bool:
    return _dt.date.today().isoformat() >= V1_SUNSET


def validate_v2(path: Path, skill_name: str, text: str, keys: set[str]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_V2 - keys
    if missing:
        errors.append(f"v2 missing keys: {', '.join(sorted(missing))}")

    name_val = extract_scalar(text, "name")
    if name_val and name_val != skill_name:
        errors.append(f"name mismatch: contract has {name_val!r}, directory is {skill_name!r}")

    layer_val = extract_scalar(text, "layer")
    if layer_val and layer_val not in VALID_LAYERS:
        errors.append(f"layer invalid: {layer_val!r} (must be A/B/C/D)")

    for key in LIST_FIELDS & keys:
        if not list_has_item(text, key):
            errors.append(f"{key} must contain at least one item")

    return errors


def validate_v1(path: Path, skill_name: str, text: str, keys: set[str]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_V1 - keys
    if missing:
        errors.append(f"v1 missing keys: {', '.join(sorted(missing))}")

    name_val = extract_scalar(text, "name")
    if name_val and name_val != skill_name:
        errors.append(f"name mismatch: contract has {name_val!r}, directory is {skill_name!r}")

    for key in {"inputs", "outputs", "deterministic_scripts", "side_effects",
                "downstream_consumers", "forbidden_actions"} & keys:
        if not list_has_item(text, key):
            errors.append(f"{key} must contain at least one item")

    return errors


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    skills_dir = repo / "skills"
    failures = 0
    warnings = 0
    v1_count = 0
    v2_count = 0

    print("=========================================")
    print(" MedSci Skill Contract Validator (v1+v2)")
    print("=========================================")
    sunset_msg = f" (v1 sunset {V1_SUNSET})"
    if past_v1_sunset():
        sunset_msg = f" (PAST v1 sunset {V1_SUNSET}: v1 is now FAIL)"
    print(sunset_msg)

    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        contract = skill_dir / "skill.yml"
        if not contract.exists():
            warnings += 1
            print(f"WARN {skill_dir.name}: skill.yml missing (migration warning)")
            continue

        text = contract.read_text(encoding="utf-8")
        keys = parse_top_level_keys(text)
        schema_version = extract_scalar(text, "schema_version") or "1"

        if schema_version == "2":
            v2_count += 1
            errors = validate_v2(contract, skill_dir.name, text, keys)
            if errors:
                failures += 1
                print(f"FAIL {skill_dir.name} [v2]: {'; '.join(errors)}")
            else:
                print(f"PASS {skill_dir.name} [v2]")
        elif schema_version == "1":
            v1_count += 1
            errors = validate_v1(contract, skill_dir.name, text, keys)
            if past_v1_sunset():
                # Escalate: v1 failures and a sunset error
                errors.append(f"v1 past sunset {V1_SUNSET}; upgrade to schema_version: 2")
                failures += 1
                print(f"FAIL {skill_dir.name} [v1-expired]: {'; '.join(errors)}")
            elif errors:
                failures += 1
                print(f"FAIL {skill_dir.name} [v1]: {'; '.join(errors)}")
            else:
                warnings += 1
                print(f"WARN {skill_dir.name} [v1]: valid but upgrade to v2 before {V1_SUNSET}")
        else:
            failures += 1
            print(f"FAIL {skill_dir.name}: unknown schema_version {schema_version!r}")

    cap = repo / "capabilities.yml"
    if not cap.exists():
        failures += 1
        print("FAIL capabilities.yml missing")
    else:
        text = cap.read_text(encoding="utf-8")
        missing_markers = [m for m in ("schema_version:", "domains:", "owner:", "rule:") if m not in text]
        if missing_markers:
            failures += 1
            print(f"FAIL capabilities.yml missing markers: {missing_markers}")
        else:
            print("PASS capabilities.yml")

    print("=========================================")
    print(f" v1 contracts: {v1_count}  |  v2 contracts: {v2_count}")
    print(f" Contract warnings: {warnings}")
    print(f" Contract failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
