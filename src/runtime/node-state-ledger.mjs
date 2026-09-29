import crypto from "node:crypto";
import { closeSync, existsSync, fsyncSync, openSync, readFileSync, renameSync, rmSync, statSync, writeSync } from "node:fs";
import { dirname, join } from "node:path";

const canonical = value => JSON.stringify(value, (_key, item) =>
  item && !Array.isArray(item) && typeof item === "object"
    ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
const digest = value => crypto.createHash("sha256").update(canonical(value)).digest("hex");
const snapshot = value => JSON.parse(JSON.stringify(value));
const defaultState = () => ({ deliveries: {}, active: {} });
const owners = new Map();
function fileIdentity(path) {
  try {
    const stat = statSync(path, { bigint: true });
    return [stat.dev, stat.ino, stat.size, stat.mtimeNs, stat.ctimeNs].join(":");
  } catch (error) {
    if (error.code === "ENOENT") return null;
    throw error;
  }
}

function writeAll(fd, value) {
  const bytes = Buffer.from(value, "utf8");
  let offset = 0;
  while (offset < bytes.length) {
    const written = writeSync(fd, bytes, offset, bytes.length - offset);
    if (written < 1) throw new Error("LEDGER_SHORT_WRITE");
    offset += written;
  }
}

function syncDirectory(path) {
  const fd = openSync(dirname(path), "r");
  try { fsyncSync(fd); } finally { closeSync(fd); }
}
function atomic(path, contents) {
  const temporary = `${path}.${process.pid}.${crypto.randomUUID()}.tmp`;
  try {
    const fd = openSync(temporary, "wx", 0o600);
    try { writeAll(fd, contents); fsyncSync(fd); } finally { closeSync(fd); }
    renameSync(temporary, path);
    syncDirectory(path);
  } finally { rmSync(temporary, { force: true }); }
}
function changed(previous, next) {
  const lanes = new Set();
  const occurrences = [];
  for (const field of ["active", "diagnostics"]) {
    const before = previous?.[field] ?? {}, after = next[field] ?? {};
    for (const lane of new Set([...Object.keys(before), ...Object.keys(after)])) {
      if (canonical(before[lane] ?? null) === canonical(after[lane] ?? null)) continue;
      lanes.add(lane);
      occurrences.push({ lane, field, invocationId: after[lane]?.invocationId ?? before[lane]?.invocationId ?? null,
        outcome: after[lane]?.outcome ?? null });
    }
  }
  return { lanes: [...lanes].sort(), occurrences: occurrences.sort((a, b) =>
    a.lane.localeCompare(b.lane) || a.field.localeCompare(b.field)) };
}

export class NodeStateLedger {
  constructor(statePath, ledgerPath = join(dirname(statePath), "node-state-ledger.jsonl"), hooks = {}) {
    this.statePath = statePath;
    this.path = ledgerPath;
    this.headPath = `${ledgerPath}.head`;
    this.lockPath = `${ledgerPath}.writer`;
    this.hooks = hooks;
  }
  lock() {
    if (owners.has(this.lockPath)) {
      if (readFileSync(this.lockPath, "utf8") !== owners.get(this.lockPath)) throw new Error("LEDGER_WRITER_CHANGED");
      return;
    }
    try {
      const identity = `${process.pid}:${crypto.randomUUID()}\n`;
      const fd = openSync(this.lockPath, "wx", 0o600);
      try { writeAll(fd, identity); fsyncSync(fd); } finally { closeSync(fd); }
      syncDirectory(this.lockPath);
      owners.set(this.lockPath, identity);
    } catch (error) {
      if (error.code !== "EEXIST") throw error;
      const identity = readFileSync(this.lockPath, "utf8");
      const pid = Number(identity.trim().split(":")[0]);
      if (pid === process.pid) throw new Error("LEDGER_WRITER_UNVERIFIED");
      if (!Number.isSafeInteger(pid) || pid < 1) throw new Error("LEDGER_WRITER_UNVERIFIED");
      try { process.kill(pid, 0); throw new Error("LEDGER_WRITER_BUSY"); }
      catch (probe) { if (probe.code !== "ESRCH") throw probe; }
      rmSync(this.lockPath);
      syncDirectory(this.lockPath);
      return this.lock();
    }
  }
  replay() {
    this.lock();
    if (this.cached && this.cached.source === fileIdentity(this.path)
        && this.cached.head === fileIdentity(this.headPath)) return this.cached.record;
    if (!existsSync(this.path)) {
      if (existsSync(this.headPath)) throw new Error("LEDGER_TRUNCATED");
      const legacy = existsSync(this.statePath) ? JSON.parse(readFileSync(this.statePath, "utf8")) : defaultState();
      this.appendRecord(null, legacy, true);
    }
    const sourceIdentity = fileIdentity(this.path), headIdentity = fileIdentity(this.headPath);
    const bytes = readFileSync(this.path, "utf8");
    if (!bytes.endsWith("\n")) throw new Error("LEDGER_TRUNCATED");
    const lines = bytes.trimEnd().split("\n");
    let previous = null;
    const records = [];
    for (const line of lines) {
      let record;
      try { record = JSON.parse(line); } catch { throw new Error("LEDGER_CORRUPT"); }
      const { digest: recordedDigest, ...body } = record;
      if (line !== canonical(record) || record.schemaVersion !== 1
          || typeof record.revision !== "string" || !record.revision
          || record.sequence !== (previous?.sequence ?? -1) + 1
          || record.genesis !== !previous
          || (record.genesis && record.historyBeforeGenesis !== "UNKNOWN")
          || record.previousDigest !== (previous?.digest ?? null)
          || (previous && record.revision !== previous.revision)
          || typeof record.sourceUtc !== "string" || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(record.sourceUtc)
          || !Number.isFinite(Date.parse(record.sourceUtc))
          || digest(record.state) !== record.stateDigest
          || digest(body) !== recordedDigest
          || (previous && Date.parse(record.sourceUtc) < Date.parse(previous.sourceUtc))) throw new Error("LEDGER_CORRUPT_OR_FORKED");
      previous = record;
      records.push(record);
    }
    if (!previous || previous.sequence < 0) throw new Error("LEDGER_CORRUPT");
    let repairedHead = false;
    if (existsSync(this.headPath)) {
      const head = JSON.parse(readFileSync(this.headPath, "utf8"));
      if (head.revision !== previous.revision || !Number.isSafeInteger(head.sequence)
          || head.sequence < 0 || head.sequence > previous.sequence
          || records[head.sequence].digest !== head.digest) throw new Error("LEDGER_TRUNCATED_OR_FORKED");
      // A crash after append and before the head update leaves a recoverable lag.
      if (head.sequence < previous.sequence) {
        atomic(this.headPath, `${JSON.stringify({ revision: previous.revision, sequence: previous.sequence, digest: previous.digest })}\n`);
        repairedHead = true;
      }
    } else {
      atomic(this.headPath, `${JSON.stringify({ revision: previous.revision, sequence: previous.sequence, digest: previous.digest })}\n`);
      repairedHead = true;
    }
    if (sourceIdentity !== fileIdentity(this.path)
        || (!repairedHead && headIdentity !== fileIdentity(this.headPath))) throw new Error("LEDGER_CHANGED_DURING_REPLAY");
    this.cached = repairedHead ? null : { record: previous, source: sourceIdentity, head: headIdentity };
    return previous;
  }
  appendRecord(previous, state, genesis = false) {
    this.cached = null;
    const postState = snapshot(state);
    const revision = previous?.revision ?? crypto.randomUUID();
    const sequence = (previous?.sequence ?? -1) + 1;
    const delta = genesis ? { lanes: [], occurrences: [] } : changed(previous?.state, postState);
    const body = { schemaVersion: 1, revision, sequence, previousDigest: previous?.digest ?? null,
      sourceUtc: new Date().toISOString(), genesis, historyBeforeGenesis: genesis ? "UNKNOWN" : undefined,
      changedLanes: delta.lanes,
      occurrences: delta.occurrences.map((entry, index) => ({ ...entry, id: `${revision}:${sequence}:${index}` })),
      stateDigest: digest(postState), state: postState };
    const record = { ...body, digest: digest(body) };
    this.hooks.beforeAppend?.(record);
    const fd = openSync(this.path, "a", 0o600);
    try {
      writeAll(fd, `${canonical(record)}\n`);
      fsyncSync(fd);
    } finally { closeSync(fd); }
    syncDirectory(this.path);
    this.hooks.afterAppend?.(record);
    atomic(this.headPath, `${JSON.stringify({ revision, sequence, digest: record.digest })}\n`);
    return record;
  }
  read() {
    const record = this.replay();
    const expected = `${JSON.stringify(record.state, null, 2)}\n`;
    let projected;
    try { projected = JSON.parse(readFileSync(this.statePath, "utf8")); } catch { projected = null; }
    if (digest(projected) !== record.stateDigest) {
      this.hooks.beforeProjection?.(record);
      atomic(this.statePath, expected);
      this.hooks.afterProjection?.(record);
    }
    return snapshot(record.state);
  }
  save(state) {
    const previous = this.replay();
    const record = this.appendRecord(previous, state);
    this.hooks.beforeProjection?.(record);
    atomic(this.statePath, `${JSON.stringify(record.state, null, 2)}\n`);
    this.hooks.afterProjection?.(record);
    return record;
  }
  assertFence() {
    const record = this.replay();
    if (!existsSync(this.statePath) || digest(JSON.parse(readFileSync(this.statePath, "utf8"))) !== record.stateDigest)
      throw new Error("LEDGER_PROJECTION_FENCE_UNAVAILABLE");
    return { revision: record.revision, sequence: record.sequence, digest: record.digest };
  }
}
