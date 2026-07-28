#!/usr/bin/env python3
"""Exclusion-code validity gate — a code that excludes a design the protocol
INCLUDES removes eligible studies in bulk while passing every downstream check
(meta-analysis Phase 3f).

The screening sheet can be internally perfect — every reviewer agrees, every
count reconciles, Cohen's kappa is high — and still be wrong at the source: the
*code itself* excludes a study design or population that the registered protocol's
eligibility criteria explicitly admit. Nothing else can see this. Consistency,
arithmetic, and inter-rater gates all operate on the cells; the defect is in the
legend, above the cells, and it deletes eligible studies quietly and in bulk.

Three verdicts, each computed by comparing the exclusion codes ACTUALLY APPLIED in
the screening artifacts against the code legend + eligibility text REGISTERED in
the protocol:

  1. CODE_CONTRADICTS_ELIGIBILITY (Major)  a used code's stated reason excludes a
       design/population on an axis (comparator, randomisation) that the protocol's
       own eligibility text names as ELIGIBLE. e.g. the protocol admits single-arm
       case series, and the screening excludes studies as "not comparative". This
       is the study-loss defect: the code is applied consistently and the sheet is
       coherent, but the code should not exist.
  2. CODE_NOT_REGISTERED (Major)  a code applied in the artifacts is absent from
       the registered legend — an off-protocol exclusion reason with no documented
       basis (also the PRISMA item 16a registered-vs-used drift).
  3. CODE_RENUMBERED (Minor)  a code present in BOTH the legend and the artifacts
       carries a DIFFERENT meaning in each (disjoint reason wording): the same
       number means two things. A documentation defect, not a study-loss defect —
       reported at a lower severity, which is the discrimination that matters.

Deterministic and conservative — it stays silent unless it can prove the defect:
  * CONTRADICTS fires only when the exclusion reason AND an affirmative, NON-negated
    eligibility sentence match the SAME design axis. A protocol that *excludes*
    single-arm studies and a code that excludes "not comparative" do NOT contradict
    — the eligibility text has to say the excluded design is eligible.
  * NOT_REGISTERED fires only when a legend was actually found in the protocol
    (no legend -> cannot assess -> silent, never a false positive on absence).
  * RENUMBERED fires only when both sides carry a reason and their content words
    are disjoint.
  * Missing/blank inputs degrade to a clean run rather than firing.

INPUT
  --protocol PATH       registered protocol / PROSPERO markdown or text (required).
  --screening PATH ...  one or more screening artifact TSV/CSV files (required).
  --code-col NAME       exclusion-code column override (else auto-detected).
  --reason-col NAME     exclusion-reason column override (else auto-detected).

OUTPUT  (--out path)
  {"detector": "check_exclusion_code_validity", "protocol", "screening",
   "claims": [{verdict, severity, code, detail, where}], "summary": {...}}
  CODE_CONTRADICTS_ELIGIBILITY and CODE_NOT_REGISTERED are Major candidates;
  CODE_RENUMBERED is Minor.

Stdlib-only (csv / re / json / argparse / pathlib). Exit codes: 0 clean (or
report-only), 1 a Major claim exists (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# --- code token: F1, E12, X2 (1-3 letters + 1-2 digits) --------------------
CODE_TOKEN_RE = re.compile(r"\b([A-Z]{1,3}\d{1,2})\b")

CODE_COL_CANDS = [
    "exclusion_code", "excl_code", "exclusion code", "reason_code", "reason code",
    "code", "exclude_code", "exclusioncode", "exclusion",
]
REASON_COL_CANDS = [
    "exclusion_reason", "excl_reason", "exclusion reason", "reason_text", "reason",
    "rationale", "justification", "notes",
]

# --- legend line forms in a protocol ---------------------------------------
# "F1 = duplicate", "F2: no comparative data", "F3 — cannot separate", "F4) x".
# Plain hyphen is NOT a separator (it collides with ranges like "F1-F5"). The
# meaning must contain a letter and must not itself begin with a code token.
LEGEND_LINE_RE = re.compile(r"\b([A-Z]{1,3}\d{1,2})\s*(?:=|:|—|–|\))\s*([^,;|\n]{3,})")

# --- eligibility signals ---------------------------------------------------
ELIG_INCLUDE_RE = re.compile(
    r"\b(eligible|were\s+included|are\s+included|will\s+be\s+included|"
    r"we\s+included|included\s+if|permitted|admitted)\b", re.I)
ELIG_NEGATION_RE = re.compile(
    r"\b(not\s+eligible|ineligible|not\s+included|were\s+excluded|are\s+excluded|"
    r"excluded\s+if|were\s+not|are\s+not|no\s+longer)\b", re.I)
INCLUDE_HEADING_RE = re.compile(
    r"^#{0,6}\s*\**\s*(?:inclusion\s+criteria|eligibility\s+criteria|eligible\s+stud(?:y|ies)|"
    r"included\s+stud(?:y|ies)|types?\s+of\s+stud(?:y|ies)(?:\s+to\s+be\s+included)?|study\s+designs?)\b",
    re.I | re.M)
NEXT_HEADING_RE = re.compile(r"^#{1,6}\s", re.M)
# prefix match on purpose: "exclu" must fire on exclude/excluded/exclusion, so no
# trailing \b (there is no word boundary between "exclu" and "ded").
EXCLUDE_CUE_RE = re.compile(r"(?im)^.*\b(?:exclu|not\s+eligible|ineligible)")

# --- design axes: (exclusion reason) vs (protocol says it is eligible) ------
# Both sides must match the SAME axis. Extensible: add an axis with an exclusion
# regex and the affirmative-eligibility regex for the same design/population.
# Only comparator + randomisation ship — the axes with a real study-loss failure.
AXES = [
    {
        "name": "comparator design",
        "exclusion": re.compile(
            r"not\s+comparative|non-?comparative|no\s+(?:comparator|control(?:\s+group|\s+arm)?|"
            r"comparison\s+group)|single[-\s]?arm|case\s+series|uncontrolled|"
            r"lack(?:ed|ing|s)?\s+(?:a\s+)?(?:comparator|control)", re.I),
        "inclusion": re.compile(
            r"single[-\s]?arm|case\s+series|non-?comparative|uncontrolled|"
            r"comparator\s+(?:was\s+|is\s+)?not\s+required|without\s+(?:a\s+)?(?:comparator|control)", re.I),
    },
    {
        "name": "randomisation",
        "exclusion": re.compile(
            r"not\s+randomi[sz]ed|non-?randomi[sz]ed|not\s+(?:an?\s+)?RCTs?|"
            r"observational\s+(?:stud(?:y|ies)|designs?)\s+(?:were\s+)?excluded", re.I),
        "inclusion": re.compile(
            r"observational\s+stud|non-?randomi[sz]ed\s+stud|"
            r"cohort\s+(?:stud(?:y|ies)|designs?)\s+(?:were\s+|are\s+)?(?:eligible|included|permitted)", re.I),
    },
]

_STOP = {
    "the", "a", "an", "of", "to", "no", "not", "non", "or", "and", "study", "studies",
    "data", "design", "for", "with", "without", "full", "text", "paper", "were", "was",
    "are", "is", "target", "type", "types",
}


def read_table(path: Path) -> list[dict[str, str]]:
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(fh, delimiter=delimiter)]


def find_col(rows: list[dict[str, str]], candidates: list[str]) -> str | None:
    if not rows:
        return None
    lower = {k.lower(): k for k in rows[0].keys()}
    for cand in candidates:            # exact match first
        if cand.lower() in lower:
            return lower[cand.lower()]
    for key in rows[0].keys():          # then substring
        lk = key.lower()
        if any(cand.lower() in lk for cand in candidates):
            return key
    return None


def norm_code(raw: str) -> str:
    m = CODE_TOKEN_RE.search((raw or "").upper())
    return m.group(1) if m else ""


def content_tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", (s or "").lower()) if w not in _STOP and len(w) > 2}


def collect_used_codes(paths: list[Path], code_col_arg: str | None,
                       reason_col_arg: str | None) -> dict[str, set[str]]:
    """code -> set of reason strings actually applied in the screening artifacts."""
    used: dict[str, set[str]] = {}
    for path in paths:
        rows = read_table(path)
        if not rows:
            continue
        code_col = code_col_arg or find_col(rows, CODE_COL_CANDS)
        reason_col = reason_col_arg or find_col(rows, REASON_COL_CANDS)
        for row in rows:
            raw_code = row.get(code_col, "") if code_col else ""
            raw_reason = row.get(reason_col, "") if reason_col else ""
            code = norm_code(raw_code) or norm_code(raw_reason)
            if not code:
                continue
            reason = raw_reason.strip()
            if not reason and raw_code:
                # salvage a reason from the code column ("F2 - not comparative")
                reason = CODE_TOKEN_RE.sub("", raw_code, count=1).strip(" -:—–\t")
            used.setdefault(code, set())
            if reason:
                used[code].add(reason)
    return used


def extract_legend(text: str) -> dict[str, str]:
    """Registered code -> meaning, from markdown-table rows and inline forms."""
    legend: dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 2:
                c = norm_code(cells[0])
                meaning = cells[1]
                if (c and cells[0].strip().upper() == c and meaning
                        and re.search(r"[A-Za-z]", meaning) and not set(meaning) <= set("-| ")
                        and not CODE_TOKEN_RE.match(meaning.upper())):
                    legend.setdefault(c, meaning)
                    continue
        for m in LEGEND_LINE_RE.finditer(s):
            c, meaning = m.group(1).upper(), m.group(2).strip()
            if (meaning and re.search(r"[A-Za-z]", meaning)
                    and not CODE_TOKEN_RE.match(meaning.upper()) and c not in legend):
                legend[c] = meaning
    return legend


def inclusion_text(protocol: str) -> str:
    """Text where the protocol AFFIRMATIVELY names an eligible design/population:
    non-negated inclusion sentences + inclusion-heading blocks truncated at the
    first exclusion cue (so an Excluded sub-list under an Eligibility heading does
    not leak in)."""
    parts: list[str] = []
    for s in re.split(r"(?<=[.!?])\s+|\n", protocol):
        if ELIG_INCLUDE_RE.search(s) and not ELIG_NEGATION_RE.search(s):
            parts.append(s)
    for m in INCLUDE_HEADING_RE.finditer(protocol):
        start = m.end()
        nxt = NEXT_HEADING_RE.search(protocol, start)
        block = protocol[start: nxt.start() if nxt else len(protocol)]
        cut = EXCLUDE_CUE_RE.search(block)
        if cut:
            block = block[:cut.start()]
        parts.append(block)
    return "\n".join(parts)


def check(protocol_text: str, used: dict[str, set[str]]) -> list[dict]:
    legend = extract_legend(protocol_text)
    inc_text = inclusion_text(protocol_text)
    claims: list[dict] = []

    for code in sorted(used):
        reasons = used[code]
        reason_blob = ((legend.get(code, "") + " ; " + " ; ".join(sorted(reasons)))).strip(" ;")

        # 1. CODE_CONTRADICTS_ELIGIBILITY — same design axis on both sides.
        for axis in AXES:
            if axis["exclusion"].search(reason_blob) and axis["inclusion"].search(inc_text):
                elig = axis["inclusion"].search(inc_text)
                claims.append({
                    "verdict": "CODE_CONTRADICTS_ELIGIBILITY",
                    "severity": "Major",
                    "code": code,
                    "detail": (f"exclusion code {code} ({reason_blob[:80]!r}) excludes on the "
                               f"{axis['name']} axis, but the protocol's eligibility text names that "
                               f"design as eligible ({elig.group(0)!r}); this code deletes studies the "
                               f"protocol includes — remove the code or amend the registered criteria"),
                    "where": reason_blob[:120],
                })
                break

        # 2. CODE_NOT_REGISTERED — used but absent from the registered legend.
        if legend and code not in legend:
            claims.append({
                "verdict": "CODE_NOT_REGISTERED",
                "severity": "Major",
                "code": code,
                "detail": (f"code {code} is applied in the screening artifacts but is absent from the "
                           f"registered exclusion-code legend ({sorted(legend)}); an off-protocol reason "
                           f"with no documented basis — register it or reclassify the affected records"),
                "where": (reason_blob or code)[:120],
            })

        # 3. CODE_RENUMBERED — same code, disjoint meaning in legend vs use.
        if code in legend and reasons:
            legend_toks = content_tokens(legend[code])
            used_toks: set[str] = set()
            for r in reasons:
                used_toks |= content_tokens(r)
            if legend_toks and used_toks and not (legend_toks & used_toks):
                claims.append({
                    "verdict": "CODE_RENUMBERED",
                    "severity": "Minor",
                    "code": code,
                    "detail": (f"code {code} is registered as {legend[code][:50]!r} but applied as "
                               f"{sorted(reasons)[0][:50]!r} — the same code number carries two meanings; "
                               f"realign the legend and the artifacts"),
                    "where": f"{code}: {legend[code][:60]}",
                })
    return claims


def analyze(protocol: str, screening: list[str], code_col: str | None,
            reason_col: str | None) -> dict:
    ppath = Path(protocol)
    if not ppath.is_file():
        sys.stderr.write(f"ERROR: protocol not found: {protocol}\n")
        sys.exit(2)
    spaths = [Path(s) for s in screening]
    for sp in spaths:
        if not sp.is_file():
            sys.stderr.write(f"ERROR: screening file not found: {sp}\n")
            sys.exit(2)
    used = collect_used_codes(spaths, code_col, reason_col)
    claims = check(ppath.read_text(encoding="utf-8"), used)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "protocol": str(ppath),
        "screening": [str(s) for s in spaths],
        "codes_used": sorted(used),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_minor": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Verdict | Severity | Code | Detail |", "|---|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['code']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | — | every applied code is registered and consistent with eligibility |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Exclusion-code validity gate (Phase 3f).")
    ap.add_argument("--protocol", required=True, help="registered protocol / PROSPERO markdown or text")
    ap.add_argument("--screening", required=True, nargs="+", help="screening artifact TSV/CSV file(s)")
    ap.add_argument("--code-col", help="exclusion-code column override")
    ap.add_argument("--reason-col", help="exclusion-reason column override")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.protocol, args.screening, args.code_col, args.reason_col)

    if not args.quiet:
        print("=" * 44)
        print(" Exclusion-Code Validity (Phase 3f)")
        print("=" * 44)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} code(s) unregistered or contradicting eligibility.")
        elif s["n_minor"]:
            print(f"MINOR: {s['n_minor']} renumbered code(s); no study-loss defect.")
        else:
            print("OK: every applied exclusion code is registered and consistent with the protocol.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps({"detector": "check_exclusion_code_validity", **result}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
