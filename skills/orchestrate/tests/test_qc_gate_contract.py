#!/usr/bin/env python3
"""Contract test: /orchestrate's QC gates read fields the upstream skills actually emit.

/orchestrate ships no code; its --e2e safety lives in the Post-Skill Validation table of
SKILL.md and in node N8 of references/dialogue_nodes.md. This test pins those rows to the
JSON contracts of the skills they gate, so they cannot drift back to a check that clears a
manuscript the upstream skill marked as blocked:

  - the /self-review row must read `fatal_count` (a key of the Phase 3c JSON) and route
    fatal findings away from the DOCX build;
  - the /check-reporting row must read `qc/reporting_checklist.json` (a declared
    check-reporting output) and its `missing` count (a key of the Part D JSON), and must not
    accept an inline report that leaves no file;
  - every backticked field N8 triggers on must exist in the self-review JSON, and no
    backticked category name may appear there (self-review emits letter categories A-J).

Run:  python3 skills/orchestrate/tests/test_qc_gate_contract.py
Exit 0 = all cases pass; 1 = a case failed; 2 = an input file could not be read.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ORCH = ROOT / "skills" / "orchestrate"
SR_SPEC = ROOT / "skills" / "self-review" / "references" / "phases" / "phase3c_json_output.md"
CR_TEMPLATES = ROOT / "skills" / "check-reporting" / "references" / "report_templates.md"
CR_SKILL_YML = ROOT / "skills" / "check-reporting" / "skill.yml"


class InputError(Exception):
    pass


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc


def _first_json_block(text: str, path: Path) -> dict:
    m = re.search(r"```json\s*\n(.*?)\n```", text, re.S)
    if not m:
        raise InputError(f"no ```json block in {path}")
    try:
        return json.loads(m.group(1))
    except ValueError as exc:
        raise InputError(f"unparseable ```json block in {path}: {exc}") from exc


def _validation_row(skill_md: str, skill: str) -> list[str]:
    """Cells of the Post-Skill Validation table row for `/skill`."""
    sec = re.search(r"^### Post-Skill Validation\s*$(.*?)^#{2,3} ", skill_md, re.M | re.S)
    if not sec:
        raise InputError("SKILL.md has no '### Post-Skill Validation' section")
    for line in sec.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == f"`/{skill}`":
            return cells
    raise InputError(f"Post-Skill Validation table has no `/{skill}` row")


def _n8_context(nodes_md: str) -> str:
    sec = re.search(r"^### N8\..*?$(.*?)^### ", nodes_md, re.M | re.S)
    if not sec:
        raise InputError("dialogue_nodes.md has no '### N8.' node")
    m = re.search(r"^- \*\*context:\*\*(.*)$", sec.group(1), re.M)
    if not m:
        raise InputError("N8 has no '- **context:**' line")
    return m.group(1)


def _has_path(obj: dict, path: str) -> bool:
    """`fatal_count` or `issues[].severity` against an example JSON object."""
    cur: object = obj
    for part in path.split("."):
        is_list = part.endswith("[]")
        key = part[:-2] if is_list else part
        if not isinstance(cur, dict) or key not in cur:
            return False
        cur = cur[key]
        if is_list:
            if not isinstance(cur, list) or not cur:
                return False
            cur = cur[0]
    return True


def check(orch_dir: Path) -> list[str]:
    skill_md = _read(orch_dir / "SKILL.md")
    nodes_md = _read(orch_dir / "references" / "dialogue_nodes.md")
    sr_json = _first_json_block(_read(SR_SPEC), SR_SPEC)
    cr_text = _read(CR_TEMPLATES)
    part_d = cr_text.split("Part D", 1)
    if len(part_d) < 2:
        raise InputError(f"no 'Part D' section in {CR_TEMPLATES}")
    cr_json = _first_json_block(part_d[1], CR_TEMPLATES)
    cr_outputs = _read(CR_SKILL_YML)

    errors: list[str] = []

    # --- /self-review row -------------------------------------------------------------
    sr = _validation_row(skill_md, "self-review")
    sr_check = sr[2] if len(sr) > 2 else ""
    if not _has_path(sr_json, "fatal_count"):
        errors.append("self-review Phase 3c JSON no longer has `fatal_count`")
    if "fatal_count" not in sr_check:
        errors.append("/self-review validation does not read `fatal_count`")
    if "N8" not in sr_check:
        errors.append("/self-review validation does not route fatal findings to N8")

    # --- /check-reporting row ---------------------------------------------------------
    cr = _validation_row(skill_md, "check-reporting")
    cr_expected = cr[1] if len(cr) > 1 else ""
    cr_check = cr[2] if len(cr) > 2 else ""
    if "qc/reporting_checklist.json" not in cr_outputs:
        errors.append("check-reporting skill.yml no longer declares qc/reporting_checklist.json")
    if "missing" not in cr_json:
        errors.append("check-reporting Part D JSON no longer has `missing`")
    if "qc/reporting_checklist.json" not in cr_expected:
        errors.append("/check-reporting validation does not expect qc/reporting_checklist.json")
    if "inline" in cr_expected.lower():
        errors.append("/check-reporting validation accepts an inline report (no file to check)")
    if "`missing" not in cr_check:
        errors.append("/check-reporting validation does not read the `missing` count")

    # --- N8 trigger -------------------------------------------------------------------
    ctx = _n8_context(nodes_md)
    tokens = re.findall(r"`([^`]+)`", ctx)
    if not tokens:
        errors.append("N8 trigger names no JSON field")
    for tok in tokens:
        path = re.match(r"[A-Za-z_][A-Za-z0-9_]*(?:\[\])?(?:\.[A-Za-z_][A-Za-z0-9_]*(?:\[\])?)*", tok)
        if not path or not _has_path(sr_json, path.group(0)):
            errors.append(f"N8 trigger `{tok}` is not a field of the self-review JSON")
    if "fatal" not in ctx:
        errors.append("N8 trigger does not key on severity fatal")
    return errors


MAIN_SR_ROW = ("| `/self-review` | Review report with JSON block (when --json) | Check JSON block is "
               "parseable. Accept the optional `consensus` array |")
MAIN_CR_ROW = "| `/check-reporting` | `qc/reporting_checklist.md` or inline report | Check file existence |"
MAIN_N8_CTX = ("- **context:** self-review returned `accuracy` / `data_fidelity` / "
               "`protocol_mismatch` / `numerical_claim` fatal")


def _mutated(tmp: Path, *, sr_row: str | None = None, cr_row: str | None = None,
             n8_ctx: str | None = None) -> Path:
    dst = tmp / "orchestrate"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(ORCH, dst)
    skill = (dst / "SKILL.md").read_text(encoding="utf-8")
    if sr_row is not None:
        skill = re.sub(r"^\| `/self-review` \|.*$", lambda _m: sr_row, skill, count=1, flags=re.M)
    if cr_row is not None:
        skill = re.sub(r"^\| `/check-reporting` \|.*$", lambda _m: cr_row, skill, count=1, flags=re.M)
    (dst / "SKILL.md").write_text(skill, encoding="utf-8")
    if n8_ctx is not None:
        nodes = (dst / "references" / "dialogue_nodes.md").read_text(encoding="utf-8")
        head, _, tail = nodes.partition("### N8.")
        tail = re.sub(r"^- \*\*context:\*\*.*$", lambda _m: n8_ctx, tail, count=1, flags=re.M)
        (dst / "references" / "dialogue_nodes.md").write_text(head + "### N8." + tail, encoding="utf-8")
    return dst


def main() -> int:
    failures: list[str] = []
    try:
        # Negative control: the live skill must be clean.
        live = check(ORCH)
        if live:
            failures.append("live skill should be clean, got: " + "; ".join(live))

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cases = [
                # (name, mutation kwargs, substring the error must contain)
                ("self-review row only parses JSON",
                 {"sr_row": MAIN_SR_ROW}, "does not read `fatal_count`"),
                ("check-reporting row accepts inline report",
                 {"cr_row": MAIN_CR_ROW}, "accepts an inline report"),
                ("check-reporting row ignores missing count",
                 {"cr_row": MAIN_CR_ROW}, "does not read the `missing` count"),
                ("N8 triggers on category names self-review never emits",
                 {"n8_ctx": MAIN_N8_CTX}, "`accuracy` is not a field"),
            ]
            for name, kw, needle in cases:
                errs = check(_mutated(tmp, **kw))
                if not any(needle in e for e in errs):
                    failures.append(f"{name}: expected an error containing {needle!r}, got {errs}")
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("OK: orchestrate QC gates match self-review / check-reporting JSON contracts "
          "(live clean; 4 regressions flagged)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
