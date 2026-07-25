#!/usr/bin/env python3
"""The validation loss this project has never measured.

`scripts/check_detector_crossfire.py` runs every detector across the fixtures this repo ships as
its own picture of good work, and its closing paragraph names the gap it cannot close:

    "A new detector still owes what NO SHIPPABLE CORPUS CAN SUPPLY: two real manuscripts, at
     least one of them known-good."

No shippable corpus can supply it because published papers cannot be committed here (see
LICENSING.md). So the detectors are tested exclusively against fixtures authored ALONGSIDE THEM —
challenge cards, demo manuscripts. In machine-learning terms that is a training set, and a
detector passing its own challenge card is a training accuracy of 100%: true, and uninformative.
Nothing in this repo has ever measured the other number.

This does. It points the crossfire machinery (imported, never re-implemented — its invocation
rules were paid for with 31 clobbered fixtures) at a LOCAL corpus of real, accepted, published
open-access papers under `_corpus/heldout/`, which are gitignored and never distilled. If detector
count keeps climbing while the fire rate on already-accepted papers climbs with it, that is
recursive verification drift with a number attached instead of a feeling.

WHY A FIRE IS NOT A FALSE POSITIVE
    A published paper is not a defect-free paper. This whole project exists because reviewers miss
    things, so a detector firing on an accepted paper may be exactly right. Calling every fire a
    false positive would manufacture the alarming trend it claims to detect — the same class of
    error as a derived quantity crossing its own threshold.

    So this reports two different things and refuses to conflate them:

      fire rate            fired_pairs / ran_pairs. Always computable, needs no judgment, means
                           only "how often does the stack speak on already-accepted work".
      false-positive rate  spurious / (real + spurious), from HUMAN dispositions. Withheld
                           entirely until labels exist, and always printed with its coverage.

    The trend in fire rate is interpretable before any labelling, because the corpus is frozen:
    the papers do not change, so a rise across runs is a change in the detectors.

WHY "NEVER FIRED" IS REPORTED SEPARATELY FROM "NEVER RAN"
    `fired == 0` has two causes that look identical in a summary and mean opposite things: the
    detector was exercised and stayed silent (evidence), or it never got a subject it could read
    (no evidence). The prune decision in review-harvest turns on exactly this distinction, and
    project `qc/` harvesting cannot supply it — that only observes detectors somebody happened to
    run. A frozen corpus observes all of them on every run.

THE SEVERITY BAR, AND WHY IT IS NOT THE DEFAULT ONE (paid for on 2026-07-25)
    The first version of this file invoked `<detector> --manuscript <paper>` and read the exit
    code. But 32 of 42 manuscript detectors document exit 1 as CONDITIONAL ON --strict: without it
    they print a Major finding and exit 0. Re-running the pilot corpus at both bars: 5 fires at the
    default bar, 45 at the strict bar, and SEVEN detectors this instrument had recorded as
    "observed clean" fire the moment they are allowed to speak.

    That is the instrument committing the error it exists to detect — a check whose output and exit
    code disagree, read by its exit code alone. So the bar is now explicit: --strict is passed to
    every detector whose --help offers it, the bar actually used is recorded PER DETECTOR in the
    artifact, and `--bar both` records the default-bar outcome alongside as a secondary series.
    A rate whose bar is not recorded is not reportable, and rates at different bars are not
    comparable — the ledger refuses to difference them.

WHY AN OUTCOME IS PER PAIR AND NEVER TERMINATES THE LOOP (also paid for on 2026-07-25)
    Exit 2 is overloaded. It means "you did not give me the flags I need" (a property of the
    DETECTOR) and also "this paper has no section for me to check — skipped" (a property of the
    PAPER). The first version treated both as a detector-level skip and `break`ed out of the paper
    loop, so `check_credit_integrity` was measured on 5 of 12 papers in filename order and the
    remaining 7 — which held THREE more fires, one of them Major — were never measured at all.
    Which papers got measured was a function of alphabetical sort order.

    Every pair now gets its own outcome from a closed taxonomy, and no outcome stops the loop:

      fire            exit 1 at the declared bar
      clean           exit 0 — OBSERVED clean
      not_applicable  exit 2, detector's own "... — skipped": the paper has no subject for it
      unsupplied      exit 2, usage error naming a flag we cannot supply from a bare manuscript
      timeout         no exit inside the limit
      harness_void    exit 2 with "not found" — WE handed it a bad path. Voids the run.

    Only `fire` and `clean` are in the fire-rate denominator. A detector is reported as full,
    partial or never-ran with its own denominator, and appears in exactly one of those categories —
    the old summary managed to report 33 run AND 10 skipped out of 42.

FINDINGS, NOT JUST FIRES
    One exit can carry several claims. The pilot's systematic-review fire asserted both "no data
    availability statement" (true — a real omission in an accepted paper) and "no COI statement"
    (false — Elsevier's "Declaration of competing interest" was there and unrecognised). Labelled
    at pair level, either label is a lie. So bracketed claim lines (`[hard] key: message`,
    `[major] CODE: message`) are extracted as individual findings, the worksheet is finding-level,
    and the false-positive rate has FINDINGS as its denominator while the fire rate has PAIRS.

INPUTS
  --corpus       directory of held-out papers as .md/.txt (default: _corpus/heldout/).
  --manifest     optional _corpus/manifest.json. When given, a paper is measured only if a record
                 whose record_id equals its filename stem declares split=heldout. Unbacked papers
                 are named and excluded — an unverified corpus makes an unverifiable number.
  --bar          strict (default) | default | both. Which severity bar detectors are invoked at.
  --dispositions optional CSV (paper,detector[,code],verdict,disposition,note) with disposition in
                 {real, spurious, unsure}. A row without `code` labels every finding of that pair.
                 Without this file, no false-positive rate is printed.
  --worksheet    write unlabelled findings to this CSV for a human to label.
  --ledger       JSONL run history; append this run and print the delta against the last entry.
  --only         comma-separated detector names, for tests and for re-checking one detector.
  --out          JSON artifact.

Exit: 0 measurement completed (never blocks — this is an instrument, not a gate), 2 harness broke.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

RE_DIR = Path(__file__).resolve().parents[1]
REPO = RE_DIR.parent
sys.path.insert(0, str(REPO / "scripts"))

try:
    import check_detector_crossfire as cf  # noqa: E402  (path set above)
except Exception as exc:  # pragma: no cover - import failure is a harness break
    print(f"harness: cannot import the crossfire machinery: {exc}", file=sys.stderr)
    raise SystemExit(2)

DEFAULT_CORPUS = REPO / "_corpus" / "heldout"
DISPOSITIONS = ("real", "spurious", "unsure")
SEPARATOR_RE = re.compile(r"^[\s=~*_\-─—–]+$")
VERDICT_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")

# Outcomes in the fire-rate denominator. Everything else is UNOBSERVED and is reported as such.
MEASURED = ("fire", "clean")
OUTCOMES = ("fire", "clean", "not_applicable", "unsupplied", "timeout")

# One claim inside one exit. Two house formats are in use and both must parse, because a regex
# that knows one of them undercounts the other — the same single-vocabulary trap that produced
# ledger C1/C2 in the detectors themselves:
#     [hard] data_availability_present: no Data Availability statement found
#     [MAJOR] REFERENCE_STANDARD_UNDEFINED L21  Methods names no reference standard
FINDING_RE = re.compile(
    r"^\s*\[(?P<sev>[A-Za-z][A-Za-z_ -]{1,15})\]\s+(?P<code>[A-Za-z][A-Za-z0-9_.\-]*)\b"
    r"\s*(?:L\d+)?\s*[:\-]?\s*(?P<msg>.*)$"
)
# A detector's own severity word, mapped to two tiers. Blocking-tier findings are the ones a
# reviewer would call findings; advisory ones are the stack clearing its throat. The tier is
# recorded per finding so the false-positive rate can be reported for both and for Majors alone.
BLOCKING_SEV = {"major", "blocker", "hard", "critical", "error", "fail", "p0"}
ADVISORY_SEV = {"minor", "warn", "warning", "soft", "info", "note", "advisory", "unspecified"}
# A detector that declares its own inapplicability, e.g. "no author-contributions section — skipped."
SELF_SKIP_RE = re.compile(r"\bskipp?ed\b", re.I)
USAGE_RE = re.compile(r"^usage:", re.M)
NOT_FOUND_RE = re.compile(r"\bnot found\b|No such file", re.I)


def accepts_strict(det) -> bool:
    """Ask the detector, once, whether it has a bar above its default. Never guess it."""
    return "--strict" in cf.read_usage(det.path)


def classify_outcome(rc: int, stdout: str, stderr: str) -> tuple:
    """(outcome, detail). The closed taxonomy from the module docstring.

    Order matters. A usage error and a self-declared skip both exit 2 and mean opposite things:
    the first is about the detector, the second about the paper. Collapsing them is how a corpus
    silently shrinks — and how a detector that abstains on everything scores perfectly.
    """
    blob = (stderr or "") + "\n" + (stdout or "")
    if rc == 0:
        return "clean", None
    if rc == 1:
        return "fire", None
    if rc == 2:
        if NOT_FOUND_RE.search(blob):
            return "harness_void", blob.strip()[:200]
        if USAGE_RE.search(blob):
            return "unsupplied", "needs " + cf.missing_flag_from(stderr, stdout, ("--manuscript",))
        if SELF_SKIP_RE.search(blob):
            first = next((ln.strip() for ln in blob.splitlines() if ln.strip()), "")
            return "not_applicable", first[:200]
        return "unsupplied", "needs " + cf.missing_flag_from(stderr, stdout, ("--manuscript",))
    # A crash is the harness's problem to explain, never a quiet skip.
    return "harness_void", f"exit {rc}: " + blob.strip()[:180]


def extract_findings(stdout: str, stderr: str, fallback: str) -> List[dict]:
    """The individual claims inside one exit, so each can be labelled on its own merits.

    Falls back to a single finding carrying the verdict token, because a detector that fires
    without bracketed claim lines still made exactly one claim.
    """
    out: List[dict] = []
    seen = set()
    for ln in ((stderr or "") + "\n" + (stdout or "")).splitlines():
        m = FINDING_RE.match(ln)
        if not m:
            continue
        sev = m.group("sev").strip().lower()
        key = (sev, m.group("code"))
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "severity": sev,
                "tier": "blocking" if sev in BLOCKING_SEV else "advisory",
                "code": m.group("code"),
                "message": m.group("msg").strip()[:300],
                "parsed": True,
            }
        )
    if not out:
        # No parseable claim line. The exit still asserted something, so record one finding and
        # mark it unparsed — the count of these is the parser's own coverage, reported per run.
        out.append({"severity": "unspecified", "tier": "advisory", "code": fallback or "UNSPECIFIED",
                    "message": fallback, "parsed": False})
    return out


def verdict_line(stdout: str, stderr: str) -> str:
    """The one line a human needs to label this fire — and it is usually not on stdout.

    Detectors in this repo print a banner to stdout and the verdict CODE to stderr. A first
    draft read `stdout or stderr` and wrote a row of '=' into every worksheet row, which is a
    worksheet nobody can label. Read both, skip rules, prefer a verdict token.
    """
    lines = [ln.strip() for ln in ((stderr or "") + "\n" + (stdout or "")).splitlines()]
    lines = [ln for ln in lines if ln and not SEPARATOR_RE.match(ln)]
    for ln in lines:
        if VERDICT_TOKEN_RE.match(ln):
            return ln[:200]
    for ln in lines:
        if ln.lower().startswith("verdict:"):
            return ln[:200]
    return lines[0][:200] if lines else ""


def load_heldout(manifest_path: Path) -> Dict[str, dict]:
    """record_id -> {frozen_at, coverage}, for records actually declared held out."""
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"harness: cannot read manifest {manifest_path}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    return {
        r["record_id"]: {
            "frozen_at": str(r.get("frozen_at", "?")),
            "coverage": r.get("coverage") or {},
        }
        for r in data.get("records", [])
        if isinstance(r, dict) and r.get("split") == "heldout" and r.get("record_id")
    }


def separation_report(coverages: Dict[str, dict]) -> dict:
    """Is this corpus N papers, or one paper measured N times?

    A held-out corpus earns its denominator by SPANNING designs. Six papers that are all
    retrospective single-centre CT detection studies are one pattern with six labels: a detector
    silent across them is silent on that pattern, and "42 detectors clean on 6 papers" reads as
    six times the evidence it is. This is the corpus-side of the same rule
    check_panel_diversity applies to reviewers — a majority in one value is concentration, and a
    repeated full tuple is a duplicate episode, not a second observation.
    """
    axes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tuples: Dict[tuple, List[str]] = defaultdict(list)
    declared = {k: v for k, v in coverages.items() if v}
    for paper, cov in declared.items():
        for axis, value in sorted(cov.items()):
            axes[axis][str(value)] += 1
        tuples[tuple(sorted((k, str(v)) for k, v in cov.items()))].append(paper)
    n = len(declared)
    concentrated = [
        {"axis": axis, "value": val, "n": cnt, "of": n}
        for axis, vals in axes.items()
        for val, cnt in vals.items()
        if n >= 3 and cnt > n / 2
    ]
    collapsed = [sorted(v) for v in tuples.values() if len(v) > 1]
    return {
        "n_declared": n,
        "n_undeclared": len(coverages) - n,
        "axes": {a: dict(v) for a, v in axes.items()},
        "distinct_profiles": len(tuples),
        "concentrated": concentrated,
        "collapsed": collapsed,
    }


def load_dispositions(path: Path) -> Dict[tuple, str]:
    """(paper, detector, code) -> label, with (paper, detector, None) as a pair-wide fallback.

    The pair-wide form is what the pilot's worksheet produced, before findings were separable.
    Reading it still is deliberate: an old label file should keep working, and where it disagrees
    with a finding-level label the finding-level one wins (it is the more specific claim).
    """
    out: Dict[tuple, str] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = (row.get("disposition") or "").strip().lower()
            if d not in DISPOSITIONS:
                continue
            code = (row.get("code") or "").strip() or None
            out[((row.get("paper") or "").strip(), (row.get("detector") or "").strip(), code)] = d
    return out


def label_for(labels: Dict[tuple, str], paper: str, detector: str, code: str) -> Optional[str]:
    return labels.get((paper, detector, code)) or labels.get((paper, detector, None))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument(
        "--bar",
        choices=("strict", "default", "both"),
        default="strict",
        help="severity bar detectors are invoked at. strict (default) passes --strict to every "
        "detector whose --help offers it, because most document exit 1 as conditional on it; "
        "both also records the default-bar outcome as a secondary series.",
    )
    ap.add_argument("--dispositions", type=Path)
    ap.add_argument("--worksheet", type=Path)
    ap.add_argument("--ledger", type=Path)
    ap.add_argument("--only", help="comma-separated detector names")
    ap.add_argument(
        "--roster-out",
        type=Path,
        help="write the detector roster (name, bar, file sha256) and exit without measuring. "
        "This is what a pre-registration freezes: a rate belongs to a named set of detectors at a "
        "named content hash, or it belongs to nothing.",
    )
    ap.add_argument("--out", type=Path)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)

    if a.roster_out:
        import hashlib

        roster = [
            {
                "detector": d.name,
                "path": str(d.path.relative_to(REPO)),
                "bar": "strict" if (a.bar in ("strict", "both") and accepts_strict(d)) else "default",
                "sha256": hashlib.sha256(d.path.read_bytes()).hexdigest(),
            }
            for d in sorted(cf.discover(), key=lambda x: x.name)
            if d.family == "manuscript"
        ]
        a.roster_out.parent.mkdir(parents=True, exist_ok=True)
        a.roster_out.write_text(
            json.dumps({"bar_policy": a.bar, "n_detectors": len(roster), "detectors": roster},
                       indent=2),
            encoding="utf-8",
        )
        n_strict = sum(1 for r in roster if r["bar"] == "strict")
        print(f"roster: {len(roster)} manuscript detector(s), {n_strict} at --strict -> {a.roster_out}")
        return 0

    # Detectors run with cwd inside a throwaway sandbox, so a default `qc/...` report lands there
    # instead of in the repo. That makes every path handed to them absolute-or-broken: a relative
    # --corpus resolves against the CALLER's cwd, which the subprocess does not share. The first
    # real run was invoked as `--corpus _corpus/heldout`; every detector answered "manuscript not
    # found", and this harness relabelled that as "needs an input this fixture cannot supply" —
    # a skip reason it invented for a file it had failed to hand over, on 34 of 42 detectors, in
    # an instrument whose whole job is honest accounting.
    a.corpus = a.corpus.resolve()

    if not a.corpus.is_dir():
        print(
            f"harness: no held-out corpus at {a.corpus}\n"
            "  This is expected on a fresh clone: the corpus is real published papers, which are\n"
            "  gitignored and never committed (reverse_engineer/LICENSING.md). See HELDOUT.md for\n"
            "  how to build and freeze one.",
            file=sys.stderr,
        )
        return 2

    papers = sorted(p for p in a.corpus.iterdir() if p.suffix.lower() in (".md", ".txt"))
    unbacked: List[str] = []
    frozen_at = "unverified"
    separation = None
    if a.manifest:
        heldout = load_heldout(a.manifest)
        kept = []
        for p in papers:
            if p.stem in heldout:
                kept.append(p)
            else:
                unbacked.append(p.name)
        papers = kept
        dates = sorted({heldout[p.stem]["frozen_at"] for p in papers})
        frozen_at = dates[-1] if dates else "unverified"
        separation = separation_report({p.stem: heldout[p.stem]["coverage"] for p in papers})

    if not papers:
        print(
            "harness: zero measurable papers. A run that silently measures nothing is worse than\n"
            "  no measurement — refusing to emit a rate.",
            file=sys.stderr,
        )
        if unbacked:
            print(f"  no heldout manifest record for: {', '.join(unbacked)}", file=sys.stderr)
        return 2

    dets = [d for d in cf.discover() if d.family == "manuscript"]
    if a.only:
        want = {s.strip() for s in a.only.split(",") if s.strip()}
        missing = want - {d.name for d in dets}
        if missing:
            print(
                f"harness: --only named detector(s) that do not exist or take no --manuscript: "
                f"{', '.join(sorted(missing))}",
                file=sys.stderr,
            )
            return 2
        dets = [d for d in dets if d.name in want]
    if not dets:
        print("harness: found no manuscript-family detectors", file=sys.stderr)
        return 2

    bars = {d.name: ("strict" if (a.bar in ("strict", "both") and accepts_strict(d)) else "default")
            for d in dets}

    before = cf.hash_tree(papers)
    work = Path(tempfile.mkdtemp(prefix="heldout-"))
    # outcome counters per detector, one bucket per taxonomy member — no detector is ever counted
    # in two categories, and no category is a synonym for another.
    tally: Dict[str, Dict[str, int]] = {d.name: {o: 0 for o in OUTCOMES} for d in dets}
    reasons: Dict[str, Dict[str, str]] = defaultdict(dict)  # detector -> outcome -> example reason
    fires: List[dict] = []
    findings: List[dict] = []
    default_bar_fires = 0  # secondary series under --bar both

    def run_one(det, paper: Path, strict: bool):
        sandbox = Path(tempfile.mkdtemp(dir=work))  # a default qc/ path lands HERE
        cmd = ["python3", str(det.path), "--manuscript", str(paper)]  # inputs only, ever
        if strict:
            cmd.append("--strict")
        return cf.sh(cmd, cwd=sandbox)

    print("=" * 78)
    print(f" Held-out crossfire — {len(dets)} detector(s) x {len(papers)} accepted paper(s)")
    print(f" bar: {a.bar}")
    print("=" * 78)

    try:
        for d in dets:
            strict = bars[d.name] == "strict"
            for paper in papers:
                try:
                    r = run_one(d, paper, strict)
                except subprocess.TimeoutExpired:
                    # A timeout is a property of THIS pair. The next paper still gets measured.
                    tally[d.name]["timeout"] += 1
                    reasons[d.name].setdefault("timeout", f"timed out on {paper.stem}")
                    continue

                outcome, detail = classify_outcome(r.returncode, r.stdout, r.stderr)
                if outcome == "harness_void":
                    # WE handed it something it could not read. Recording that as a detector skip is
                    # how the instrument lies to itself. Fail loudly instead.
                    print(
                        f"\nharness: {d.name} could not read {paper.stem} — the harness built a bad "
                        f"command, this is not a detector skip.\n  {detail}",
                        file=sys.stderr,
                    )
                    return 2

                tally[d.name][outcome] += 1
                if detail:
                    reasons[d.name].setdefault(outcome, detail)

                if outcome == "fire":
                    verdict = verdict_line(r.stdout, r.stderr)
                    claims = extract_findings(r.stdout, r.stderr, verdict)
                    fires.append({"paper": paper.stem, "detector": d.name, "verdict": verdict,
                                  "bar": bars[d.name], "n_findings": len(claims)})
                    for c in claims:
                        findings.append({"paper": paper.stem, "detector": d.name,
                                         "bar": bars[d.name], **c})
                    print(f"  FIRED {d.name} x {paper.stem}"
                          + (f"  ({len(claims)} claims)" if len(claims) > 1 else ""))
                elif a.verbose:
                    print(f"  {outcome:<15} {d.name} x {paper.stem}")

                # Secondary series: what the OLD bar would have recorded for this same pair. This is
                # the number that made seven detectors look observed-clean.
                if a.bar == "both" and strict:
                    try:
                        r0 = run_one(d, paper, False)
                    except subprocess.TimeoutExpired:
                        continue
                    if classify_outcome(r0.returncode, r0.stdout, r0.stderr)[0] == "fire":
                        default_bar_fires += 1
    finally:
        after = cf.hash_tree(papers)
        changed = [k for k in before if before[k] != after.get(k)]
        shutil.rmtree(work, ignore_errors=True)

    if changed:
        print("\nFAIL: a detector WROTE INTO THE CORPUS. The run is void.", file=sys.stderr)
        for c in changed:
            print(f"  modified: {c}", file=sys.stderr)
        return 2

    measured = {n: sum(t[o] for o in MEASURED) for n, t in tally.items()}
    ran_pairs = sum(measured.values())
    fired_pairs = sum(t["fire"] for t in tally.values())
    unobserved_pairs = sum(t[o] for t in tally.values() for o in OUTCOMES if o not in MEASURED)
    if ran_pairs == 0:
        print("\nharness: zero pairs ran — no measurement taken.", file=sys.stderr)
        return 2
    fire_rate = fired_pairs / ran_pairs

    # A detector sits in exactly ONE of these. The old summary reported 33 run and 10 skipped out
    # of 42, because a detector truncated mid-corpus was counted as both.
    full = sorted(n for n, m in measured.items() if m == len(papers))
    partial = sorted(n for n, m in measured.items() if 0 < m < len(papers))
    never = sorted(n for n, m in measured.items() if m == 0)

    # ---- dispositions: the only path to a false-positive rate -------------------------------
    # Denominator is FINDINGS, not pairs: one exit can carry a true claim and a false one.
    labels = load_dispositions(a.dispositions) if a.dispositions else {}
    for f in findings:
        f["disposition"] = label_for(labels, f["paper"], f["detector"], f["code"])
    lab = [f["disposition"] for f in findings]
    n_spurious = sum(1 for x in lab if x == "spurious")
    n_real = sum(1 for x in lab if x == "real")
    n_unsure = sum(1 for x in lab if x == "unsure")
    n_unlabelled = sum(1 for x in lab if x is None)
    fp_rate = n_spurious / (n_real + n_spurious) if (n_real + n_spurious) else None

    exercised = sorted(n for n, t in tally.items() if measured[n] and not t["fire"])
    print("-" * 78)
    print(f"  papers measured : {len(papers)}   (corpus frozen: {frozen_at})")
    print(f"  detectors       : {len(full)} full / {len(partial)} partial / {len(never)} never ran"
          f"   (of {len(dets)})")
    n_block = sum(1 for f in findings if f["tier"] == "blocking")
    n_unparsed = sum(1 for f in findings if not f["parsed"])
    print(f"  pairs           : {ran_pairs}   fired: {fired_pairs}   findings: {len(findings)}"
          f" ({n_block} blocking-tier, {n_unparsed} with no parseable claim line)")
    print(f"  unobserved pairs: {unobserved_pairs} "
          f"(not_applicable {sum(t['not_applicable'] for t in tally.values())}, "
          f"unsupplied {sum(t['unsupplied'] for t in tally.values())}, "
          f"timeout {sum(t['timeout'] for t in tally.values())}) — no evidence either way")
    print(f"  FIRE RATE       : {fire_rate:.3f}  <- the trend to watch across runs")
    if a.bar == "both":
        print(f"  default-bar fires: {default_bar_fires} of the same {ran_pairs} pairs "
              f"(rate {default_bar_fires / ran_pairs:.3f}) — secondary series, not comparable")
    print(f"  silent-when-run : {len(exercised)} detector(s) — OBSERVED clean, not unobserved")
    n_strict = sum(1 for v in bars.values() if v == "strict")
    print(f"  bar             : {n_strict} detector(s) at --strict, {len(dets) - n_strict} at their "
          f"default exit code")
    if unbacked:
        print(f"  EXCLUDED (no heldout manifest record): {', '.join(unbacked)}")

    if separation is not None:
        print("-" * 78)
        if separation["n_declared"] == 0:
            print(
                "  SEPARATION: undeclared. No record carries `coverage`, so this reports "
                f"{len(papers)} papers\n"
                "    without knowing whether they are 1 design or 6. Declare coverage axes to make\n"
                "    the denominator mean something."
            )
        else:
            print(
                f"  SEPARATION: {separation['distinct_profiles']} distinct design profile(s) "
                f"across {separation['n_declared']} declared paper(s)"
                + (f" ({separation['n_undeclared']} undeclared)" if separation["n_undeclared"] else "")
            )
            for axis, vals in sorted(separation["axes"].items()):
                shown = ", ".join(f"{v}={c}" for v, c in sorted(vals.items()))
                print(f"    {axis}: {shown}")
            for c in separation["concentrated"]:
                print(
                    f"    CONCENTRATED: {c['axis']}={c['value']} holds {c['n']}/{c['of']} papers — "
                    "silence here is evidence about that value, not about the axis."
                )
            for group in separation["collapsed"]:
                print(
                    f"    COLLAPSED: {', '.join(group)} share an identical profile — one pattern "
                    "measured twice, not two observations."
                )
    for name in partial:
        t = tally[name]
        print(f"  PARTIAL {name}: measured {measured[name]}/{len(papers)} papers "
              f"(not_applicable {t['not_applicable']}, unsupplied {t['unsupplied']}, "
              f"timeout {t['timeout']}) — the rest are unobserved, not clean")
    for name in never:
        why = next((reasons[name][o] for o in ("unsupplied", "not_applicable", "timeout")
                    if o in reasons[name]), "no reason recorded")
        print(f"  NEVER RAN {name} ({why}) — unobserved, NOT evidence of a clean detector")

    if findings:
        print("-" * 78)
        if fp_rate is None:
            print(
                f"  FALSE-POSITIVE RATE: WITHHELD — {n_unlabelled} finding(s) across "
                f"{len(fires)} fire(s), 0 labelled.\n"
                "    A fire on an accepted paper may be a real defect reviewers missed. Label the\n"
                "    worksheet (real / spurious / unsure) before any FP claim is made."
            )
        else:
            cov = (len(findings) - n_unlabelled) / len(findings)
            print(
                f"  FALSE-POSITIVE RATE: {fp_rate:.3f}  "
                f"({n_spurious} spurious / {n_real + n_spurious} decided; "
                f"{n_unsure} unsure, {n_unlabelled} unlabelled; coverage {cov:.0%})"
            )
            print("    denominator is FINDINGS, not fires — one exit can carry a true claim and a "
                  "false one.")
            blocking = [f for f in findings if f["tier"] == "blocking"]
            b_sp = sum(1 for f in blocking if f["disposition"] == "spurious")
            b_dec = b_sp + sum(1 for f in blocking if f["disposition"] == "real")
            if b_dec:
                print(f"    blocking-tier only: {b_sp / b_dec:.3f} ({b_sp}/{b_dec} decided) — the "
                      "rate for claims the stack calls Major")
            if cov < 1.0:
                print("    Partial coverage — unlabelled findings could move this either way.")

    if a.worksheet:
        todo = [f for f in findings if f["disposition"] is None]
        with a.worksheet.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["paper", "detector", "code", "severity", "verdict", "disposition", "note"])
            for f in todo:
                w.writerow([f["paper"], f["detector"], f["code"], f["severity"],
                            f["message"], "", ""])
        print(f"\n  worksheet: {len(todo)} unlabelled finding(s) -> {a.worksheet}")

    payload = {
        "corpus": str(a.corpus),
        "frozen_at": frozen_at,
        "bar": a.bar,
        "n_papers": len(papers),
        "n_detectors_full": len(full),
        "n_detectors_partial": len(partial),
        "n_detectors_never_ran": len(never),
        "pairs_ran": ran_pairs,
        "pairs_fired": fired_pairs,
        "pairs_unobserved": unobserved_pairs,
        "n_findings": len(findings),
        "n_findings_blocking": sum(1 for f in findings if f["tier"] == "blocking"),
        "n_findings_unparsed": sum(1 for f in findings if not f["parsed"]),
        "fire_rate": round(fire_rate, 4),
        "fire_rate_default_bar": (round(default_bar_fires / ran_pairs, 4)
                                  if a.bar == "both" else None),
        "false_positive_rate": None if fp_rate is None else round(fp_rate, 4),
        "labels": {
            "spurious": n_spurious,
            "real": n_real,
            "unsure": n_unsure,
            "unlabelled": n_unlabelled,
        },
        "per_detector": {
            d.name: {
                "bar": bars[d.name],
                "measured": measured[d.name],
                "status": ("full" if d.name in full else
                           "partial" if d.name in partial else "never_ran"),
                **tally[d.name],
                "reasons": dict(reasons[d.name]),
            }
            for d in dets
        },
        "excluded_unbacked": unbacked,
        "separation": separation,
        "fires": fires,
        "findings": findings,
    }

    # ---- the trend. A level with no trend says nothing. --------------------------------------
    if a.ledger and a.only:
        print(
            "-" * 78 + "\n"
            "  LEDGER SKIPPED: --only ran a SUBSET of the detectors. Appending a partial run to the\n"
            "  trend series would make the next comparison read a filter as a change in the\n"
            "  detectors — our own behaviour manufacturing our own metric. Run without --only to\n"
            "  record a trend point."
        )
    elif a.ledger:
        prev = None
        if a.ledger.is_file():
            for line in a.ledger.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    try:
                        prev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
        entry = {k: payload[k] for k in ("frozen_at", "bar", "n_papers", "n_detectors_full",
                                         "pairs_ran", "pairs_fired", "fire_rate",
                                         "false_positive_rate")}
        with a.ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if prev and prev.get("bar", "default") != payload["bar"]:
            # Differencing two bars would read an invocation change as a change in the detectors.
            # The pilot series was recorded at the default bar and cannot be continued.
            print("-" * 78)
            print(
                f"  TREND: not comparable — severity bar changed "
                f"({prev.get('bar', 'default')} -> {payload['bar']}). A rate measured at a bar where\n"
                "    most detectors cannot exit non-zero is not the same quantity. Series restarts."
            )
        elif prev and prev.get("n_papers") == payload["n_papers"]:
            d_rate = payload["fire_rate"] - prev.get("fire_rate", 0.0)
            d_det = payload["n_detectors_full"] - prev.get("n_detectors_full", 0)
            print("-" * 78)
            print(
                f"  TREND vs last run: detectors {d_det:+d}, fire rate {d_rate:+.3f}\n"
                "    Same frozen papers, so a rise is a change in the DETECTORS, not the corpus.\n"
                "    Detectors up and fire rate up together is the overfitting signature: prune or\n"
                "    label before adding more."
            )
        elif prev:
            print("-" * 78)
            print(
                f"  TREND: not comparable — corpus size changed "
                f"({prev.get('n_papers')} -> {payload['n_papers']} papers)."
            )

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  json: {a.out}")

    print(
        "\n  This is an instrument, not a gate: it never fails a build. What it can be wrong about\n"
        "  is coverage — a detector silent across the corpus is silent ON THESE PAPERS, which is\n"
        "  evidence only to the extent the corpus spans the designs it reads."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
