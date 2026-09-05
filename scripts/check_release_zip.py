#!/usr/bin/env python3
"""Verify a built classroom release ZIP is consumable by the self-updater.

This runs the SAME code the updater runs against a downloaded release — `update.safe_extract`
(per-entry traversal/symlink/zip-bomb rejection + `distribution_files.json` allowlist & per-file
sha256) and `update.validate_provenance` — so the release workflow cannot publish a ZIP the
updater would later refuse to install. Source comparison is opt-in; privacy inspection
also requires exiftool and pdftotext for packaged binary assets.

Usage:
    python3 scripts/check_release_zip.py --zip dist/medsci-skills-classroom-macos.zip \
        [--expect-tag v4.7.0] [--require-provenance]

Exit 0 = the ZIP is single-rooted, every inventory file is present with a matching size+hash, no
unsafe/extra entries exist, `installers/install.py` is present, and (if provenance is injected) its
tag/version are internally consistent and match --expect-tag.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "installers"))
import release_payload as payload
import update  # noqa: E402  (reuse the updater's own verify/safe-extract path)


def check_zip(zip_path: Path, expect_tag: str | None, require_provenance: bool, *,
              source_root: Path | None = None, expect_sha: str | None = None,
              privacy_check: bool = False, report_path: Path | None = None,
              reference: Path | None = None) -> list[str]:
    """Return a list of problems (empty == OK)."""
    problems: list[str] = []
    data = zip_path.read_bytes()
    if reference is not None and data != reference.read_bytes():
        return ['downloaded ZIP differs from the verified pre-upload bytes']

    # Single root + inventory + manifest version, read exactly as the updater does. Note: the
    # inventory is read FROM the ZIP, so this proves the ZIP is internally self-consistent (every
    # payload file matches the bundled distribution_files.json). That the inventory itself equals the
    # real source tree is a separate anchor — gen_distribution_manifest.py --check, run by validate.yml
    # and re-run by release.yml before the build — also checked here when --source-root is supplied.
    try:
        root, inventory = update.read_inventory_from_zip(data)
    except update.UpdateError:
        return ["inventory: invalid release inventory"]
    if source_root is not None or privacy_check:
        with zipfile.ZipFile(zip_path) as z:
            if any(not n.startswith(root + '/') for n in z.namelist() if not n.endswith('/')):
                return ['ZIP contains entries outside the verified payload root']
    man_version = update.read_manifest_version_from_zip(data, root)
    if man_version == "unknown":
        problems.append("distribution_manifest.json missing or unparseable in ZIP")

    # Full safe-extract round-trip: proves every inventory entry present, hashes match, no
    # traversal/symlink/dup/zip-bomb/extra entries (raises UpdateError otherwise).
    with tempfile.TemporaryDirectory(prefix="relzip-") as tmp:
        extract = Path(tmp) / "payload"
        extract.mkdir()
        try:
            update.safe_extract(data, extract, inventory)
        except update.UpdateError:
            problems.append("safe-extract: unsafe or inconsistent ZIP payload")
            return problems  # nothing else is trustworthy if extraction fails

        if not (extract / "installers" / "install.py").is_file():
            problems.append("payload has no installers/install.py")

        prov_path = extract / "provenance.json"
        if not prov_path.is_file():
            if require_provenance:
                problems.append("provenance.json missing (release builds must inject it)")
            elif expect_tag:
                # --expect-tag must not pass vacuously on a provenance-less ZIP.
                problems.append(f"--expect-tag {expect_tag} given but provenance.json is absent (cannot verify tag)")
        else:
            try:
                prov = json.loads(prov_path.read_text(encoding="utf-8"))
                if not isinstance(prov, dict):
                    raise ValueError('not an object')
            except ValueError:
                return ['invalid provenance JSON']
            if expect_sha and prov.get('git_sha') != expect_sha:
                problems.append('provenance git_sha differs from the selected source commit')
            ptag, pver = prov.get("tag", ""), prov.get("version", "")
            # tag/version internal consistency: vX.Y.Z <-> X.Y.Z, version == manifest version.
            if ptag and pver and (ptag[1:] if ptag.startswith("v") else ptag) != pver:
                problems.append("provenance tag inconsistent with version")
            if pver and man_version != "unknown" and pver != man_version:
                problems.append("provenance version differs from manifest version")
            # The updater's own provenance check (tag + version) against the expected tag.
            if expect_tag:
                try:
                    update.validate_provenance(extract, expect_tag, man_version)
                except update.UpdateError:
                    problems.append("validate_provenance: release tag/version mismatch")
                if ptag and ptag != expect_tag:
                    problems.append("provenance tag differs from expected tag")

        files = {p.relative_to(extract).as_posix(): p.read_bytes()
                 for p in extract.rglob('*') if p.is_file()}
        if source_root is not None:
            problems.extend(payload.compare_source(files, source_root, 'zip'))
        counts = None
        if privacy_check:
            findings, counts = payload.privacy(files)
            problems.extend(findings)
        payload.write_report(report_path, zip_path, files, problems, channel='zip', counts=counts)
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify a built classroom release ZIP is updater-consumable.")
    ap.add_argument("--zip", required=True, type=Path, help="path to a built classroom ZIP")
    ap.add_argument("--expect-tag", default=None, help="assert provenance tag == this release tag")
    ap.add_argument("--require-provenance", action="store_true", help="fail if provenance.json is absent")
    ap.add_argument('--source-root', type=Path, help='selected release checkout; compare every payload byte')
    ap.add_argument('--expect-sha', help='selected source commit recorded by provenance')
    ap.add_argument('--privacy', action='store_true', help='inspect actual text and binary metadata')
    ap.add_argument('--report', type=Path, help='write hashes and inspection coverage; never raw findings')
    ap.add_argument('--reference', type=Path, help='pre-upload ZIP whose exact bytes must match')
    args = ap.parse_args(argv)

    if args.report:
        args.report.unlink(missing_ok=True)
    if not args.zip.is_file():
        print(f"FAIL: no such ZIP: {args.zip}", file=sys.stderr)
        return 2
    try:
        problems = check_zip(args.zip, args.expect_tag, args.require_provenance,
                             source_root=args.source_root, expect_sha=args.expect_sha,
                             privacy_check=args.privacy, report_path=args.report, reference=args.reference)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, payload.PayloadError):
        print('FAIL: release ZIP inspection could not complete', file=sys.stderr)
        return 2
    if problems:
        print(f"FAIL: {args.zip.name} is not updater-consumable:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    inv_n = len(update.read_inventory_from_zip(args.zip.read_bytes())[1])
    print(f"OK: {args.zip.name} — single root, {inv_n} inventory files match, install.py present"
          + (f", provenance tag {args.expect_tag}" if args.expect_tag else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
