import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { EventRelay } from '../src/runtime/dispatcher.mjs';

function fixture(t, overrides = {}) {
  const root = mkdtempSync(join(tmpdir(), 'b-disp-resource-'));
  const removed = [], launches = [], preflights = [], transitions = [];
  let serial = 0;
  const manager = {
    plan: ({ invocationId, item, role }) => ({ invocationId, repository: item.repository, issue: item.issue, role,
      path: join(root, `resource-${++serial}`), createdAt: new Date().toISOString(), lifecycle: 'ALLOCATING' }),
    allocate: record => ({ ...record, lifecycle: 'READY' }),
    cleanup: record => { removed.push(record.path); return { ...record, lifecycle: 'REMOVED' }; },
  };
  const relay = new EventRelay({ repository: 'ExampleOrg/sample-project', statePath: join(root, 'state.json'),
    workers: { PRODUCER: { logDirectory: root }, VERIFIER: { logDirectory: root } }, worktreeManager: manager,
    workerLogins: { PRODUCER: 'producer-bot', VERIFIER: 'verifier-bot' },
    authority: { resolveItem: async item => item, currentStatus: async () => 'IMPLEMENT', durableResult: async () => null,
      listItems: async () => [], transition: async (_item, target) => transitions.push(target) },
    preflight: async request => { preflights.push(request); return { ok: true }; },
    launch: request => { const child = new EventEmitter(); child.pid = 12000 + launches.length;
      child.stdout = new EventEmitter(); child.stderr = new EventEmitter(); child.exitCode = null;
      launches.push({ ...request, child }); return child; },
    setTimeout: () => 1, clearTimeout() {}, ...overrides,
  });
  t.after(() => relay.stop());
  const item = issue => ({ repository: 'ExampleOrg/sample-project', issue, itemId: `PVTI_${issue}` });
  return { root, relay, manager, removed, launches, preflights, transitions, item };
}

test('concurrent Issues and roles reserve distinct invocation paths before preflight and launch', async t => {
  const f = fixture(t);
  await Promise.all([f.relay.start(f.item(1), 'PRODUCER', 'IMPLEMENT'), f.relay.start(f.item(2), 'PRODUCER', 'IMPLEMENT'), f.relay.start(f.item(1), 'VERIFIER', 'VERIFY')]);
  assert.equal(new Set(f.launches.map(x => x.worktree)).size, 3);
  assert.equal(f.preflights.length, 3);
  for (const launched of f.launches) {
    const resource = f.relay.state().resources[launched.invocationId];
    assert.equal(resource.path, launched.worktree);
    assert.equal(resource.pid, launched.child.pid);
    assert.equal(resource.role, launched.role);
    assert.equal(f.preflights.find(x => x.invocationId === launched.invocationId).worktree, launched.worktree);
  }
});

test('allocator path collision fails before second preflight or launch', async t => {
  const f = fixture(t); const plan = f.manager.plan;
  f.manager.plan = request => ({ ...plan(request), path: join(f.root, 'same') });
  await f.relay.start(f.item(1), 'PRODUCER', 'IMPLEMENT');
  await assert.rejects(f.relay.start(f.item(2), 'PRODUCER', 'IMPLEMENT'), /WORKTREE.*COLLISION/);
  assert.equal(f.launches.length, 1); assert.equal(f.preflights.length, 1); assert.deepEqual(f.removed, []);
});

test('result while child lives retains resource, exit cleans only its own path and keeps logs', async t => {
  const f = fixture(t);
  await f.relay.start(f.item(1), 'PRODUCER', 'IMPLEMENT');
  await f.relay.start(f.item(2), 'PRODUCER', 'IMPLEMENT');
  const active = [...f.relay.active.values()][0];
  await f.relay.routeResult(active, 'VERIFY');
  assert.deepEqual(f.removed, []);
  active.closed = true; active.child.exitCode = 0;
  await f.relay.complete(active);
  assert.deepEqual(f.removed, [f.launches[0].worktree]);
  const resource = f.relay.state().resources[active.invocationId];
  assert.equal(resource.lifecycle, 'REMOVED'); assert.ok(resource.logPath);
  f.relay.reconcileResources(); assert.equal(f.removed.length, 1);
});

test('cleanup failure is a resource diagnostic, never a workflow rewrite', async t => {
  const f = fixture(t); f.manager.cleanup = () => { throw new Error('dirty checkout retained'); };
  await f.relay.start(f.item(1), 'PRODUCER', 'IMPLEMENT');
  const active = [...f.relay.active.values()][0];
  await f.relay.routeResult(active, 'VERIFY'); active.closed = true; active.child.exitCode = 0;
  await f.relay.complete(active);
  assert.deepEqual(f.transitions, ['VERIFY']);
  assert.equal(f.relay.state().diagnostics[active.lane].outcome, 'VERIFY_TO_VERIFY');
  assert.equal(f.relay.state().resources[active.invocationId].cleanupDiagnostic, 'dirty checkout retained');
});

test('failed durable-result read preserves exited worktree for recovery', async t => {
  const f = fixture(t);
  f.relay.options.authority.durableResult = async () => { throw new Error('read interrupted'); };
  await f.relay.start(f.item(1), 'PRODUCER', 'IMPLEMENT');
  const active = [...f.relay.active.values()][0]; active.closed = true; active.child.exitCode = 0;
  await f.relay.complete(active);
  assert.deepEqual(f.removed, []);
  assert.equal(f.relay.state().resources[active.invocationId].path, f.launches[0].worktree);
  assert.equal(f.relay.state().diagnostics[active.lane].outcome, 'COMPLETION_ERROR');
});

test('a crash in launch without a durable PID retains its allocation for diagnosis', async t => {
  const f = fixture(t, { launch: () => { throw new Error('launch outcome unknown'); } });
  await assert.rejects(f.relay.start(f.item(1), 'PRODUCER', 'IMPLEMENT'), /launch outcome unknown/);
  assert.deepEqual(f.removed, []);
  assert.equal(Object.values(f.relay.state().resources)[0].lifecycle, 'LAUNCHING');
  f.relay.reconcileResources(); assert.deepEqual(f.removed, []);
});

test('orphan recovery preserves plausible live and ambiguous launching resources, reclaims confirmed inactive', async t => {
  const f = fixture(t, { isProcessAlive: pid => pid === 555 });
  const records = ['dead', 'live', 'uncertain'].map((invocationId, index) => ({
    ...f.manager.plan({ invocationId, item: f.item(index + 1), role: 'PRODUCER' }),
    lifecycle: index === 2 ? 'LAUNCHING' : 'RUNNING', ...(index < 2 ? { pid: index === 0 ? 444 : 555 } : {}),
  }));
  f.relay.save({ deliveries: {}, active: {}, resources: Object.fromEntries(records.map(r => [r.invocationId, r])) });
  await f.relay.startupReconcile();
  assert.deepEqual(f.removed, [records[0].path]);
  assert.notEqual(f.relay.state().resources.live.lifecycle, 'REMOVED');
  assert.notEqual(f.relay.state().resources.uncertain.lifecycle, 'REMOVED');
});

test('preflight failure reclaims allocation without launching and retains ownership evidence', async t => {
  const f = fixture(t, { preflight: async () => ({ ok: false }) });
  await f.relay.start(f.item(1), 'PRODUCER', 'IMPLEMENT');
  assert.equal(f.launches.length, 0); assert.equal(f.removed.length, 1);
  assert.equal(Object.values(f.relay.state().resources)[0].lifecycle, 'REMOVED');
});
