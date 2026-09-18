import assert from 'node:assert/strict';
import test from 'node:test';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, writeFileSync, rmSync, chmodSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { classifyRepositoryState } from '../src/config/repository-state.mjs';
const digest = (text) => createHash('sha256').update(text).digest('hex');
function fixture(t) {
  const dir = mkdtempSync(join(tmpdir(), 'b-disp-state-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const git = (...args) => execFileSync('git', args, { cwd: dir, stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim();
  git('init', '-q'); git('config', 'user.name', 'Synthetic'); git('config', 'user.email', 'synthetic@example.test');
  writeFileSync(join(dir, 'tracked'), 'baseline\n'); git('add', '.'); git('commit', '-qm', 'baseline');
  const evidence = (path, status, text) => ({ path, status, sha256: digest(text), reason: 'Bounded packet output', authority: 'reviewed-task-101' });
  return { dir, git, evidence };
}
test('known untracked packet passes; unexplained or altered packet fails', (t) => {
  const { dir, evidence } = fixture(t);
  writeFileSync(join(dir, 'packet.md'), 'authorized');
  const known = [evidence('packet.md', '??', 'authorized')];
  assert.equal(classifyRepositoryState(dir, known), 'KNOWN_AUTHORIZED');
  assert.equal(classifyRepositoryState(dir), 'UNEXPLAINED');
  writeFileSync(join(dir, 'packet.md'), 'different');
  assert.equal(classifyRepositoryState(dir, known), 'UNEXPLAINED');
});
test('tracked work requires exact content, status, authority and staged content evidence', (t) => {
  const { dir, git, evidence } = fixture(t);
  writeFileSync(join(dir, 'tracked'), 'authorized');
  assert.equal(classifyRepositoryState(dir, [evidence('tracked', ' M', 'authorized')]), 'KNOWN_AUTHORIZED');
  assert.equal(classifyRepositoryState(dir, [{ ...evidence('tracked', ' M', 'authorized'), authority: '' }]), 'UNEXPLAINED');
  git('add', 'tracked');
  const staged = evidence('tracked', 'M ', 'authorized');
  assert.equal(classifyRepositoryState(dir, [staged]), 'UNEXPLAINED');
  assert.equal(classifyRepositoryState(dir, [{ ...staged, indexSha256: digest('authorized') }]), 'KNOWN_AUTHORIZED');
  writeFileSync(join(dir, 'tracked'), 'later');
  assert.equal(classifyRepositoryState(dir, [{ ...evidence('tracked', 'MM', 'later'), indexSha256: digest('later') }]), 'UNEXPLAINED');
});
test('merge conflicts remain conflicting even with caller change evidence', (t) => {
  const { dir, git, evidence } = fixture(t);
  git('checkout', '-qb', 'other'); writeFileSync(join(dir, 'tracked'), 'other\n'); git('commit', '-qam', 'other');
  git('checkout', '-q', '-'); writeFileSync(join(dir, 'tracked'), 'main\n'); git('commit', '-qam', 'main');
  assert.throws(() => git('merge', 'other'));
  assert.equal(classifyRepositoryState(dir, [evidence('tracked', 'UU', 'anything')]), 'CONFLICTING');
});
test('preflight accepts reviewed packet alongside synchronized upstream and verified identity', (t) => {
  const { dir, git, evidence } = fixture(t);
  git('update-ref', 'refs/remotes/origin/main', 'HEAD');
  git('config', 'remote.origin.url', 'https://github.com/sample/widget.git');
  git('config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*');
  git('config', `branch.${git('branch', '--show-current')}.remote`, 'origin');
  git('config', `branch.${git('branch', '--show-current')}.merge`, 'refs/heads/main');
  const gh = join(dir, '.git', 'fake-gh');
  writeFileSync(gh, '#!/bin/sh\nprintf "synthetic-worker\\n"\n'); chmodSync(gh, 0o700);
  writeFileSync(join(dir, 'packet.md'), 'authorized');
  const worker = { worktree: dir, gitName: 'Synthetic', gitEmail: 'synthetic@example.test', githubLogin: 'synthetic-worker', ghConfigDir: join(dir, '.git'), executables: { githubCli: gh }, knownChanges: [evidence('packet.md', '??', 'authorized')] };
  const result = JSON.parse(execFileSync(process.execPath, [fileURLToPath(new URL('../scripts/worker-preflight', import.meta.url)), '--json'], { cwd: dir, input: JSON.stringify(worker), env: { PATH: process.env.PATH }, encoding: 'utf8' }));
  assert.equal(result.safe_to_start, true);
  assert.equal(result.classification, 'KNOWN_AUTHORIZED');
  assert.equal(result.github, 'VERIFIED');
});
test('worker GitHub shim removes ambient tokens and forces selected configuration', (t) => {
  const { dir } = fixture(t);
  const gh = join(dir, '.git', 'fake-gh');
  writeFileSync(gh, '#!/bin/sh\nprintf "%s|%s|%s|%s|%s|%s" "$GH_CONFIG_DIR" "${GH_TOKEN-unset}" "${GITHUB_TOKEN-unset}" "${GH_ENTERPRISE_TOKEN-unset}" "${GITHUB_ENTERPRISE_TOKEN-unset}" "$1"\n'); chmodSync(gh, 0o700);
  const result = execFileSync('bash', [fileURLToPath(new URL('../scripts/worker-gh', import.meta.url)), 'api'], { env: { PATH: process.env.PATH, B_DISP_GH_CONFIG_DIR: '/synthetic/role-auth', B_DISP_GH_EXECUTABLE: gh, GH_CONFIG_DIR: '/wrong', GH_TOKEN: 'ambient', GITHUB_TOKEN: 'ambient', GH_ENTERPRISE_TOKEN: 'ambient', GITHUB_ENTERPRISE_TOKEN: 'ambient' }, encoding: 'utf8' });
  assert.equal(result, '/synthetic/role-auth|unset|unset|unset|unset|api');
});
