import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { EventEmitter } from 'node:events';
import { EventRelay } from '../src/runtime/dispatcher.mjs';
import { GitHubAuthority, parseInvocationSignal } from '../src/github/authority.mjs';

// Synthetic persisted aliases exercise compatibility without private state.
const roleNames = { PRODUCER: 'MORTY', VERIFIER: 'JC' };
const workerLogins = { MORTY: 'producer-bot', JC: 'verifier-bot' };
const repository = 'ExampleOrg/sample-project';
const startedAt = '2030-01-01T00:00:00.800Z';
function fixture(t, status = 'IMPLEMENT', role = roleNames.PRODUCER) {
  const directory = mkdtempSync(join(tmpdir(), 'b-disp-legacy-'));
  const statePath = join(directory, 'state.json');
  const item = { repository, issue: 701, itemId: 'PVTI_synthetic', status };
  const lane = `${repository}#701:${role}`;
  const invocationId = `${lane}:synthetic-old-id`;
  const claim = { item, role, status, lane, invocationId, startedAt, pid: 12345 };
  const launches = [], transitions = [], comments = [];
  let current = status;
  const authority = new GitHubAuthority({ roleNames, workerLogins, repository, owner: 'ExampleOrg', projectNumber: 1, gh: () => JSON.stringify(comments) });
  authority.listItems = async () => [{ ...item, status: current }];
  authority.resolveItem = async item => item;
  authority.currentStatus = async () => current;
  authority.transition = async (_item, target) => { transitions.push(target); current = target; };
  authority.enrichContentNode = async () => item;
  const relay = new EventRelay({ statePath, repository, roleNames, workerLogins, authority,
    workers: { MORTY: {}, JC: {} }, isProcessAlive: () => true,
    setTimeout: () => ({ unref() {} }), clearTimeout() {}, preflight: async () => ({ ok: true }),
    launch: request => { launches.push(request); const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter(); child.exitCode = null; child.pid = 45678; return child; },
  });
  const historical = { deliveries: { old: { state: 'PROCESSED', at: startedAt }, unfinished: { state: 'PROCESSING', at: startedAt } },
    active: { [lane]: claim }, diagnostics: { 'unrelated:JC': { invocationId: 'unchanged:JC:diagnostic', role: 'JC', outcome: 'DURABLE_RESULT_MISSING' } },
    closures: { 'unchanged:MORTY:closure': { role: 'MORTY', invocationId: 'unchanged:MORTY:closure', result: 'DONE' } },
    founderExceptions: { 'unchanged:JC:exception': { role: 'JC', invocationId: 'unchanged:JC:exception', outcome: 'FOUNDER_EXCEPTION' } } };
  writeFileSync(statePath, JSON.stringify(historical));
  t.after(() => { relay.stop(); rmSync(directory, { recursive: true, force: true }); });
  return { relay, statePath, item, lane, claim, historical, launches, transitions, comments };
}
function resultEvent(claim, result, login = workerLogins[claim.role]) {
  return { headers: { 'x-github-event': 'issue_comment', 'x-github-delivery': 'synthetic-new-delivery' },
    payload: { action: 'created', repository: { full_name: repository }, issue: { number: 701 },
      comment: { created_at: '2030-01-01T00:00:00Z', user: { login }, body: `<!-- B-DISP: INVOCATION=${claim.invocationId} RESULT=${result} -->` } } };
}

test('legacy surviving lanes and all historical collections remain byte-for-byte unchanged on startup', async t => {
  for (const [status, role] of [['IMPLEMENT', 'MORTY'], ['VERIFY', 'JC']]) {
    const f = fixture(t, status, role); const before = readFileSync(f.statePath, 'utf8');
    await f.relay.startupReconcile();
    assert.equal(readFileSync(f.statePath, 'utf8'), before);
    assert.deepEqual(f.launches, []); assert.deepEqual(Object.keys(f.relay.state().active), [f.lane]);
  }
});

