#!/usr/bin/env python3
"""Nothing leaves a clinician's laptop without passing through here.

The people who edit these skills are physicians, and they edit them *while working on real
manuscripts, real registries, and real patients*. A local edit can therefore carry, without
anyone intending it: a patient identifier, a hospital name, an IRB approval number, a
manuscript ID under review, a co-author's name, an email address, or an absolute path with
the user's own account name in it. A contribution flow that simply uploads "the files you
changed" is a PHI leak with a friendly button on it.

So this gate runs on the exact text that would be sent, and it is the load-bearing part of
the /contribute skill.

WHAT THIS IS NOT. It is not a guarantee. No pattern list can recognise every patient name or
every hospital, and a scanner that is *believed* to be complete is more dangerous than no
scanner at all, because it replaces the human check. This tool exists to (a) stop the obvious
leak and (b) put every questionable line in front of the person who wrote it. The contract of
the skill is that the author reads the diff — every line — and confirms. The scan narrows what
they must think hardest about; it does not do their thinking.

Verdicts (all block by default; the author may override an individual finding with a reason):
  PHI_SUSPECTED      a patient-level identifier (MRN-like ID, national ID, date of birth,
                     accession/study UID). Never overridable — see below.
  IDENTITY           a personal name, email address, or phone number
  INSTITUTION        a hospital / clinic / medical-centre name
  APPROVAL_ID        an IRB / ethics approval or exemption number
  MANUSCRIPT_ID      a journal submission ID (a manuscript under review is confidential)
  LOCAL_PATH         an absolute path containing the user's account name
  SECRET             an API key or token

PHI_SUSPECTED is not overridable by this script. If a line looks like patient data, the
correct action is to delete the line, not to argue with the scanner.

Exit code: **1 if anything at all was found** — this gate fails closed. A tool that returns
success while printing a hospital name is a tool that will eventually be trusted to have said
nothing. `--warn-only` suppresses that for inspection, but never in the contribution flow, and a
patient-level finding still fails even then.

Usage:
    check_contribution_safety.py --changes qc/local_changes.json [--out qc/safety.json]
    check_contribution_safety.py --text some_file.md          # scan one file

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- patient-level identifiers. These are the ones that must never be argued with. ----------
PHI = [
    ("national_id_kr", re.compile(r"\b\d{6}[-–]\d{7}\b")),                 # RRN
    ("national_id_us", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),              # SSN
    ("mrn_like", re.compile(r"\b(?:mrn|chart|patient|pt|case)\s*(?:no\.?|number|id|#)?\s*[:=#]?\s*\d{5,12}\b", re.I)),
    ("accession", re.compile(r"\b(?:accession|study\s*uid|series\s*uid|sop\s*uid)\s*[:=#]?\s*[\d.]{8,}\b", re.I)),
    ("dicom_uid", re.compile(r"\b1\.2\.(?:840|392|410)(?:\.\d+){3,}\b")),
    ("dob", re.compile(r"\b(?:dob|date of birth|생년월일)\s*[:=]?\s*\d{2,4}[-/.]\d{1,2}[-/.]\d{1,2}\b", re.I)),
]

IDENTITY = [
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("phone", re.compile(r"\b(?:\+\d{1,3}[- ]?)?(?:\d{2,4}[- ]){2}\d{3,4}\b")),
    # An honorific in front of a name is a strong, low-false-positive signal.
    ("named_person", re.compile(
        r"\b(?:Dr\.?|Prof\.?|Professor|MD|Ph\.?D)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"
        r"|[가-힣]{2,4}\s*(?:교수님?|선생님|박사|원장)")),
]

INSTITUTION = re.compile(
    r"\b[A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,3}\s+"
    r"(?:Hospital|Medical Cent(?:er|re)|Clinic|Health System|Infirmary|Sanatorium|Univ(?:ersity)? Hospital)\b"
    r"|[가-힣]{2,10}(?:병원|의료원|의원|보건소)"
)

APPROVAL_ID = re.compile(
    r"\b(?:IRB|ERB|REC|ethics)\b[^.\n]{0,40}?\b(?:no\.?|number|approval|#)?\s*[:=#]?\s*"
    r"[A-Z0-9]{2,}[-/][A-Z0-9-]{2,}\b"
    r"|\b(?:IRB|ERB)\s*[:#-]?\s*\d{4}[-/]\d{2,}\b",
    re.I,
)

# A submission ID: LETTERS-D-YY-NNNNN, LETTERS-YY-NNNN, etc. A manuscript under review is
# confidential; leaking its ID in a public commit is a real disclosure.
MANUSCRIPT_ID = re.compile(r"\b[A-Z]{2,6}(?:-[A-Z])?-\d{2}-\d{3,6}\b")

LOCAL_PATH = re.compile(r"(?:/Users/|/home/|C:\\Users\\)(?!(?:runner|user|you|username|<)\b)[\w.-]+")

SECRET = re.compile(
    r"\b(?:sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})\b"
)

SEVERITY = {
    "PHI_SUSPECTED": "blocker",
    "SECRET": "blocker",
    "IDENTITY": "major",
    "INSTITUTION": "major",
    "APPROVAL_ID": "major",
    "MANUSCRIPT_ID": "major",
    "LOCAL_PATH": "major",
}

ADVICE = {
    "PHI_SUSPECTED": "Delete this line. Do not rephrase it, and do not argue with the scanner — "
                     "a contribution never needs patient-level data to make its point.",
    "SECRET": "Delete it, and rotate the credential: assume it is already compromised.",
    "IDENTITY": "Replace the person with their role (\"the corresponding author\", \"a reviewer\").",
    "INSTITUTION": "Replace with a generic descriptor (\"a tertiary-care hospital\").",
    "APPROVAL_ID": "Remove the number; \"approved by the institutional review board\" is enough.",
    "MANUSCRIPT_ID": "Remove it. A manuscript under review is confidential, and its ID identifies it.",
    "LOCAL_PATH": "Replace your home directory with a placeholder (~ or <path>).",
}


def scan_text(text: str, source: str) -> list[dict]:
    findings: list[dict] = []

    def add(verdict: str, line_no: int, line: str, match: str, rule: str) -> None:
        findings.append(
            {
                "verdict": verdict,
                "severity": SEVERITY[verdict],
                "source": source,
                "line": line_no,
                "rule": rule,
                "match": match,
                "context": line.strip()[:160],
                "advice": ADVICE[verdict],
            }
        )

    for i, line in enumerate(text.splitlines(), 1):
        for rule, rx in PHI:
            m = rx.search(line)
            if m:
                add("PHI_SUSPECTED", i, line, m.group(0), rule)
        if (m := SECRET.search(line)):
            add("SECRET", i, line, m.group(0)[:12] + "…", "credential")
        for rule, rx in IDENTITY:
            m = rx.search(line)
            if m:
                add("IDENTITY", i, line, m.group(0), rule)
        if (m := INSTITUTION.search(line)):
            add("INSTITUTION", i, line, m.group(0), "institution")
        if (m := APPROVAL_ID.search(line)):
            add("APPROVAL_ID", i, line, m.group(0), "approval")
        if (m := MANUSCRIPT_ID.search(line)):
            add("MANUSCRIPT_ID", i, line, m.group(0), "submission_id")
        if (m := LOCAL_PATH.search(line)):
            add("LOCAL_PATH", i, line, m.group(0), "home_dir")

    return findings


def audit(changes_file: Path | None, text_file: Path | None) -> dict:
    findings: list[dict] = []
    scanned: list[str] = []

    if text_file:
        findings += scan_text(text_file.read_text(encoding="utf-8", errors="replace"), text_file.name)
        scanned.append(str(text_file))
    else:
        data = json.loads(changes_file.read_text(encoding="utf-8"))  # type: ignore[union-attr]
        for c in data.get("changes", []):
            if c["kind"] == "deleted" or not c.get("text", True):
                continue
            p = Path(c["abs"])
            if not p.is_file():
                continue
            body = p.read_text(encoding="utf-8", errors="replace")
            findings += scan_text(body, f"{c['skill']}/{c['path']}")
            scanned.append(f"{c['skill']}/{c['path']}")

    blockers = [f for f in findings if f["severity"] == "blocker"]
    return {
        "detector": "check_contribution_safety",
        "files_scanned": scanned,
        "findings": findings,
        "summary": {v: sum(1 for f in findings if f["verdict"] == v) for v in SEVERITY},
        "blockers": len(blockers),
        "safe_to_send": not findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--changes", type=Path, help="find_local_changes.py --json output")
    g.add_argument("--text", type=Path, help="scan a single file")
    ap.add_argument("--out", type=Path)
    # FAIL-CLOSED. Most detectors in this repo are advisory by default and gate under --strict.
    # This one is the opposite, deliberately: it is the last thing between a clinician's laptop
    # and a public commit, and a tool that returns success while it is printing a hospital name
    # is a tool that will eventually be trusted to have said nothing. Finding anything is a
    # failure until a human clears it.
    ap.add_argument("--warn-only", action="store_true",
                    help="report findings but exit 0 anyway (never use this in the contribution flow)")
    ap.add_argument("--strict", action="store_true", help=argparse.SUPPRESS)  # kept: it is the default
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    rep = audit(a.changes, a.text)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not a.quiet:
        n = len(rep["files_scanned"])
        if rep["safe_to_send"]:
            print(f"Scanned {n} file(s). Nothing matched a known identifier pattern.")
            print(
                "\nThat is NOT a certificate. No pattern list recognises every patient name or every\n"
                "hospital. Read the diff yourself — every line — before you send it. The scan tells you\n"
                "what to think hardest about; it does not think for you."
            )
        else:
            print(f"Scanned {n} file(s). {len(rep['findings'])} thing(s) must not leave this machine:\n")
            for f in rep["findings"]:
                print(f"  [{f['severity'].upper()}] {f['verdict']}  {f['source']}:{f['line']}")
                print(f"      found : {f['match']}")
                print(f"      line  : {f['context']}")
                print(f"      do    : {f['advice']}\n")
            if rep["blockers"]:
                print(
                    f"{rep['blockers']} of these look like patient-level data or a credential. Those are not\n"
                    "negotiable: remove the lines and run this again. Nothing is sent until it is clean."
                )

    if rep["findings"] and not a.warn_only:
        return 1
    if rep["blockers"]:
        return 1  # a blocker is a blocker even under --warn-only
    return 0


if __name__ == "__main__":
    sys.exit(main())
