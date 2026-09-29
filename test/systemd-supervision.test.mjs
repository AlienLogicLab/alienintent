import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import * as module from '../src/runtime/systemd-supervision.mjs';
const config = { mode: 'systemd', runtimeMilliseconds: 12000, stopGraceMilliseconds: 1000, startupMilliseconds: 2000, systemdRun: '/bin/systemd-run', systemctl: '/bin/systemctl', env: '/usr/bin/env' };
function fixture(initialManagerId = 'a'.repeat(32)) {
  assert.equal(typeof module.createSystemdSupervisor, 'function', 'bounded ownership adapter must exist');
  const calls = [], effects = [], client = new EventEmitter(); client.pid = 123;
  let retainedFailure = false;
  let unit = null, populated = false, managerId = initialManagerId;
  const root = '/user.slice/user-1000.slice/user@1000.service';
  const readFile = path => {
    if (path.endsWith('/boot_id')) return 'boot-id';
    if (path.endsWith('/cgroup.controllers')) return 'cpu memory';
    if (path.endsWith('/cgroup.events')) return `populated ${populated ? 1 : 0}\nfrozen 0\n`;
    throw new Error(`unexpected file ${path}`);
  };
  const transport = (command, args) => {
    calls.push({ command, args });
    if (args.includes('show')) {
      if (!args.includes('--')) return { UserspaceTimestampMonotonic: managerId === 'c'.repeat(32) ? '200' : '100', ControlGroup: root };
      if (args.at(-1) === 'init.scope') return { Id: 'init.scope', InvocationID: managerId, ControlGroup: `${root}/init.scope`, LoadState: 'loaded' };
      return unit ?? { LoadState: 'not-found' };
    }
    if (args.includes('reset-failed')) { effects.push('reset-failed'); unit = null; return {}; }
    if (args.includes('kill')) { effects.push('kill'); return {}; }
    if (args.includes('stop')) { effects.push('stop'); if (!retainedFailure) unit = null; populated = false; return {}; }
    throw new Error('unexpected command');
  };
  const adapter = module.createSystemdSupervisor(config, { transport, readFile, uid: () => 1000, spawn: (command, args, options) => { calls.push({ command, args, options }); effects.push('launch'); return client; } });
  const request = { invocationId: 'org/repo#1:PRODUCER:id', resource: { path: '/tmp/work $ with spaces', invocationId: 'org/repo#1:PRODUCER:id' } };
  const owner = adapter.plan(request);
  const running = () => { populated = true; unit = { Id: owner.unit, Description: owner.binding, InvocationID: 'b'.repeat(32), ControlGroup: owner.cgroup, LoadState: 'loaded', ActiveState: 'active', SubState: 'running', Type: 'exec', ExitType: 'cgroup', Restart: 'no', KillMode: 'control-group', SendSIGKILL: 'yes', RemainAfterExit: 'yes', RuntimeMaxUSec: '12s', TimeoutStartUSec: '2s', TimeoutStopUSec: '1s', RuntimeRandomizedExtraUSec: '0', ExecMainCode: '1', ExecMainStatus: '0', Result: 'success' }; };
  return { adapter, owner, request, calls, effects, client, running, get unit() { return unit; }, set unit(v) { unit = v; }, set populated(v) { populated = v; }, set managerId(v) { managerId = v; }, set retainedFailure(v) { retainedFailure = v; } };
}
test('unit planning is deterministic and bound to immutable invocation and path', () => {
  const f = fixture();
  assert.deepEqual(f.adapter.plan(f.request), f.owner);
  assert.notEqual(f.adapter.plan({ ...f.request, invocationId: f.request.invocationId + '2' }).unit, f.owner.unit);
  assert.equal(f.effects.length, 0);
});
test('bounded launch preserves literal argv and sanitized environment and applies hard properties', () => {
  const f = fixture();
  f.adapter.launch(f.owner, '/provider', ['$HOME', 'quote" with spaces', '%n'], { cwd: f.request.resource.path, env: { HOME: '/auth $ "', PATH: '/safe', LANG: 'C' } }, '/tmp/log % $');
  const launch = f.calls.at(-1);
  assert.ok(launch.args.includes('--expand-environment=no'));
  assert.ok(launch.args.includes('--property=ExitType=cgroup'));
  assert.ok(launch.args.includes('--property=RuntimeMaxSec=12000ms'));
  assert.ok(launch.args.includes('--property=TimeoutStopSec=1000ms'));
  assert.ok(launch.args.includes('--property=TimeoutStartSec=2000ms'));
  assert.deepEqual(launch.args.slice(launch.args.indexOf('/usr/bin/env')), ['/usr/bin/env', '-i', 'HOME=/auth $ "', 'PATH=/safe', 'LANG=C', '/provider', '$HOME', 'quote" with spaces', '%n']);
  assert.equal(launch.options.env.GH_TOKEN, undefined);
});
test('collision or unavailable manager refuses launch without direct fallback', () => {
  const f = fixture(); f.running();
  assert.throws(() => f.adapter.launch(f.owner, '/provider', [], { env: {}, cwd: '/tmp' }, '/tmp/log'), /COLLISION/);
  assert.equal(f.effects.length, 0);
  f.managerId = 'c'.repeat(32);
  assert.throws(() => f.adapter.observe(f.owner, () => {}), /MANAGER/);
});
test('client death and exited leader never release a populated cgroup', () => {
  const f = fixture(); f.running();
  const saved = [];
  f.client.emit('close', 0); f.unit.ExecMainStatus = '0';
  assert.equal(f.adapter.observe(f.owner, x => saved.push(x)).terminal, false);
  f.unit.SubState = 'exited';
  assert.equal(f.adapter.observe(f.owner, x => saved.push(x)).terminal, false);
  assert.deepEqual(f.effects, []);
});
test('terminal receipt and stop intent precede owned stop and survive metadata collection', () => {
  const f = fixture(); f.running(); f.unit.SubState = 'exited'; f.populated = false;
  const saved = []; let persisted = f.owner;
  const outcome = f.adapter.observe(persisted, next => { saved.push(structuredClone(next)); persisted = next; f.effects.push('persist'); });
  assert.equal(outcome.terminal, true);
  assert.ok(saved.find(x => x.terminalReceipt?.invocationId === f.request.invocationId && x.stopIntent));
  assert.ok(f.effects.indexOf('persist') < f.effects.indexOf('stop'));
  assert.equal(persisted.stopConfirmed, true);
  assert.equal(f.adapter.observe(persisted, () => {}).terminal, true);
});
test('missing unit without receipt, wrong identity and reused manager invocation hold', () => {
  const f = fixture();
  assert.throws(() => f.adapter.observe(f.owner, () => {}), /MISSING/);
  f.running(); f.unit.Description = 'other';
  assert.throws(() => f.adapter.observe(f.owner, () => {}), /OWNERSHIP/);
  f.running();
  let saved = f.owner;
  f.adapter.observe(saved, x => { saved = x; });
  f.unit.InvocationID = 'd'.repeat(32);
  assert.throws(() => f.adapter.observe(saved, () => {}), /OWNERSHIP/);
});
test('cancellation targets only a matching unit and holds until its cgroup is empty', () => {
  const f = fixture(); f.running();
  assert.equal(typeof f.adapter.cancel, 'function');
  const saved = [];
  f.adapter.cancel(f.owner, owner => saved.push(owner));
  assert.equal(saved.at(-1).cancellationIntent, true);
  assert.deepEqual(f.calls.at(-1).args, ['--user', 'kill', '--signal=SIGKILL', '--kill-whom=all', '--', f.owner.unit]);
  assert.equal(f.adapter.observe(saved.at(-1), () => {}).terminal, false);
  f.unit.Description = 'unrelated';
  assert.throws(() => f.adapter.cancel(f.owner, () => {}), /OWNERSHIP/);
});