test('legacy optional claim fields may be missing without normalization or duplicate admission', async t => {
  const f = fixture(t); const state = { deliveries: {}, active: { [f.lane]: { invocationId: f.claim.invocationId, startedAt, pid: 12345 } } };
  writeFileSync(f.statePath, JSON.stringify(state)); const before = readFileSync(f.statePath, 'utf8');
  await f.relay.startupReconcile();
  assert.equal(readFileSync(f.statePath, 'utf8'), before); assert.deepEqual(f.launches, []);
});

for (const [role, status, result, target] of [['MORTY', 'IMPLEMENT', 'VERIFY', 'VERIFY'], ['JC', 'VERIFY', 'ACCEPT', 'ACCEPT']]) {
  test(`legacy ${role} exact marker routes while retaining lane, role, invocation and historical records`, async t => {
    const f = fixture(t, status, role);
    const marker = resultEvent(f.claim, result).payload.comment.body;
    assert.equal(parseInvocationSignal(marker, f.claim, roleNames), result);
    assert.equal(parseInvocationSignal(marker.replace('synthetic-old-id', 'wrong-id'), f.claim, roleNames), null);
    f.comments.push({ body: marker, created_at: '2030-01-01T00:00:00Z', user: { login: workerLogins[role] } });
    assert.equal(f.relay.options.authority.durableResult(f.claim), result);
    await f.relay.acceptEvent(resultEvent(f.claim, result));
    const state = f.relay.state();
    assert.deepEqual(f.transitions, [target]); assert.deepEqual(f.launches, []);
    assert.deepEqual(Object.keys(state.active), [f.lane]);
    assert.equal(state.active[f.lane].role, role); assert.equal(state.active[f.lane].invocationId, f.claim.invocationId);
    assert.equal(state.diagnostics[f.lane].invocationId, f.claim.invocationId);
    for (const key of ['closures', 'founderExceptions']) assert.deepEqual(state[key], f.historical[key]);
    assert.deepEqual(state.deliveries.old, f.historical.deliveries.old);
    assert.deepEqual(state.deliveries.unfinished, f.historical.deliveries.unfinished);
  });
}

test('legacy pending closure signal recovers DONE using the same exact invocation and lane', async t => {
  const f = fixture(t, 'ACCEPT');
  f.historical.active[f.lane].pendingSignal = { value: 'DONE', target: 'DONE' };
  writeFileSync(f.statePath, JSON.stringify(f.historical));
  await f.relay.startupReconcile();
  const state = f.relay.state();
  assert.deepEqual(f.transitions, ['DONE']); assert.deepEqual(f.launches, []);
  assert.deepEqual(Object.keys(state.active), [f.lane]);
  assert.equal(state.closures[f.claim.invocationId].role, 'MORTY');
  assert.equal(state.closures[f.claim.invocationId].invocationId, f.claim.invocationId);
  assert.equal(state.closures[f.claim.invocationId].result, 'DONE');
  assert.deepEqual(state.closures['unchanged:MORTY:closure'], f.historical.closures['unchanged:MORTY:closure']);
});

test('legacy exception blocks ordinary re-admission and preserves optional historical exception fields', async t => {
  const f = fixture(t, 'ACCEPT');
  f.historical.active = {};
  f.historical.diagnostics[f.lane] = { ...f.claim, outcome: 'FOUNDER_EXCEPTION', result: 'FOUNDER_EXCEPTION' };
  writeFileSync(f.statePath, JSON.stringify(f.historical));
  await f.relay.startupReconcile();
  assert.deepEqual(f.launches, []); assert.deepEqual(f.transitions, []);
  assert.deepEqual(f.relay.state(), f.historical);
  assert.equal(f.relay.events.at(-1).outcome, 'FOUNDER_EXCEPTION');
});

