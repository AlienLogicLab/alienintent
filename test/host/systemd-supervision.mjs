// Explicit host proof only. Not part of scripts/check.mjs. No providers/network.
// Run: rtk proxy node test/host/systemd-supervision.mjs
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createSystemdSupervisor } from '../../src/runtime/systemd-supervision.mjs';
import { EventRelay } from '../../src/runtime/dispatcher.mjs';

const config = { mode: 'systemd', runtimeMilliseconds: 2500, stopGraceMilliseconds: 500, startupMilliseconds: 1000,
  systemdRun: '/usr/bin/systemd-run', systemctl: '/usr/bin/systemctl', env: '/usr/bin/env' };
const root = mkdtempSync(join(tmpdir(), 'alienintent-supervision-host-'));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const alive = pid => { try { process.kill(pid, 0); return true; } catch (error) { if (error.code === 'ESRCH') return false; throw error; } };
async function until(check, milliseconds = 8000) {
  const deadline = Date.now() + milliseconds;
  while (Date.now() < deadline) { if (await check()) return; await delay(25); }
  throw new Error('HOST_PROOF_DEADLINE_EXCEEDED');
}
const sentinel = spawn(process.execPath, ['-e', 'setInterval(()=>{},1000)'], { stdio: 'ignore' });
const receipts = [], clients = [];
try {
  for (const scenario of ['literal-success', 'blocked-loop-term-resistant', 'client-death-live-parent', 'client-death-orphan-setsid']) {
    const directory = join(root, scenario + ' %n $ space');
    // Test resources are deliberately synthetic; no repository worktree is used.
    const { mkdirSync } = await import('node:fs'); mkdirSync(directory);
    const marker = join(directory, 'started.json'), log = join(directory, 'worker.log');
    const code = scenario === 'literal-success'
      ? `require('fs').writeFileSync(${JSON.stringify(marker)},JSON.stringify({argv:process.argv.slice(1),env:process.env,cwd:process.cwd()}));`
      : scenario === 'client-death-orphan-setsid'
        ? `const c=require('child_process').spawn(process.execPath,['-e',${JSON.stringify(`process.on('SIGTERM',()=>{});require('fs').writeFileSync(${JSON.stringify(marker)},JSON.stringify({pid:process.pid,ppid:process.ppid}));setInterval(()=>{},1000);`)}],{detached:true,stdio:'ignore'});c.unref();`
        : `process.on('SIGTERM',()=>{});require('fs').writeFileSync(${JSON.stringify(marker)},JSON.stringify({pid:process.pid}));setInterval(()=>{},1000);`;
    let owner, launches = 0, removals = 0, child;
    let adapter = createSystemdSupervisor(config);
    const launch = request => {
      launches++;
      child = adapter.launch(request.resource.supervision, process.execPath, ['-e', code, '$HOME', 'quote" with spaces', '%n'], { cwd: directory, env: { HOME: '/synthetic auth $ "', PATH: '/usr/bin:/bin', LITERAL: 'value %n $HOME "' } }, log);
      clients.push(child); child.on('error', () => {});
      return child;
    };
    launch.plan = request => adapter.plan(request);
    launch.observe = (resource, persist) => adapter.observe(resource.supervision, persist);
    const item = { repository: 'synthetic/local', issue: 1, itemId: 'synthetic' };
    const options = { statePath: join(directory, 'state.json'), repository: item.repository,
      workerLogins: { PRODUCER: 'synthetic-worker' }, workers: { PRODUCER: { logDirectory: directory } },
      worktreeManager: { plan: ({ invocationId, role }) => ({ invocationId, role, repository: item.repository, issue: item.issue, path: directory, lifecycle: 'ALLOCATING' }), allocate: record => ({ ...record, lifecycle: 'READY' }), cleanup: record => { removals++; return { ...record, lifecycle: 'REMOVED' }; } },
      preflight: async () => ({ ok: true }), launch,
      authority: { listItems: async () => [{ ...item, status: 'IMPLEMENT' }], resolveItem: async x => x, currentStatus: async () => 'IMPLEMENT', durableResult: async () => null, transition: async () => { throw new Error('EXIT_MUST_NOT_TRANSITION'); } },
      inspectionIntervalMs: 1000, setTimeout: () => 1, clearTimeout() {}, isProcessAlive: () => false };
    let relay = new EventRelay(options);
    const startedAt = Date.now();
    await relay.start(item, 'PRODUCER', 'IMPLEMENT');
    const active = [...relay.active.values()][0];
    await until(() => existsSync(marker));
    owner = relay.state().resources[active.invocationId].supervision;
    if (scenario === 'literal-success') {
      const received = JSON.parse(readFileSync(marker, 'utf8'));
      assert.deepEqual(received.argv, ['$HOME', 'quote" with spaces', '%n']);
      assert.deepEqual(received.env, { HOME: '/synthetic auth $ "', PATH: '/usr/bin:/bin', LITERAL: 'value %n $HOME "' });
      assert.equal(received.cwd, directory);
    } else {
      if (scenario.startsWith('client-death')) {
        await until(() => { try { return !adapter.observe(owner, x => { owner = x; }).terminal; } catch { return false; } });
        if (alive(child.pid)) process.kill(child.pid, 'SIGKILL');
        await delay(50);
        await relay.complete(active);
        assert.equal(Object.keys(relay.state().active).length, 1);
        assert.equal(removals, 0);
        relay.stop();
        adapter = createSystemdSupervisor(config); // Recovery uses persisted ownership.
        relay = new EventRelay(options);
        await relay.startupReconcile();
        assert.equal(launches, 1); assert.equal(removals, 0);
      }
      // This blocks Node's dispatcher loop past runtime + stop grace. systemd is
      // the only mechanism able to terminate the TERM-resistant test processes.
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 4500);
      const pid = JSON.parse(readFileSync(marker, 'utf8')).pid;
      // Orphan zombies can await the host's reaper; a zombie cannot execute work.
      if (alive(pid)) assert.match(readFileSync(`/proc/${pid}/stat`, 'utf8'), /^\d+ \(.+\) Z /);
      assert.ok(alive(sentinel.pid), 'unrelated sentinel must survive');
    }
    await until(async () => {
      const resource = relay.state().resources[active.invocationId];
      try { return adapter.observe(resource.supervision, supervision => relay.updateResource(active.invocationId, { supervision })).terminal; } catch { return false; }
    });
    owner = relay.state().resources[active.invocationId].supervision;
    assert.ok(owner.terminalReceipt); assert.equal(owner.stopConfirmed, true);
    assert.ok(alive(sentinel.pid));
    receipts.push({ scenario, elapsedMilliseconds: Date.now() - startedAt, owner, launches, removals });
    relay.stop();
    writeFileSync(join(root, 'receipts.json'), JSON.stringify(receipts, null, 2));
    console.log(`PASS ${scenario}`);
  }
  console.log(`HOST_PROOF_PASS ${join(root, 'receipts.json')}`);
} catch (error) {
  console.error(`HOST_PROOF_BLOCKED_OR_FAILED ${error.message}; evidence=${root}`);
  // No broad cleanup: each created service has its independent runtime bound.
  // Unverified/mismatched units are deliberately retained for inspection.
  process.exitCode = 1;
} finally {
  for (const client of clients) { if (client.exitCode === null && client.signalCode === null) client.kill("SIGKILL"); client.stdout?.destroy(); client.stderr?.destroy(); client.unref(); }
  if (alive(sentinel.pid)) sentinel.kill('SIGKILL');
}
