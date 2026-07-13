#!/usr/bin/env python3
"""AI-disclosure + data/code-availability statement detector (sync-submission).

Top medical-AI journals (Lancet Digital Health, Radiology / Radiology:AI, npj
Digital Medicine, Nature Medicine) now require, before peer review:
  - an AI/LLM-use disclosure that itself names the tool **version**, the **access
    channel**, the **date / date-range**, and the **responsible party** (the four
    tokens FLAIR F1.6 / TRIPOD-LLM / MI-CLEAR-LLM demand; the tool NAME, e.g.
    ChatGPT/Claude, is the applicability identifier that triggers the check, NOT
    one of the four required tokens), with no unresolved placeholders;
  - a Data Availability statement (not a hollow "available on reasonable request"
    when the journal expects a repository);
  - a Code Availability statement with a resolvable URL/DOI for an AI/ML study.

This detector scans the manuscript for those statements and checks them against
references/journal_availability_policy.json (public facts, journal-keyed). It is
deterministic and stdlib-only.

INPUTS
  --manuscript   markdown file (required).
  --journal      journal stem (selects the policy row; falls back to "default").
  --policy       path to journal_availability_policy.json (default: alongside skill).
  --ai-study     treat as an AI/ML study (code availability becomes expected).
  --require      repeatable hard-required statement(s): ai_disclosure |
                 data_availability | code_availability | funding | coi. An absent
                 required statement is a BLOCKER regardless of --strict.
  --strict       promote advisory (P1) findings to blockers.
  --out          JSON report path (default: qc/disclosure_availability_report.json).

VERDICT / EXIT
  CLEAN        no findings.
  ADVISORY     only P1 (warn) findings.
  BLOCKER      a hard rule failed: a --require'd statement absent, OR an AI
               disclosure present but missing a required token / carrying a
               placeholder.
  Exit: 0 clean/advisory (or report-only); 1 BLOCKER (or ADVISORY under --strict);
        2 input/usage error.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AI_TRIGGER = re.compile(
    r"generative ai|large language model|\bLLM\b|ai[- ]assisted|"
    r"assisted (?:the|with|in) (?:writing|drafting|editing)|"
    r"\bChatGPT\b|\bGPT-?[0-9]|\bClaude\b|\bCopilot\b|\bGemini\b|\bLlama\b",
    re.IGNORECASE,
)
TOKEN_VERSION = re.compile(r"\b\d+\.\d+\b|\bGPT-?\d|\b(?:Claude|Gemini|Llama|GPT)\s+\d", re.IGNORECASE)
TOKEN_CHANNEL = re.compile(r"\bAPI\b|\bchat\b|\bweb\b|\bBedrock\b|\bAzure\b|\binterface\b|\bapp\b", re.IGNORECASE)
TOKEN_DATE = re.compile(r"\b20\d{2}\b")
TOKEN_RESPONSIBLE = re.compile(
    r"\bby [A-Z]\.\s?[A-Z]\.|the authors|reviewed by|deployed by|operated by|under the supervision",
    re.IGNORECASE,
)
PLACEHOLDER = re.compile(r"\[(?:version|date|tool|name|model|n)\]|\bTODO\b|XXXX|\bTBD\b", re.IGNORECASE)

REASONABLE_REQUEST = re.compile(r"available (?:from the (?:corresponding )?author )?on (?:reasonable )?request", re.IGNORECASE)
RESOLVABLE = re.compile(r"https?://|doi\.org/|\bgithub\.com\b|\bzenodo\b|\bosf\.io\b|10\.\d{4,}/", re.IGNORECASE)

SECTION_LABELS = {
    "data_availability": r"data availability|availability of data",
    "code_availability": r"code availability|availability of code|software availability",
    "funding": r"funding|financial support|grant support",
    "coi": r"conflicts? of interest|competing interests?|declaration of interests?|disclosure",
}


def _err(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2


def load_policy(path: Path, journal: str | None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if journal:
        row = data.get("journals", {}).get(journal.strip().lower())
        if row:
            return row
    return data.get("default", {})


def find_section(text: str, pattern: str) -> str | None:
    """Return the block of text under a heading/bold label matching `pattern`."""
    lines = text.splitlines()
    head = re.compile(r"^\s*(?:#{1,6}\s*|\*\*\s*)?(?:" + pattern + r")\b", re.IGNORECASE)
    start = None
    for i, ln in enumerate(lines):
        if head.search(ln):
            start = i
            break
    if start is None:
        return None
    out = [lines[start]]
    for ln in lines[start + 1:]:
        if re.match(r"^\s*#{1,6}\s+\S", ln):
            break
        out.append(ln)
    return "\n".join(out).strip()


def ai_disclosure_block(text: str) -> str | None:
    """Find the paragraph that carries the AI-use disclosure (the one that trips
    AI_TRIGGER), preferring an explicit AI-disclosure-style heading if present."""
    for pat in (r"ai (?:use )?disclosure|use of (?:generative )?ai|artificial intelligence",):
        blk = find_section(text, pat)
        if blk and AI_TRIGGER.search(blk):
            return blk
    # else: the first paragraph that mentions an AI tool
    for para in re.split(r"\n\s*\n", text):
        if AI_TRIGGER.search(para):
            return para.strip()
    return None


def check(text: str, policy: dict, ai_study: bool, require: set[str], strict: bool) -> dict:
    findings: list[dict] = []

    # --- AI disclosure (only when the manuscript actually used/mentioned an AI tool) ---
    blk = ai_disclosure_block(text)
    if blk is not None:
        tokens = {
            "version": bool(TOKEN_VERSION.search(blk)),
            "access channel": bool(TOKEN_CHANNEL.search(blk)),
            "date": bool(TOKEN_DATE.search(blk)),
            "responsible party": bool(TOKEN_RESPONSIBLE.search(blk)),
        }
        missing = [k for k, v in tokens.items() if not v]
        if missing:
            findings.append({"rule": "ai_disclosure_tokens", "severity": "hard",
                             "detail": f"AI disclosure missing required token(s): {', '.join(missing)}"})
        if PLACEHOLDER.search(blk):
            findings.append({"rule": "ai_disclosure_placeholder", "severity": "hard",
                             "detail": "AI disclosure contains an unresolved placeholder ([version]/[date]/TODO/...)"})
    elif "ai_disclosure" in require:
        findings.append({"rule": "ai_disclosure_present", "severity": "hard",
                         "detail": "no AI-use disclosure found, but --require ai_disclosure was set"})

    # --- Data availability ---
    data_blk = find_section(text, SECTION_LABELS["data_availability"])
    data_required = policy.get("data_required", False) or ("data_availability" in require)
    if data_blk is None:
        if data_required:
            findings.append({"rule": "data_availability_present", "severity": "hard",
                             "detail": "no Data Availability statement found"})
    else:
        if policy.get("repository_required") and REASONABLE_REQUEST.search(data_blk) and not RESOLVABLE.search(data_blk):
            findings.append({"rule": "data_availability_hollow", "severity": "soft",
                             "detail": "Data Availability is 'available on request' but the journal expects a repository/DOI"})

    # --- Code availability (AI/ML studies) ---
    code_blk = find_section(text, SECTION_LABELS["code_availability"])
    code_required = ("code_availability" in require) or (ai_study and policy.get("code_required_if_ai", False))
    if code_blk is None:
        if code_required:
            findings.append({"rule": "code_availability_present", "severity": "hard",
                             "detail": "no Code Availability statement found for an AI/ML study"})
    elif not RESOLVABLE.search(code_blk):
        findings.append({"rule": "code_availability_resolvable", "severity": "soft",
                         "detail": "Code Availability statement has no resolvable URL/DOI (github/zenodo/doi.org)"})

    # --- Funding / COI presence ---
    for key in ("funding", "coi"):
        blk2 = find_section(text, SECTION_LABELS[key])
        if blk2 is None:
            sev = "hard" if key in require else "soft"
            findings.append({"rule": f"{key}_present", "severity": sev,
                             "detail": f"no {key.upper() if key == 'coi' else key.title()} statement found"})

    hard = any(f["severity"] == "hard" for f in findings)
    if hard:
        verdict = "BLOCKER"
    elif findings:
        verdict = "BLOCKER" if strict else "ADVISORY"
    else:
        verdict = "CLEAN"
    return {"verdict": verdict, "ai_disclosure_found": blk is not None, "findings": findings}


def main() -> int:
    ap = argparse.ArgumentParser(description="Check AI-disclosure + data/code-availability statements.")
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--journal")
    ap.add_argument("--policy")
    ap.add_argument("--ai-study", action="store_true")
    ap.add_argument("--require", action="append", default=[],
                    choices=["ai_disclosure", "data_availability", "code_availability", "funding", "coi"])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    man = Path(args.manuscript)
    if not man.is_file():
        return _err(f"manuscript not found: {man}")
    policy_path = Path(args.policy) if args.policy else \
        Path(__file__).resolve().parent.parent / "references" / "journal_availability_policy.json"
    if not policy_path.is_file():
        return _err(f"policy not found: {policy_path}")

    policy = load_policy(policy_path, args.journal)
    report = check(man.read_text(encoding="utf-8"), policy, args.ai_study, set(args.require), args.strict)

    out_path = Path(args.out) if args.out else Path("qc") / "disclosure_availability_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"detector": "check_disclosure_availability", **report}, indent=2) + "\n", encoding="utf-8")

    print("=" * 41)
    print(" Disclosure & Availability")
    print("=" * 41)
    print(f"journal: {args.journal or 'default'}   ai-study: {args.ai_study}")
    print(f"verdict: {report['verdict']}")
    for f in report["findings"]:
        print(f"  [{f['severity']}] {f['rule']}: {f['detail']}")
    print(f"report: {out_path}")

    if report["verdict"] == "BLOCKER":
        print("\nDISCLOSURE_AVAILABILITY_BLOCKER", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
