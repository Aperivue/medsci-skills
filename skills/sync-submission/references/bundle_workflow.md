# Preserve sources while assembling a submission bundle

`sync_submission.py build` copies files byte for byte. It does not rewrite prose,
reformat third-party templates, render documents, or certify a submission. Use
the existing manuscript/figure/supplement renderers first, inspect their output,
then declare exactly which files belong in this journal package.

## From changed sources to final files

1. Preserve the previous submitted/frozen package. Work from canonical sources in
   a new revision directory. Do not run side-effecting checks against the only
   copy of a submitted package; use an isolated project copy for that audit.
2. Before rendering, record SHA-256 hashes of the manuscript, supplement sources,
   bibliography, tables, figures, configuration and any reference template actually
   used. Run the existing renderer and confirm those inputs did not change during
   the run. Record its command/version and the output in the bundle declaration.
3. Inspect the actual final DOCX/PDF, including tables, figures, equations, Unicode,
   captions, pagination, tracked changes and hidden metadata. A source-text check
   does not establish that those survived conversion. Keep review notes local.
4. Build using the declaration, run the existing preflight with explicit final
   file paths where discovery would select only one file, then audit again to
   connect its report to the bundle. Only freeze the chosen byte snapshot after
   the existing skill's submission review steps. Freeze is not approval.

```bash
python scripts/sync_submission.py build --project-root . --journal example \
  --bundle-spec bundle.json
python scripts/preflight_gate.py --project-root . --journal example \
  --docx submission/example/manuscript/final.docx
python scripts/sync_submission.py audit --project-root . --journal example
python scripts/sync_submission.py freeze --project-root . --journal example
```

Paths above are relative to this skill directory for the scripts and to the
chosen project root for the declaration's inputs. Use absolute script paths when
running from a research project. `--bundle-spec` itself is project-relative.

The declaration is an input to the existing build, not a second output ledger.
The canonical manuscript is always included as `manuscript/manuscript.md`.
Additional entries in `bundle.json` use schema version 1:

```json
{
  "schema_version": 1,
  "artifacts": [{
    "id": "final-word",
    "role": "manuscript_docx",
    "source": "build/final.docx",
    "target": "manuscript/final.docx",
    "derived_from": [{
      "path": "manuscript/manuscript.md",
      "sha256": "sha256:REPLACE_WITH_THE_HASH_OBSERVED_BEFORE_RENDERING"
    }],
    "transformation": {
      "kind": "rendered",
      "command": ["pandoc", "manuscript/manuscript.md", "-o", "build/final.docx"],
      "version": "RECORD_THE_RENDERER_VERSION"
    },
    "rights": {"status": "original"}
  }]
}
```

Repeat entries for the final PDF, supplement, cover letter, title page, tables,
figures and required notices. List every render dependency, not just the main
manuscript. Commands are recorded declarations; build never executes them. Do
not attach today's source hashes to an old output without actually rebuilding.
If a declared dependency changed, build stops and asks for the existing renderer
to be rerun. A declared link is not authenticated proof of how an output was made.

For a runnable example using only original synthetic text and a synthetic table:

```bash
python examples/build_synthetic_bundle.py --project-root /tmp/synthetic-submission
# Optional real PDF, using the installed render-pdf-doc skill and XeLaTeX:
python examples/build_synthetic_bundle.py --project-root /tmp/synthetic-submission-pdf --pdf
```

## Output contract and limits

- `.journal_meta.json` schema 2 records each file's source/output hashes, pinned
  render inputs, declared transformation and rights, plus explicit unassessed
  content/visual review. `artifact_manifest.json` retains its existing schema and
  other fields; its selected `submissions` entry carries the same artifacts.
- `qc/submission_sync_{journal}.json` schema 2 reports changed/missing source,
  output or dependency files and unregistered package files. A clean legacy
  manuscript-only audit does not claim full-package coverage. Exit 0 means no
  tracked drift, 1 means drift, and 2 means missing/invalid input.
- `preflight_gate_report.json` schema 2 lists executed/skipped/error checks and
  their invocation targets. Its byte binding covers the declared sources,
  dependencies and package present before and after the run, **not every input
  of every check**. `package_bytes_current` in sync audit means only that this
  binding still matches. Changes to an undeclared bibliography or external
  profile require rerunning the relevant checks even if that binding matches.
- Preflight's compatibility field `submission_safe` means no configured blocker
  or error. Read `coverage`, warnings and `readiness: not_assessed` as well. An
  exit-zero check may have its own partial-coverage limitations. No aggregated
  pass is propagated to an individual PDF's visual review or semantic fidelity.
- Missing reports remain `not_run`, legacy/unbound reports remain `unbound`, and
  changed bundles make recorded checks `stale` on every audit, including reruns.
- Build refuses frozen/submitted packages, edited outputs, undeclared files that
  would be lost, removed registered files, symlinks, hidden input/target paths,
  traversal, hard-link source aliases and overlapping/case-colliding targets.
  Use a new revision journal slug for a deliberately different package.
- Builds stage copies and roll back ordinary replacement failures. A cooperative
  project lock serializes build/freeze manifest mutations. This is not a filesystem
  transaction or protection against external concurrent editors or power loss.
  After an interrupted process, inspect its lock/staging directory before recovery.

## Reuse rights and fidelity

The default `rights.status` is `unknown`; nothing infers permission from download
success, a DOI, a journal logo, or an unchanged hash. `original` and `documented`
are user declarations, not legal determinations. For `documented`, provide
`source`, `license_or_permission`, `attribution`, and `changes`; retain permission
evidence locally and include required notices in the actual distributed files.
Do not put private permission correspondence or identifiers in a public example.

Keep an official source unmodified where required. If an adaptation is permitted,
retain the source/version and describe changes; do not label your adapted summary
as the official checklist. This repository's MIT license does not relicense
third-party templates or papers. Its index is `THIRD-PARTY-NOTICES.md`.

CC BY 4.0 requires attribution, a license link and an indication of changes.
CC BY-NC-ND 4.0 also restricts commercial use and distribution of adaptations;
its deed distinguishes a mere format change from an adaptation. Consult the
specific material's actual terms and intended use rather than treating every
file conversion as an adaptation or every open-access item as redistributable.
Sources: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and
[CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).