test('legacy fresh admission uses configured alias in lane, marker and closure bootstrap', async t => {
  const f = fixture(t, 'ACCEPT'); f.historical.active = {};
  writeFileSync(f.statePath, JSON.stringify(f.historical));
  await f.relay.startupReconcile();
  assert.equal(f.launches.length, 1); const request = f.launches[0];
  assert.equal(request.role, 'MORTY'); assert.ok(request.invocationId.startsWith(`${f.lane}:`));
  assert.ok(request.bootstrap.includes(`INVOCATION=${request.invocationId} RESULT=DONE`));
  assert.ok(request.bootstrap.includes('no additional VERIFIER review'));
  assert.deepEqual(Object.keys(f.relay.state().active), [f.lane]);
});


test('display names change presentation only, preserving legacy lanes and exact protocol markers', async t => {
  const f = fixture(t, 'ACCEPT'); f.historical.active = {};
  f.relay.options.workerDisplayNames = { MORTY: 'Build specialist', JC: 'Independent reviewer' };
  writeFileSync(f.statePath, JSON.stringify(f.historical));
  await f.relay.startupReconcile();
  const request = f.launches[0];
  assert.equal(request.role, 'MORTY');
  assert.deepEqual(Object.keys(f.relay.state().active), [f.lane]);
  assert.ok(request.invocationId.startsWith(`${f.lane}:`));
  assert.ok(request.bootstrap.includes('Worker: Build specialist.'));
  assert.ok(request.bootstrap.includes('no additional Independent reviewer review'));
  assert.ok(request.bootstrap.includes(`<!-- B-DISP: INVOCATION=${request.invocationId} RESULT=DONE -->`));
  assert.ok(request.bootstrap.includes(`<!-- B-DISP: INVOCATION=${request.invocationId} CONTROL=RETURN_TO_IMPLEMENT -->`));
  assert.ok(!request.bootstrap.includes('RESULT=VERIFY'));
});

test('new admission preserves the configured author in active, diagnostic and closure records', async t => {
  const f = fixture(t, 'ACCEPT'); f.historical.active = {};
  writeFileSync(f.statePath, JSON.stringify(f.historical));
  await f.relay.startupReconcile();
  const claim = f.relay.state().active[f.lane];
  assert.equal(claim.workerLogin, 'producer-bot');
  await f.relay.acceptEvent(resultEvent(claim, 'DONE'));
  const state = f.relay.state();
  assert.equal(state.active[f.lane].workerLogin, 'producer-bot');
  assert.equal(state.diagnostics[f.lane].workerLogin, 'producer-bot');
  assert.equal(state.closures[claim.invocationId].workerLogin, 'producer-bot');
});

for (const mode of ['unknown-role', 'changed-identity']) {
  test(`configuration handoff ${mode} blocks startup and direct admission without changing state`, async t => {
    const f = fixture(t);
    if (mode === 'unknown-role') {
      f.relay.roleNames = { PRODUCER: 'PRODUCER', VERIFIER: 'VERIFIER' };
      f.relay.roles = { IMPLEMENT: 'PRODUCER', VERIFY: 'VERIFIER', ACCEPT: 'PRODUCER' };
    } else {
      f.historical.active[f.lane].workerLogin = 'previous-producer';
      writeFileSync(f.statePath, JSON.stringify(f.historical));
    }
    const before = readFileSync(f.statePath, 'utf8');
    await assert.rejects(f.relay.startupReconcile(), /CONFIGURATION_MISMATCH/);
    await assert.rejects(f.relay.acceptEvent(resultEvent(f.claim, "VERIFY")), /CONFIGURATION_MISMATCH/);
    await assert.rejects(f.relay.start(f.item, f.relay.roleNames.PRODUCER, 'IMPLEMENT'), /CONFIGURATION_MISMATCH/);
    assert.equal(readFileSync(f.statePath, 'utf8'), before);
    assert.deepEqual(f.launches, []); assert.deepEqual(f.transitions, []);
  });
}
