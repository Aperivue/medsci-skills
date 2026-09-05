#!/usr/bin/env python3
"""Shared release-payload plumbing for the existing ZIP and npm audits.

Uses the updater's archive limits, the public identifier scanner, contribution
credential patterns and the asset metadata scanner. Findings never quote values.
No code from an unpacked payload is imported or executed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'installers'))
import update
import check_precedent


def _module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


asset = _module('release_asset_privacy', 'skills/sync-submission/scripts/check_asset_anonymization.py')
safety = _module('release_contribution_safety', 'skills/contribute/scripts/check_contribution_safety.py')
BINARY = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.pdf', '.docx', '.pptx', '.xlsx'}
OFFICE = {'.docx', '.pptx', '.xlsx'}
# Exactly one reviewed synthetic token in the contribution scanner's regression.
# A different token in the same file still fails; the credential is never stored here.
SYNTHETIC_SECRETS = {
    ('skills/contribute/tests/test_contribution_safety.sh',
     '03aafb028d538b06c4341bf8cf2a692a3c6d1f36e34e0e0b376f407c6117a246'),
}
EXIF_TAGS = ('Author Creator LastModifiedBy LastSavedBy Copyright Artist Owner OwnerName '
             'CompanyName Manager HostComputer UserComment Subject Title Description Keywords '
             'Comment Producer CreatorTool Software').split()


class PayloadError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def label(path):
    # Even a filename can contain a private identifier. Logs use opaque file IDs.
    return 'file-' + digest(path.encode())[:12]


def tar_files(path):
    """Read a single package/ root; reject links, duplicates and unsafe paths."""
    files, modes, seen = {}, {}, set()
    total = 0
    with tarfile.open(path, 'r:gz') as archive:
        for i, member in enumerate(archive, 1):
            if i > update.MAX_ENTRIES:
                raise PayloadError('tar entry limit exceeded')
            name = member.name.rstrip('/') if member.isdir() else member.name
            parts = name.split('/')
            if (parts[0] != 'package' or any(p in ('', '.', '..') for p in parts)
                    or '\\' in name or ':' in name):
                raise PayloadError(f'unsafe tar entry #{i}')
            if member.isdir():
                continue
            if not member.isfile() or len(parts) < 2:
                raise PayloadError(f'non-regular tar entry #{i}')
            rel = '/'.join(parts[1:])
            if rel.casefold() in seen:
                raise PayloadError(f'duplicate tar entry #{i}')
            seen.add(rel.casefold())
            total += member.size
            if member.size < 0 or total > update.MAX_TOTAL_UNCOMPRESSED:
                raise PayloadError('tar uncompressed size limit exceeded')
            data = archive.extractfile(member).read()
            if len(data) != member.size:
                raise PayloadError(f'truncated tar entry #{i}')
            files[rel], modes[rel] = data, member.mode
    if not files:
        raise PayloadError('tarball has no payload files')
    return files, modes


def tracked_files(source):
    try:
        top = subprocess.check_output(['git', '-C', str(source), 'rev-parse', '--show-toplevel'], text=True).strip()
        if Path(top).resolve() != source.resolve():
            raise PayloadError('source-root must be the root of the selected Git checkout')
        raw = subprocess.check_output(['git', '-C', str(source), 'ls-files', '-z'], text=True)
    except subprocess.CalledProcessError as exc:
        raise PayloadError('cannot enumerate the selected source checkout') from exc
    return set(raw.rstrip('\0').split('\0'))


def npm_expected(source):
    config = json.loads((source / 'package.json').read_text())
    include = config.get('files', [])
    if not isinstance(include, list) or not include or any(
            not isinstance(p, str) or not p or any(c in p for c in '*?[]') for p in include):
        raise PayloadError('npm source requires an explicit files allowlist')
    # npm always includes root README/licence files as well as package.json.
    return {p for p in tracked_files(source) if p == 'package.json'
            or ('/' not in p and p.lower().startswith(('readme', 'license', 'licence')))
            or any(p == x.rstrip('/') or p.startswith(x.rstrip('/') + '/') for x in include)}


def compare_source(files, source, channel):
    if channel == 'npm':
        expected = npm_expected(source)
    else:
        inv = json.loads((source / 'metadata/distribution_files.json').read_text())['files']
        expected = {e['path'] for e in inv} | (update.METADATA_ALLOWLIST - {'provenance.json'})
    actual = set(files) - ({'provenance.json'} if channel == 'zip' else set())
    problems = []
    for kind, paths in [('missing', expected - actual), ('unexpected', actual - expected)]:
        problems.extend(f'{kind} source payload {label(p)}' for p in sorted(paths))
    for p in sorted(actual & expected):
        target = source / p
        if ('_corpus' in Path(p).parts or not target.resolve().is_relative_to(source.resolve())
                or target.is_symlink() or not target.is_file() or target.read_bytes() != files[p]):
            problems.append(f'bytes differ from selected source: {label(p)}')
    return problems


def privacy(files):
    """Scan the actual bytes; publication attribution stays allowed in root READMEs."""
    problems = []
    counts = {'text': 0, 'binary_metadata': 0, 'office_xml_parts': 0, 'pdf_text': 0}
    hashes = check_precedent.load_hashes()
    author_hashes = check_precedent.load_hashes(allow_author=True)

    def scan(text, rel, *, hidden=False):
        allowed = author_hashes if re.fullmatch(r'README(?:\.[A-Za-z-]+)?\.md', rel) else hashes
        if check_precedent.scan_text(text, allowed):
            problems.append(f'private identifier: {label(rel)}')
        cleaned = text.replace('private-journal-profiles', 'journal-profiles')
        if re.search(r'\.claude/(plans|projects|private)', cleaned):
            problems.append(f'private configuration path: {label(rel)}')
        if hidden and asset.DOCX_ABS_PATH_RE.search(text):
            problems.append(f'home path in hidden metadata: {label(rel)}')
        for match in safety.SECRET.finditer(text):
            if (rel, digest(match.group().encode())) not in SYNTHETIC_SECRETS:
                problems.append(f'credential pattern: {label(rel)}')

    with tempfile.TemporaryDirectory(prefix='release-privacy-') as temp:
        binaries = []
        for i, (rel, data) in enumerate(sorted(files.items())):
            scan(rel, rel)
            suffix = Path(rel).suffix.lower()
            if suffix in BINARY:
                path = Path(temp) / f'asset-{i}{suffix}'
                path.write_bytes(data)
                binaries.append((rel, path))
                if suffix == '.pdf':
                    try:
                        proc = subprocess.run(['pdftotext', '-q', str(path), '-'],
                            capture_output=True, text=True, check=True, timeout=60)
                        scan(proc.stdout, rel)
                        counts['pdf_text'] += 1
                    except (OSError, subprocess.SubprocessError):
                        problems.append(f'PDF text could not be inspected: {label(rel)}')
                if suffix in OFFICE:
                    try:
                        with zipfile.ZipFile(io.BytesIO(data)) as z:
                            parts = z.infolist()
                            if len(parts) > update.MAX_ENTRIES or sum(x.file_size for x in parts) > update.MAX_TOTAL_UNCOMPRESSED:
                                raise PayloadError('office archive limits exceeded')
                            for part in parts:
                                if part.filename.endswith(('.xml', '.rels')):
                                    counts['office_xml_parts'] += 1
                                    scan(z.read(part).decode('utf-8'), rel, hidden=True)
                        # Reuse the submission scanner's all-part embedded-path check.
                        if asset._docx_embedded_abs_paths(path):
                            problems.append(f'embedded document path: {label(rel)}')
                    except (zipfile.BadZipFile, UnicodeError, RuntimeError, PayloadError):
                        problems.append(f'unreadable office package: {label(rel)}')
            else:
                try:
                    scan(data.decode('utf-8'), rel)
                    counts['text'] += 1
                except UnicodeError:
                    problems.append(f'unsupported binary (not scanned): {label(rel)}')
        if binaries:
            try:
                proc = subprocess.run(['exiftool', '-json', *['-' + t for t in EXIF_TAGS],
                                       *[str(p) for _, p in binaries]], capture_output=True, text=True, timeout=60)
                if proc.returncode != 0:
                    raise PayloadError('metadata extraction failed')
                records = json.loads(proc.stdout)
                by_path = {r['SourceFile']: r for r in records}
                for rel, path in binaries:
                    record = by_path.get(str(path))
                    if record is None or 'Error' in record or 'Warning' in record:
                        raise PayloadError('metadata extraction incomplete')
                    scan(json.dumps({k: v for k, v in record.items() if k != 'SourceFile'}, ensure_ascii=False), rel, hidden=True)
                    counts['binary_metadata'] += 1
            except (OSError, ValueError, KeyError, subprocess.TimeoutExpired, PayloadError):
                problems.append('binary metadata could not be fully inspected (exiftool required)')
    return sorted(set(problems)), counts


def write_report(path, artifact, files, problems, *, channel, counts=None):
    report = {'schema_version': 1, 'channel': channel, 'artifact_sha256': digest(artifact.read_bytes()),
              'file_count': len(files), 'ok': not problems, 'problems': problems,
              'privacy': {'performed': counts is not None, 'scanned': counts},
              'files': [{'path': p, 'size': len(data), 'sha256': digest(data)}
                        for p, data in sorted(files.items())] if not problems else []}
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + '\n')
    return report