test('real init.scope has no InvocationID; manager startup identity remains mandatory', () => {
  const f = fixture('');
  assert.equal(f.owner.manager.startedAtMonotonic, '100');
});

test('timeout metadata is captured before clearing only the owned failed unit', () => {
  const f = fixture(); f.running(); f.unit.ActiveState = 'failed'; f.unit.SubState = 'failed'; f.unit.Result = 'timeout'; f.populated = false; f.retainedFailure = true;
  let saved;
  assert.equal(f.adapter.observe(f.owner, x => { saved = x; }).terminal, true);
  assert.equal(saved.terminalReceipt.result, 'timeout');
  assert.deepEqual(f.effects, ['stop', 'reset-failed']);
});

test('persisted manager key order cannot refuse the same manager or accept a changed one', () => {
  const f = fixture();
  const reordered = { ...f.owner, manager: Object.fromEntries(Object.entries(f.owner.manager).reverse()) };
  assert.notEqual(JSON.stringify(reordered.manager), JSON.stringify(f.owner.manager));
  f.adapter.launch(reordered, '/provider', [], { env: {}, cwd: '/tmp' }, '/tmp/log');
  assert.deepEqual(f.effects, ['launch']);
  for (const key of ['uid', 'bootId', 'startedAtMonotonic', 'cgroup']) {
    const changed = { ...reordered, manager: { ...reordered.manager, [key]: key === 'uid' ? 1001 : 'changed' } };
    assert.throws(() => f.adapter.launch(changed, '/provider', [], { env: {}, cwd: '/tmp' }, '/tmp/log'), /SUPERVISION_MANAGER_CHANGED/);
    const missing = { ...reordered.manager }; delete missing[key];
    assert.throws(() => f.adapter.launch({ ...reordered, manager: missing }, '/provider', [], { env: {}, cwd: '/tmp' }, '/tmp/log'), /SUPERVISION_MANAGER_CHANGED/);
  }
  assert.deepEqual(f.effects, ['launch']);
});

test('pre-spawn absence proof refuses changed resource identity, a unit, or a populated cgroup', () => {
  const f = fixture();
  assert.equal(f.adapter.absent(f.owner, f.request.resource.path), true);
  assert.equal(f.adapter.absent({ ...f.owner, unit: 'alienintent-other.service' }, f.request.resource.path), false);
  assert.equal(f.adapter.absent(f.owner, '/tmp/other-worktree'), false);
  f.running();
  assert.equal(f.adapter.absent(f.owner, f.request.resource.path), false);
  f.unit = null; f.populated = true;
  assert.equal(f.adapter.absent(f.owner, f.request.resource.path), false);
  f.populated = false; f.managerId = 'c'.repeat(32);
  assert.throws(() => f.adapter.absent(f.owner, f.request.resource.path), /SUPERVISION_MANAGER_CHANGED/);
  assert.deepEqual(f.effects, []);
});
