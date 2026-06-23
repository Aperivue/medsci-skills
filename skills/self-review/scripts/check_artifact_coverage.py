#!/usr/bin/env python3
"""Methods <-> Results <-> disk artifact coverage gate (self-review Phase 2.5f).

Two directional failures survive a single prose pass because the manuscript is
internally consistent:

  FORWARD  PROMISED_ABSENT   an analysis named in the Methods / Statistical
                            Analysis subsection (a sensitivity analysis, multiple
                            imputation, an interaction test, a subgroup, mediation,
                            a competing-risk or landmark model, an E-value) never
                            reaches Results. Methods promised it; the paper never
                            delivered it.
  REVERSE  DISK_UNREPORTED   an analysis output that exists on disk (an
                            added-value DeLong CSV, a calibration table) is never
                            mentioned in the manuscript. The work was done and run
                            but its result — which may contradict the headline —
                            is silently absent.
  FORWARD2 PROMISED_STAT_NO_VALUE  a named statistic framed as a bound/ceiling/
                            de-confounded value (e.g. "the de-confounded reader AUC
                            is reported in Table S16", "the classifier ceiling AUC")
                            is promised with a reporting verb but never given a
                            numeric value anywhere in the manuscript or supplement.
                            This is the "described but never quantified" reviewer
                            catch — the bound that makes the primary estimand
                            interpretable, marked Addressed in a checklist yet
                            absent from every table. Conservative: fires only on a
                            bound/ceiling/de-confounded framing whose statistic has
                            zero associated numeric values in the whole corpus.

The reverse direction is the false-positive-prone one, so it is calibrated: when
an `_analysis_outputs.md` manifest exists (written by /analyze-stats) it is the
source of truth; otherwise the analysis directory is globbed and a finding is only
a Major when the file stem carries an analysis-bearing token (delong, nested,
added-value, interaction, sensitivity, subgroup, mediation, imputation, landmark,
calibration, dca, nri, idi). A cryptic stem with no such token is a Minor flag.

INPUTS
  --manuscript    manuscript markdown/text (required).
  --analysis-dir  directory of analysis outputs. If omitted, the first existing of
                  output/analysis/, analysis/, results/ is used. An
                  `_analysis_outputs.md` manifest in that dir (or alongside the
                  manuscript) takes precedence as the output source of truth.

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manuscript, analysis_dir, manifest, claims[{verdict, severity, detail, where}], summary}
  PROMISED_ABSENT is always Major; DISK_UNREPORTED is Major or Minor per the rule
  above. Exit 1 (with --strict) when any Major-severity claim exists.

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Promised analyses: key -> (detect-in-Methods regex, appears-in-Results regex).
# The Results regex is intentionally looser (the concept can be phrased differently
# downstream) but still anchored to the analysis name.
PROMISED = {
    "multiple imputation": (r"multiple imputation|\bm\s*=\s*\d+\s*imput|imputed using",
                            r"imput-|imputation|imputed"),
    "sensitivity analysis": (r"sensitivity analys[ie]s", r"sensitivity analys[ie]s"),
    "leave-one-out": (r"leave[-\s]one[-\s]out", r"leave[-\s]one[-\s]out"),
    "interaction": (r"interaction (?:term|test|analys|effect)|tested? for interaction|"
                    r"p[-\s]?(?:for[-\s])?interaction",
                    r"interaction|p[-\s]?(?:for[-\s])?interaction|effect modif"),
    "subgroup": (r"subgroup analys", r"subgroup"),
    "mediation": (r"mediation (?:analys|model)", r"mediation|mediat"),
    "competing risk": (r"competing[-\s]risk|fine[-\s]?gray|subdistribution",
                       r"competing[-\s]risk|fine[-\s]?gray|subdistribution|cumulative incidence"),
    "landmark": (r"landmark analys", r"landmark"),
    "E-value": (r"e[-\s]?value", r"e[-\s]?value"),
}

ANALYSIS_TOKENS = (
    "delong", "nested", "added", "addedvalue", "incremental", "interaction",
    "sensitivity", "subgroup", "mediation", "imputation", "imputed", "landmark",
    "calibration", "dca", "netbenefit", "nri", "idi", "competing", "finegray",
    "tipping", "leaveone", "bootstrap",
)
OUTPUT_EXT = (".csv", ".tsv", ".r", ".py", ".rds")
MANIFEST_NAME = "_analysis_outputs.md"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def split_sections(text: str) -> list[tuple[str, str]]:
    """Return (heading, body) for each markdown heading region."""
    sections, heading, buf = [], "(preamble)", []
    for line in text.splitlines():
        m = re.match(r"^#{1,4}\s+(.*)", line)
        if m:
            sections.append((heading, "\n".join(buf)))
            heading = re.sub(r"[*_`]", "", m.group(1)).strip()
            buf = []
        else:
            buf.append(line)
    sections.append((heading, "\n".join(buf)))
    return sections


def section_text(sections: list[tuple[str, str]], names: tuple[str, ...]) -> str:
    out = []
    for heading, body in sections:
        h = heading.lower()
        if any(n in h for n in names):
            out.append(body)
    return "\n".join(out)


# --- FORWARD: promised-but-absent ------------------------------------------

def check_forward(text: str) -> list[dict]:
    sections = split_sections(text)
    methods = section_text(sections, ("method", "statistical analys", "analysis plan"))
    results = section_text(sections, ("result", "finding"))
    if not methods.strip():
        return []  # no Methods section to read promises from
    # If there is no separate Results section, compare against the whole document
    # minus the Methods text (conservative: avoids matching a promise to itself).
    haystack = results if results.strip() else text
    claims = []
    for key, (mre, rre) in PROMISED.items():
        if re.search(mre, methods, re.I):
            if not re.search(rre, haystack, re.I):
                claims.append({
                    "verdict": "PROMISED_ABSENT",
                    "severity": "Major",
                    "detail": (f"Methods promises a '{key}' analysis, but it does not "
                               f"appear in Results"),
                    "where": "Methods → Results",
                })
    return claims


# --- FORWARD2: promised statistic that is never given a number --------------

# Statistic nouns whose *value* is the deliverable. "sensitivity" excludes the
# "sensitivity analysis" sense.
STAT_NOUN = re.compile(
    r"\bAUROC\b|\bAUC\b|\bc[-\s]?statistic\b|\bc[-\s]?index\b"
    r"|\bsensitivity\b(?!\s+analys)|\bspecificity\b|\bnet benefit\b|\bcalibration slope\b",
    re.IGNORECASE)
# A bound/ceiling/de-confounded framing — the cases where a promised-but-unquantified
# statistic is the load-bearing bound, not an ordinary reported metric.
PROMISE_FRAME = re.compile(
    r"\bceiling\b|\bde[-\s]?confounded\b|\bupper[-\s]bound\b|\blower[-\s]bound\b|\bbound(?:s|ed|ing)?\b"
    r"|\bchance[-\s]level\b|\bdiscriminat\w*\s+ceiling\b",
    re.IGNORECASE)
REPORT_VERB = re.compile(
    r"\b(?:is|are|was|were)\s+(?:reported|read|given|shown|presented|computed|provided|derived)\b"
    r"|reported in (?:Table|Supplement|Supplementary)|\bwe report\b|\bsee (?:Table|Supplement)",
    re.IGNORECASE)
# A numeric value a statistic can take: a 0.xx discrimination value or an N% rate.
STAT_VALUE = re.compile(r"\b0\.\d{2,3}\b|\b\d{1,3}(?:\.\d+)?\s?%")


def _sentences(text: str) -> list[str]:
    flat = re.sub(r"\s*\n\s*", " ", text)
    return [s for s in re.split(r"(?<=[.;])\s+", flat) if s.strip()]


def check_promised_stat(methods_supp: str, corpus: str) -> list[dict]:
    """Fire when a bound/ceiling/de-confounded statistic is promised with a
    reporting verb but no numeric value for that statistic exists in the corpus."""
    claims = []
    # statistic tokens that DO have an associated value somewhere in the corpus
    valued: set[str] = set()
    for sent in _sentences(corpus):
        if STAT_VALUE.search(sent):
            for sm in STAT_NOUN.finditer(sent):
                valued.add(sm.group(0).lower().replace(" ", "").replace("-", ""))
    seen: set[str] = set()
    for sent in _sentences(methods_supp):
        if STAT_VALUE.search(sent):
            continue  # the value is right here — not a promise
        if not (STAT_NOUN.search(sent) and PROMISE_FRAME.search(sent) and REPORT_VERB.search(sent)):
            continue
        for sm in STAT_NOUN.finditer(sent):
            tok = sm.group(0)
            key = tok.lower().replace(" ", "").replace("-", "")
            if key in valued or key in seen:
                continue
            seen.add(key)
            claims.append({
                "verdict": "PROMISED_STAT_NO_VALUE",
                "severity": "Major",
                "detail": (f"a bound/ceiling/de-confounded '{tok}' is promised with a "
                           f"reporting verb but no numeric value for it appears in the "
                           f"manuscript or supplement"),
                "where": sent.strip()[:160],
            })
    return claims


# --- REVERSE: disk-present-but-unreported -----------------------------------

def find_analysis_dir(manuscript: Path, override: str | None) -> Path | None:
    if override:
        p = Path(override)
        return p if p.is_dir() else None
    base = manuscript.resolve().parent
    for cand in ("output/analysis", "analysis", "results", "output"):
        for root in (base, base.parent):
            p = root / cand
            if p.is_dir():
                return p
    return None


def parse_manifest(path: Path) -> list[str]:
    """Return declared output basenames from an _analysis_outputs.md manifest.
    Lines like '- `table1.csv` -- desc' or '* roc_curve.pdf'."""
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        for m in re.finditer(r"`([^`]+\.[A-Za-z0-9]{1,5})`", line):
            items.append(m.group(1))
        if not re.search(r"`", line):
            m = re.search(r"[-*]\s+([\w./-]+\.[A-Za-z0-9]{1,5})", line)
            if m:
                items.append(m.group(1))
    return items


def stem_tokens(name: str) -> list[str]:
    stem = Path(name).stem
    toks = re.split(r"[_\-.\s]+", stem)
    return [t for t in toks if len(t) >= 4 and re.search(r"[a-z]", t.lower())]


def mentioned(name: str, body_norm: str) -> bool:
    toks = stem_tokens(name)
    if not toks:
        return True  # nothing distinctive to look for -> do not flag
    return any(_norm(t) in body_norm for t in toks)


def check_reverse(text: str, manuscript: Path, analysis_dir: str | None) -> tuple[list[dict], dict]:
    body_norm = _norm(text)
    meta = {"analysis_dir": None, "manifest": None}
    # 1) manifest precedence
    manifest_files: list[str] = []
    for cand in (manuscript.resolve().parent / MANIFEST_NAME,):
        if cand.is_file():
            manifest_files = parse_manifest(cand)
            meta["manifest"] = str(cand)
            break
    adir = find_analysis_dir(manuscript, analysis_dir)
    if adir is not None:
        meta["analysis_dir"] = str(adir)
        mpath = adir / MANIFEST_NAME
        if not manifest_files and mpath.is_file():
            manifest_files = parse_manifest(mpath)
            meta["manifest"] = str(mpath)

    claims = []
    if manifest_files:
        for name in sorted(set(manifest_files)):
            if Path(name).suffix.lower() not in OUTPUT_EXT:
                continue  # figures (.pdf/.png) are checked by /make-figures legends
            if not mentioned(name, body_norm):
                claims.append({
                    "verdict": "DISK_UNREPORTED",
                    "severity": "Major",
                    "detail": (f"manifest output '{name}' is not mentioned anywhere in "
                               f"the manuscript"),
                    "where": meta["manifest"],
                })
        return claims, meta

    # 2) glob fallback (calibrated severity)
    if adir is None:
        return claims, meta
    for f in sorted(adir.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in OUTPUT_EXT:
            continue
        if mentioned(f.name, body_norm):
            continue
        analysis_bearing = any(_norm(t) in ANALYSIS_TOKENS for t in stem_tokens(f.name))
        claims.append({
            "verdict": "DISK_UNREPORTED",
            "severity": "Major" if analysis_bearing else "Minor",
            "detail": (f"analysis output '{f.name}' exists on disk but is not mentioned "
                       f"in the manuscript" + (" (analysis-bearing name)" if analysis_bearing else "")),
            "where": str(f.relative_to(adir.parent) if adir.parent in f.parents else f),
        })
    return claims, meta


# --- driver ----------------------------------------------------------------

def analyze(manuscript: str, analysis_dir: str | None, supplements: list[str] | None = None) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    text = p.read_text(encoding="utf-8")

    supp_texts = []
    for s in supplements or []:
        sp = Path(s)
        if not sp.is_file():
            sys.stderr.write(f"ERROR: supplement not found: {s}\n")
            sys.exit(2)
        supp_texts.append(sp.read_text(encoding="utf-8", errors="replace"))

    claims = check_forward(text)
    rev, meta = check_reverse(text, p, analysis_dir)
    claims += rev

    # FORWARD2: promised-but-unquantified bound/ceiling statistic. The promise may
    # live in the Methods or in the supplement; the value may live anywhere.
    sections = split_sections(text)
    methods = section_text(sections, ("method", "statistical analys", "analysis plan"))
    methods_supp = "\n".join([methods] + supp_texts)
    corpus = "\n".join([text] + supp_texts)
    claims += check_promised_stat(methods_supp, corpus)

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "analysis_dir": meta["analysis_dir"],
        "manifest": meta["manifest"],
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Direction | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | Methods↔Results↔disk all reconciled |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Methods<->Results<->disk coverage gate (Phase 2.5f).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--analysis-dir", help="analysis-output dir (default: output/analysis, analysis, results)")
    ap.add_argument("--supplement", action="append", default=[], metavar="PATH",
                    help="supplement file(s) to include in the promised-statistic corpus (repeatable)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, args.analysis_dir, args.supplement)

    if not args.quiet:
        print("=" * 41)
        print(" Artifact Coverage (Phase 2.5f)")
        print("=" * 41)
        if result["manifest"]:
            print(f"manifest: {result['manifest']}")
        elif result["analysis_dir"]:
            print(f"analysis dir (globbed): {result['analysis_dir']}")
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} coverage gap(s).")
        else:
            print("OK: Methods/Results/disk reconciled.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
