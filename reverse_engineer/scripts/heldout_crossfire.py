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

INPUTS
  --corpus       directory of held-out papers as .md/.txt (default: _corpus/heldout/).
  --manifest     optional _corpus/manifest.json. When given, a paper is measured only if a record
                 whose record_id equals its filename stem declares split=heldout. Unbacked papers
                 are named and excluded — an unverified corpus makes an unverifiable number.
  --dispositions optional CSV (paper,detector,verdict,disposition,note) with disposition in
                 {real, spurious, unsure}. Without it, no false-positive rate is printed.
  --worksheet    write unlabelled fires to this CSV for a human to label.
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
    out: Dict[tuple, str] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            d = (row.get("disposition") or "").strip().lower()
            if d not in DISPOSITIONS:
                continue
            out[((row.get("paper") or "").strip(), (row.get("detector") or "").strip())] = d
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--dispositions", type=Path)
    ap.add_argument("--worksheet", type=Path)
    ap.add_argument("--ledger", type=Path)
    ap.add_argument("--only", help="comma-separated detector names")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)

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

    before = cf.hash_tree(papers)
    work = Path(tempfile.mkdtemp(prefix="heldout-"))
    ran: Dict[str, int] = defaultdict(int)
    fired: Dict[str, int] = defaultdict(int)
    skipped: Dict[str, str] = {}
    fires: List[dict] = []

    print("=" * 78)
    print(f" Held-out crossfire — {len(dets)} detector(s) x {len(papers)} accepted paper(s)")
    print("=" * 78)

    try:
        for d in dets:
            for paper in papers:
                sandbox = Path(tempfile.mkdtemp(dir=work))  # a default qc/ path lands HERE
                cmd = ["python3", str(d.path), "--manuscript", str(paper)]  # inputs only, ever
                try:
                    r = cf.sh(cmd, cwd=sandbox)
                except subprocess.TimeoutExpired:
                    skipped[d.name] = "timed out"
                    break
                if r.returncode == 2:
                    # "not found" is never a skip: the detector is telling us the harness handed it
                    # a path it could not open. Recording that as a missing-input skip is how the
                    # instrument lies to itself. Fail loudly instead.
                    if re.search(r"\bnot found\b|No such file", (r.stderr or "") + (r.stdout or "")):
                        print(
                            f"\nharness: {d.name} could not open {paper} — the harness built a bad "
                            f"command, this is not a detector skip.\n  {(r.stderr or '').strip()[:200]}",
                            file=sys.stderr,
                        )
                        return 2
                    skipped[d.name] = "needs " + cf.missing_flag_from(
                        r.stderr, r.stdout, ("--manuscript",)
                    )
                    break
                ran[d.name] += 1
                if r.returncode != 0:
                    fired[d.name] += 1
                    fires.append(
                        {
                            "paper": paper.stem,
                            "detector": d.name,
                            "verdict": verdict_line(r.stdout, r.stderr),
                        }
                    )
                    print(f"  FIRED {d.name} x {paper.stem}")
                elif a.verbose:
                    print(f"  ok    {d.name} x {paper.stem}")
    finally:
        after = cf.hash_tree(papers)
        changed = [k for k in before if before[k] != after.get(k)]
        shutil.rmtree(work, ignore_errors=True)

    if changed:
        print("\nFAIL: a detector WROTE INTO THE CORPUS. The run is void.", file=sys.stderr)
        for c in changed:
            print(f"  modified: {c}", file=sys.stderr)
        return 2

    ran_pairs = sum(ran.values())
    fired_pairs = sum(fired.values())
    if ran_pairs == 0:
        print("\nharness: zero pairs ran — no measurement taken.", file=sys.stderr)
        return 2
    fire_rate = fired_pairs / ran_pairs

    # ---- dispositions: the only path to a false-positive rate -------------------------------
    labels = load_dispositions(a.dispositions) if a.dispositions else {}
    lab = [labels.get((f["paper"], f["detector"])) for f in fires]
    n_spurious = sum(1 for x in lab if x == "spurious")
    n_real = sum(1 for x in lab if x == "real")
    n_unsure = sum(1 for x in lab if x == "unsure")
    n_unlabelled = sum(1 for x in lab if x is None)
    fp_rate = n_spurious / (n_real + n_spurious) if (n_real + n_spurious) else None

    exercised = sorted(n for n in (d.name for d in dets) if ran.get(n, 0) and not fired.get(n, 0))
    print("-" * 78)
    print(f"  papers measured : {len(papers)}   (corpus frozen: {frozen_at})")
    print(f"  detectors run   : {len(ran)}   skipped: {len(skipped)}")
    print(f"  pairs           : {ran_pairs}   fired: {fired_pairs}")
    print(f"  FIRE RATE       : {fire_rate:.3f}  <- the trend to watch across runs")
    print(f"  silent-when-run : {len(exercised)} detector(s) — OBSERVED clean, not unobserved")
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
    for name, why in sorted(skipped.items()):
        print(f"  SKIPPED {name} ({why}) — unobserved, NOT evidence of a clean detector")

    if fires:
        print("-" * 78)
        if fp_rate is None:
            print(
                f"  FALSE-POSITIVE RATE: WITHHELD — {n_unlabelled} fire(s), 0 labelled.\n"
                "    A fire on an accepted paper may be a real defect reviewers missed. Label the\n"
                "    worksheet (real / spurious / unsure) before any FP claim is made."
            )
        else:
            cov = (len(fires) - n_unlabelled) / len(fires)
            print(
                f"  FALSE-POSITIVE RATE: {fp_rate:.3f}  "
                f"({n_spurious} spurious / {n_real + n_spurious} decided; "
                f"{n_unsure} unsure, {n_unlabelled} unlabelled; coverage {cov:.0%})"
            )
            if cov < 1.0:
                print("    Partial coverage — unlabelled fires could move this in either direction.")

    if a.worksheet:
        todo = [f for f in fires if (f["paper"], f["detector"]) not in labels]
        with a.worksheet.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["paper", "detector", "verdict", "disposition", "note"])
            for f in todo:
                w.writerow([f["paper"], f["detector"], f["verdict"], "", ""])
        print(f"\n  worksheet: {len(todo)} unlabelled fire(s) -> {a.worksheet}")

    payload = {
        "corpus": str(a.corpus),
        "frozen_at": frozen_at,
        "n_papers": len(papers),
        "n_detectors_run": len(ran),
        "n_detectors_skipped": len(skipped),
        "pairs_ran": ran_pairs,
        "pairs_fired": fired_pairs,
        "fire_rate": round(fire_rate, 4),
        "false_positive_rate": None if fp_rate is None else round(fp_rate, 4),
        "labels": {
            "spurious": n_spurious,
            "real": n_real,
            "unsure": n_unsure,
            "unlabelled": n_unlabelled,
        },
        "per_detector": {
            d.name: {
                "ran": ran.get(d.name, 0),
                "fired": fired.get(d.name, 0),
                "skipped": skipped.get(d.name),
            }
            for d in dets
        },
        "excluded_unbacked": unbacked,
        "separation": separation,
        "fires": fires,
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
        entry = {k: payload[k] for k in ("frozen_at", "n_papers", "n_detectors_run",
                                         "pairs_ran", "pairs_fired", "fire_rate",
                                         "false_positive_rate")}
        with a.ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if prev and prev.get("n_papers") == payload["n_papers"]:
            d_rate = payload["fire_rate"] - prev.get("fire_rate", 0.0)
            d_det = payload["n_detectors_run"] - prev.get("n_detectors_run", 0)
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
