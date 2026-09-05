#!/usr/bin/env python3
"""Synthetic normal and broken release artifacts; no publication or credentials."""
import hashlib
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import release_payload as payload
import check_release_zip as zcheck
import check_npm_package_contents as ncheck


class PayloadControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'; self.root.mkdir()
        self.out = Path(self.temp.name) / 'artifacts'; self.out.mkdir()
        self.files = {'README.md': b'Synthetic public documentation.\n',
                      'README_FIRST.md': b'Synthetic setup.\n', 'LICENSE': b'Synthetic license.\n',
                      'installers/install.py': b'print("Synthetic installer")\n',
                      'bin/medsci-skills.js': b'#!/usr/bin/env node\n',
                      'skills/demo/SKILL.md': b'Synthetic example skill.\n'}
        config = {'name': 'medsci-skills', 'version': '9.9.9',
                  'files': ['skills/', 'installers/install.py', 'bin/medsci-skills.js',
                            'README.md', 'README_FIRST.md', 'LICENSE', 'metadata/']}
        self.files['package.json'] = json.dumps(config).encode()
        self.files['metadata/distribution_manifest.json'] = json.dumps({
            'schema_version': 1, 'version': '9.9.9', 'owned_skills': ['demo']}).encode()
        self.refresh_inventory()
        for rel, data in self.files.items():
            path = self.root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.track()

    def track(self):
        subprocess.run(['git', '-C', str(self.root), 'add', '--', *sorted(self.files)], check=True)

    def refresh_inventory(self, files=None):
        files = self.files if files is None else files
        rows = [{'path': p, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                for p, data in sorted(files.items()) if p.startswith(('skills/', 'installers/'))
                or p in ('LICENSE', 'README_FIRST.md')]
        files['metadata/distribution_files.json'] = json.dumps({'schema_version': 1, 'files': rows}).encode()

    def zip(self, files=None, *, sha='a'*40, tag='v9.9.9', omit=(), extra=None):
        files = self.files if files is None else files
        inv = json.loads(files['metadata/distribution_files.json'])['files']
        names = {x['path'] for x in inv} | {'metadata/distribution_files.json', 'metadata/distribution_manifest.json'}
        path = self.out / 'test.zip'
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name in sorted(names - set(omit)):
                z.writestr('release/' + name, files[name])
            z.writestr('release/provenance.json', json.dumps({'schema_version':1, 'version':'9.9.9', 'tag':tag, 'git_sha':sha}))
            if extra:
                z.writestr(*extra)
        return path

    def tar(self, files=None, *, name='test.tgz', omit=(), extra=None, cli_mode=0o755, mtime=0):
        files = self.files if files is None else files
        path = self.out / name
        with tarfile.open(path, 'w:gz') as t:
            for rel, data in sorted(files.items()):
                if rel in omit: continue
                info = tarfile.TarInfo('package/' + rel); info.size = len(data); info.mtime = mtime
                info.mode = cli_mode if rel == 'bin/medsci-skills.js' else 0o644
                t.addfile(info, io.BytesIO(data))
            if extra:
                info, data = extra
                info.size = len(data)
                t.addfile(info, io.BytesIO(data))
        return path

    def check_zip(self, path, **kwargs):
        return zcheck.check_zip(path, 'v9.9.9', True, source_root=self.root, expect_sha='a'*40, **kwargs)

    def check_npm(self, path, **kwargs):
        return ncheck.check_tarball(path, source_root=self.root, expect_version='9.9.9', **kwargs)

    def test_clean_zip_has_a_real_inspection_report(self):
        report = self.out / 'report.json'
        self.assertEqual(self.check_zip(self.zip(), privacy_check=True, report_path=report), [])
        result = json.loads(report.read_text())
        self.assertTrue(result['ok']); self.assertTrue(result['privacy']['performed'])
        self.assertGreater(result['privacy']['scanned']['text'], 0)

    def test_self_consistent_zip_is_still_bound_to_selected_source(self):
        forged = dict(self.files); forged['skills/demo/SKILL.md'] = b'Different synthetic content'
        self.refresh_inventory(forged)
        path = self.zip(forged)
        self.assertEqual(zcheck.check_zip(path, 'v9.9.9', True), [])
        self.assertTrue(any('source' in p for p in self.check_zip(path)))

    def test_zip_missing_inventory_file_is_rejected(self):
        self.assertTrue(self.check_zip(self.zip(omit=['skills/demo/SKILL.md'])))

    def test_wrong_source_commit_is_rejected(self):
        self.assertTrue(any('git_sha' in p for p in self.check_zip(self.zip(sha='b'*40))))

    def test_wrong_zip_tag_is_rejected(self):
        self.assertTrue(self.check_zip(self.zip(tag='v8.8.8')))

    def test_ignored_archive_sidecar_is_not_a_release_payload(self):
        self.assertTrue(self.check_zip(self.zip(extra=('__MACOSX/synthetic.txt', b'Synthetic'))))

    def test_downloaded_zip_must_match_preupload_bytes(self):
        path = self.zip(); reference = self.out / 'reference.zip'; reference.write_bytes(path.read_bytes())
        self.assertEqual(self.check_zip(path, reference=reference), [])
        path.write_bytes(path.read_bytes()+b'different archive comment')
        self.assertTrue(any('pre-upload' in p for p in self.check_zip(path, reference=reference)))

    def test_normal_npm_payload_passes(self):
        self.assertEqual(self.check_npm(self.tar(), privacy_check=True), [])

    def test_npm_missing_deep_skill_asset_is_rejected(self):
        self.assertTrue(any('missing' in p for p in self.check_npm(self.tar(omit=['skills/demo/SKILL.md']))))

    def test_npm_unlisted_scratch_file_is_rejected(self):
        files = dict(self.files); files['skills/demo/private-draft.txt'] = b'Synthetic'
        self.assertTrue(any('unexpected' in p for p in self.check_npm(self.tar(files))))

    def test_npm_same_version_different_bytes_is_rejected(self):
        files = dict(self.files); files['skills/demo/SKILL.md'] = b'Wrong payload'
        self.assertTrue(any('bytes differ' in p for p in self.check_npm(self.tar(files))))

    def test_npm_wrong_version_is_rejected(self):
        files = dict(self.files); config = json.loads(files['package.json']); config['version'] = '8.8.8'
        files['package.json'] = json.dumps(config).encode()
        self.assertTrue(any('identity/version' in p for p in self.check_npm(self.tar(files))))

    def test_npm_executable_bit_is_verified(self):
        self.assertTrue(any('executable' in p for p in self.check_npm(self.tar(cli_mode=0o644))))

    def test_npm_headers_may_change_but_payload_must_not(self):
        before = self.tar(name='before.tgz', mtime=1)
        after = self.tar(name='after.tgz', mtime=2)
        self.assertNotEqual(before.read_bytes(), after.read_bytes())
        self.assertEqual(self.check_npm(after, reference=before), [])
        with tarfile.open(after, 'w:gz') as t:
            entry = tarfile.TarInfo('package/README.md'); entry.size = 7
            t.addfile(entry, io.BytesIO(b'changed'))
        self.assertTrue(self.check_npm(after, reference=before))

    def test_tar_traversal_links_and_duplicates_are_rejected(self):
        for name, kind in [('package/../escape', tarfile.REGTYPE),
                           ('package/link', tarfile.SYMTYPE), ('package/README.md', tarfile.REGTYPE)]:
            with self.subTest(name=name):
                info = tarfile.TarInfo(name); info.type = kind; info.linkname = 'README.md'
                path = self.tar(extra=(info, b''))
                with self.assertRaises(payload.PayloadError): payload.tar_files(path)

    def test_new_credential_in_existing_synthetic_fixture_still_fails(self):
        rel = 'skills/contribute/tests/test_contribution_safety.sh'
        source = (ROOT / rel).read_text()
        original = payload.safety.SECRET.search(source).group()
        self.assertEqual(payload.privacy({rel: original.encode()})[0], [])
        token = 'sk-' + 'Q'*32
        problems, _ = payload.privacy({rel: (original+'\n'+token).encode()})
        self.assertTrue(any('credential' in p for p in problems))
        self.assertNotIn(token, str(problems))

    def test_hidden_office_path_is_found_without_printing_it(self):
        hidden = '/' + 'Users' + '/synthetic-owner/source.csl'
        binary = io.BytesIO()
        with zipfile.ZipFile(binary, 'w') as z:
            z.writestr('docProps/custom.xml', '<Properties><path>'+hidden+'</path></Properties>')
        for suffix in ('.docx', '.pptx', '.xlsx'):
            problems, counts = payload.privacy({'skills/demo/template'+suffix: binary.getvalue()})
            self.assertTrue(any('path' in p for p in problems))
            self.assertEqual(counts['office_xml_parts'], 1)
            self.assertNotIn(hidden, str(problems))

    def test_unreadable_office_package_does_not_pass(self):
        problems, _ = payload.privacy({'skills/demo/template.docx': b'not a document'})
        self.assertTrue(any('unreadable office' in p for p in problems))

    def test_missing_metadata_tool_is_not_a_clean_scan(self):
        with patch.object(payload.subprocess, 'run', side_effect=FileNotFoundError):
            problems, counts = payload.privacy({'skills/demo/example.png': b'synthetic'})
        self.assertTrue(any('could not' in p for p in problems)); self.assertEqual(counts['binary_metadata'], 0)

    def test_identifier_scan_includes_r_source(self):
        text = 'Synthetic confidential label'
        hashed = hashlib.sha256(text.lower().encode()).hexdigest()
        with patch.object(payload.check_precedent, 'load_hashes', return_value={hashed}):
            problems, _ = payload.privacy({'skills/demo/example.R': text.encode()})
        self.assertTrue(any('private identifier' in p for p in problems))
        self.assertNotIn(text, str(problems))

    def step(self, name, **extra_env):
        steps = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']['release']['steps']
        run, = [s['run'] for s in steps if s.get('name', '').startswith(name)]
        env = dict(os.environ, RELEASE_TAG='v9.9.9', SOURCE_SHA='a'*40, **extra_env)
        return subprocess.run(['bash', '-e', '-c', run], cwd=self.root, env=env, capture_output=True, text=True)

    def tools_checkout(self):
        (self.root / '.release-tools').symlink_to(ROOT, target_is_directory=True)
        (self.root / 'dist').mkdir(exist_ok=True)

    def test_workflow_builds_selected_source_and_preserves_other_output(self):
        self.tools_checkout()
        sentinel = self.root / 'dist/keep.txt'; sentinel.write_text('keep')
        result = self.step('Build classroom release ZIPs')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sentinel.read_text(), 'keep')
        for platform in ('macos', 'windows'):
            path = self.root / f'dist/medsci-skills-classroom-{platform}.zip'
            self.assertEqual(self.check_zip(path), [])
        self.assertEqual(self.step('Verify ZIPs are consumable').returncode, 0)

    def test_workflow_records_tag_commit_not_dispatch_sha(self):
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Synthetic Test',
                        '-c', 'user.email=test@example.org', 'commit', '-qm', 'Synthetic source'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'tag', 'v9.9.9'], check=True)
        expected = subprocess.check_output(['git', '-C', str(self.root), 'rev-parse', 'HEAD'], text=True).strip()
        env_file = self.out / 'env'
        result = self.step('Resolve the selected release commit', GITHUB_ENV=str(env_file), GITHUB_SHA='b'*40)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(env_file.read_text(), f'SOURCE_SHA={expected}\n')

    def test_workflow_publishes_the_inspected_tarball_and_skips_existing_version(self):
        stub = self.out / 'npm'
        stub.write_text('#!/bin/sh\nif [ "$1" = view ]; then exit "$EXISTS_EXIT"; fi\nprintf "%s\\n" "$@" > "$CALLS"\n')
        stub.chmod(0o755); calls = self.out / 'calls'
        for exists in ('1', '0'):
            calls.unlink(missing_ok=True)
            result = self.step('Publish to npm', PATH=str(self.out)+os.pathsep+os.environ['PATH'],
                               EXISTS_EXIT=exists, CALLS=str(calls))
            self.assertEqual(result.returncode, 0, result.stderr)
            if exists == '1':
                self.assertEqual(calls.read_text().splitlines(), ['publish', './dist/medsci-skills-9.9.9.tgz',
                                 '--ignore-scripts', '--provenance', '--access', 'public'])
            else:
                self.assertFalse(calls.exists())

    def test_workflow_downloaded_zip_missing_or_mutated_is_rejected(self):
        self.tools_checkout()
        stub = self.out / 'gh'
        stub.write_text('#!/bin/sh\nmkdir -p dist/downloaded\ncp dist/*.zip dist/downloaded/\n'
                        'if [ "$DAMAGE" = mutate ]; then printf changed >> dist/downloaded/medsci-skills-classroom-macos.zip; fi\n'
                        'if [ "$DAMAGE" = missing ]; then rm dist/downloaded/medsci-skills-classroom-windows.zip; fi\n')
        stub.chmod(0o755)
        for platform in ('macos', 'windows'):
            (self.root / f'dist/medsci-skills-classroom-{platform}.zip').write_bytes(self.zip().read_bytes())
        for damage in ('none', 'mutate', 'missing'):
            result = self.step('Download and compare published ZIPs', DAMAGE=damage,
                               PATH=str(self.out)+os.pathsep+os.environ['PATH'])
            self.assertEqual(result.returncode == 0, damage == 'none', result.stderr)

    def test_notes_are_checked_before_upload_without_echoing_credentials(self):
        self.tools_checkout()
        notes = self.root / 'CHANGELOG.md'
        notes.write_text('## [9.9.9]\n\nSynthetic release notes.\n')
        self.assertEqual(self.step('Extract release notes').returncode, 0)
        token = 'sk-' + 'Q'*32
        notes.write_text('## [9.9.9]\n\n'+token+'\n')
        result = self.step('Extract release notes')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(token, result.stdout+result.stderr)

    def test_workflow_checks_before_and_after_publication_with_pinned_tools(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())
        steps = workflow['jobs']['release']['steps']
        names = [s['name'] for s in steps]
        index = lambda prefix: next(i for i,n in enumerate(names) if n.startswith(prefix))
        self.assertLess(index('Verify actual npm'), index('Create GitHub Release'))
        self.assertLess(index('Extract release notes'), index('Create GitHub Release'))
        self.assertLess(index('Create GitHub Release'), index('Download and compare published ZIPs'))
        self.assertLess(index('Publish to npm'), index('Download and compare published npm'))
        checkout = steps[index('Checkout verification tools')]['with']
        self.assertEqual(checkout['ref'], '${{ github.workflow_sha }}')
        self.assertFalse(checkout['persist-credentials'])
        after = steps[index('Download and compare published npm')]
        self.assertEqual(after['if'], "env.HAS_NPM_TOKEN == 'true'")
        self.assertIn('--published-version', after['run']); self.assertIn('--reference', after['run'])

    def registry_responses(self, data, *, version='9.9.9', integrity=None, url=None):
        url = url or 'https://registry.npmjs.org/medsci-skills/-/medsci-skills-9.9.9.tgz'
        integrity = integrity or 'sha512-'+base64.b64encode(hashlib.sha512(data).digest()).decode()
        info = {'name':'medsci-skills', 'version':version, 'dist':{'tarball':url, 'integrity':integrity}}
        body = io.BytesIO(data); body.geturl = lambda: url
        return [io.BytesIO(json.dumps(info).encode()), body]

    def test_registry_download_checks_integrity_and_actual_selected_source(self):
        data = self.tar().read_bytes(); dest = self.out / 'download.tgz'
        with patch.object(ncheck.urllib.request, 'urlopen', side_effect=self.registry_responses(data)):
            ncheck.download_published('9.9.9', dest)
        self.assertEqual(dest.read_bytes(), data); self.assertEqual(self.check_npm(dest), [])

    def test_registry_wrong_version_integrity_or_host_fails(self):
        data = self.tar().read_bytes(); dest = self.out / 'download.tgz'
        for kwargs in ({'version':'8.8.8'}, {'integrity':'sha512-wrong'}, {'url':'https://example.org/package.tgz'}):
            with patch.object(ncheck.urllib.request, 'urlopen', side_effect=self.registry_responses(data, **kwargs)):
                with self.assertRaises(payload.PayloadError): ncheck.download_published('9.9.9', dest)
            self.assertFalse(dest.exists())

    def test_registry_unavailable_never_leaves_a_passable_download(self):
        dest = self.out / 'download.tgz'
        with patch.object(ncheck.urllib.request, 'urlopen', side_effect=ncheck.urllib.error.URLError('unavailable')), \
                patch.object(ncheck.time, 'sleep') as sleep:
            with self.assertRaises(payload.PayloadError): ncheck.download_published('9.9.9', dest)
        self.assertEqual(sleep.call_count, 4); self.assertFalse(dest.exists())

    def test_malformed_package_identity_is_rejected(self):
        files = dict(self.files); files['package.json'] = b'[]'
        self.assertTrue(self.check_npm(self.tar(files)))

    def test_zip_rejection_does_not_quote_untrusted_entry_paths(self):
        private = 'synthetic-private-value'
        path = self.zip(extra=('release/'+private, b'synthetic'))
        findings = self.check_zip(path)
        self.assertTrue(findings); self.assertNotIn(private, str(findings))


if __name__ == '__main__':
    unittest.main()
