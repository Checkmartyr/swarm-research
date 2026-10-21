#!/usr/bin/env node
'use strict';

const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const SKILL_NAME = 'swarm-research';
const CONTENT_PATHS = ['SKILL.md', 'agents', 'references', 'scripts'];

function usage() {
  return `Install the swarm-research Codex skill

Usage:
  npx -y @checkmartyr/swarm-research [--dry-run] [--force] [--dest <directory>]

Options:
  --dry-run       Show the target and files without writing anything
  --force         Replace an existing skill installation
  --dest <dir>    Install into this exact skill directory
  --help          Show this help

Default target: <CODEX_HOME>/skills/swarm-research, or ~/.codex/skills/swarm-research
`;
}

function parseArgs(args) {
  const options = { dryRun: false, force: false, dest: null, help: false };
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    if (arg === '--dry-run') options.dryRun = true;
    else if (arg === '--force') options.force = true;
    else if (arg === '--help' || arg === '-h') options.help = true;
    else if (arg === '--dest') {
      if (!args[i + 1] || args[i + 1].startsWith('--')) throw new Error('--dest requires a directory path');
      options.dest = args[++i];
    } else throw new Error(`Unknown option: ${arg}`);
  }
  return options;
}

function defaultTarget(env = process.env, home = os.homedir()) {
  const codexHome = env.CODEX_HOME || path.join(home, '.codex');
  return path.join(codexHome, 'skills', SKILL_NAME);
}

async function listFiles(root, relative = '') {
  const absolute = path.join(root, relative);
  const stat = await fs.stat(absolute);
  if (stat.isFile()) return [relative];
  const entries = await fs.readdir(absolute, { withFileTypes: true });
  const result = [];
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const child = path.join(relative, entry.name);
    if (entry.isDirectory()) result.push(...await listFiles(root, child));
    else if (entry.isFile()) result.push(child);
  }
  return result;
}

async function install({ target, dryRun = false, force = false, packageRoot = PACKAGE_ROOT }) {
  const resolvedTarget = path.resolve(target);
  const sourceFiles = [];
  for (const entry of CONTENT_PATHS) sourceFiles.push(...await listFiles(packageRoot, entry));

  let targetExists = false;
  try {
    await fs.access(resolvedTarget);
    targetExists = true;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  if (targetExists && !force) {
    throw new Error(`Target already exists: ${resolvedTarget}\nUse --force to replace it.`);
  }
  if (dryRun) return { target: resolvedTarget, files: sourceFiles, replaced: targetExists, dryRun: true };

  const parent = path.dirname(resolvedTarget);
  const suffix = `${process.pid}-${Date.now()}`;
  const stage = path.join(parent, `.${SKILL_NAME}.stage-${suffix}`);
  await fs.mkdir(parent, { recursive: true });
  try {
    await fs.mkdir(stage, { recursive: true });
    for (const relative of sourceFiles) {
      const destination = path.join(stage, relative);
      await fs.mkdir(path.dirname(destination), { recursive: true });
      await fs.copyFile(path.join(packageRoot, relative), destination);
    }
    await fs.mkdir(resolvedTarget, { recursive: true });
    await fs.cp(stage, resolvedTarget, { recursive: true, force: true });
    await fs.rm(stage, { recursive: true, force: true });
  } catch (error) {
    await fs.rm(stage, { recursive: true, force: true });
    throw error;
  }
  return { target: resolvedTarget, files: sourceFiles, replaced: targetExists, dryRun: false };
}

async function main(args = process.argv.slice(2)) {
  try {
    const options = parseArgs(args);
    if (options.help) {
      process.stdout.write(usage());
      return 0;
    }
    const target = options.dest ? path.resolve(options.dest) : defaultTarget();
    const result = await install({ target, dryRun: options.dryRun, force: options.force });
    const action = result.dryRun ? 'Dry run' : result.replaced ? 'Updated' : 'Installed';
    process.stdout.write(`${action} swarm-research at ${result.target}\n`);
    process.stdout.write(`${result.files.length} files ${result.dryRun ? 'would be copied' : 'copied'}.\n`);
    if (result.dryRun) process.stdout.write(result.files.map(file => `  ${file}`).join('\n') + '\n');
    return 0;
  } catch (error) {
    process.stderr.write(`swarm-research: ${error.message}\n`);
    return 1;
  }
}

module.exports = { CONTENT_PATHS, defaultTarget, install, main, parseArgs, usage };
if (require.main === module) main().then(code => { process.exitCode = code; });

