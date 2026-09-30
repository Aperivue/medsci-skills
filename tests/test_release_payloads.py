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

    def write_config(self, entries):
        files = dict(self.files); config = json.loads(files['package.json']); config['files'] = entries
        files['package.json'] = json.dumps(config).encode()
        (self.root / 'package.json').write_bytes(files['package.json'])
        return files

    def test_npm_files_exclusion_is_predicted_segment_by_segment(self):
        test_file = 'skills/demo/tests/test_demo.sh'
        (self.root / test_file).parent.mkdir(parents=True); (self.root / test_file).write_bytes(b'Synthetic.\n')
        subprocess.run(['git', '-C', str(self.root), 'add', '--', test_file], check=True)
        files = self.write_config(['skills/', '!skills/*/tests/', 'installers/install.py', 'bin/medsci-skills.js',
                                   'README.md', 'README_FIRST.md', 'LICENSE', 'metadata/'])
        expected = payload.npm_expected(self.root)
        self.assertNotIn(test_file, expected); self.assertIn('skills/demo/SKILL.md', expected)
        self.assertEqual(self.check_npm(self.tar(files)), [])
        files[test_file] = b'Synthetic.\n'
        self.assertTrue(any('unexpected' in p for p in self.check_npm(self.tar(files))))

    def test_npm_files_patterns_it_cannot_predict_are_refused(self):
        for entry in ('skills/*/', '!skills/**/tests/', '!skills/de?o/', '!'):
            with self.subTest(entry=entry):
                self.write_config(['skills/', entry, 'README.md'])
                with self.assertRaises(payload.PayloadError): payload.npm_expected(self.root)

    def test_repository_npm_payload_ships_doctor_and_no_skill_tests(self):
        # install.py imports doctor.py for its closing "what else this computer needs" summary, and
        # docs/install.md tells people to run it; skill tests stay in the repository, as in the ZIP.
        expected = payload.npm_expected(ROOT)
        self.assertIn('installers/doctor.py', expected)
        self.assertEqual([p for p in expected if p.startswith('skills/') and p.split('/')[2:3] == ['tests']], [])
        self.assertIn('skills/orchestrate/SKILL.md', expected)

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
        env = dict(os.environ, RELEASE_TAG='v9.9.9', SOURCE_SHA='a'*40)
        env.update(extra_env)
        return subprocess.run(['bash', '-e', '-c', run], cwd=self.root, env=env, capture_output=True, text=True)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), '-c', 'user.name=Synthetic Test',
                                        '-c', 'user.email=test@example.org', *args], text=True).strip()

    def commit_and_tag(self, *tags, message='Synthetic source'):
        self.git('commit', '-q', '--allow-empty', '-m', message)
        for tag in tags:
            self.git('tag', tag)
        return self.git('rev-parse', 'HEAD')

    def stub(self, name, body):
        path = self.out / name
        path.write_text('#!/bin/bash\n' + body)
        path.chmod(0o755)
        return str(self.out) + os.pathsep + os.environ['PATH']

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

    def test_run_triggered_from_another_commit_is_rejected(self):
        # The attestation and npm provenance sign GITHUB_SHA, the commit the run was triggered
        # from; the ZIP records the tag's commit. A recovery dispatched from main for an older tag
        # (v5.27.0's was) therefore signed main's commit as the payload's source. The run must
        # come from the tag's own commit, and the recorded SOURCE_SHA is still the tag's.
        expected = self.commit_and_tag('v9.9.9')
        env_file = self.out / 'env'
        elsewhere = self.step('Resolve the selected release commit', GITHUB_ENV=str(env_file), GITHUB_SHA='b'*40)
        self.assertNotEqual(elsewhere.returncode, 0, 'a run from another commit would sign the wrong provenance')
        self.assertIn('--ref v9.9.9', elsewhere.stderr)
        self.assertFalse(env_file.exists())
        from_tag = self.step('Resolve the selected release commit', GITHUB_ENV=str(env_file), GITHUB_SHA=expected)
        self.assertEqual(from_tag.returncode, 0, from_tag.stderr)
        self.assertEqual(env_file.read_text(), f'SOURCE_SHA={expected}\n')

    def preflight(self, source_sha, runs, **env):
        # `gh api --jq` prints one "status conclusion url" line per Validate run; the stub prints
        # the lines the case supplies, one set per call, and records what it was asked. Like gh,
        # it returns the second page only when asked to --paginate.
        path = self.stub('gh', 'echo "$*" >> "$CALLS"\n'
                               'var="STUB_RUNS_$(grep -c "" "$CALLS")"; val="${!var}"\n'
                               'printf "%s" "${val:-$STUB_RUNS}"\n'
                               'case "$*" in *--paginate*) printf "%s" "${STUB_RUNS_PAGE2:-}" ;; esac\n')
        calls = self.out / 'gh-calls'
        calls.unlink(missing_ok=True)
        env = dict(dict(VALIDATE_WAIT_WINDOW='0', VALIDATE_WAIT_INTERVAL='0'), **env)
        result = self.step('Preflight', SOURCE_SHA=source_sha, STUB_RUNS=runs, CALLS=str(calls), PATH=path,
                           GITHUB_REPOSITORY='Synthetic/repo', **env)
        return result, (calls.read_text() if calls.exists() else '')

    def test_preflight_requires_the_commit_on_main_and_a_passing_validate_run(self):
        # Validate does not run on tag pushes. Before this preflight, a tag on a commit whose
        # Validate run failed, or that no Validate run ever saw, published anyway.
        self.git('checkout', '-q', '-b', 'main')
        on_main = self.commit_and_tag('v9.9.9')
        self.git('remote', 'add', 'origin', str(self.root))
        ok = 'completed success https://example.org/runs/1\n'

        result, calls = self.preflight(on_main, ok)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('actions/workflows/validate.yml/runs?head_sha=' + on_main, calls)

        for runs, why in [('', 'no Validate run'),
                          ('completed failure https://example.org/runs/2\n', 'did not pass'),
                          (ok + 'completed cancelled https://example.org/runs/3\n', 'did not pass'),
                          ('in_progress none https://example.org/runs/4\n', 'still running')]:
            with self.subTest(runs=runs):
                result, _ = self.preflight(on_main, runs)
                self.assertNotEqual(result.returncode, 0, f'{runs!r} must not publish')
                self.assertIn(why, result.stderr)

        # A failed run on the second page of results is still a failed run.
        page1 = ''.join(f'completed success https://example.org/runs/{i}\n' for i in range(100))
        result, calls = self.preflight(on_main, page1, STUB_RUNS_PAGE2='completed failure https://example.org/runs/101\n')
        self.assertNotEqual(result.returncode, 0, 'a failure on page 2 must not publish')
        self.assertIn('runs/101', result.stderr)

        # A run still in progress is waited for, not failed on sight.
        result, calls = self.preflight(on_main, ok, STUB_RUNS_1='queued none https://example.org/runs/5\n',
                                       VALIDATE_WAIT_WINDOW='30')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls.splitlines()), 2)

        # Green CI on a commit main never had is still not a release of main.
        self.git('checkout', '-q', '-b', 'side')
        off_main = self.commit_and_tag('v9.9.10', message='Synthetic side change')
        self.git('checkout', '-q', 'main')
        result, calls = self.preflight(off_main, ok, RELEASE_TAG='v9.9.10')
        self.assertNotEqual(result.returncode, 0, 'a tag off main must not publish')
        self.assertIn('not on main', result.stderr)
        self.assertEqual(calls, '')

    def test_preflight_runs_before_anything_is_built_with_a_read_only_scope(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())
        names = [s['name'] for s in workflow['jobs']['release']['steps']]
        index = lambda prefix: next(i for i, n in enumerate(names) if n.startswith(prefix))
        self.assertLess(index('Resolve the selected release commit'), index('Preflight'))
        self.assertLess(index('Preflight'), index('Build classroom release ZIPs'))
        self.assertLess(index('Preflight'), index('Create GitHub Release'))
        perms = workflow['permissions']
        self.assertEqual(perms.get('actions'), 'read')
        self.assertEqual({k for k, v in perms.items() if v == 'write'}, {'contents', 'id-token', 'attestations'})

    def test_publish_job_node_supports_trusted_publishing(self):
        # npm documents trusted publishing as needing Node >= 22.14.0 as well as npm >= 11.5.1.
        steps = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']['release']['steps']
        node, = [s['with']['node-version'] for s in steps if 'setup-node' in s.get('uses', '')]
        parts = [int(x) for x in str(node).split('.')]
        self.assertTrue(parts[0] > 22 or (parts[0] == 22 and (len(parts) == 1 or parts[1] >= 14)),
                        f'node-version {node} is below the 22.14 trusted publishing requires')

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
        self.assertLess(index('Publish to npm'), index('npm must actually carry'))
        self.assertLess(index('npm must actually carry'), index('Download and compare published npm'))
        checkout = steps[index('Checkout verification tools')]['with']
        self.assertEqual(checkout['ref'], '${{ github.workflow_sha }}')
        self.assertFalse(checkout['persist-credentials'])
        after = steps[index('Download and compare published npm')]
        self.assertEqual(after['if'], "env.NPM_PUBLISH == 'true'")
        self.assertIn('--published-version', after['run']); self.assertIn('--reference', after['run'])

        # v5.27.0 was tagged and released while npm stayed on 5.26.2: the credential had
        # expired, and nothing downstream read the registry. Two things keep that from
        # recurring, and both are asserted here because both are one edit from gone.
        guard = workflow['jobs']['release']['env']['NPM_PUBLISH']
        self.assertNotIn('secrets.', guard,
                         'gating the npm steps on a secret turns a lost credential into a green skip')
        assertion = steps[index('npm must actually carry')]
        self.assertEqual(assertion['if'], "env.NPM_PUBLISH == 'true'")
        # Not merely "the word `npm view` appears somewhere in the step" — the value that
        # is COMPARED has to come from the registry. Weakening the assignment to
        # PUBLISHED="${VER}" leaves a second `npm view` in the error branch, and a
        # substring check passes while the gate no longer checks anything.
        self.assertIn('PUBLISHED="$(npm view "medsci-skills@${VER}" version', assertion['run'],
                      'the compared value must come from the registry, not from the job itself')
        self.assertIn('exit 1', assertion['run'])

    def releases(self, *pages):
        # Stub `gh api [--paginate] .../releases --jq EXPR`: the step's own jq expression is applied
        # (with real jq, as gh would) to canned API pages, the second page only under --paginate.
        # Returns the env that points the step at it.
        self.stub('gh', 'expr=""; all=0\n'
                        'while [ $# -gt 0 ]; do case "$1" in --jq) expr="$2"; shift 2 ;; '
                        '--paginate) all=1; shift ;; *) shift ;; esac; done\n'
                        'printf "%s" "$STUB_REL_1" | jq -r "$expr"\n'
                        '[ "$all" = 1 ] && [ -n "${STUB_REL_2:-}" ] && printf "%s" "$STUB_REL_2" | jq -r "$expr"\n'
                        'exit 0\n')
        env = {'GITHUB_REPOSITORY': 'Synthetic/repo', 'STUB_REL_1': '[]', 'STUB_REL_2': ''}
        for i, page in enumerate(pages, 1):
            env[f'STUB_REL_{i}'] = json.dumps([{'tag_name': t, 'draft': d, 'prerelease': pre}
                                               for t, d, pre in page])
        return env

    def test_npm_propagation_wait_fails_when_the_version_never_appears(self):
        # npm publishes asynchronously ("may take a few minutes to become available"; 5 min 20 s
        # observed on 2026-09-24), so this step waits. The failure mode a string check cannot see
        # is a wait that gives up and calls it success - then a release that never reached the
        # registry goes green. Both branches are executed here against a stubbed `npm`.
        self.out.mkdir(exist_ok=True)
        stub = self.out / 'npm'
        stub.write_text('#!/bin/bash\n[ "$STUB_HAS_VERSION" = "1" ] && echo 9.9.9\nexit 0\n')
        stub.chmod(0o755)
        env = dict(PATH=str(self.out) + os.pathsep + os.environ['PATH'],
                   NPM_PROPAGATION_WINDOW='1', NPM_PROPAGATION_INTERVAL='0',
                   **self.releases([('v9.9.9', False, False)]))

        never = self.step('npm must actually carry', STUB_HAS_VERSION='0', **env)
        self.assertNotEqual(never.returncode, 0,
                            'a version that never reaches the registry must fail the release')
        self.assertIn('still does not carry', never.stdout + never.stderr)

        arrives = self.step('npm must actually carry', STUB_HAS_VERSION='1', **env)
        self.assertEqual(arrives.returncode, 0, arrives.stdout + arrives.stderr)
        self.assertIn('npm carries 9.9.9', arrives.stdout)

    def test_newest_release_must_be_npm_latest_but_an_older_recovery_need_not(self):
        # A recovery run finds the version already on npm and skips the publish; the old check
        # then asked only whether the version existed. With `latest` still on the previous release,
        # it went green while `npx medsci-skills@latest` kept installing the old one.
        path = self.stub('npm', 'case "$*" in *dist-tags.latest*) echo "$STUB_LATEST" ;; *) echo 9.9.9 ;; esac\n')
        env = dict(PATH=path, NPM_PROPAGATION_WINDOW='0', NPM_PROPAGATION_INTERVAL='0')
        run = lambda latest, *pages: self.step('npm must actually carry', STUB_LATEST=latest,
                                               **env, **self.releases(*pages))

        nothing = run('9.9.9')
        self.assertNotEqual(nothing.returncode, 0, 'unreadable releases must not skip the latest check')

        this = ('v9.9.9', False, False)
        stale = run('9.9.8', [this])
        self.assertNotEqual(stale.returncode, 0, 'the newest release with a stale latest must fail')
        self.assertIn('npm dist-tag add medsci-skills@9.9.9 latest', stale.stdout)
        current = run('9.9.9', [this])
        self.assertEqual(current.returncode, 0, current.stdout)
        self.assertIn('latest points to it', current.stdout)

        # Higher versions that are not published releases do not make this one old: a draft, a
        # prerelease, and a stray tag with no release at all (v99.0.0 on a commit that failed the
        # preflight). Before, the highest TAG decided, and the stray tag waived this very check.
        self.commit_and_tag('v99.0.0')
        unpublished = run('9.9.8', [this, ('v98.0.0', True, False), ('v97.0.0', False, True)])
        self.assertNotEqual(unpublished.returncode, 0, 'an unpublished higher version must not waive the check')
        self.assertIn('npm dist-tag add medsci-skills@9.9.9 latest', unpublished.stdout)

        # v9.10.0, a published release on the SECOND page of results, sorts after v9.9.9 as a
        # version (not as text), so v9.9.9 is an older release being recovered and `latest` stays.
        older = run('9.10.0', [this], [('v9.10.0', False, False)])
        self.assertEqual(older.returncode, 0, older.stdout)
        self.assertIn('older than v9.10.0', older.stdout)
        self.assertIn('left alone', older.stdout)

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
