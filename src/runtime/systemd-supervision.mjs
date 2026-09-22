import { execFileSync, spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const fields = ['Id', 'LoadState', 'Description', 'InvocationID', 'ControlGroup', 'ActiveState', 'SubState', 'Type', 'ExitType', 'Restart', 'KillMode', 'SendSIGKILL', 'RemainAfterExit', 'RuntimeMaxUSec', 'TimeoutStartUSec', 'TimeoutStopUSec', 'RuntimeRandomizedExtraUSec', 'ExecMainCode', 'ExecMainStatus', 'Result'];
const parse = text => Object.fromEntries(String(text).trim().split('\n').filter(line => line.includes('=')).map(line => [line.slice(0, line.indexOf('=')), line.slice(line.indexOf('=') + 1)]));
function milliseconds(text) {
  if (text === '0') return 0;
  let total = 0;
  const parts = String(text).trim().split(/\s+/);
  for (const part of parts) {
    const match = part.match(/^(\d+(?:\.\d+)?)(us|ms|s|min|h|d)$/);
    if (!match) return NaN;
    total += Number(match[1]) * { us: 0.001, ms: 1, s: 1000, min: 60000, h: 3600000, d: 86400000 }[match[2]];
  }
  return total;
}
// Only manager-connection variables enter the client. The service starts env -i,
// so neither manager defaults nor connection variables reach the provider.
function managerEnvironment(environment) {
  return Object.fromEntries(['HOME', 'USER', 'LOGNAME', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS'].filter(key => environment[key] !== undefined).map(key => [key, environment[key]]));
}
export function createSystemdSupervisor(config, dependencies = {}) {
  if (config?.mode !== 'systemd') throw new Error('SUPERVISION_CONFIGURATION_REQUIRED');
  for (const key of ['runtimeMilliseconds', 'stopGraceMilliseconds', 'startupMilliseconds']) if (!Number.isSafeInteger(config[key]) || config[key] <= 0 || config[key] > 2147483647) throw new Error('SUPERVISION_LIMIT_REQUIRED');
  for (const key of ['systemdRun', 'systemctl', 'env']) if (typeof config[key] !== 'string' || !config[key].startsWith('/') || config[key].includes('\0')) throw new Error('SUPERVISION_EXECUTABLE_REQUIRED');
  const readFile = dependencies.readFile ?? (path => readFileSync(path, 'utf8'));
  const env = managerEnvironment(dependencies.environment ?? process.env);
  const transport = dependencies.transport ?? ((command, args) => {
    try { return parse(execFileSync(command, args, { env, encoding: 'utf8', timeout: 5000, stdio: ['ignore', 'pipe', 'pipe'] })); }
    catch (error) {
      const value = parse(error.stdout ?? '');
      if (error.status === 1 && value.LoadState === 'not-found') return value;
      throw new Error('SUPERVISION_MANAGER_UNAVAILABLE');
    }
  });
  const show = unit => transport(config.systemctl, ['--user', 'show', '--no-pager', `--property=${fields.join(',')}`, '--', unit]);
  function manager() {
    readFile('/sys/fs/cgroup/cgroup.controllers');
    const identity = transport(config.systemctl, ['--user', 'show', '--no-pager', '--property=UserspaceTimestampMonotonic,ControlGroup']);
    if (!/^[1-9][0-9]*$/.test(identity.UserspaceTimestampMonotonic ?? '') || !/^\/user.slice\/user-[0-9]+.slice\/user@[0-9]+.service$/.test(identity.ControlGroup ?? '')) throw new Error('SUPERVISION_MANAGER_IDENTITY_REQUIRED');
    return { uid: (dependencies.uid ?? process.getuid)(), bootId: readFile('/proc/sys/kernel/random/boot_id').trim(), startedAtMonotonic: identity.UserspaceTimestampMonotonic, cgroup: identity.ControlGroup };
  }
  function verifyManager(owner) {
    if (JSON.stringify(manager()) !== JSON.stringify(owner.manager)) throw new Error('SUPERVISION_MANAGER_CHANGED');
  }
  function empty(owner) {
    try {
      const text = readFile(`/sys/fs/cgroup${owner.cgroup}/cgroup.events`);
      if (!/^populated [01]$/m.test(text)) throw new Error('SUPERVISION_CGROUP_UNAVAILABLE');
      return /^populated 0$/m.test(text);
    } catch (error) { if (error.code === 'ENOENT') return true; throw error; }
  }
  function owned(owner, unit) {
    if (unit.LoadState !== 'loaded' || unit.Id !== owner.unit || unit.Description !== owner.binding
        || !/^[a-f0-9]{32}$/.test(unit.InvocationID ?? '')
        || (owner.systemdInvocationId && unit.InvocationID !== owner.systemdInvocationId)
        || (unit.ControlGroup !== owner.cgroup && !(unit.ControlGroup === '' && ['exited', 'dead', 'failed'].includes(unit.SubState)))) throw new Error('SUPERVISION_OWNERSHIP_MISMATCH');
    const properties = { Type: 'exec', ExitType: 'cgroup', Restart: 'no', KillMode: 'control-group', SendSIGKILL: 'yes', RemainAfterExit: 'yes' };
    for (const [key, value] of Object.entries(properties)) if (unit[key] !== value) throw new Error('SUPERVISION_PROPERTIES_MISMATCH');
    for (const [key, value] of [['RuntimeMaxUSec', owner.limits.runtimeMilliseconds], ['TimeoutStartUSec', owner.limits.startupMilliseconds], ['TimeoutStopUSec', owner.limits.stopGraceMilliseconds], ['RuntimeRandomizedExtraUSec', 0]]) if (milliseconds(unit[key]) !== value) throw new Error('SUPERVISION_PROPERTIES_MISMATCH');
  }
  return {
    plan({ invocationId, resource }) {
      if (!invocationId || !resource?.path?.startsWith('/')) throw new Error('SUPERVISION_RESOURCE_REQUIRED');
      const identity = manager();
      const digest = createHash('sha256').update(JSON.stringify([invocationId, resource.path])).digest('hex');
      const unit = `alienintent-${digest}.service`;
      return { mode: 'systemd', invocationId, unit, binding: `AlienIntent invocation ${digest}`, manager: identity,
        cgroup: `${identity.cgroup}/app.slice/${unit}`, limits: { runtimeMilliseconds: config.runtimeMilliseconds, startupMilliseconds: config.startupMilliseconds, stopGraceMilliseconds: config.stopGraceMilliseconds } };
    },
    launch(owner, command, args, options, logPath) {
      verifyManager(owner);
      if (show(owner.unit).LoadState !== 'not-found') throw new Error('SUPERVISION_UNIT_COLLISION');
      const properties = { Type: 'exec', ExitType: 'cgroup', Restart: 'no', RemainAfterExit: 'yes', RuntimeMaxSec: `${owner.limits.runtimeMilliseconds}ms`, TimeoutStartSec: `${owner.limits.startupMilliseconds}ms`, TimeoutStopSec: `${owner.limits.stopGraceMilliseconds}ms`, RuntimeRandomizedExtraSec: '0', KillMode: 'control-group', SendSIGKILL: 'yes', WorkingDirectory: options.cwd, StandardOutput: `append:${logPath}`, StandardError: `append:${logPath}` };
      const argv = ['--user', '--wait', `--unit=${owner.unit}`, '--slice=app.slice', `--description=${owner.binding}`, '--expand-environment=no', ...Object.entries(properties).map(([key, value]) => `--property=${key}=${value}`), '--', config.env, '-i', ...Object.entries(options.env).map(([key, value]) => `${key}=${value}`), command, ...args];
      return (dependencies.spawn ?? spawn)(config.systemdRun, argv, { env, stdio: ['ignore', 'pipe', 'pipe'] });
    },
    cancel(owner, persist) {
      verifyManager(owner);
      const unit = show(owner.unit); owned(owner, unit);
      owner = { ...owner, systemdInvocationId: unit.InvocationID, cancellationIntent: true };
      persist(owner);
      // Explicit cancellation is immediate and only affects this owned cgroup.
      // It is not release; the normal observer must still capture terminal proof.
      owned(owner, show(owner.unit));
      transport(config.systemctl, ['--user', 'kill', '--signal=SIGKILL', '--kill-whom=all', '--', owner.unit]);
    },
    observe(owner, persist) {
      verifyManager(owner);
      let unit = show(owner.unit);
      if (unit.LoadState === 'not-found') {
        if (owner.terminalReceipt && owner.stopConfirmed && empty(owner)) return { terminal: true, receipt: owner.terminalReceipt };
        throw new Error('SUPERVISION_UNIT_MISSING');
      }
      owned(owner, unit);
      if (!owner.systemdInvocationId) { owner = { ...owner, systemdInvocationId: unit.InvocationID }; persist(owner); }
      const terminal = (unit.ActiveState === 'active' && unit.SubState === 'exited') || ['inactive', 'failed'].includes(unit.ActiveState);
      if (!terminal || !empty(owner)) return { terminal: false };
      if (!owner.terminalReceipt) {
        owner = { ...owner, terminalReceipt: { invocationId: owner.invocationId, manager: owner.manager, unit: owner.unit, systemdInvocationId: unit.InvocationID, cgroup: owner.cgroup, observedAt: new Date().toISOString(), result: unit.Result, mainCode: unit.ExecMainCode, mainStatus: unit.ExecMainStatus }, stopIntent: true };
        persist(owner);
      }
      // Re-read immediately before a unit mutation; transport success alone never
      // releases ownership. A crash between stop and confirmation safely holds.
      unit = show(owner.unit); owned(owner, unit);
      transport(config.systemctl, ['--user', 'stop', '--', owner.unit]);
      owner = { ...owner, stopConfirmed: true }; persist(owner);
      verifyManager(owner);
      unit = show(owner.unit);
      if (unit.LoadState !== 'not-found') {
        owned(owner, unit);
        if (unit.ActiveState === 'failed' && empty(owner)) {
          // stop preserves failed-unit metadata. The receipt already holds it;
          // clear only this revalidated failure so it can become inactive.
          transport(config.systemctl, ['--user', 'reset-failed', '--', owner.unit]);
          verifyManager(owner); unit = show(owner.unit);
          if (unit.LoadState !== 'not-found') { owned(owner, unit); if (unit.ActiveState !== 'inactive') return { terminal: false }; }
        } else if (unit.ActiveState !== 'inactive') return { terminal: false };
      }
      return { terminal: empty(owner), receipt: owner.terminalReceipt };
    },
  };
}
