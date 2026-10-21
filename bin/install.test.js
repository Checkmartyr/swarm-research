'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { test } = require('node:test');
const { defaultTarget, install, parseArgs } = require('./install');

test('default target respects CODEX_HOME and otherwise uses .codex', () => {
  assert.equal(defaultTarget({ CODEX_HOME: 'X:/codex' }, 'C:/Users/test'), path.join('X:/codex', 'skills', 'swarm-research'));
  assert.equal(defaultTarget({}, 'C:/Users/test'), path.join('C:/Users/test', '.codex', 'skills', 'swarm-research'));
});

test('argument parser handles supported options and rejects unknown options', () => {
  assert.deepEqual(parseArgs(['--dry-run', '--force', '--dest', 'C:/skills/swarm-research']), {
    dryRun: true, force: true, dest: 'C:/skills/swarm-research', help: false
  });
  assert.throws(() => parseArgs(['--mystery']), /Unknown option/);
  assert.throws(() => parseArgs(['--dest']), /requires a directory/);
});

test('dry run lists files without creating target', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'swarm-installer-'));
  try {
    const source = path.join(root, 'package');
    const target = path.join(root, 'destination');
    for (const dir of ['agents', 'references', 'scripts']) await fs.mkdir(path.join(source, dir), { recursive: true });
    await fs.writeFile(path.join(source, 'SKILL.md'), 'skill');
    await fs.writeFile(path.join(source, 'references', 'guide.md'), 'guide');
    const result = await install({ packageRoot: source, target, dryRun: true });
    assert.deepEqual(result.files, ['SKILL.md', path.join('references', 'guide.md')]);
    await assert.rejects(fs.access(target), { code: 'ENOENT' });
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
});

test('install refuses overwrite unless forced, and forced update preserves unrelated files', async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'swarm-installer-'));
  try {
    const source = path.join(root, 'package');
    const target = path.join(root, 'destination');
    for (const dir of ['agents', 'references', 'scripts']) await fs.mkdir(path.join(source, dir), { recursive: true });
    await fs.writeFile(path.join(source, 'SKILL.md'), 'new skill');
    await fs.writeFile(path.join(source, 'scripts', 'validate.py'), 'validator');
    await fs.mkdir(target);
    await fs.writeFile(path.join(target, 'old.txt'), 'stale');
    await assert.rejects(install({ packageRoot: source, target }), /Use --force/);
    const result = await install({ packageRoot: source, target, force: true });
    assert.equal(result.replaced, true);
    assert.equal(await fs.readFile(path.join(target, 'SKILL.md'), 'utf8'), 'new skill');
    assert.equal(await fs.readFile(path.join(target, 'old.txt'), 'utf8'), 'stale');
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
});

