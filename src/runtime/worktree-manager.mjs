import { randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, lstatSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';

const fail = message => { throw new Error(`AlienIntent worktree: ${message}`); };
const within = (root, path) => { const r = relative(root, path); return r !== '' && !r.startsWith(`..${sep}`) && r !== '..' && !isAbsolute(r); };
function safePath(path) {
  if (typeof path !== 'string' || !isAbsolute(path) || resolve(path) !== path) fail('invalid absolute path');
  for (let current = path; ; current = dirname(current)) {
    if (existsSync(current) || (() => { try { return lstatSync(current).isSymbolicLink(); } catch { return false; } })()) {
      if (lstatSync(current).isSymbolicLink()) fail('symlink path rejected');
    }
    if (dirname(current) === current) break;
  }
  return path;
}

// Ownership is resource metadata only. The dispatcher alone decides whether
// process/result/recovery handling permits calling cleanup.
export function createWorktreeManager({ repository, repositoryStore, worktreeRoot, baselineRef, git = 'git' }) {
  const run = (cwd, ...args) => execFileSync(git, ['-C', cwd, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], env: Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('GIT_'))) }).trim();
  safePath(repositoryStore); safePath(worktreeRoot);
  if (repositoryStore === worktreeRoot || within(worktreeRoot, repositoryStore) || within(repositoryStore, worktreeRoot)) fail('canonical store and worker root must be separate');
  if (typeof repository !== 'string' || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) fail('invalid repository');
  if (typeof baselineRef !== 'string' || !baselineRef || baselineRef.startsWith('-') || /[\s\0]/.test(baselineRef)) fail('invalid baseline ref');
  const commonDir = realpathSync(run(repositoryStore, 'rev-parse', '--path-format=absolute', '--git-common-dir'));
  if (realpathSync(run(repositoryStore, 'rev-parse', '--absolute-git-dir')) !== commonDir) fail('canonical store is a linked worker checkout');
  const ownershipRoot = join(commonDir, 'b-disp-ownership');
  function validateSource() {
    safePath(repositoryStore); safePath(worktreeRoot); safePath(commonDir); safePath(ownershipRoot);
    if (realpathSync(run(repositoryStore, 'rev-parse', '--path-format=absolute', '--git-common-dir')) !== commonDir) fail('canonical store changed');
    const origin = run(repositoryStore, 'remote', 'get-url', 'origin');
    if (![`https://github.com/${repository}`, `https://github.com/${repository}.git`, `git@github.com:${repository}.git`, `ssh://git@github.com/${repository}.git`].includes(origin)) fail('canonical origin does not match repository');
  }
  const ownerFields = ['resourceId', 'invocationId', 'repository', 'repositoryStore', 'issue', 'role', 'path', 'branch', 'baselineRef', 'baselineCommit', 'createdAt'];
  function validateRecord(record) {
    validateSource();
    if (!record || !/^[a-f0-9-]{36}$/.test(record.resourceId ?? '')) fail('invalid resource ownership');
    if (record.repository !== repository || record.repositoryStore !== repositoryStore || record.baselineRef !== baselineRef
        || record.path !== join(worktreeRoot, record.resourceId) || record.branch !== `b-disp/${record.resourceId}`
        || !/^[a-f0-9]{40,64}$/.test(record.baselineCommit ?? '') || !record.invocationId || !record.role
        || !Number.isSafeInteger(record.issue) || record.issue <= 0) fail('invalid resource ownership/path');
    safePath(record.path);
    return join(ownershipRoot, `${record.resourceId}.json`);
  }
  function checkOwner(record, marker) {
    safePath(marker);
    const owner = JSON.parse(readFileSync(marker, 'utf8'));
    if (ownerFields.some(field => record[field] !== owner[field])) fail('resource ownership mismatch');
  }
  validateSource();
  return {
    plan({ invocationId, item, role }) {
      validateSource();
      if (typeof invocationId !== 'string' || !invocationId || typeof role !== 'string' || !role || !Number.isSafeInteger(item?.issue) || item.issue <= 0
          || (item.repository && item.repository !== repository)) fail('invalid invocation');
      const resourceId = randomUUID();
      return { resourceId, invocationId, repository, repositoryStore, issue: item.issue, role, path: join(worktreeRoot, resourceId), branch: `b-disp/${resourceId}`,
        baselineRef, baselineCommit: run(repositoryStore, 'rev-parse', '--verify', '--end-of-options', `${baselineRef}^{commit}`), createdAt: new Date().toISOString(), lifecycle: 'ALLOCATING' };
    },
    allocate(record, worker) {
      const marker = validateRecord(record);
      if (record.lifecycle !== 'ALLOCATING' || existsSync(record.path) || existsSync(marker)) fail('allocation collision');
      if (!worker?.gitName || !worker?.gitEmail) fail('missing worker Git identity');
      mkdirSync(worktreeRoot, { recursive: true }); mkdirSync(ownershipRoot, { recursive: true, mode: 0o700 });
      writeFileSync(marker, JSON.stringify(record), { flag: 'wx', mode: 0o600 });
      // Worktree config isolates identities. Existing core.worktree settings
      // require installation repair rather than silently changing their meaning.
      let coreWorktree = ''; try { coreWorktree = run(repositoryStore, 'config', '--local', '--get', 'core.worktree'); } catch {}
      if (coreWorktree) fail('canonical core.worktree configuration unsupported');
      const bare = run(repositoryStore, 'rev-parse', '--is-bare-repository') === 'true';
      run(repositoryStore, 'config', 'extensions.worktreeConfig', 'true');
      if (bare) {
        run(repositoryStore, 'config', '--worktree', 'core.bare', 'true');
        try { run(repositoryStore, 'config', '--local', '--unset', 'core.bare'); }
        catch (error) { if (error.status !== 5) throw error; }
      }
      run(repositoryStore, 'worktree', 'add', '-b', record.branch, record.path, record.baselineCommit);
      run(record.path, 'config', '--worktree', 'user.name', worker.gitName);
      run(record.path, 'config', '--worktree', 'user.email', worker.gitEmail);
      const symbolic = run(repositoryStore, 'rev-parse', '--symbolic-full-name', baselineRef);
      if (symbolic.startsWith('refs/remotes/')) run(record.path, 'branch', '--set-upstream-to', baselineRef, record.branch);
      return { ...record, lifecycle: 'READY' };
    },
    cleanup(record) {
      const marker = validateRecord(record); checkOwner(record, marker);
      const entries = run(repositoryStore, 'worktree', 'list', '--porcelain', '-z').split('\0\0').filter(Boolean).map(entry => Object.fromEntries(entry.split('\0').filter(Boolean).map(line => { const at = line.indexOf(' '); return at < 0 ? [line, true] : [line.slice(0, at), line.slice(at + 1)]; })));
      const registered = entries.find(entry => entry.worktree === record.path);
      if (!existsSync(record.path)) {
        if (registered) fail('registered worktree missing; retain for diagnosis');
        return { ...record, lifecycle: 'REMOVED' };
      }
      if (!registered || registered.branch !== `refs/heads/${record.branch}` || registered.locked) fail('worktree registration/branch mismatch');
      if (realpathSync(run(record.path, 'rev-parse', '--path-format=absolute', '--git-common-dir')) !== commonDir) fail('worktree repository mismatch');
      if (run(record.path, 'status', '--porcelain=v1', '--untracked-files=all', '--ignored')) fail('dirty worktree retained');
      run(repositoryStore, 'worktree', 'remove', record.path);
      return { ...record, lifecycle: 'REMOVED' };
    },
  };
}
