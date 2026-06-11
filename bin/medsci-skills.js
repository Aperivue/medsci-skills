#!/usr/bin/env node
/*
 * medsci-skills — terminal-friendly installer shortcut for the MedSci Skills suite.
 *
 * Zero-dependency Node shim. The actual install logic lives in the dependency-free
 * Python installer (installers/install.py); this CLI only wraps it and adds a light
 * `doctor` diagnostic. For deep environment diagnostics use the in-agent `setup-medsci`
 * skill — this `doctor` is intentionally a thin npm-level check, not a replacement.
 *
 * Canonical distribution stays the GitHub repo + Claude Code plugin marketplace;
 * this package is a convenience shortcut for terminal users.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const PKG_ROOT = path.resolve(__dirname, '..');
const INSTALLER = path.join(PKG_ROOT, 'installers', 'install.py');
const CATALOG = path.join(PKG_ROOT, 'metadata', 'skills_catalog.json');

function readPkg() {
  try {
    return JSON.parse(fs.readFileSync(path.join(PKG_ROOT, 'package.json'), 'utf8'));
  } catch (e) {
    return { name: 'medsci-skills', version: 'unknown' };
  }
}

function pythonCmd() {
  // Require a Python 3 interpreter — installers/install.py is Python 3 only.
  // 'python' is accepted only if it reports Python 3.x (some systems alias it to 2.7).
  for (const cmd of ['python3', 'python']) {
    const r = spawnSync(cmd, ['--version'], { encoding: 'utf8' });
    if (r.status === 0) {
      const out = (r.stdout || '') + (r.stderr || ''); // Py2 prints version to stderr
      if (/Python 3\./.test(out)) return cmd;
    }
  }
  return null;
}

function printHelp() {
  const pkg = readPkg();
  process.stdout.write(
`${pkg.name} v${pkg.version}
MedSci Skills — medical/scientific research skill suite for AI coding agents.

Usage:
  npx @aperivue/medsci-skills <command> [options]
  medsci-skills <command> [options]      (after a global install)

Commands:
  install [--target all|claude|codex|cursor] [--cursor-project <dir>] [--dry-run]
                       Copy the skills into your agent's skill folder.
                       Delegates to the dependency-free Python installer and
                       passes every flag through (including Cursor rule install).
  list                 List the bundled skills, grouped by category.
  doctor               Quick environment check (Node, Python, skill folders).
                       For a full check, run the in-agent 'setup-medsci' skill.
  --version, -v        Print the package version.
  --help, -h           Show this help.

Notes:
  - npm/npx is a terminal-friendly shortcut. The canonical install paths are the
    Claude Code plugin marketplace and the GitHub repo (see the project README).
  - 'install'/'doctor' require python3 on PATH (the installer is dependency-free).
`);
}

function cmdVersion() {
  process.stdout.write(readPkg().version + '\n');
}

function cmdList() {
  let catalog;
  try {
    catalog = JSON.parse(fs.readFileSync(CATALOG, 'utf8'));
  } catch (e) {
    process.stderr.write('Could not read the skills catalog (' + CATALOG + ').\n');
    return 1;
  }
  const skills = Array.isArray(catalog.skills) ? catalog.skills : [];
  const groups = new Map();
  for (const s of skills) {
    const label = s.category_label || s.category || 'Other';
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push(s.slug);
  }
  process.stdout.write(`MedSci Skills — ${skills.length} skills\n`);
  for (const [label, slugs] of groups) {
    process.stdout.write(`\n${label}\n  ${slugs.sort().join(', ')}\n`);
  }
  return 0;
}

function cmdDoctor() {
  const pkg = readPkg();
  const py = pythonCmd();
  const claudeDir = path.join(os.homedir(), '.claude', 'skills');
  const codexDir = path.join(os.homedir(), '.agents', 'skills');
  const lines = [];
  lines.push(`medsci-skills doctor — ${pkg.name} v${pkg.version}`);
  lines.push(`  node           : ${process.version}`);
  lines.push(`  python3        : ${py ? py + ' (found)' : 'NOT FOUND — needed for install'}`);
  lines.push(`  installer      : ${fs.existsSync(INSTALLER) ? 'present' : 'MISSING'}`);
  lines.push(`  ~/.claude/skills : ${fs.existsSync(claudeDir) ? 'exists' : 'not yet created'}`);
  lines.push(`  ~/.agents/skills : ${fs.existsSync(codexDir) ? 'exists' : 'not yet created'}`);
  lines.push('');
  lines.push('For a full environment check (Python, R, Git, Zotero, MCP servers),');
  lines.push("run the in-agent 'setup-medsci' skill after installing.");
  process.stdout.write(lines.join('\n') + '\n');
  return py ? 0 : 1;
}

function cmdInstall(rest) {
  const py = pythonCmd();
  if (!py) {
    process.stderr.write(
      'python3 was not found on your PATH.\n' +
      'The installer is a dependency-free Python script. Install Python 3, or use the\n' +
      'git / classroom / plugin-marketplace install paths described in the project README.\n');
    return 1;
  }
  if (!fs.existsSync(INSTALLER)) {
    process.stderr.write('Installer not found at ' + INSTALLER + '\n');
    return 1;
  }
  const r = spawnSync(py, [INSTALLER, ...rest], { stdio: 'inherit' });
  return r.status == null ? 1 : r.status;
}

function main(argv) {
  const args = argv.slice(2);
  if (args.length === 0 || args[0] === '--help' || args[0] === '-h' || args[0] === 'help') {
    printHelp();
    return 0;
  }
  if (args[0] === '--version' || args[0] === '-v' || args[0] === 'version') {
    cmdVersion();
    return 0;
  }
  switch (args[0]) {
    case 'list':
      return cmdList();
    case 'doctor':
      return cmdDoctor();
    case 'install':
      return cmdInstall(args.slice(1));
    default:
      process.stderr.write(`Unknown command: ${args[0]}\n\n`);
      printHelp();
      return 2;
  }
}

process.exit(main(process.argv));
