import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, existsSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createWorktreeManager } from '../src/runtime/worktree-manager.mjs';

const git = (cwd, ...args) => execFileSync('git', ['-C', cwd, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
function fixture(t) {
  const dir = mkdtempSync(join(tmpdir(), 'b-disp-worktrees-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const repositoryStore = join(dir, 'store'); mkdirSync(repositoryStore);
  git(repositoryStore, 'init', '-b', 'main');
  git(repositoryStore, 'config', 'user.name', 'Canonical'); git(repositoryStore, 'config', 'user.email', 'canonical@example.test');
  writeFileSync(join(repositoryStore, '.gitignore'), 'ignored\n');
  git(repositoryStore, 'add', '.'); git(repositoryStore, 'commit', '-m', 'baseline');
  git(repositoryStore, 'remote', 'add', 'origin', 'https://github.com/Example/repo.git');
  git(repositoryStore, 'update-ref', 'refs/remotes/origin/main', 'HEAD');
  const options = { repository: 'Example/repo', repositoryStore, worktreeRoot: join(dir, 'workers'), baselineRef: 'origin/main' };
  const manager = createWorktreeManager(options);
  const plan = (id = 'invocation-1', role = 'PRODUCER') => manager.plan({ invocationId: id, item: { issue: 7, repository: options.repository }, role });
  const worker = { gitName: 'Producer', gitEmail: 'producer@example.test' };
  return { dir, options, manager, plan, worker, repositoryStore };
}

test('allocations are unique, pinned, track origin and isolate identity', t => {
  const f = fixture(t); const a = f.plan(); const b = f.plan('invocation-2', 'VERIFIER');
  assert.notEqual(a.path, b.path); assert.equal(a.lifecycle, 'ALLOCATING');
  const ready = f.manager.allocate(a, f.worker);
  f.manager.allocate(b, { gitName: 'Verifier', gitEmail: 'verifier@example.test' });
  assert.equal(ready.lifecycle, 'READY'); assert.equal(git(a.path, 'rev-parse', 'HEAD'), a.baselineCommit);
  assert.equal(git(a.path, 'rev-parse', '--abbrev-ref', '@{upstream}'), 'origin/main');
  assert.equal(git(a.path, 'config', 'user.name'), 'Producer');
  assert.equal(git(b.path, 'config', 'user.name'), 'Verifier');
  assert.equal(git(f.repositoryStore, 'config', 'user.name'), 'Canonical');
});
test('cleanup is idempotent and retains branch and another invocation', t => {
  const f = fixture(t); const a = f.manager.allocate(f.plan(), f.worker); const b = f.manager.allocate(f.plan('two'), f.worker);
  assert.equal(f.manager.cleanup(a).lifecycle, 'REMOVED'); assert.equal(f.manager.cleanup(a).lifecycle, 'REMOVED');
  assert.equal(existsSync(a.path), false); assert.equal(existsSync(b.path), true);
  assert.ok(git(f.repositoryStore, 'rev-parse', '--verify', a.branch));
});
test('path escapes, canonical path, collisions and cross-owner cleanup fail closed', t => {
  const f = fixture(t); const a = f.plan();
  assert.throws(() => f.manager.allocate({ ...a, path: f.repositoryStore }, f.worker));
  assert.throws(() => f.manager.allocate({ ...a, path: join(f.dir, 'escape') }, f.worker));
  mkdirSync(a.path, { recursive: true }); assert.throws(() => f.manager.allocate(a, f.worker));
  rmSync(a.path, { recursive: true });
  const b = f.manager.allocate(f.plan('two'), f.worker);
  assert.throws(() => f.manager.cleanup({ ...b, invocationId: 'other' }));
  assert.throws(() => f.manager.cleanup({ ...a, path: b.path }));
  assert.equal(existsSync(b.path), true);
});
test('dirty and ignored worker material prevents cleanup', t => {
  const f = fixture(t); const a = f.manager.allocate(f.plan(), f.worker);
  writeFileSync(join(a.path, 'ignored'), 'evidence');
  assert.throws(() => f.manager.cleanup(a), /dirty/i); assert.equal(existsSync(a.path), true);
});
test('wrong repository, linked canonical store and symlink roots are rejected', t => {
  const f = fixture(t); const a = f.manager.allocate(f.plan(), f.worker);
  assert.throws(() => createWorktreeManager({ ...f.options, repository: 'Other/repo' }).plan({ invocationId: 'x', item: { issue: 7 }, role: 'PRODUCER' }));
  assert.throws(() => createWorktreeManager({ ...f.options, repositoryStore: a.path }));
  symlinkSync(f.options.worktreeRoot, join(f.dir, 'alias'));
  assert.throws(() => createWorktreeManager({ ...f.options, worktreeRoot: join(f.dir, 'alias') }));
});
test('bare canonical stores preserve canonical bare configuration and isolate linked identity', t => {
  const f = fixture(t); const bare = join(f.dir, 'bare.git');
  git(f.repositoryStore, 'clone', '--bare', f.repositoryStore, bare);
  git(bare, 'remote', 'set-url', 'origin', 'https://github.com/Example/repo.git');
  const manager = createWorktreeManager({ ...f.options, repositoryStore: bare, baselineRef: 'main' });
  const a = manager.allocate(manager.plan({ invocationId: 'bare-worker', item: { issue: 8 }, role: 'PRODUCER' }), f.worker);
  assert.equal(git(bare, 'rev-parse', '--is-bare-repository'), 'true');
  assert.equal(git(a.path, 'rev-parse', '--is-bare-repository'), 'false');
  assert.equal(git(a.path, 'config', 'user.name'), 'Producer');
  const b = manager.allocate(manager.plan({ invocationId: 'bare-verifier', item: { issue: 8 }, role: 'VERIFIER' }), { gitName: 'Verifier', gitEmail: 'verifier@example.test' });
  assert.equal(git(b.path, 'config', 'user.name'), 'Verifier');
  assert.equal(manager.cleanup(a).lifecycle, 'REMOVED');
});
test('cleanup survives restart and rejects replaced symlink and branch checkouts', t => {
  const f = fixture(t); const a = f.manager.allocate(f.plan(), f.worker);
  git(a.path, 'switch', '-c', 'worker-evidence');
  assert.throws(() => f.manager.cleanup(a), /branch mismatch/);
  git(a.path, 'switch', a.branch);
  const fresh = createWorktreeManager(f.options);
  assert.equal(fresh.cleanup(JSON.parse(JSON.stringify(a))).lifecycle, 'REMOVED');
  symlinkSync(f.repositoryStore, a.path);
  assert.throws(() => fresh.cleanup(a), /symlink/);
  assert.equal(existsSync(join(f.repositoryStore, '.git')), true);
});
test('baseline is pinned even if configured ref moves after planning', t => {
  const f = fixture(t); const a = f.plan();
  git(f.repositoryStore, 'commit', '--allow-empty', '-m', 'new baseline');
  git(f.repositoryStore, 'update-ref', 'refs/remotes/origin/main', 'HEAD');
  f.manager.allocate(a, f.worker);
  assert.equal(git(a.path, 'rev-parse', 'HEAD'), a.baselineCommit);
  assert.notEqual(git(f.repositoryStore, 'rev-parse', 'HEAD'), a.baselineCommit);
});
