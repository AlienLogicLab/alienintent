import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { lstatSync, readFileSync, readlinkSync } from 'node:fs';
import { join } from 'node:path';

const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
export function classifyRepositoryState(worktree, knownChanges = []) {
  const git = (args) => execFileSync('git', args, { cwd: worktree });
  const records = git(['status', '--porcelain=v1', '-z', '--untracked-files=all']).toString().split('\0').filter(Boolean);
  if (!Array.isArray(knownChanges)) return 'UNEXPLAINED';
  const seen = new Set();
  for (let i = 0; i < records.length; i++) {
    const status = records[i].slice(0, 2), path = records[i].slice(3);
    if (status.includes('U') || ['AA', 'DD'].includes(status)) return 'CONFLICTING';
    // Renames need provenance for both paths; hold them for explicit resolution.
    if (/[RC]/.test(status)) return 'UNEXPLAINED';
    const entries = knownChanges.filter((entry) => entry.path === path);
    if (entries.length !== 1) return 'UNEXPLAINED';
    const evidence = entries[0];
    if (evidence.status !== status || !evidence.reason?.trim() || !evidence.authority?.trim()) return 'UNEXPLAINED';
    seen.add(path);
    let digest;
    try {
      const file = join(worktree, path), stat = lstatSync(file);
      if (!stat.isFile() && !stat.isSymbolicLink()) return 'UNEXPLAINED';
      digest = hash(stat.isSymbolicLink() ? readlinkSync(file) : readFileSync(file));
    } catch (error) { if (error.code !== 'ENOENT') throw error; digest = null; }
    if (digest !== evidence.sha256) return 'UNEXPLAINED';
    if (status[0] !== ' ' && status !== '??') {
      const indexDigest = status[0] === 'D' ? null : hash(git(['show', `:${path}`]));
      if (indexDigest !== evidence.indexSha256) return 'UNEXPLAINED';
    }
  }
  if (knownChanges.some((entry) => !seen.has(entry.path))) return 'UNEXPLAINED';
  return records.length ? 'KNOWN_AUTHORIZED' : 'SYNCED';
}
