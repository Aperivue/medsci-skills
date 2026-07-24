#!/usr/bin/env python3
"""Submission pre-flight gate — the single last-step-before-freeze halt check.

medsci-skills already ships deterministic detectors + /verify-refs, but they are
invoked piecemeal. This orchestrator runs the submission-risk checks together,
once, before freeze/submission, aggregates them into one audit manifest
(qc/preflight_gate_report.json), and EXITS NON-ZERO on any blocker so a CI step
or build wrapper can halt. It composes existing scripts via subprocess and
reimplements none of them; the halt decision is driven by each sub-check's
normalized exit code (not by parsing its JSON), so a sub-check schema change
cannot silently weaken the gate.

DEFAULT TIERS — only the unambiguous, deterministic errors halt by default:
  P0 (halt):  placeholders (blocker markers), citation_keys (UNDEFINED [@key]),
              references (duplicate PMID/DOI, offline-deterministic; fabricated/
              author-mismatch too under --online), sync_drift (canonical hash),
              checklist_dump_leak (internal /check-reporting audit dump in a
              reviewer-facing file).
  P1 (warn):  xref, copy_divergence, scope_drift, cover_letter_drift,
              cross_document_n, cross_artifact_stale (heuristic / conditional —
              they RUN and REPORT but do not halt unless promoted). Promote with
              --strict (all P1 -> P0), --double-blind (asset_anonymization -> P0),
              or --require ID. Drop a check with --skip ID.

A check whose inputs are absent is recorded "skipped" (NA), never a blocker — so
the gate is tolerant of projects that lack a cover letter, rendered docx, copies,
etc. The offline references pass is deterministic and catches duplicates +
pagination placeholders; an online /verify-refs --strict (PubMed/CrossRef) remains
the authoritative fabrication/author check.

Stdlib-only. Exit codes: 0 clean (no blocker), 1 halt (>=1 blocker), 2 gate
config/IO error (e.g. a --require'd check could not run).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Repo root: skills/sync-submission/scripts/preflight_gate.py -> parents[3].
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from sync_submission import resolve_canonical, submission_md_path  # noqa: E402

PY = sys.executable

S = {
    "placeholders": REPO_ROOT / "skills/write-paper/scripts/check_placeholders.py",
    "citation_keys": REPO_ROOT / "skills/manage-refs/scripts/check_citation_keys.py",
    "verify_refs": REPO_ROOT / "skills/verify-refs/scripts/verify_refs.py",
    "sync_submission": REPO_ROOT / "skills/sync-submission/scripts/sync_submission.py",
    "cross_artifact_stale": REPO_ROOT / "skills/sync-submission/scripts/check_cross_artifact_stale.py",
    "cross_document_n": REPO_ROOT / "skills/sync-submission/scripts/cross_document_n_check.py",
    "xref": REPO_ROOT / "skills/manage-refs/scripts/check_xref.py",
    "copy_divergence": REPO_ROOT / "skills/sync-submission/scripts/detect_copy_divergence.py",
    "scope_drift": REPO_ROOT / "skills/sync-submission/scripts/scope_drift_check.py",
    "cover_letter_drift": REPO_ROOT / "skills/sync-submission/scripts/cover_letter_drift_check.py",
    "asset_anonymization": REPO_ROOT / "skills/sync-submission/scripts/check_asset_anonymization.py",
    "checklist_dump_leak": REPO_ROOT / "skills/sync-submission/scripts/check_checklist_dump_leak.py",
    "portal_field_residue": REPO_ROOT / "skills/sync-submission/scripts/check_portal_field_residue.py",
    "figure_readiness": REPO_ROOT / "skills/sync-submission/scripts/figure_portal_readiness_check.py",
}


class Ctx:
    """Resolved input paths (convention from --project-root/--journal, flags override)."""

    def __init__(self, args):
        self.root = Path(args.project_root).resolve()
        self.journal = args.journal
        self.online = args.online
        self.qc = self.root / "qc"
        self.manuscript = self._manuscript(args)
        self.bib = self._first(args.bib, [
            self.root / "references/library.bib",
            self.root / "refs.bib",
            self.root / "references.bib",
            (self.manuscript.parent / "refs.bib") if self.manuscript else None,
            (self.manuscript.parent / "_src/refs.bib") if self.manuscript else None,
        ])
        self.docx = self._first(args.docx, sorted(
            (self.root / "submission" / self.journal / "manuscript").glob("*.docx")
        ) if self.journal else [])
        self.copies = [Path(c).resolve() for c in (args.copy or [])]
        self.cover_letter = self._first(args.cover_letter, [
            (self.root / "submission" / self.journal / "cover_letter.md") if self.journal else None,
        ])
        self.asset_dir = self._first_dir(args.asset_dir, [
            (self.root / "submission" / self.journal) if self.journal else None,
        ])
        self.prospero = self._first(args.prospero, sorted((self.root / "prospero").glob("*.md")))
        self.pool_lock = self._first(args.pool_lock, [
            self.root / "FINAL_POOL_LOCK.yaml",
            self.root / "2_Data/FINAL_POOL_LOCK.yaml",
        ])
        self.aux = [d for d in [self.root / "supplement", self.root / "supplementary", self.qc]
                    if d.is_dir()]
        self.portal_fields = self._first_dir(getattr(args, "portal_fields", None), [
            self.root / "portal_fields",
            (self.root / "submission" / self.journal / "portal_fields") if self.journal else None,
        ])
        self.figures_dir = self._first_dir(getattr(args, "figures_dir", None), [
            (self.root / "submission" / self.journal / "figures") if self.journal else None,
            self.root / "figures",
            self.root / "manuscript" / "figures",
        ])
        self.figure_accept = getattr(args, "figure_accept", []) or []
        self.figure_max_mb = getattr(args, "figure_max_mb", 25.0)

    def _manuscript(self, args):
        if args.manuscript:
            return Path(args.manuscript).resolve()
        c = resolve_canonical(self.root, None)
        return c if c.exists() else None

    @staticmethod
    def _first(explicit, candidates):
        if explicit:
            return Path(explicit).resolve()
        for c in candidates:
            if c and Path(c).is_file():
                return Path(c).resolve()
        return None

    @staticmethod
    def _first_dir(explicit, candidates):
        if explicit:
            return Path(explicit).resolve()
        for c in candidates:
            if c and Path(c).is_dir():
                return Path(c).resolve()
        return None


# --- check registry ----------------------------------------------------------
# Each check: build_argv(ctx) -> argv list or None (None => skipped, missing input);
# exit_map maps a return code to ok/finding/skipped/error; tier P0/P1; promote flags;
# artifact relative to qc/ (for the human message). Halt is decided ONLY by the
# normalized status, never by parsing the artifact.

def _argv_placeholders(c):
    if not c.manuscript:
        return None
    return [PY, str(S["placeholders"]), "--manuscript", str(c.manuscript),
            "--quiet", "--out", str(c.qc / "placeholder_audit.json")]

def _argv_citation_keys(c):
    if not (c.manuscript and c.bib):
        return None
    return [PY, str(S["citation_keys"]), str(c.manuscript), str(c.bib)]

def _argv_references(c):
    src = c.bib or c.manuscript
    if not src:
        return None
    argv = [PY, str(S["verify_refs"]), str(src), "--project-root", str(c.root)]
    if not c.online:
        argv.append("--offline")
    return argv

def _argv_sync_drift(c):
    if not c.journal:
        return None
    if not resolve_canonical(c.root, None).exists():
        return None
    return [PY, str(S["sync_submission"]), "audit",
            "--project-root", str(c.root), "--journal", c.journal]

def _argv_cross_artifact(c):
    if not (c.manuscript and c.aux):
        return None
    argv = [PY, str(S["cross_artifact_stale"]), "--manuscript", str(c.manuscript),
            "--quiet", "--out", str(c.qc / "cross_artifact.json")]
    for d in c.aux:
        argv += ["--aux", str(d)]
    return argv

def _argv_cross_document_n(c):
    if not c.manuscript:
        return None
    argv = [PY, str(S["cross_document_n"]), "--root", str(c.root),
            "--out", str(c.qc / "cross_document_n.json")]
    if c.pool_lock:
        argv += ["--pool-lock", str(c.pool_lock)]
    return argv

def _argv_xref(c):
    if not (c.manuscript and c.docx):
        return None
    return [PY, str(S["xref"]), "--md", str(c.manuscript), "--docx", str(c.docx),
            "--quiet", "--strict", "--out", str(c.qc / "xref_audit.json")]

def _argv_copy_divergence(c):
    if not (c.manuscript and c.copies):
        return None
    argv = [PY, str(S["copy_divergence"]), "--ssot", str(c.manuscript),
            "--strict", "--out", str(c.qc / "copy_divergence.json")]
    for cp in c.copies:
        argv += ["--copy", str(cp)]
    return argv

def _argv_scope_drift(c):
    if not c.manuscript:
        return None
    argv = [PY, str(S["scope_drift"]), "--manuscript", str(c.manuscript),
            "--quiet", "--out", str(c.qc / "scope_drift.json")]
    if c.prospero:
        argv += ["--prospero", str(c.prospero)]
    return argv

def _argv_cover_letter(c):
    if not (c.manuscript and c.cover_letter):
        return None
    argv = [PY, str(S["cover_letter_drift"]), "--manuscript", str(c.manuscript),
            "--cover-letter", str(c.cover_letter), "--out", str(c.qc / "cover_letter_drift.json")]
    if c.bib:
        argv += ["--refs", str(c.bib)]
    return argv

def _argv_asset_anon(c):
    if not c.asset_dir:
        return None
    return [PY, str(S["asset_anonymization"]), "--dir", str(c.asset_dir),
            "--quiet", "--out", str(c.qc / "asset_anon.json")]

def _argv_checklist_dump(c):
    if not c.asset_dir:
        return None
    return [PY, str(S["checklist_dump_leak"]), "--dir", str(c.asset_dir),
            "--quiet", "--out", str(c.qc / "checklist_dump_leak.json")]

def _argv_portal_residue(c):
    if not c.portal_fields:
        return None
    return [PY, str(S["portal_field_residue"]), "--dir", str(c.portal_fields),
            "--quiet", "--out", str(c.qc / "portal_field_residue.json")]

def _argv_figure_readiness(c):
    if not c.figures_dir:
        return None
    argv = [PY, str(S["figure_readiness"]), "--figures-dir", str(c.figures_dir),
            "--max-mb", str(c.figure_max_mb), "--quiet",
            "--out", str(c.qc / "figure_readiness.json")]
    for ext in c.figure_accept:
        argv += ["--accept", ext]
    return argv


CHECKS = [
    {"id": "placeholders", "tier": "P0", "build": _argv_placeholders,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "placeholder_audit.json"},
    {"id": "citation_keys", "tier": "P0", "build": _argv_citation_keys,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": None},
    {"id": "references", "tier": "P0", "build": _argv_references,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped", 3: "skipped"},
     "artifact": "reference_audit.json", "post": "references"},
    {"id": "sync_drift", "tier": "P0", "build": _argv_sync_drift,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": None},
    {"id": "cross_artifact_stale", "tier": "P1", "build": _argv_cross_artifact,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "cross_artifact.json",
     "strict_promote": True},
    {"id": "cross_document_n", "tier": "P1", "build": _argv_cross_document_n,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "cross_document_n.json",
     "strict_promote": True},
    {"id": "xref", "tier": "P1", "build": _argv_xref,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "xref_audit.json",
     "strict_promote": True},
    {"id": "copy_divergence", "tier": "P1", "build": _argv_copy_divergence,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "copy_divergence.json",
     "strict_promote": True},
    {"id": "scope_drift", "tier": "P1", "build": _argv_scope_drift,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "scope_drift.json",
     "strict_promote": True},
    # cover_letter_drift has INVERTED exit codes: 0 clean, 2 drift, 1 missing input.
    {"id": "cover_letter_drift", "tier": "P1", "build": _argv_cover_letter,
     "exit_map": {0: "ok", 2: "finding", 1: "skipped"}, "artifact": "cover_letter_drift.json",
     "strict_promote": True},
    {"id": "asset_anonymization", "tier": "P1", "build": _argv_asset_anon,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "asset_anon.json",
     "double_blind_promote": True},
    # A leaked /check-reporting or /self-review audit dump in a reviewer-facing
    # file is never acceptable (exposes auto-fix notes, raw JSON, stale content)
    # — P0 blocker, independent of blinding.
    {"id": "checklist_dump_leak", "tier": "P0", "build": _argv_checklist_dump,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "checklist_dump_leak.json"},
    # Markdown residue (---, **bold**, ^x^, [text](url)) in a paste-verbatim portal
    # .txt field would print literally in the published abstract/keyword field.
    {"id": "portal_field_residue", "tier": "P1", "build": _argv_portal_residue,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "portal_field_residue.json",
     "strict_promote": True},
    # A figure over the portal's size cap (25 MB) or in a rejected format (SNAPP takes no
    # .png) bounces at the upload button — deterministic from the file's bytes + extension.
    {"id": "figure_readiness", "tier": "P1", "build": _argv_figure_readiness,
     "exit_map": {0: "ok", 1: "finding", 2: "skipped"}, "artifact": "figure_readiness.json",
     "strict_promote": True},
]


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _message(check_id, status, artifact_path, stdout):
    """Compact human message from the sub-check artifact (best effort, never gates)."""
    j = _load(artifact_path) if artifact_path else None
    if check_id == "references" and j:
        c = j.get("counts", {}) if isinstance(j.get("counts"), dict) else {}
        dups = j.get("duplicate_findings") or []
        bits = []
        if dups:
            bits.append(f"{len(dups)} duplicate ref(s)")
        for k in ("FABRICATED", "MISMATCH", "UNVERIFIED"):
            if c.get(k):
                bits.append(f"{c[k]} {k.lower()}")
        return ", ".join(bits) or "references verified"
    if check_id == "placeholders" and j:
        s = j.get("summary", {})
        return f"{s.get('blocker', 0)} blocker, {s.get('warn', 0)} warn marker(s)"
    if check_id == "cross_document_n" and j:
        return f"{j.get('drift_count', 0)} N-drift(s)"
    if check_id == "cover_letter_drift" and j:
        return f"{len(j.get('drifts', []))} cover-letter drift(s)"
    if check_id == "scope_drift" and j:
        return f"{len(j.get('limitations_only_anchors', []))} limitations-only anchor(s)"
    if check_id == "copy_divergence" and j:
        return str(j.get("verdict", "")) or "copies checked"
    if check_id in ("cross_artifact_stale", "asset_anonymization", "checklist_dump_leak",
                    "portal_field_residue", "figure_readiness") and j:
        return ", ".join(f"{k}={v}" for k, v in (j.get("summary") or {}).items()) or "scanned"
    if check_id == "sync_drift" and artifact_path is None and stdout:
        try:
            return json.loads(stdout).get("status", "")
        except json.JSONDecodeError:
            return ""
    # citation_keys / sync_drift: last non-empty stdout line
    if stdout:
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        return lines[-1][:120] if lines else ""
    return ""


def run_check(spec, ctx, args):
    cid = spec["id"]
    in_skip = cid in args.skip
    in_require = cid in args.require
    if in_skip:
        return {"id": cid, "tier": spec["tier"], "script": _rel(S[_script_key(cid)]),
                "ran": False, "exit_code": None, "status": "skipped",
                "blocker": False, "artifact": None, "message": "skipped by --skip"}

    # effective tier
    effective_p0 = (spec["tier"] == "P0"
                    or in_require
                    or (spec.get("strict_promote") and args.strict)
                    or (spec.get("double_blind_promote") and args.double_blind))

    argv = spec["build"](ctx)
    artifact_path = ctx.qc / spec["artifact"] if spec.get("artifact") else None
    if argv is None:
        status = "error" if in_require else "skipped"
        msg = "required check could not run (missing input)" if in_require else "missing input"
        return {"id": cid, "tier": "P0" if effective_p0 else "P1",
                "script": _rel(S[_script_key(cid)]), "ran": False, "exit_code": None,
                "status": status, "blocker": False, "artifact": None, "message": msg}

    ctx.qc.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(argv, capture_output=True, text=True)
    rc = proc.returncode
    base = spec["exit_map"].get(rc, "error")

    # references offline: exit 0 can still carry UNVERIFIED -> advisory warn
    if base == "ok" and spec.get("post") == "references":
        j = _load(artifact_path)
        if j and j.get("requires_manual_reference_check"):
            base = "warn_post"

    if base == "finding":
        status = "blocker" if effective_p0 else "warn"
    elif base == "warn_post":
        status = "warn"
    else:
        status = base  # ok / skipped / error

    msg = _message(cid, status, artifact_path, proc.stdout)
    if status == "error":
        msg = (proc.stderr.strip().splitlines() or ["unexpected exit"])[-1][:160] if proc.stderr else f"unexpected exit {rc}"
    if base == "warn_post" and not msg:
        msg = "unverified references — run online /verify-refs"

    return {"id": cid, "tier": "P0" if effective_p0 else "P1",
            "script": _rel(S[_script_key(cid)]), "ran": True, "exit_code": rc,
            "status": status, "blocker": status == "blocker",
            "artifact": _rel(artifact_path) if (artifact_path and artifact_path.exists()) else None,
            "message": msg}


_SCRIPT_KEY = {
    "placeholders": "placeholders", "citation_keys": "citation_keys", "references": "verify_refs",
    "sync_drift": "sync_submission", "cross_artifact_stale": "cross_artifact_stale",
    "cross_document_n": "cross_document_n", "xref": "xref", "copy_divergence": "copy_divergence",
    "scope_drift": "scope_drift", "cover_letter_drift": "cover_letter_drift",
    "asset_anonymization": "asset_anonymization",
    "checklist_dump_leak": "checklist_dump_leak",
    "portal_field_residue": "portal_field_residue",
    "figure_readiness": "figure_readiness",
}


def _script_key(cid):
    return _SCRIPT_KEY[cid]


def _rel(p):
    try:
        return str(Path(p).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Submission pre-flight gate — run submission-risk checks and halt on any blocker.")
    ap.add_argument("--project-root", default=".", help="project root (default: .)")
    ap.add_argument("--journal", default=None, help="journal slug under submission/ (for sync/cover/asset checks)")
    ap.add_argument("--strict", action="store_true", help="promote all P1 checks to halting (P0)")
    ap.add_argument("--online", action="store_true",
                    help="run the references check online (PubMed/CrossRef) so fabricated/mismatched refs halt too")
    ap.add_argument("--double-blind", action="store_true", help="promote asset_anonymization to halting (P0)")
    ap.add_argument("--require", action="append", default=[], metavar="ID",
                    help="force a check to halting; error if it cannot run (repeatable)")
    ap.add_argument("--skip", action="append", default=[], metavar="ID", help="drop a check (repeatable)")
    ap.add_argument("--manuscript", default=None)
    ap.add_argument("--bib", default=None)
    ap.add_argument("--docx", default=None)
    ap.add_argument("--copy", action="append", default=[], help="hand-maintained copy to check (repeatable)")
    ap.add_argument("--cover-letter", default=None)
    ap.add_argument("--asset-dir", default=None)
    ap.add_argument("--portal-fields", default=None,
                    help="directory of portal paste-verbatim .txt fields (abstract.txt, keywords.txt, …)")
    ap.add_argument("--figures-dir", default=None,
                    help="directory of figure files to size/format-check (default: submission/<journal>/figures or ./figures)")
    ap.add_argument("--figure-accept", action="append", default=[], metavar="EXT",
                    help="portal-accepted figure extension (repeatable; e.g. tiff jpeg eps for SNAPP). Omit to size-check only.")
    ap.add_argument("--figure-max-mb", type=float, default=25.0,
                    help="figure size cap in MB for the readiness check (default 25)")
    ap.add_argument("--prospero", default=None)
    ap.add_argument("--pool-lock", default=None)
    ap.add_argument("--out", default=None, help="report path (default: <project-root>/qc/preflight_gate_report.json)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    known = {c["id"] for c in CHECKS}
    bad = (set(args.require) | set(args.skip)) - known
    if bad:
        sys.stderr.write(f"ERROR: unknown check id(s): {', '.join(sorted(bad))}\n"
                         f"known: {', '.join(sorted(known))}\n")
        return 2

    ctx = Ctx(args)
    if not ctx.root.is_dir():
        sys.stderr.write(f"ERROR: project root not found: {ctx.root}\n")
        return 2

    checks = [run_check(spec, ctx, args) for spec in CHECKS]

    summary = {k: 0 for k in ("ok", "warn", "blocker", "skipped", "error")}
    for c in checks:
        summary[c["status"]] = summary.get(c["status"], 0) + 1
    halt = any(c["blocker"] for c in checks)
    gate_error = any(c["status"] == "error" for c in checks)

    report = {
        "schema_version": 1,
        "generated_by": "preflight_gate.py",
        "project_root": str(ctx.root),
        "journal": ctx.journal,
        "strict": args.strict,
        "online": args.online,
        "double_blind": args.double_blind,
        "submission_safe": not halt,
        "halt": halt,
        "summary": summary,
        "checks": checks,
    }

    out = Path(args.out).resolve() if args.out else (ctx.qc / "preflight_gate_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.quiet:
        print("=" * 49)
        print(" Submission Pre-Flight Gate")
        print("=" * 49)
        print("| Check | Tier | Status | Detail |")
        print("|---|---|---|---|")
        for c in checks:
            print(f"| {c['id']} | {c['tier']} | {c['status']} | {c['message']} |")
        print()
        print(f"summary: {summary}")
        print(f"wrote {_rel(out)}")
        if gate_error:
            print("\nERROR: a required check could not run — fix inputs or adjust --require.")
        elif halt:
            blockers = [c["id"] for c in checks if c["blocker"]]
            print(f"\nHALT: {len(blockers)} blocker(s) — {', '.join(blockers)}. Submission is NOT safe.")
        else:
            print("\nOK: no blockers. Submission pre-flight passed"
                  + (" (P1 warnings may remain — see table)." if summary["warn"] else "."))

    if gate_error:
        return 2
    return 1 if halt else 0


if __name__ == "__main__":
    sys.exit(main())
