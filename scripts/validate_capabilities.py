#!/usr/bin/env python3
"""Skill-registry consistency check (issue #15).

`capabilities.yml` declares the *contested* domains — the ones where more than
one skill overlaps and ownership must be adjudicated (owner + overlaps). Each
`skills/<name>/skill.yml` in turn declares its `owner_domain`. Nothing currently
asserts that these two views agree, so drift accumulates silently: a malformed
`skill.yml` (an unquoted colon) parses nowhere and is never caught; a skill can
claim a declared domain it neither owns nor overlaps; a domain can name an owner
that does not exist.

This validator enforces the invariants that must hold for the registry to be
trustworthy. It deliberately encodes the *actual* design — capabilities.yml
declares only the overlapping domains; the ~30 single-skill domains are
self-owned and intentionally absent — rather than the naive "every skill in
exactly one declared domain", which would false-positive on every self-owned
skill.

Invariants
----------
  1. Every skills/*/skill.yml is valid YAML and declares `name` (== its
     directory) and a non-empty string `owner_domain`.  [catches malformation]
  2. Every declared domain's `owner` resolves to an existing skill whose own
     `owner_domain` equals that domain (owner ⇄ skill agreement).
  3. Every skill whose `owner_domain` is a *declared* domain is either that
     domain's owner or listed in its `overlaps` (no silent claimant).
  4. Every `overlaps` entry resolves to an existing skill with a skill.yml.
  5. Every umbrella's member list resolves to declared domains.

Exit 0 when the registry is consistent. With --strict, exit 1 on any drift
(CI gate). Requires PyYAML (already a CI dependency).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml


def _load_yaml(path: Path):
    """Return (data, error). error is a one-line string on parse failure."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh), None
    except yaml.YAMLError as exc:
        first = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
        return None, first
    except OSError as exc:
        return None, str(exc)


def _umbrella_members(value) -> list[str]:
    """Umbrella values are [[domain, ...], "description"]; return the domain list."""
    if isinstance(value, list) and value and isinstance(value[0], list):
        return [m for m in value[0] if isinstance(m, str)]
    if isinstance(value, dict):
        got = value.get("includes") or value.get("domains") or []
        return [m for m in got if isinstance(m, str)]
    if isinstance(value, list):
        return [m for m in value if isinstance(m, str)]
    return []


def validate(root: Path) -> list[str]:
    """Return a list of violation strings (empty == consistent)."""
    violations: list[str] = []

    cap_path = root / "capabilities.yml"
    if not cap_path.is_file():
        return [f"capabilities.yml not found at {cap_path}"]
    cap, err = _load_yaml(cap_path)
    if err:
        return [f"capabilities.yml is not valid YAML: {err}"]
    cap = cap or {}
    domains = cap.get("domains", {}) or {}
    umbrellas = cap.get("umbrellas", {}) or {}
    declared = set(domains.keys())

    # --- Invariant 1: every skill.yml valid + name + owner_domain ---
    skills_dir = root / "skills"
    skill_owner_domain: dict[str, str] = {}
    skill_dirs = sorted(p for p in skills_dir.glob("*") if p.is_dir()) if skills_dir.is_dir() else []
    for sd in skill_dirs:
        name = sd.name
        yml = sd / "skill.yml"
        if not yml.is_file():
            violations.append(f"[{name}] skill.yml missing")
            continue
        data, err = _load_yaml(yml)
        if err:
            violations.append(f"[{name}] skill.yml is not valid YAML: {err}")
            continue
        data = data or {}
        declared_name = data.get("name")
        if declared_name != name:
            violations.append(
                f"[{name}] skill.yml name={declared_name!r} does not match directory"
            )
        od = data.get("owner_domain")
        if not isinstance(od, str) or not od.strip():
            violations.append(f"[{name}] skill.yml has no non-empty owner_domain")
        else:
            skill_owner_domain[name] = od

    existing_skills = {sd.name for sd in skill_dirs}

    # --- Invariant 2: declared domain owner resolves + agrees ---
    for dname, dbody in domains.items():
        dbody = dbody or {}
        owner = dbody.get("owner")
        if not owner:
            violations.append(f"domain '{dname}' has no owner")
            continue
        if owner not in existing_skills:
            violations.append(f"domain '{dname}' owner '{owner}' has no skills/{owner}/")
            continue
        owner_od = skill_owner_domain.get(owner)
        if owner_od != dname:
            violations.append(
                f"domain '{dname}' owner '{owner}' declares owner_domain={owner_od!r} "
                f"(expected '{dname}')"
            )
        # --- Invariant 4: overlaps resolve ---
        for ov in dbody.get("overlaps", []) or []:
            if ov not in existing_skills:
                violations.append(
                    f"domain '{dname}' overlaps '{ov}' which has no skills/{ov}/"
                )

    # --- Invariant 3: a skill claiming a *declared* domain must own or overlap it ---
    for skill, od in skill_owner_domain.items():
        if od not in declared:
            continue  # self-owned domain, intentionally absent from capabilities.yml
        dbody = domains.get(od, {}) or {}
        allowed = {dbody.get("owner")} | set(dbody.get("overlaps", []) or [])
        if skill not in allowed:
            violations.append(
                f"[{skill}] claims declared domain '{od}' but is neither its owner "
                f"nor in its overlaps (add it to capabilities.yml domains.{od}.overlaps)"
            )

    # --- Invariant 5: umbrella members resolve to declared domains ---
    for uname, ubody in umbrellas.items():
        for member in _umbrella_members(ubody):
            if member not in declared:
                violations.append(
                    f"umbrella '{uname}' references undeclared domain '{member}'"
                )

    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="repo root containing capabilities.yml and skills/ (default: inferred)",
    )
    ap.add_argument("--strict", action="store_true", help="exit 1 on any drift (CI gate)")
    args = ap.parse_args()

    root = Path(args.root)
    violations = validate(root)

    if not violations:
        print("OK: skill registry is consistent (capabilities.yml ⇄ skills/*/skill.yml).")
        return 0

    print(f"REGISTRY DRIFT ({len(violations)}):")
    for v in violations:
        print(f"  {v}")

    if args.strict:
        print("\nSKILL_REGISTRY_DRIFT: capabilities.yml and skills/*/skill.yml disagree.", file=sys.stderr)
        return 1
    print("\n(non-strict: reported only; rerun with --strict to fail.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
