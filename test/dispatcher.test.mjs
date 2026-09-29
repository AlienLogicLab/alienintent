import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { appendFileSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { EventRelay, verifyWebhookSignature } from "../src/runtime/dispatcher.mjs";
import { GitHubAuthority } from "../src/github/authority.mjs";

function child(pid = 1001) { const c = new EventEmitter(); c.stdout = new EventEmitter(); c.stderr = new EventEmitter(); c.exitCode = null; c.pid = pid; return c; }
function subject(overrides = {}) {
  const launches = []; const transitions = []; const children = [];
  const statePath = join(mkdtempSync(join(tmpdir(), "b-disp-v3-")), "state.json");
  const relay = new EventRelay({ statePath, repository: "ExampleOrg/sample-project", executionEnabled: true,
    authority: { enrichContentNode: async () => ({ repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1" }), durableResult: async () => null, transition: async (_item, status) => transitions.push(status), listItems: async () => [] },
    preflight: async () => ({ ok: true }), launch: ({ role }) => { launches.push(role); const c = child(); children.push(c); return c; }, workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, workers: { PRODUCER: {}, VERIFIER: {} }, ...overrides });
  relay.options.authority.resolveItem ??= async item => item;
  relay.options.authority.currentStatus ??= async item => {
    const claim = Object.values(relay.state().active).find(value => value.item?.issue === item.issue)
      ?? Object.values(relay.state().active)[0];
    return claim?.status ?? (claim?.role === "VERIFIER" ? "VERIFY" : "IMPLEMENT");
  };
  return { relay, launches, transitions, children, statePath };
}
function event(status, id = "d1") { return { headers: { "x-github-event": "projects_v2_item", "x-github-delivery": id }, payload: { action: "edited", organization: { login: "ExampleOrg" }, projects_v2_item: { id: "PVT_1", content_node_id: "I_303" }, changes: { field_value: { field_name: "Status", to: status } } } }; }
function resultEvent({ repository = "ExampleOrg/sample-project", issue = 303, invocationId, result = "VERIFY", login = "producer-bot", id = "comment-1", body } = {}) { return { headers: { "x-github-event": "issue_comment", "x-github-delivery": id }, payload: { action: "created", repository: { full_name: repository }, issue: { number: issue }, comment: { body: body ?? `<!-- B-DISP: INVOCATION=${invocationId} RESULT=${result} -->`, user: { login } } } }; }
test("rejects invalid webhook signatures", () => { assert.equal(verifyWebhookSignature("secret", Buffer.from("payload"), "sha256=nope"), false); });

test("routes validated IMPLEMENT and VERIFY events once without project reread", async () => { const { relay, launches } = subject(); await relay.acceptEvent(event("IMPLEMENT")); await relay.acceptEvent(event("VERIFY", "d2")); assert.deepEqual(launches, ["PRODUCER", "VERIFIER"]); assert.equal(relay.metrics.projectLists, 0); });
test("builds role-specific durable-result bootstrap with the exact current invocation", async () => {
  const launches = [];
  const { relay } = subject({ launch: (request) => { launches.push(request); return child(); } });
  await relay.acceptEvent(event("IMPLEMENT"));
  const producer = launches[0];
  assert.equal(producer.item.repository, "ExampleOrg/sample-project");
  assert.equal(producer.item.issue, 303);
  assert.match(producer.bootstrap, new RegExp(`INVOCATION=${producer.invocationId.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=VERIFY`));
  assert.match(producer.bootstrap, new RegExp(`INVOCATION=${producer.invocationId.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=FOUNDER_EXCEPTION`));
  assert.match(producer.bootstrap, new RegExp(`<!-- B-DISP: INVOCATION=${producer.invocationId.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=VERIFY -->`));
  assert.match(producer.bootstrap, new RegExp(`<!-- B-DISP: INVOCATION=${producer.invocationId.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=FOUNDER_EXCEPTION -->`));
  assert.doesNotMatch(producer.bootstrap, /RESULT=ACCEPT|RESULT=REJECT/);
  assert.match(producer.bootstrap, /Use that durable assignment as the source of execution authority\./);
  assert.match(producer.bootstrap, /Carry out repository and GitHub changes that it authorizes\./);
  assert.match(producer.bootstrap, /Changes to another repository require explicit authorization in the durable task\./);
  assert.match(producer.bootstrap, /Only the exact invocation marker communicates a workflow RESULT; it does not narrow the execution authority of the assignment\./);
  assert.match(producer.bootstrap, /Finish by publishing exactly one GitHub Issue comment containing/);
  assert.match(producer.bootstrap, /stdout and chat cannot supply a workflow result\./);
  await relay.acceptEvent(event("VERIFY", "verifier-bootstrap"));
  const verifier = launches[1];
  for (const result of ["ACCEPT", "REJECT", "FOUNDER_EXCEPTION"]) assert.match(verifier.bootstrap, new RegExp(`<!-- B-DISP: INVOCATION=${verifier.invocationId.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=${result} -->`));
  assert.doesNotMatch(verifier.bootstrap, /RESULT=VERIFY/);
  assert.match(verifier.bootstrap, /Use that durable assignment as the source of execution authority\./);
  assert.match(verifier.bootstrap, /Carry out repository and GitHub changes that it authorizes\./);
  assert.match(verifier.bootstrap, /Changes to another repository require explicit authorization in the durable task\./);
  assert.match(verifier.bootstrap, /Only the exact invocation marker communicates a workflow RESULT; it does not narrow the execution authority of the assignment\./);
  assert.match(verifier.bootstrap, /Finish by publishing exactly one GitHub Issue comment containing/);
  assert.match(verifier.bootstrap, /stdout and chat cannot supply a workflow result\./);
});
test("ignores invalid, unsupported, non-status, and duplicate deliveries", async () => { const { relay, launches } = subject(); await relay.acceptEvent({ ...event("IMPLEMENT"), headers: { "x-github-event": "push", "x-github-delivery": "bad" } }); await relay.acceptEvent({ ...event("IMPLEMENT"), payload: { ...event("IMPLEMENT").payload, changes: { field_value: { field_name: "Title", to: "x" } } } }); await relay.acceptEvent(event("IMPLEMENT")); await relay.acceptEvent(event("IMPLEMENT")); assert.deepEqual(launches, ["PRODUCER"]); });

test("result comment before child exit transitions exactly once without chaining", async () => { const { relay, launches, transitions, children } = subject(); await relay.acceptEvent(event("IMPLEMENT")); const invocationId = [...relay.active.values()][0].invocationId; await relay.acceptEvent(resultEvent({ invocationId })); children[0].emit("close", 0); await new Promise((resolve) => setImmediate(resolve)); assert.deepEqual(transitions, ["VERIFY"]); assert.deepEqual(launches, ["PRODUCER"]); });
test("wrong repository, Issue, author, invocation, role result, duplicate marker, and stale result comments cannot transition", async () => { const { relay, transitions } = subject(); await relay.acceptEvent(event("IMPLEMENT")); const invocationId = [...relay.active.values()][0].invocationId; const invalid = [resultEvent({ invocationId, repository: "elsewhere/repo", id: "wrong-repository" }), resultEvent({ invocationId, issue: 304, id: "wrong-issue" }), resultEvent({ invocationId, login: "someone-else", id: "wrong-author" }), resultEvent({ invocationId: "other-invocation", id: "stale" }), resultEvent({ invocationId, result: "ACCEPT", id: "illegal-result" }), resultEvent({ invocationId, id: "multiple", body: `<!-- B-DISP: INVOCATION=${invocationId} RESULT=VERIFY -->\n<!-- B-DISP: INVOCATION=${invocationId} RESULT=VERIFY -->` })]; for (const received of invalid) await relay.acceptEvent(received); assert.deepEqual(transitions, []); assert.equal(relay.state().active["ExampleOrg/sample-project#303:PRODUCER"].invocationId, invocationId); });
test("liveness inspects but never kills a quiet live child", async () => { const { relay, children } = subject(); await relay.acceptEvent(event("IMPLEMENT")); assert.equal(await relay.inspectLiveness([...relay.active.values()][0].invocationId), "HEALTHY_ACTIVE"); assert.equal(children[0].exitCode, null); });
test("startup scans exactly once and launches actionable work", async () => { let scans = 0; const { relay, launches } = subject({ authority: { enrichContentNode: async () => null, durableResult: async () => null, transition: async () => {}, listItems: async () => { scans++; return [{ repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "IMPLEMENT" }]; } } }); await relay.startupReconcile(); await relay.startupReconcile(); assert.equal(scans, 1); assert.deepEqual(launches, ["PRODUCER"]); });

test("startup leaves a persisted claim alone only when its launched worker still exists", async () => { const { relay, launches, statePath } = subject({ isProcessAlive: (pid) => pid === 4455, authority: { enrichContentNode: async () => null, durableResult: async () => null, transition: async () => {}, listItems: async () => [{ repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "IMPLEMENT" }] } }); writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { "ExampleOrg/sample-project#303:PRODUCER": { invocationId: "surviving", startedAt: "2026-09-04T00:00:00.000Z", pid: 4455 } } })); await relay.startupReconcile(); assert.deepEqual(launches, []); assert.equal(relay.events.at(-1).outcome, "SURVIVING_INVOCATION_EXISTS"); });

test("startup routes an exact durable result before probing the persisted worker", async () => { const { relay, launches, transitions, statePath } = subject({ isProcessAlive: () => true, authority: { enrichContentNode: async () => null, durableResult: async () => "VERIFY", transition: async (_item, target) => transitions.push(target), listItems: async () => [{ repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "IMPLEMENT" }] } }); writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { "ExampleOrg/sample-project#303:PRODUCER": { invocationId: "completed", startedAt: "2026-09-04T00:00:00.000Z", pid: 4455 } } })); await relay.startupReconcile(); assert.deepEqual(transitions, ["VERIFY"]); assert.deepEqual(launches, []); });

test("startup clears a stale claim and starts exactly one fresh worker", async () => { const { relay, launches, statePath } = subject({ isProcessAlive: () => false, authority: { enrichContentNode: async () => null, durableResult: async () => null, transition: async () => {}, listItems: async () => [{ repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "IMPLEMENT" }] } }); writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { "ExampleOrg/sample-project#303:PRODUCER": { invocationId: "stale", startedAt: "2026-09-04T00:00:00.000Z", pid: 4455 } } })); await relay.startupReconcile(); assert.deepEqual(launches, ["PRODUCER"]); assert.notEqual(relay.state().active["ExampleOrg/sample-project#303:PRODUCER"].invocationId, "stale"); });

test("startup frees DONE dead claims without discarding retained resources or diagnostics", async () => {
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "DONE" };
  const resource = { invocationId: "stale", path: "/tmp/retained-diagnostic-worktree", lifecycle: "READY" };
  const diagnostic = { invocationId: "stale", outcome: "DURABLE_RESULT_MISSING" };
  const { relay, launches, statePath } = subject({ isProcessAlive: () => false,
    worktreeManager: { cleanup: () => { throw new Error("dirty worktree retained"); } },
    authority: { listItems: async () => [item], durableResult: async () => null } });
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: {
    "ExampleOrg/sample-project#303:PRODUCER": { invocationId: "stale", item, role: "PRODUCER", status: "IMPLEMENT", startedAt: "2026-09-04T00:00:00.000Z", pid: 4455 },
  }, diagnostics: { "ExampleOrg/sample-project#303:PRODUCER": diagnostic }, resources: { stale: resource } }));
  await relay.startupReconcile();
  assert.deepEqual(relay.state().active, {});
  assert.deepEqual(relay.state().diagnostics["ExampleOrg/sample-project#303:PRODUCER"], diagnostic);
  assert.deepEqual(relay.state().resources.stale, resource);
  assert.deepEqual(launches, []);
});

test("startup preserves a live DONE worker claim", async () => {
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "DONE" };
  const { relay, launches, statePath } = subject({ isProcessAlive: (pid) => pid === 4455,
    authority: { listItems: async () => [item], durableResult: async () => null } });
  const lane = "ExampleOrg/sample-project#303:PRODUCER";
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: {
    [lane]: { invocationId: "live", item, role: "PRODUCER", status: "IMPLEMENT", startedAt: "2026-09-04T00:00:00.000Z", pid: 4455 },
  } }));
  await relay.startupReconcile();
  assert.equal(relay.state().active[lane].invocationId, "live");
  assert.deepEqual(launches, []);
});

test("startup preserves a supervised DONE worker despite a dead launcher pid", async () => {
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "DONE" };
  const lane = "ExampleOrg/sample-project#303:PRODUCER";
  const launch = () => { throw new Error("unexpected launch"); };
  launch.observe = () => ({ terminal: false });
  const { relay, statePath } = subject({ isProcessAlive: () => false, launch,
    authority: { listItems: async () => [item], durableResult: async () => null } });
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: {
    [lane]: { invocationId: "supervised", item, role: "PRODUCER", status: "IMPLEMENT", startedAt: "2026-09-04T00:00:00.000Z", pid: 4455 },
  }, resources: { supervised: { invocationId: "supervised", path: "/tmp/supervised-diagnostic-worktree", supervision: { unit: "worker.service" } } } }));
  await relay.startupReconcile();
  assert.equal(relay.state().active[lane].invocationId, "supervised");
});



test("a reserved delivery blocks concurrent duplicate processing", async () => { let release; const blocked = new Promise((resolve) => { release = resolve; }); let enrichments = 0; const { relay, launches } = subject({ authority: { enrichContentNode: async () => { enrichments++; await blocked; return { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1" }; }, durableResult: async () => null, transition: async () => {}, listItems: async () => [] } }); const first = relay.acceptEvent(event("IMPLEMENT", "same")); await new Promise((resolve) => setImmediate(resolve)); const duplicate = await relay.acceptEvent(event("IMPLEMENT", "same")); assert.equal(duplicate.duplicate, true); release(); await first; assert.equal(enrichments, 1); assert.deepEqual(launches, ["PRODUCER"]); });

test("restart resumes a committed PROCESSING project delivery after append interruption", async () => {
  let enrichments = 0;
  const { relay, launches } = subject({ authority: {
    enrichContentNode: async () => { enrichments++; return { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1" }; },
    durableResult: async () => null, transition: async () => {}, listItems: async () => [],
  } });
  relay.ledger.hooks.afterAppend = record => {
    if (record.state.deliveries.interrupted?.state === "PROCESSING") throw new Error("INTERRUPTED_AFTER_APPEND");
  };
  await assert.rejects(relay.acceptEvent(event("IMPLEMENT", "interrupted")), /INTERRUPTED_AFTER_APPEND/);
  const interruptedRecords = readFileSync(relay.ledger.path, "utf8").trimEnd().split("\n");
  assert.equal(interruptedRecords.length, 2); // Genesis and committed reservation.
  assert.equal(enrichments, 0);
  assert.deepEqual(launches, []);
  assert.equal(relay.state().deliveries.interrupted.state, "PROCESSING");
  const restarted = new EventRelay({ ...relay.options, ledgerHooks: {} });
  assert.deepEqual(await restarted.acceptEvent(event("IMPLEMENT", "interrupted")), { accepted: true });
  assert.equal(restarted.state().deliveries.interrupted.state, "PROCESSED");
  assert.equal(enrichments, 1);
  assert.deepEqual(launches, ["PRODUCER"]);
  assert.equal((await restarted.acceptEvent(event("IMPLEMENT", "interrupted"))).duplicate, true);
  assert.deepEqual(launches, ["PRODUCER"]);
});

test("a committed PROCESSED delivery survives acknowledgement interruption", async () => {
  const { relay, launches } = subject();
  let interrupted = false;
  relay.ledger.hooks.afterAppend = record => {
    if (!interrupted && record.state.deliveries.acknowledgement?.state === "PROCESSED") {
      interrupted = true;
      throw new Error("INTERRUPTED_BEFORE_ACKNOWLEDGEMENT");
    }
  };
  await assert.rejects(relay.acceptEvent(event("IMPLEMENT", "acknowledgement")), /INTERRUPTED_BEFORE_ACKNOWLEDGEMENT/);
  const committed = JSON.parse(readFileSync(relay.ledger.path, "utf8").trimEnd().split("\n").at(-1));
  assert.equal(committed.state.deliveries.acknowledgement.state, "PROCESSED");
  const restarted = new EventRelay({ ...relay.options, ledgerHooks: {} });
  assert.equal(restarted.state().deliveries.acknowledgement.state, "PROCESSED");
  assert.equal((await restarted.acceptEvent(event("IMPLEMENT", "acknowledgement"))).duplicate, true);
  assert.deepEqual(launches, ["PRODUCER"]);
});

test("restart resumes a committed PROCESSING result delivery without repeating the status effect", async () => {
  const { relay, transitions } = subject();
  await relay.acceptEvent(event("IMPLEMENT"));
  const invocationId = [...relay.active.values()][0].invocationId;
  const before = readFileSync(relay.ledger.path, "utf8").trimEnd().split("\n").length;
  relay.ledger.hooks.afterAppend = record => {
    if (record.state.deliveries["result-interrupted"]?.state === "PROCESSING") throw new Error("INTERRUPTED_RESULT_RESERVATION");
  };
  const received = resultEvent({ invocationId, id: "result-interrupted" });
  await assert.rejects(relay.acceptEvent(received), /INTERRUPTED_RESULT_RESERVATION/);
  assert.equal(readFileSync(relay.ledger.path, "utf8").trimEnd().split("\n").length, before + 1);
  assert.deepEqual(transitions, []);
  const restarted = new EventRelay({ ...relay.options, ledgerHooks: {} });
  assert.deepEqual(await restarted.acceptEvent(received), { accepted: true });
  assert.deepEqual(transitions, ["VERIFY"]);
  assert.equal(restarted.state().deliveries["result-interrupted"].state, "PROCESSED");
  assert.equal((await restarted.acceptEvent(received)).duplicate, true);
  assert.deepEqual(transitions, ["VERIFY"]);
});

test("a successfully processed delivery remains deduplicated", async () => { const { relay, launches } = subject(); await relay.acceptEvent(event("IMPLEMENT", "processed")); const duplicate = await relay.acceptEvent(event("IMPLEMENT", "processed")); assert.equal(duplicate.duplicate, true); assert.deepEqual(launches, ["PRODUCER"]); });

test("a failed dispatch releases its delivery reservation for same-id redelivery", async () => { let fail = true; const { relay, launches } = subject({ launch: ({ role }) => { if (fail) { fail = false; throw new Error("launch failed"); } launches.push(role); return child(); } }); await assert.rejects(relay.acceptEvent(event("IMPLEMENT", "retryable")), /launch failed/); assert.equal(relay.state().deliveries.retryable, undefined); await relay.acceptEvent(event("IMPLEMENT", "retryable")); assert.deepEqual(launches, ["PRODUCER"]); });

test("a failed enrichment releases its delivery reservation for same-id redelivery", async () => { let fail = true; let enrichments = 0; const { relay, launches } = subject({ authority: { enrichContentNode: async () => { enrichments++; if (fail) { fail = false; throw new Error("enrichment failed"); } return { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1" }; }, durableResult: async () => null, transition: async () => {}, listItems: async () => [] } }); await assert.rejects(relay.acceptEvent(event("IMPLEMENT", "enrichment-retryable")), /enrichment failed/); assert.equal(relay.state().deliveries["enrichment-retryable"], undefined); await relay.acceptEvent(event("IMPLEMENT", "enrichment-retryable")); assert.equal(enrichments, 2); assert.deepEqual(launches, ["PRODUCER"]); });

test("distinct deliveries reserve one lane before asynchronous preflight", async () => {
  let release;
  const barrier = new Promise((resolve) => { release = resolve; });
  const { relay, launches } = subject({ preflight: async () => { await barrier; return { ok: true }; } });
  const starts = [relay.acceptEvent(event("IMPLEMENT", "race-1")), relay.acceptEvent(event("IMPLEMENT", "race-2"))];
  await new Promise((resolve) => setImmediate(resolve));
  const reserved = Object.keys(relay.state().active).length;
  release(); await Promise.all(starts);
  assert.equal(reserved, 1);
  assert.deepEqual(launches, ["PRODUCER"]);
});

for (const exitCode of [0, 1]) test(`exit ${exitCode} without exact marker releases lane with durable failure evidence`, async () => {
  const { relay, children, launches, transitions } = subject();
  await relay.acceptEvent(event("IMPLEMENT"));
  const active = [...relay.active.values()][0];
  children[0].exitCode = exitCode; children[0].emit("close", exitCode);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(relay.state().active[active.lane], undefined);
  assert.equal(relay.state().diagnostics[active.lane].outcome, "DURABLE_RESULT_MISSING");
  assert.equal(relay.state().diagnostics[active.lane].invocationId, active.invocationId);
  assert.equal(relay.state().diagnostics[active.lane].exitCode, exitCode);
  assert.deepEqual(transitions, []);
  await relay.acceptEvent(event("IMPLEMENT", "legitimate-retry"));
  assert.deepEqual(launches, ["PRODUCER", "PRODUCER"]);
  const replacement = [...relay.active.values()][0];
  await relay.complete(active);
  assert.equal(relay.state().active[active.lane].invocationId, replacement.invocationId);
  assert.equal([...relay.active.values()][0], replacement);
});

test("exit discovers and routes the exact clean result without webhook delivery", async () => {
  const { relay, children, transitions } = subject();
  let query;
  relay.options.authority.durableResult = async (request) => { query = request; return "VERIFY"; };
  await relay.acceptEvent(event("IMPLEMENT"));
  const active = [...relay.active.values()][0];
  children[0].exitCode = 0; children[0].emit("close", 0);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(query.invocationId, active.invocationId);
  assert.deepEqual(transitions, ["VERIFY"]);
  assert.equal(relay.state().active[active.lane], undefined);
});

test("owned invocation timer inspects and stops without Project polling or relaunch", async () => {
  const timers = new Map(); let timerId = 0; let now = 0;
  const { relay, launches, children } = subject({ now: () => now, inspectionIntervalMs: 1000, quietInspectionMs: 2000,
    setTimeout: (fn, ms) => { assert.equal(ms, 1000); timers.set(++timerId, fn); return timerId; },
    clearTimeout: (id) => timers.delete(id), inspectWorker: () => ({ state: "S", waitChannel: "futex_wait" }) });
  await relay.startupReconcile(); await relay.acceptEvent(event("IMPLEMENT"));
  assert.equal(timers.size, 1);
  async function tick() { const [id, fn] = timers.entries().next().value; timers.delete(id); now += 1000; await fn(); }
  await tick(); assert.equal(relay.events.at(-1).outcome, "HEALTHY_ACTIVE");
  await tick(); assert.equal(relay.events.at(-1).outcome, "QUIET_BUT_PLAUSIBLY_WORKING");
  relay.options.inspectWorker = () => ({ state: "S", waitChannel: "tty_read" });
  await tick(); assert.equal(relay.events.at(-1).outcome, "WAITING_FOR_INPUT");
  relay.options.inspectWorker = () => ({ state: "T", waitChannel: "do_signal_stop" });
  await tick(); assert.equal(relay.events.at(-1).outcome, "STUCK");
  assert.equal(relay.metrics.projectLists, 1); assert.deepEqual(launches, ["PRODUCER"]);
  assert.equal(children[0].exitCode, null);
  relay.stop(); assert.equal(timers.size, 0);
});

test("liveness consumes durable result but retains live lane until close", async () => {
  const { relay, transitions, launches, children } = subject();
  await relay.acceptEvent(event("IMPLEMENT"));
  const active = [...relay.active.values()][0];
  relay.options.authority.durableResult = async () => "VERIFY";
  assert.equal(await relay.inspectLiveness(active.invocationId), "RESULT_ALREADY_DURABLE");
  await relay.acceptEvent(event("IMPLEMENT", "still-live"));
  assert.deepEqual(launches, ["PRODUCER"]); assert.deepEqual(transitions, ["VERIFY"]);
  children[0].exitCode = 0; children[0].emit("close", 0);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(relay.state().active[active.lane], undefined);
  assert.deepEqual(transitions, ["VERIFY"]);
});

test("missing expected worker login and edited/deleted comments fail closed", async () => {
  const { relay, transitions } = subject({ workerLogins: {} });
  await relay.acceptEvent(event("IMPLEMENT"));
  const invocationId = [...relay.active.values()][0].invocationId;
  const received = resultEvent({ invocationId }); delete received.payload.comment.user.login;
  await relay.acceptEvent(received);
  relay.options.workerLogins = { PRODUCER: "producer-bot" };
  for (const action of ["edited", "deleted"]) {
    const received = resultEvent({ invocationId, id: action }); received.payload.action = action;
    await relay.acceptEvent(received);
  }
  assert.deepEqual(transitions, []);
});

test("concurrent result comments and close coalesce one transition", async () => {
  const { relay, transitions, children } = subject();
  let release;
  const blocked = new Promise((resolve) => { release = resolve; });
  relay.options.authority.transition = async (_item, target) => { transitions.push(target); await blocked; };
  await relay.acceptEvent(event("IMPLEMENT"));
  const active = [...relay.active.values()][0];
  const first = relay.acceptEvent(resultEvent({ invocationId: active.invocationId }));
  const second = relay.acceptEvent(resultEvent({ invocationId: active.invocationId, id: "second-comment" }));
  children[0].exitCode = 0; children[0].emit("close", 0);
  release(); await Promise.all([first, second]); await relay.complete(active);
  assert.deepEqual(transitions, ["VERIFY"]);
  assert.equal(relay.state().active[active.lane], undefined);
});

test("shutdown during preflight cancels launch and releases only its reservation", async () => {
  let release; const blocked = new Promise((resolve) => { release = resolve; });
  const { relay, launches } = subject({ preflight: async () => { await blocked; return { ok: true }; } });
  const start = relay.acceptEvent(event("IMPLEMENT"));
  await new Promise((resolve) => setImmediate(resolve)); relay.stop(); release(); await start;
  assert.deepEqual(launches, []); assert.deepEqual(relay.state().active, {});
});

test("close cancels inspection timer and read failure is diagnostic, not missing-result proof", async () => {
  const timers = new Map();
  const { relay, children } = subject({ setTimeout: (fn) => { timers.set(1, fn); return 1; }, clearTimeout: (id) => timers.delete(id) });
  await relay.acceptEvent(event("IMPLEMENT")); const active = [...relay.active.values()][0];
  relay.options.authority.durableResult = async () => { throw new Error("GitHub unavailable"); };
  children[0].exitCode = 1; children[0].emit("close", 1);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(timers.size, 0); assert.equal(relay.state().active[active.lane], undefined);
  assert.equal(relay.state().diagnostics[active.lane].outcome, "COMPLETION_ERROR");
});

test("startup preserves wrong-author evidence before releasing stale invocation", async () => {
  const { relay, statePath } = subject();
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "IMPLEMENT" };
  const lane = relay.lane(item, "PRODUCER");
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { [lane]: { invocationId: "stale", startedAt: "2026-09-01T00:00:00Z" } } }));
  relay.options.authority.listItems = async () => [item];
  relay.options.authority.durableResult = async () => ({ kind: "WORKER_IDENTITY_MISMATCH", evidence: { commentId: 22, author: "wrong" } });
  await relay.startupReconcile();
  assert.ok(relay.events.some((event) => event.outcome === "WORKER_IDENTITY_MISMATCH"));
  assert.equal(relay.state().diagnostics[lane].evidence.commentId, 22);
});

test("stopping during an in-flight inspection prevents routing and rescheduling", async () => {
  let timer, schedules = 0, release;
  const { relay, transitions } = subject({ setTimeout: (fn) => { timer = fn; schedules++; return 1; }, clearTimeout: () => {} });
  await relay.acceptEvent(event("IMPLEMENT"));
  relay.options.authority.durableResult = () => new Promise((resolve) => { release = resolve; });
  const inspecting = timer(); relay.stop(); release("VERIFY"); await inspecting;
  assert.deepEqual(transitions, []); assert.equal(schedules, 1);
});

test("timer interval is bounded even for invalid configuration", async () => {
  for (const [requested, expected] of [[0, 1000], [1e12, 300000], [NaN, 60000]]) {
    let interval;
    const { relay } = subject({ inspectionIntervalMs: requested, setTimeout: (_fn, ms) => { interval = ms; return 1; }, clearTimeout: () => {} });
    await relay.acceptEvent(event("IMPLEMENT")); assert.equal(interval, expected); relay.stop();
  }
});

test("preflight failure on one lane does not remove another reserved lane", async () => {
  const { relay, launches } = subject({ preflight: async ({ role }) => ({ ok: role === "VERIFIER" }) });
  await Promise.all([relay.acceptEvent(event("IMPLEMENT", "producer-fails")), relay.acceptEvent(event("VERIFY", "verifier-starts"))]);
  assert.deepEqual(launches, ["VERIFIER"]);
  assert.equal(Object.keys(relay.state().active).length, 1);
  assert.equal(Object.values(relay.state().active)[0].role, "VERIFIER");
});

test("wrong-author noise cannot erase a consumed Founder exception on close", async () => {
  const { relay, children, launches } = subject();
  await relay.acceptEvent(event("IMPLEMENT"));
  const active = [...relay.active.values()][0];
  await relay.acceptEvent(resultEvent({ invocationId: active.invocationId, result: "FOUNDER_EXCEPTION" }));
  await relay.acceptEvent(resultEvent({ invocationId: active.invocationId, login: "wrong", id: "noise" }));
  children[0].exitCode = 0; children[0].emit("close", 0);
  await new Promise((resolve) => setImmediate(resolve));
  await relay.acceptEvent(event("IMPLEMENT", "must-remain-halted"));
  assert.deepEqual(launches, ["PRODUCER"]);
});

test("VERIFIER ACCEPT discovered on close routes Accept without launching another worker", async () => {
  const { relay, children, transitions, launches } = subject();
  relay.options.authority.durableResult = async () => "ACCEPT";
  await relay.acceptEvent(event("VERIFY")); children[0].exitCode = 0; children[0].emit("close", 0);
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(transitions, ["ACCEPT"]); assert.deepEqual(launches, ["VERIFIER"]);
});

for (const exact of [false, true]) test(`exit uses real Issue marker parser (exact current result: ${exact})`, async () => {
  const { relay, children, transitions } = subject();
  let invocationId;
  const authority = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, repository: "ExampleOrg/sample-project", gh: (args) => {
    assert.equal(args[1], "repos/ExampleOrg/sample-project/issues/303/comments");
    return JSON.stringify([
      { body: "<!-- B-DISP: RESULT=VERIFY -->", created_at: "2099-01-01T00:00:00Z", user: { login: "producer-bot" } },
      { body: `<!-- B-DISP: INVOCATION=${exact ? invocationId : "old"} RESULT=VERIFY -->`, created_at: "2099-01-01T00:00:00Z", user: { login: "producer-bot" } },
    ]);
  } });
  authority.resolveItem = async item => item;
  authority.transition = async (_item, status) => transitions.push(status);
  authority.currentStatus = async () => "IMPLEMENT";
  relay.options.authority = authority;
  await relay.start({ repository: "ExampleOrg/sample-project", issue: 303, itemId: "item" }, "PRODUCER", "IMPLEMENT");
  const active = [...relay.active.values()][0]; invocationId = active.invocationId;
  children[0].exitCode = 0; children[0].emit("close", 0);
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(transitions, exact ? ["VERIFY"] : []);
  assert.equal(relay.state().diagnostics[active.lane].outcome, exact ? "VERIFY_TO_VERIFY" : "DURABLE_RESULT_MISSING");
  assert.equal(relay.state().active[active.lane], undefined);
});

test("later Status event releases a completed surviving claim only after its pid is gone", async () => {
  const { relay, statePath, launches } = subject();
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "item", status: "IMPLEMENT" };
  const lane = relay.lane(item, "PRODUCER"); let alive = true;
  relay.options.isProcessAlive = () => alive;
  relay.options.authority.listItems = async () => [item];
  relay.options.authority.durableResult = async () => "VERIFY";
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { [lane]: { invocationId: "survivor", item, role: "PRODUCER", startedAt: "2026-09-01T00:00:00Z", pid: 123 } } }));
  await relay.startupReconcile();
  await relay.acceptEvent(event("IMPLEMENT", "still-surviving")); assert.deepEqual(launches, []);
  alive = false;
  await relay.acceptEvent(event("IMPLEMENT", "legitimate-rework")); assert.deepEqual(launches, ["PRODUCER"]);
});

test("late exact result recovers from missing-result diagnostic once, without launching", async () => {
  const { relay, children, transitions, launches } = subject();
  await relay.acceptEvent(event("IMPLEMENT")); const active = [...relay.active.values()][0];
  children[0].exitCode = 0; children[0].emit("close", 0);
  await new Promise((resolve) => setImmediate(resolve));
  await relay.acceptEvent(resultEvent({ invocationId: active.invocationId, id: "late-result" }));
  await relay.acceptEvent(resultEvent({ invocationId: active.invocationId, id: "late-duplicate" }));
  assert.deepEqual(transitions, ["VERIFY"]); assert.deepEqual(launches, ["PRODUCER"]);
  assert.equal(relay.state().active[active.lane], undefined);
});

test("late old marker cannot satisfy a successor invocation", async () => {
  const { relay, children, transitions } = subject();
  await relay.acceptEvent(event("IMPLEMENT")); const active = [...relay.active.values()][0];
  children[0].exitCode = 1; children[0].emit("close", 1);
  await new Promise((resolve) => setImmediate(resolve));
  await relay.acceptEvent(event("IMPLEMENT", "retry"));
  const current = [...relay.active.values()][0];
  await relay.acceptEvent(resultEvent({ invocationId: active.invocationId }));
  assert.deepEqual(transitions, []);
  assert.equal(relay.state().active[current.lane].invocationId, current.invocationId);
});

test("late result after an exit read error reserves routing against a competing start", async () => {
  const { relay, children, transitions, launches } = subject();
  await relay.acceptEvent(event("IMPLEMENT")); const active = [...relay.active.values()][0];
  relay.options.authority.durableResult = async () => { throw new Error("temporary GitHub failure"); };
  children[0].exitCode = 0; children[0].emit("close", 0); await new Promise((resolve) => setImmediate(resolve));
  let release; const pending = new Promise((resolve) => { release = resolve; });
  relay.options.authority.transition = async (_item, status) => { transitions.push(status); await pending; };
  const result = relay.acceptEvent(resultEvent({ invocationId: active.invocationId, id: "late-after-error" }));
  await relay.acceptEvent(event("IMPLEMENT", "competing"));
  release(); await result;
  assert.deepEqual(transitions, ["VERIFY"]); assert.deepEqual(launches, ["PRODUCER"]);
  assert.equal(relay.state().active[active.lane], undefined);
});

test("result arriving during a dead surviving claim check prevents a fresh launch", async () => {
  const { relay, statePath, transitions, launches } = subject();
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "item" };
  const lane = relay.lane(item, "PRODUCER");
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { [lane]: { item, role: "PRODUCER", invocationId: "survivor", startedAt: "2026-09-01T00:00:00Z" } } }));
  let release; relay.options.authority.durableResult = () => new Promise((resolve) => { release = resolve; });
  const start = relay.acceptEvent(event("IMPLEMENT", "after-orphan-exit")); await new Promise((resolve) => setImmediate(resolve));
  await relay.acceptEvent(resultEvent({ invocationId: "survivor" })); release(null); await start;
  assert.deepEqual(transitions, ["VERIFY"]); assert.deepEqual(launches, []);
  assert.equal(relay.state().active[lane], undefined);
});

test("a delayed old inspection cannot replace a completed successor diagnostic", async () => {
  const { relay, children, transitions } = subject();
  await relay.acceptEvent(event("IMPLEMENT")); const old = [...relay.active.values()][0];
  let release;
  relay.options.authority.durableResult = () => new Promise((resolve) => { release = resolve; });
  const inspection = relay.inspectLiveness(old.invocationId);
  relay.options.authority.durableResult = async () => null;
  children[0].exitCode = 0; children[0].emit("close", 0); await new Promise((resolve) => setImmediate(resolve));
  await relay.acceptEvent(event("IMPLEMENT", "successor")); const current = [...relay.active.values()][0];
  relay.options.authority.durableResult = async () => "VERIFY";
  children[1].exitCode = 0; children[1].emit("close", 0); await new Promise((resolve) => setImmediate(resolve));
  release({ kind: "WORKER_IDENTITY_MISMATCH", evidence: { commentId: 11 } }); await inspection;
  assert.equal(relay.state().diagnostics[old.lane].invocationId, current.invocationId);
  await relay.acceptEvent(resultEvent({ invocationId: old.invocationId, id: "obsolete-result" }));
  assert.deepEqual(transitions, ["VERIFY"]);
});

test("a delayed inspection cannot make an already-consumed result recoverable again", async () => {
  const { relay, children, transitions } = subject();
  await relay.acceptEvent(event("IMPLEMENT")); const active = [...relay.active.values()][0];
  let release; relay.options.authority.durableResult = () => new Promise((resolve) => { release = resolve; });
  const inspection = relay.inspectLiveness(active.invocationId);
  relay.options.authority.durableResult = async () => "VERIFY";
  children[0].exitCode = 0; children[0].emit("close", 0); await new Promise((resolve) => setImmediate(resolve));
  release({ kind: "WORKER_IDENTITY_MISMATCH", evidence: { commentId: 11 } }); await inspection;
  await relay.acceptEvent(resultEvent({ invocationId: active.invocationId, id: "duplicate-after-inspection" }));
  assert.deepEqual(transitions, ["VERIFY"]);
});

test("recovered result owns the lane through the routing promise cleanup microtask", async () => {
  const { relay, children, launches } = subject();
  await relay.acceptEvent(event("IMPLEMENT")); const active = [...relay.active.values()][0];
  children[0].exitCode = 0; children[0].emit("close", 0); await new Promise((resolve) => setImmediate(resolve));
  let release; const blocked = new Promise((resolve) => { release = resolve; });
  relay.options.authority.transition = () => blocked;
  const result = relay.acceptEvent(resultEvent({ invocationId: active.invocationId, id: "late-routing" }));
  const queuedStart = relay.routing.get(active.invocationId).then(() => relay.start(active.item, "PRODUCER", "IMPLEMENT"));
  release(); await Promise.all([result, queuedStart]);
  assert.deepEqual(launches, ["PRODUCER"]); assert.deepEqual(relay.state().active, {});
});

test("malformed unrelated persisted claim does not prevent a valid result comment", async () => {
  const { relay, statePath, transitions } = subject();
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { malformed: { invocationId: "broken" } } }));
  await relay.acceptEvent(resultEvent({ invocationId: "broken", id: "malformed-target" }));
  await relay.acceptEvent(event("IMPLEMENT")); const active = [...relay.active.values()][0];
  await relay.acceptEvent(resultEvent({ invocationId: active.invocationId }));
  assert.deepEqual(transitions, ["VERIFY"]);
});

test("child close remains observed when persisting its pid fails", async () => {
  const { relay, children } = subject(); const save = relay.save.bind(relay); let failed = false;
  relay.save = (state) => { if (!failed && Object.values(state.active).some((claim) => claim.pid)) { failed = true; throw new Error("pid write failed"); } return save(state); };
  await assert.rejects(relay.acceptEvent(event("IMPLEMENT")), /pid write failed/);
  children[0].exitCode = 1; children[0].emit("close", 1); await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(relay.state().active, {}); assert.equal(relay.active.size, 0);
});

function failedInvocationSubject(t, { role = "PRODUCER", outcome = "COMPLETION_ERROR", comments = [], failRead = false } = {}) {
  const fixture = subject(); const { relay, statePath, transitions } = fixture;
  t.after(() => relay.stop());
  const status = role === "PRODUCER" ? "IMPLEMENT" : "VERIFY";
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status };
  const lane = relay.lane(item, role), invocationId = `${lane}:failed-latest`;
  const diagnostic = { item, role, invocationId, outcome, startedAt: "2026-09-01T00:00:00Z" };
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: {}, diagnostics: { [lane]: diagnostic } }));
  let reads = 0;
  const authority = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, repository: item.repository, gh: (args) => {
    assert.deepEqual(args, ["api", "repos/ExampleOrg/sample-project/issues/303/comments", "--paginate"]);
    reads++;
    if (failRead) throw new Error("GitHub read unavailable");
    return JSON.stringify(comments.map(comment => ({ created_at: "2026-09-01T00:01:00Z", ...comment })));
  } });
  authority.resolveItem = async item => item;
  authority.listItems = async () => [item];
  authority.currentStatus = async () => status;
  authority.enrichContentNode = async () => item;
  authority.transition = async (_item, target) => transitions.push(target);
  relay.options.authority = authority;
  return { ...fixture, item, lane, invocationId, comments, reads: () => reads };
}

for (const entry of ["startup", "event"]) {
  for (const role of ["PRODUCER", "VERIFIER"]) {
    for (const outcome of ["COMPLETION_ERROR", "DURABLE_RESULT_MISSING", "WORKER_IDENTITY_MISMATCH"]) {
      test(`${entry} recovers ${role} exact result from ${outcome} without successor`, async t => {
        const f = failedInvocationSubject(t, { role, outcome });
        const result = role === "PRODUCER" ? "VERIFY" : "REJECT";
        f.comments.push({ body: `<!-- B-DISP: INVOCATION=${f.invocationId} RESULT=${result} -->`, user: { login: role === "PRODUCER" ? "producer-bot" : "verifier-bot" } });
        if (entry === "startup") await f.relay.startupReconcile();
        else await f.relay.acceptEvent(event(f.item.status));
        assert.deepEqual(f.transitions, [role === "PRODUCER" ? "VERIFY" : "IMPLEMENT"]);
        assert.deepEqual(f.launches, []);
        assert.equal(f.reads(), 1);
        assert.deepEqual(f.relay.state().active, {});
      });
    }
  }
  test(`${entry} failed completion read remains ambiguous and launches no successor`, async t => {
    const f = failedInvocationSubject(t, { failRead: true });
    if (entry === "startup") await f.relay.startupReconcile();
    else await f.relay.acceptEvent(event("IMPLEMENT"));
    assert.deepEqual(f.launches, []); assert.deepEqual(f.transitions, []);
    assert.equal(f.reads(), 1);
    assert.equal(f.relay.state().diagnostics[f.lane].outcome, "COMPLETION_ERROR");
    assert.equal(f.relay.state().diagnostics[f.lane].invocationId, f.invocationId);
  });
  for (const absent of ["missing", "wrong-author", "older-invocation"]) {
    test(`${entry} successful ${absent} read permits existing successor behavior`, async t => {
      const f = failedInvocationSubject(t);
      if (absent !== "missing") f.comments.push({ body: `<!-- B-DISP: INVOCATION=${absent === "older-invocation" ? "older" : f.invocationId} RESULT=VERIFY -->`, user: { login: absent === "wrong-author" ? "wrong" : "producer-bot" } });
      if (entry === "startup") await f.relay.startupReconcile();
      else await f.relay.acceptEvent(event("IMPLEMENT"));
      assert.equal(f.reads(), 1);
      assert.deepEqual(f.launches, ["PRODUCER"]); assert.deepEqual(f.transitions, []);
      assert.notEqual(f.relay.state().active[f.lane].invocationId, f.invocationId);
      if (absent === "wrong-author") assert.ok(f.relay.events.some(e => e.outcome === "WORKER_IDENTITY_MISMATCH"));
    });
  }
}

test("failed-invocation recovery reserves the lane against concurrent Status deliveries", async t => {
  const f = failedInvocationSubject(t);
  let release;
  f.relay.options.authority.durableResult = () => new Promise(resolve => { release = resolve; });
  const first = f.relay.acceptEvent(event("IMPLEMENT", "first"));
  await new Promise(resolve => setImmediate(resolve));
  await f.relay.acceptEvent(event("IMPLEMENT", "second"));
  release("VERIFY"); await first;
  assert.deepEqual(f.launches, []); assert.deepEqual(f.transitions, ["VERIFY"]);
});

test("exact webhook during failed-invocation recovery prevents successor after missing read", async t => {
  const f = failedInvocationSubject(t);
  let release;
  f.relay.options.authority.durableResult = () => new Promise(resolve => { release = resolve; });
  const first = f.relay.acceptEvent(event("IMPLEMENT"));
  await new Promise(resolve => setImmediate(resolve));
  await f.relay.acceptEvent(resultEvent({ invocationId: f.invocationId }));
  release(null); await first;
  assert.deepEqual(f.launches, []); assert.deepEqual(f.transitions, ["VERIFY"]);
});

test("a prior failed-invocation result cannot satisfy a newer failed successor", async t => {
  const f = failedInvocationSubject(t);
  await f.relay.acceptEvent(event("IMPLEMENT", "successor"));
  const newer = [...f.relay.active.values()][0];
  f.comments.push({ body: `<!-- B-DISP: INVOCATION=${f.invocationId} RESULT=VERIFY -->`, user: { login: "producer-bot" } });
  f.children[0].exitCode = 0; f.children[0].emit("close", 0);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(f.relay.state().diagnostics[f.lane].invocationId, newer.invocationId);
  await f.relay.acceptEvent(event("IMPLEMENT", "next-event"));
  assert.deepEqual(f.transitions, []); assert.deepEqual(f.launches, ["PRODUCER", "PRODUCER"]);
});

test("failed recovery transition preserves exact invocation for a later bounded event", async t => {
  const f = failedInvocationSubject(t);
  f.comments.push({ body: `<!-- B-DISP: INVOCATION=${f.invocationId} RESULT=VERIFY -->`, user: { login: "producer-bot" } });
  f.relay.options.authority.transition = async () => { throw new Error("mutation failed"); };
  await f.relay.acceptEvent(event("IMPLEMENT"));
  assert.deepEqual(f.launches, []);
  assert.equal(f.relay.state().diagnostics[f.lane].outcome, "COMPLETION_ERROR");
  f.relay.options.authority.transition = async (_item, target) => f.transitions.push(target);
  await f.relay.acceptEvent(event("IMPLEMENT", "later"));
  assert.deepEqual(f.launches, []); assert.deepEqual(f.transitions, ["VERIFY"]);
});


test("startup reuses its successful active-invocation read without a second API request", async t => {
  const f = failedInvocationSubject(t);
  const state = f.relay.state();
  state.active[f.lane] = state.diagnostics[f.lane]; delete state.diagnostics[f.lane];
  f.relay.save(state);
  let reads = 0;
  f.relay.options.authority.durableResult = async () => {
    if (++reads > 1) throw new Error("unexpected second API read");
    return null;
  };
  await f.relay.startupReconcile();
  assert.deepEqual(f.launches, ["PRODUCER"]);
  assert.equal(reads, 1);
  assert.equal(f.relay.events.filter(e => e.outcome === "DURABLE_RESULT_MISSING").length, 1);
});

test("stop during failed-invocation read prevents routing or successor launch", async t => {
  const f = failedInvocationSubject(t);
  let release;
  f.relay.options.authority.durableResult = () => new Promise(resolve => { release = resolve; });
  const starting = f.relay.start(f.item, "PRODUCER", "IMPLEMENT");
  f.relay.stop(); release("VERIFY"); await starting;
  assert.deepEqual(f.transitions, []); assert.deepEqual(f.launches, []);
  assert.equal(f.relay.state().diagnostics[f.lane].outcome, "COMPLETION_ERROR");
});

test("execution disabled preserves documented result routing while suppressing worker launch", async t => {
  const f = failedInvocationSubject(t);
  f.relay.options.executionEnabled = false;
  f.comments.push({ body: `<!-- B-DISP: INVOCATION=${f.invocationId} RESULT=VERIFY -->`, user: { login: "producer-bot" } });
  await f.relay.startupReconcile();
  assert.deepEqual(f.transitions, ["VERIFY"]); assert.deepEqual(f.launches, []);
});


for (const itemId of [900001, "PVTI_verified"]) {
  for (const result of ["VERIFY", "ACCEPT", "REJECT", "FOUNDER_EXCEPTION"]) {
    test(`synthetic Project item resolves persisted ${itemId} before ${result} and retains canonical identity`, async t => {
      const f = projectIdentitySubject(t);
      const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId };
      const role = result === "VERIFY" ? "PRODUCER" : "VERIFIER";
      const lane = f.relay.lane(item, role), invocationId = `${lane}:legacy`;
      writeFileSync(f.statePath, JSON.stringify({ deliveries: {}, active: { [lane]: { item, role, invocationId, startedAt: "2026-09-01T00:00:00Z", pid: 1001 } } }));
      await f.relay.acceptEvent(resultEvent({ invocationId, result, login: role === "PRODUCER" ? "producer-bot" : "verifier-bot" }));
      assert.equal(f.relay.state().active[lane].item.itemId, "PVTI_verified");
      assert.equal(f.relay.state().active[lane].result, result);
      assert.equal(f.relay.state().diagnostics[lane].item.itemId, "PVTI_verified");
      assert.deepEqual(f.mutations, result === "FOUNDER_EXCEPTION" ? [] : [{ itemId: "PVTI_verified", optionId: result === "VERIFY" ? "verify-option" : result === "ACCEPT" ? "accept-option" : "implement-option" }]);
      assert.equal(f.lookups(), 1);
      assert.deepEqual(f.launches, []);
    });
  }
}

for (const nodeId of [undefined, "PVTI_verified", "PVTI_wrong"]) {
  test(`synthetic Project item webhook numeric id with node_id ${nodeId} uses verified identity`, async t => {
    const f = projectIdentitySubject(t);
    const received = event("VERIFY");
    received.payload.projects_v2_item = { id: 900001, content_node_id: "I_303", ...(nodeId ? { node_id: nodeId } : {}) };
    if (nodeId === "PVTI_wrong") {
      await assert.rejects(f.relay.acceptEvent(received));
      assert.deepEqual(f.launches, []);
      assert.deepEqual(f.relay.state().active, {});
    } else {
      await f.relay.acceptEvent(received);
      assert.deepEqual(f.launches, ["VERIFIER"]);
      assert.equal(f.relay.state().active["ExampleOrg/sample-project#303:VERIFIER"].item.itemId, "PVTI_verified");
    }
    assert.deepEqual(f.mutations, []);
  });
}

for (const result of ["ACCEPT", "REJECT", "FOUNDER_EXCEPTION"]) {
  for (const itemId of [900002, "PVTI_wrong"]) {
    test(`synthetic Project item unresolved ${itemId} ${result} preserves failed recovery and blocks successor`, async t => {
      const f = projectIdentitySubject(t);
      const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId };
      const lane = f.relay.lane(item, "VERIFIER"), invocationId = `${lane}:unresolved`;
      writeFileSync(f.statePath, JSON.stringify({ deliveries: {}, active: {}, diagnostics: { [lane]: { item, role: "VERIFIER", invocationId, startedAt: "2026-09-01T00:00:00Z", outcome: "COMPLETION_ERROR" } } }));
      f.comments.push({ body: `<!-- B-DISP: INVOCATION=${invocationId} RESULT=${result} -->`, user: { login: "verifier-bot" }, created_at: "2026-09-01T00:01:00Z" });
      await assert.rejects(f.relay.acceptEvent(resultEvent({ invocationId, result, login: "verifier-bot" })));
      assert.equal(f.relay.state().diagnostics[lane].outcome, "COMPLETION_ERROR");
      assert.equal(f.relay.state().diagnostics[lane].item.itemId, itemId);
      assert.equal(f.relay.state().active[lane], undefined);
      await f.relay.start(item, "VERIFIER", "VERIFY");
      assert.deepEqual(f.mutations, []);
      assert.deepEqual(f.launches, []);
      assert.equal(f.relay.state().diagnostics[lane].result, undefined);
    });
  }
}

test("synthetic Project item membership transport failure preserves ambiguous completion and blocks successor", async t => {
  const f = projectIdentitySubject(t, { failLookup: true });
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: 900001 };
  const lane = f.relay.lane(item, "VERIFIER"), invocationId = `${lane}:lookup-failed`;
  writeFileSync(f.statePath, JSON.stringify({ deliveries: {}, active: {}, diagnostics: { [lane]: { item, role: "VERIFIER", invocationId, startedAt: "2026-09-01T00:00:00Z", outcome: "COMPLETION_ERROR" } } }));
  f.comments.push({ body: `<!-- B-DISP: INVOCATION=${invocationId} RESULT=ACCEPT -->`, user: { login: "verifier-bot" }, created_at: "2026-09-01T00:01:00Z" });
  await f.relay.start(item, "VERIFIER", "VERIFY");
  assert.equal(f.relay.state().diagnostics[lane].outcome, "COMPLETION_ERROR");
  assert.match(f.relay.state().diagnostics[lane].error, /membership lookup unavailable/);
  assert.equal(f.relay.state().diagnostics[lane].invocationId, invocationId);
  assert.equal(f.relay.state().active[lane], undefined);
  assert.deepEqual(f.mutations, []);
  assert.deepEqual(f.launches, []);
});

function projectIdentitySubject(t, { failLookup = false } = {}) {
  const fixture = subject();
  t.after(() => fixture.relay.stop());
  const mutations = [], comments = [];
  let lookups = 0;
  fixture.relay.options.authority = new GitHubAuthority({ workerLogins: { PRODUCER: "producer-bot", VERIFIER: "verifier-bot" }, owner: "ExampleOrg", projectNumber: 1, repository: "ExampleOrg/sample-project", gh: args => {
    if (args[1] === "repos/ExampleOrg/sample-project/issues/303/comments") return JSON.stringify(comments);
    assert.equal(args[1], "graphql");
    const query = args.find(value => value.startsWith("query="));
    if (query.includes("projectItems(")) {
      lookups++;
      if (failLookup) throw new Error("membership lookup unavailable");
      const issue = { number: 303, repository: { nameWithOwner: "ExampleOrg/sample-project" }, projectItems: { pageInfo: { hasNextPage: false }, nodes: [{ id: "PVTI_verified", databaseId: 900001, project: { number: 1, owner: { login: "ExampleOrg" } } }] } };
      return JSON.stringify({ data: query.includes("node(id:") ? { node: issue } : { repository: { issue } } });
    }
    if (query.includes("fieldValueByName")) {
      assert.ok(args.includes("id=PVTI_verified"));
      const claim = Object.values(fixture.relay.state().active)[0];
      return JSON.stringify({ data: { node: { id: "PVTI_verified", project: { number: 1, owner: { login: "ExampleOrg" } },
        content: { __typename: "Issue", number: 303, repository: { nameWithOwner: "ExampleOrg/sample-project" } },
        fieldValueByName: { name: claim.role === "VERIFIER" ? "VERIFY" : "IMPLEMENT" } } } });
    }
    if (query.includes("node(id:")) {
      assert.ok(args.includes("id=I_303"));
      return JSON.stringify({ data: { node: { number: 303, repository: { nameWithOwner: "ExampleOrg/sample-project" } } } });
    }
    if (query.includes("fields(first:")) return JSON.stringify({ data: { organization: { projectV2: { id: "PVT_project", fields: { pageInfo: { hasNextPage: false }, nodes: [{ id: "status-field", name: "Status", options: [{ id: "verify-option", name: "VERIFY" }, { id: "accept-option", name: "ACCEPT" }, { id: "implement-option", name: "IMPLEMENT" }] }] } } } } });
    if (query.includes("updateProjectV2ItemFieldValue")) {
      if (args.includes("itemId=900001")) throw new Error("GraphQL NOT_FOUND: Could not resolve to a node with the global id of '900001'");
      mutations.push({ itemId: args.find(value => value.startsWith("itemId=")).slice(7), optionId: args.find(value => value.startsWith("optionId=")).slice(9) });
      return JSON.stringify({ data: { updateProjectV2ItemFieldValue: { projectV2Item: { id: "PVTI_verified" } } } });
    }
    throw new Error("unexpected operation");
  } });
  return { ...fixture, mutations, comments, lookups: () => lookups };
}

// Closure tests exercise the real relay with external GitHub/process boundaries replaced.
function closureSubject(initialStatus = "ACCEPT") {
  const f = subject();
  f.relay.options.authorizedOperatorLogins = ["operator-user"];
  f.status = initialStatus;
  f.requests = [];
  f.relay.options.authority.currentStatus = async () => f.status;
  f.relay.options.authority.transition = async (_item, status) => { f.transitions.push(status); f.status = status; };
  f.relay.options.authority.listItems = async () => [{ repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: f.status }];
  f.relay.options.launch = request => { f.requests.push(request); f.launches.push(request.role); const c = child(); f.children.push(c); return c; };
  return f;
}
function closureComment(claim, signal, id = "closure-result") {
  const kind = signal === "RETURN_TO_IMPLEMENT" ? "CONTROL" : "RESULT";
  const received = resultEvent({ invocationId: claim.invocationId, id, body: `<!-- B-DISP: INVOCATION=${claim.invocationId} ${kind}=${signal} -->` });
  received.payload.comment.created_at = new Date().toISOString();
  received.payload.comment.id = 1234;
  return received;
}

for (const [phase, result, login] of [
  ["IMPLEMENT", "VERIFY", "producer-bot"], ["VERIFY", "ACCEPT", "verifier-bot"],
  ["VERIFY", "REJECT", "verifier-bot"], ["ACCEPT", "DONE", "producer-bot"],
  ["ACCEPT", "RETURN_TO_IMPLEMENT", "producer-bot"],
]) test(`stale ${phase}/${result} cannot change remote state or consume the result`, async () => {
  const f = closureSubject(phase);
  await f.relay.acceptEvent(event(phase));
  const claim = [...f.relay.active.values()][0];
  // Even a fresh result whose target happens to be current is not recovery.
  f.status = result === "VERIFY" ? "VERIFY" : result === "ACCEPT" ? "ACCEPT" : result === "DONE" ? "DONE" : "IMPLEMENT";
  const remote = f.status;
  const received = closureComment(claim, result);
  received.payload.comment.user.login = login;
  await f.relay.acceptEvent(received);
  assert.deepEqual(f.transitions, []);
  assert.equal(f.status, remote);
  const state = f.relay.state();
  assert.equal(state.active[claim.lane].result, undefined);
  assert.equal(state.active[claim.lane].control, undefined);
  assert.equal(state.active[claim.lane].pendingSignal, undefined);
  assert.equal(state.diagnostics[claim.lane].outcome, "STALE_RESULT");
  assert.equal(state.diagnostics[claim.lane].invocationId, claim.invocationId);
  assert.equal(state.diagnostics[claim.lane].observedStatus, remote);
  assert.equal(state.diagnostics[claim.lane].rejectedSignal, result);
  assert.equal(state.diagnostics[claim.lane].signalEvidence.commentId, 1234);
  f.relay.stop();
});

for (const sender of [{ type: "User", login: "outsider" }, { type: "User", login: "producer-bot" },
  { type: "Bot", login: "operator-user" }, { type: "User", login: "b-disp-example[bot]" }])
test(`operator recovery rejects ${sender.type}/${sender.login} and retains exception`, async () => {
  const f = closureSubject();
  f.relay.options.authorizedOperatorLogins = ["operator-user", "producer-bot", "b-disp-example[bot]"];
  f.relay.options.appIdentity = "b-disp-example[bot]";
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  await f.relay.acceptEvent(closureComment(claim, "FOUNDER_EXCEPTION"));
  await closeChild(f);
  const prior = f.relay.state().diagnostics[claim.lane];
  const received = event("ACCEPT", "unauthorized-recovery");
  received.payload.sender = sender;
  received.payload.changes.field_value.from = "TRIAGE";
  received.payload.projects_v2_item.updated_at = new Date(Date.parse(prior.at) + 2000).toISOString();
  await f.relay.acceptEvent(received);
  assert.equal(f.launches.length, 1);
  assert.deepEqual(f.relay.state().diagnostics[claim.lane], prior);
  assert.ok(f.relay.events.some(e => e.outcome === "UNAUTHORIZED_OPERATOR_RECOVERY"));
  f.relay.stop();
});

for (const [phase, result, login] of [["IMPLEMENT", "VERIFY", "producer-bot"], ["VERIFY", "REJECT", "verifier-bot"]])
test(`interrupted ${phase} mutation confirms target once without rewriting remote status`, async () => {
  const f = closureSubject(phase);
  await f.relay.acceptEvent(event(phase));
  const claim = [...f.relay.active.values()][0];
  const received = closureComment(claim, result);
  received.payload.comment.user.login = login;
  let writes = 0;
  f.relay.options.authority.transition = async (_item, target) => { writes++; f.status = target; throw new Error("response interrupted"); };
  await assert.rejects(f.relay.acceptEvent(received), /response interrupted/);
  assert.deepEqual(f.relay.state().active[claim.lane].pendingSignal, { value: result, target: f.status });
  f.relay.stop();
  const restarted = new EventRelay({ ...f.relay.options, isProcessAlive: () => false });
  await restarted.acceptEvent(received);
  assert.equal(writes, 1);
  assert.equal(restarted.state().active[claim.lane].result, result);
  restarted.stop();
});

for (const entry of ["exit", "inspection", "startup"]) test(`stale result from ${entry} retains evidence without remote mutation`, async () => {
  const f = closureSubject("IMPLEMENT");
  await f.relay.acceptEvent(event("IMPLEMENT"));
  const claim = [...f.relay.active.values()][0];
  f.status = "REVIEW";
  f.relay.options.authority.durableResult = async () => ({ value: "VERIFY", evidence: { commentId: 5678, author: "producer-bot" } });
  let relay = f.relay;
  if (entry === "exit") await closeChild(f);
  if (entry === "inspection") await relay.inspectLiveness(claim.invocationId);
  if (entry === "startup") {
    relay.stop();
    relay = new EventRelay({ ...relay.options, isProcessAlive: () => false });
    // Startup can still observe an earlier actionable item, but routing must recheck it.
    relay.options.authority.listItems = async () => [{ ...claim.item, status: "IMPLEMENT" }];
    await relay.startupReconcile();
  }
  assert.equal(f.status, "REVIEW");
  assert.deepEqual(f.transitions, []);
  assert.equal(relay.state().diagnostics[claim.lane].outcome, "STALE_RESULT");
  assert.equal(relay.state().diagnostics[claim.lane].signalEvidence.commentId, 5678);
  relay.stop();
});

test("unavailable current status fails without persisting mutation intent or changing remote state", async () => {
  const f = closureSubject("IMPLEMENT");
  await f.relay.acceptEvent(event("IMPLEMENT"));
  const claim = [...f.relay.active.values()][0];
  f.relay.options.authority.currentStatus = async () => { throw new Error("current status unavailable"); };
  await assert.rejects(f.relay.acceptEvent(closureComment(claim, "VERIFY")), /current status unavailable/);
  assert.deepEqual(f.transitions, []);
  assert.equal(f.relay.state().active[claim.lane].pendingSignal, undefined);
  f.relay.stop();
});

for (const storage of ["active", "diagnostics"]) for (const [phase, result, login] of [
  ["IMPLEMENT", "VERIFY", "producer-bot"], ["VERIFY", "REJECT", "verifier-bot"], ["VERIFY", "ACCEPT", "verifier-bot"],
]) test(`startup reconciles interrupted ${phase}/${result} from ${storage} before admitting target phase`, async () => {
  const f = closureSubject(phase);
  await f.relay.acceptEvent(event(phase));
  const claim = [...f.relay.active.values()][0];
  const received = closureComment(claim, result); received.payload.comment.user.login = login;
  let writes = 0;
  f.relay.options.authority.transition = async (_item, target) => { writes++; f.status = target; throw new Error("response interrupted"); };
  await assert.rejects(f.relay.acceptEvent(received), /response interrupted/);
  if (storage === "diagnostics") {
    const state = f.relay.state();
    state.diagnostics = { [claim.lane]: { ...state.active[claim.lane], outcome: "COMPLETION_ERROR" } };
    delete state.active[claim.lane]; f.relay.save(state);
  }
  f.relay.stop();
  const restarted = new EventRelay({ ...f.relay.options, isProcessAlive: () => false });
  await restarted.startupReconcile();
  assert.equal(writes, 1);
  assert.equal(restarted.state().active[claim.lane], undefined);
  assert.equal(restarted.state().diagnostics[claim.lane].outcome, `${result}_TO_${f.status}`);
  assert.equal(f.launches.length, 2);
  assert.equal(f.launches[1], f.status === "VERIFY" ? "VERIFIER" : "PRODUCER");
  restarted.stop();
});
async function closeChild(f, index = 0) {
  const active = [...f.relay.active.values()].find(value => value.child === f.children[index]);
  f.children[index].exitCode = 0;
  await f.relay.complete(active);
}

test("ACCEPT launches bounded Producer closure and cannot imply DONE", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  assert.deepEqual(f.launches, ["PRODUCER"]);
  assert.equal(f.status, "ACCEPT");
  assert.deepEqual(f.transitions, []);
  const request = f.requests[0];
  assert.match(request.bootstrap, /post-ACCEPT closure/);
  assert.match(request.bootstrap, /RESULT=DONE/);
  assert.match(request.bootstrap, /CONTROL=RETURN_TO_IMPLEMENT/);
  assert.doesNotMatch(request.bootstrap, /RESULT=VERIFY/);
});

for (const remaining of ["none", "authorized landing and operational verification"]) test(`closure dispositions ${remaining} then durable DONE transitions once`, async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  assert.ok(claim, "Producer closure must launch");
  const result = closureComment(claim, "DONE");
  result.payload.comment.body += `\nClosure evidence: ${remaining}; all required work complete or unnecessary.`;
  await f.relay.acceptEvent(result);
  await f.relay.acceptEvent(closureComment(claim, "DONE", "replay"));
  await closeChild(f);
  await f.relay.acceptEvent(event("ACCEPT", "stale-accept"));
  assert.equal(f.status, "DONE");
  assert.deepEqual(f.transitions, ["DONE"]);
  assert.deepEqual(f.launches, ["PRODUCER"]);
  assert.equal(f.relay.state().closures[claim.invocationId].result, "DONE");
});

test("closure Founder exception keeps ACCEPT and survives restart without relaunch", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  assert.ok(claim);
  await f.relay.acceptEvent(closureComment(claim, "FOUNDER_EXCEPTION"));
  await closeChild(f);
  const restarted = new EventRelay(f.relay.options);
  await restarted.startupReconcile();
  assert.equal(f.status, "ACCEPT");
  assert.deepEqual(f.transitions, []);
  assert.deepEqual(f.launches, ["PRODUCER"]);
  assert.equal(restarted.state().closures[claim.invocationId].result, "FOUNDER_EXCEPTION");
});

test("material-change control preserves evidence and hands off only after the closure child exits", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  assert.ok(claim);
  await f.relay.acceptEvent(closureComment(claim, "RETURN_TO_IMPLEMENT"));
  await f.relay.acceptEvent(event("IMPLEMENT", "handoff-webhook"));
  assert.deepEqual(f.launches, ["PRODUCER"]);
  assert.equal(f.status, "IMPLEMENT");
  await closeChild(f);
  assert.deepEqual(f.launches, ["PRODUCER", "PRODUCER"]);
  assert.match(f.requests[1].bootstrap, /RESULT=VERIFY/);
  assert.doesNotMatch(f.requests[1].bootstrap, /RESULT=DONE/);
  const evidence = f.relay.state().closures[claim.invocationId];
  assert.equal(evidence.control, "RETURN_TO_IMPLEMENT");
  assert.equal(evidence.result, undefined);
  await f.relay.acceptEvent(closureComment(claim, "RETURN_TO_IMPLEMENT", "old-control"));
  assert.deepEqual(f.transitions, ["IMPLEMENT"]);
  const implement = [...f.relay.active.values()][0];
  await f.relay.acceptEvent(resultEvent({ invocationId: implement.invocationId, id: "reworked", result: "VERIFY" }));
  await closeChild(f, 1);
  await f.relay.acceptEvent(event("VERIFY", "review-rework"));
  assert.deepEqual(f.launches, ["PRODUCER", "PRODUCER", "VERIFIER"]);
});

test("invalid closure controls and terminal combinations cannot mutate status", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  assert.ok(claim);
  const invalid = [
    resultEvent({ invocationId: claim.invocationId, result: "VERIFY", id: "verify" }),
    resultEvent({ invocationId: claim.invocationId, result: "RETURN_TO_IMPLEMENT", id: "terminal-control" }),
    closureComment({ ...claim, invocationId: "stale" }, "RETURN_TO_IMPLEMENT", "stale"),
    resultEvent({ invocationId: claim.invocationId, login: "verifier-bot", result: "DONE", id: "wrong-author" }),
    resultEvent({ invocationId: claim.invocationId, issue: 304, result: "DONE", id: "wrong-issue" }),
    resultEvent({ invocationId: claim.invocationId, repository: "else/repo", result: "DONE", id: "wrong-repo" }),
    resultEvent({ invocationId: claim.invocationId, id: "mixed", body: `<!-- B-DISP: INVOCATION=${claim.invocationId} RESULT=DONE -->\n<!-- B-DISP: INVOCATION=${claim.invocationId} CONTROL=RETURN_TO_IMPLEMENT -->` }),
  ];
  const staleTime = closureComment(claim, "RETURN_TO_IMPLEMENT", "stale-time");
  staleTime.payload.comment.created_at = "2000-01-01T00:00:00Z";
  invalid.push(staleTime);
  for (const received of invalid) await f.relay.acceptEvent(received);
  assert.deepEqual(f.transitions, []);
});

for (const signal of ["DONE", "RETURN_TO_IMPLEMENT"]) for (const afterMutation of [false, true]) test(`restart recovers ${signal} ${afterMutation ? "after" : "before"} status mutation exactly once`, async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  assert.ok(claim);
  const transition = f.relay.options.authority.transition;
  f.relay.options.authority.transition = async (item, status) => {
    if (afterMutation) await transition(item, status);
    throw new Error("interrupted routing");
  };
  await assert.rejects(f.relay.acceptEvent(closureComment(claim, signal)), /interrupted routing/);
  f.relay.stop();
  f.relay.options.authority.transition = transition;
  f.relay.options.isProcessAlive = () => false;
  f.relay.options.authority.durableResult = async () => signal;
  const restarted = new EventRelay(f.relay.options);
  await restarted.startupReconcile();
  await restarted.acceptEvent(closureComment(claim, signal, "replayed-after-restart"));
  assert.deepEqual(f.transitions, [signal === "DONE" ? "DONE" : "IMPLEMENT"]);
  assert.ok(restarted.state().closures[claim.invocationId]);
  assert.equal(f.launches.length, signal === "DONE" ? 1 : 2);
  restarted.stop();
});

test("startup recovers a surviving closure without a duplicate worker", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  assert.equal(f.launches.length, 1);
  f.relay.stop();
  f.relay.options.isProcessAlive = () => true;
  const restarted = new EventRelay(f.relay.options);
  await restarted.startupReconcile();
  assert.equal(f.launches.length, 1);
  assert.equal(restarted.events.at(-1).outcome, "SURVIVING_INVOCATION_EXISTS");
});

test("ACCEPT received while implementation still exits is resumed without another status event", async () => {
  const f = closureSubject("IMPLEMENT");
  await f.relay.acceptEvent(event("IMPLEMENT"));
  const claim = [...f.relay.active.values()][0];
  await f.relay.acceptEvent(resultEvent({ invocationId: claim.invocationId }));
  f.status = "ACCEPT";
  await f.relay.acceptEvent(event("ACCEPT", "accepted-while-exiting"));
  assert.deepEqual(f.launches, ["PRODUCER"]);
  await closeChild(f);
  assert.deepEqual(f.launches, ["PRODUCER", "PRODUCER"]);
  assert.match(f.requests[1].bootstrap, /post-ACCEPT closure/);
});

test("Issue closure event cannot change Project status", async () => {
  const f = closureSubject();
  const response = await f.relay.acceptEvent({ headers: { "x-github-event": "issues", "x-github-delivery": "issue-closed" }, payload: { action: "closed", issue: { number: 303 } } });
  assert.equal(response.accepted, false);
  assert.deepEqual(f.transitions, []);
  assert.deepEqual(f.launches, []);
});

for (const path of ["late comment", "Status recovery"]) test(`closure material handoff from ${path} resumes engineering despite an early status webhook`, async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  await closeChild(f);
  const transition = f.relay.options.authority.transition;
  f.relay.options.authority.transition = async (item, status) => {
    await transition(item, status);
    await f.relay.acceptEvent(event(status, "early-status"));
  };
  if (path === "late comment") await f.relay.acceptEvent(closureComment(claim, "RETURN_TO_IMPLEMENT"));
  else {
    f.relay.options.authority.durableResult = async () => "RETURN_TO_IMPLEMENT";
    await f.relay.acceptEvent(event("ACCEPT", "recover-exit"));
  }
  assert.deepEqual(f.transitions, ["IMPLEMENT"]);
  assert.equal(f.launches.length, 2);
  assert.match(f.requests[1].bootstrap, /RESULT=VERIFY/);
});

for (const mode of ["explicit", "bot", "stale", "missing-time", "preflight-failed"]) test(`Founder exception re-admission ${mode} preserves history and respects authority`, async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  await f.relay.acceptEvent(closureComment(claim, "FOUNDER_EXCEPTION"));
  await closeChild(f);
  const prior = f.relay.state().diagnostics[claim.lane];
  const received = event("ACCEPT", "operator-transition");
  received.payload.sender = { type: mode === "bot" ? "Bot" : "User", login: mode === "bot" ? "b-disp-example[bot]" : "operator-user" };
  received.payload.projects_v2_item.updated_at = mode === "stale" ? "2000-01-01T00:00:00Z" : new Date(Date.parse(prior.at) + 2000).toISOString();
  if (mode === "missing-time") delete received.payload.projects_v2_item.updated_at;
  received.payload.changes.field_value.from = "TRIAGE";
  if (mode === "preflight-failed") f.relay.options.preflight = async () => ({ ok: false });
  await f.relay.acceptEvent(received);
  assert.equal(f.launches.length, mode === "explicit" ? 2 : 1);
  if (mode === "explicit") {
    assert.notEqual(f.requests[1].invocationId, claim.invocationId);
    assert.deepEqual(f.relay.state().founderExceptions[claim.invocationId], prior);
  }
  assert.deepEqual(f.relay.state().diagnostics[claim.lane], prior);
});

test("surviving closure hands off when its PID exits after the restart webhook", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  await f.relay.acceptEvent(closureComment(claim, "RETURN_TO_IMPLEMENT"));
  f.relay.stop();
  let alive = true, nextTimer;
  const restarted = new EventRelay({ ...f.relay.options, isProcessAlive: () => alive,
    setTimeout: fn => { nextTimer = fn; return 1; }, clearTimeout: () => {} });
  await restarted.startupReconcile();
  await restarted.acceptEvent(event("IMPLEMENT", "survivor-handoff"));
  assert.equal(f.launches.length, 1);
  assert.equal(typeof nextTimer, "function", "existing invocation inspection must observe recovered closure exit");
  alive = false;
  await nextTimer();
  assert.equal(f.launches.length, 2);
  assert.match(f.requests[1].bootstrap, /RESULT=VERIFY/);
  assert.deepEqual(f.transitions, ["IMPLEMENT"]);
  restarted.stop();
});

test("Founder stop survives interruption before diagnostic persistence", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  f.relay.diagnostic = () => { throw new Error("diagnostic interruption"); };
  await assert.rejects(f.relay.acceptEvent(closureComment(claim, "FOUNDER_EXCEPTION")), /diagnostic interruption/);
  f.relay.stop();
  const restarted = new EventRelay({ ...f.relay.options, isProcessAlive: () => false });
  await restarted.startupReconcile();
  await restarted.acceptEvent(event("ACCEPT", "automatic-after-crash"));
  assert.equal(f.launches.length, 1);
  assert.equal(restarted.state().diagnostics[claim.lane].outcome, "FOUNDER_EXCEPTION");
});

test("Founder stop remains authoritative when live status changed during closure", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  f.status = "IMPLEMENT";
  await f.relay.acceptEvent(event("IMPLEMENT", "changed-during-closure"));
  await f.relay.acceptEvent(closureComment(claim, "FOUNDER_EXCEPTION"));
  await closeChild(f);
  assert.equal(f.launches.length, 1);
  assert.equal(f.relay.state().diagnostics[claim.lane].outcome, "FOUNDER_EXCEPTION");
});

test("startup isolates an unavailable closure item while recovering other accepted work", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  f.relay.stop();
  f.relay.options.authority.durableResult = async request => { if (request.item.issue === 303) throw new Error("temporary GitHub read failure"); return null; };
  f.relay.options.authority.listItems = async () => [303, 304].map(issue => ({ repository: "ExampleOrg/sample-project", issue, itemId: "PVT_1", status: "ACCEPT" }));
  const restarted = new EventRelay({ ...f.relay.options, isProcessAlive: () => false });
  await restarted.startupReconcile();
  assert.equal(f.requests.at(-1).item.issue, 304);
  assert.equal(restarted.state().active[claim.lane].invocationId, claim.invocationId);
  assert.equal(restarted.state().diagnostics[claim.lane].outcome, "COMPLETION_ERROR");
  restarted.stop();
});

test("committed ledger append repairs a failed projection without repeating the save", () => {
  const f = subject();
  f.relay.save({ deliveries: {}, active: {}, proof: "previous" });
  f.relay.ledger.hooks.beforeProjection = () => { throw new Error("ENOSPC"); };
  assert.throws(() => f.relay.save({ deliveries: {}, active: {}, proof: "next" }), /ENOSPC/);
  assert.equal(JSON.parse(readFileSync(f.statePath, "utf8")).proof, "previous");
  delete f.relay.ledger.hooks.beforeProjection;
  assert.equal(f.relay.state().proof, "next");
  assert.equal(JSON.parse(readFileSync(f.statePath, "utf8")).proof, "next");
});

test("ledger genesis marks unknown history and each save commits the complete post-state", () => {
  const f = subject();
  const first = f.relay.state();
  assert.deepEqual(first, { deliveries: {}, active: {} });
  const lane = "ExampleOrg/sample-project#303:PRODUCER";
  f.relay.save({ ...first, deliveries: { d1: { state: "PROCESSED" } },
    active: { [lane]: { invocationId: "one" } }, resources: { one: { path: "/tmp/one" } },
    executionLimits: { "ExampleOrg/sample-project#303": { cycle: 1 } } });
  const records = readFileSync(f.relay.ledger.path, "utf8").trim().split("\n").map(JSON.parse);
  assert.deepEqual(records.map(record => record.sequence), [0, 1]);
  assert.equal(records[0].historyBeforeGenesis, "UNKNOWN");
  assert.equal(records[1].previousDigest, records[0].digest);
  assert.equal(records[1].state.resources.one.path, "/tmp/one");
  assert.equal(records[1].state.executionLimits["ExampleOrg/sample-project#303"].cycle, 1);
  assert.deepEqual(records[1].changedLanes, [lane]);
  assert.equal(records[1].occurrences[0].id, `${records[1].revision}:1:0`);
  const restarted = new EventRelay(f.relay.options);
  assert.deepEqual(restarted.state(), records[1].state);
  assert.equal(readFileSync(f.relay.ledger.path, "utf8").trim().split("\n").length, 2);
});

test("before-append failure admits no new record, projection, or worker effect", async () => {
  const f = subject();
  f.relay.state();
  f.relay.ledger.hooks.beforeAppend = () => { throw new Error("ENOSPC"); };
  await assert.rejects(f.relay.acceptEvent(event("IMPLEMENT")), /ENOSPC/);
  delete f.relay.ledger.hooks.beforeAppend;
  assert.deepEqual(f.launches, []);
  const records = readFileSync(f.relay.ledger.path, "utf8").trim().split("\n");
  assert.equal(records.length, 1);
  assert.deepEqual(f.relay.state().active, {});
});

for (const mutation of ["partial", "sequence", "digest", "fork", "whole-record-truncation"]) {
  test(`ledger ${mutation} refuses startup before Project read or worker effect`, async () => {
    const f = subject();
    f.relay.save({ deliveries: {}, active: {}, proof: "durable" });
    const lines = readFileSync(f.relay.ledger.path, "utf8").trim().split("\n");
    if (mutation === "partial") appendFileSync(f.relay.ledger.path, "{partial");
    else if (mutation === "whole-record-truncation") writeFileSync(f.relay.ledger.path, `${lines[0]}\n`);
    else {
      const record = JSON.parse(lines[1]);
      if (mutation === "sequence") record.sequence = 7;
      if (mutation === "digest") record.state.proof = "forged";
      if (mutation === "fork") record.previousDigest = "wrong";
      writeFileSync(f.relay.ledger.path, `${lines[0]}\n${JSON.stringify(record)}\n`);
    }
    let reads = 0;
    f.relay.options.authority.listItems = async () => { reads++; return []; };
    await assert.rejects(f.relay.startupReconcile(), /LEDGER_/);
    assert.equal(reads, 0); assert.deepEqual(f.launches, []);
  });
}

test("a second process cannot become the ledger writer while the first is live", () => {
  const f = subject(); f.relay.state();
  const script = `import { NodeStateLedger } from ${JSON.stringify(new URL("../src/runtime/node-state-ledger.mjs", import.meta.url).href)}; new NodeStateLedger(process.argv[1]).read();`;
  const child = spawnSync(process.execPath, ["--input-type=module", "-e", script, f.statePath], { encoding: "utf8" });
  assert.notEqual(child.status, 0);
  assert.match(child.stderr, /LEDGER_WRITER_BUSY/);
});

test("committed append before head or projection survives replay with one sequence", () => {
  const f = subject(); f.relay.state();
  f.relay.ledger.hooks.afterAppend = () => { throw new Error("INTERRUPTED_AFTER_APPEND"); };
  assert.throws(() => f.relay.save({ deliveries: {}, active: {}, proof: "committed" }), /INTERRUPTED_AFTER_APPEND/);
  delete f.relay.ledger.hooks.afterAppend;
  const recovered = new EventRelay(f.relay.options);
  assert.equal(recovered.state().proof, "committed");
  assert.equal(readFileSync(f.relay.ledger.path, "utf8").trim().split("\n").length, 2);
  assert.equal(JSON.parse(readFileSync(f.statePath, "utf8")).proof, "committed");
});

test("projection before acknowledgement retains the one committed occurrence", () => {
  const f = subject(); f.relay.state();
  f.relay.ledger.hooks.afterProjection = () => { throw new Error("ACK_LOST"); };
  assert.throws(() => f.relay.save({ deliveries: {}, active: {}, proof: "committed" }), /ACK_LOST/);
  delete f.relay.ledger.hooks.afterProjection;
  assert.equal(f.relay.state().proof, "committed");
  assert.equal(readFileSync(f.relay.ledger.path, "utf8").trim().split("\n").length, 2);
});

test("missing source with an existing head fences startup and launch", async () => {
  const f = subject(); f.relay.state();
  const { rmSync } = await import("node:fs");
  rmSync(f.relay.ledger.path);
  let reads = 0;
  f.relay.options.authority.listItems = async () => { reads++; return []; };
  await assert.rejects(f.relay.startupReconcile(), /LEDGER_TRUNCATED/);
  assert.equal(reads, 0); assert.deepEqual(f.launches, []);
});

test("a forked head witness refuses replay even when the JSONL body is intact", async () => {
  const f = subject(); f.relay.save({ deliveries: {}, active: {}, proof: "durable" });
  const head = JSON.parse(readFileSync(f.relay.ledger.headPath, "utf8"));
  head.digest = "0".repeat(64);
  writeFileSync(f.relay.ledger.headPath, `${JSON.stringify(head)}\n`);
  await assert.rejects(f.relay.startupReconcile(), /LEDGER_TRUNCATED_OR_FORKED/);
  assert.deepEqual(f.launches, []);
});

test("interrupted replay keeps effects fenced until the committed projection is repaired", async () => {
  const f = subject(); f.relay.save({ deliveries: {}, active: {}, proof: "durable" });
  writeFileSync(f.statePath, "{partial");
  f.relay.ledger.hooks.beforeProjection = () => { throw new Error("REPLAY_INTERRUPTED"); };
  let reads = 0;
  f.relay.options.authority.listItems = async () => { reads++; return []; };
  await assert.rejects(f.relay.startupReconcile(), /REPLAY_INTERRUPTED/);
  assert.equal(reads, 0); assert.deepEqual(f.launches, []);
  delete f.relay.ledger.hooks.beforeProjection;
  const restarted = new EventRelay(f.relay.options);
  assert.equal(restarted.state().proof, "durable");
  assert.equal(readFileSync(f.relay.ledger.path, "utf8").trim().split("\n").length, 2);
});

test("Founder re-admission compares GitHub event time to GitHub signal time despite local skew", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  f.relay.options.now = () => Date.now() + 86400000;
  const stop = closureComment(claim, "FOUNDER_EXCEPTION");
  await f.relay.acceptEvent(stop);
  await closeChild(f);
  const received = event("ACCEPT", "operator-after-remote-stop");
  received.payload.sender = { type: "User", login: "operator-user" };
  received.payload.changes.field_value.from = "TRIAGE";
  received.payload.projects_v2_item.updated_at = new Date(Date.parse(stop.payload.comment.created_at) + 2000).toISOString();
  await f.relay.acceptEvent(received);
  assert.equal(f.launches.length, 2);
});

test("later operator re-admission received before stopped worker exit needs no second transition", async () => {
  const f = closureSubject();
  await f.relay.acceptEvent(event("ACCEPT"));
  const claim = [...f.relay.active.values()][0];
  const stop = closureComment(claim, "FOUNDER_EXCEPTION");
  await f.relay.acceptEvent(stop);
  const received = event("ACCEPT", "operator-before-exit");
  received.payload.sender = { type: "User", login: "operator-user" };
  received.payload.changes.field_value.from = "TRIAGE";
  received.payload.projects_v2_item.updated_at = new Date(Date.parse(stop.payload.comment.created_at) + 2000).toISOString();
  await f.relay.acceptEvent(received);
  assert.equal(f.launches.length, 1);
  await closeChild(f);
  assert.equal(f.launches.length, 2);
  assert.notEqual(f.requests[1].invocationId, claim.invocationId);
});

for (const status of ["CAPTURE", "SPECIFY", "PLAN", "TASKS", "READY", "REVIEW", "DONE", "MERGE"]) {
  test(`lifecycle ${status} never dispatches through webhook or startup`, async () => {
    let preflights = 0, enrichments = 0;
    const { relay, launches, transitions } = subject({ preflight: async () => { preflights++; return { ok: true }; } });
    relay.options.authority.enrichContentNode = async () => { enrichments++; return null; };
    relay.options.authority.listItems = async () => [{ repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVTI_1", status }];
    try {
      assert.equal((await relay.acceptEvent(event(status))).reason, "IRRELEVANT");
      await relay.startupReconcile();
      assert.deepEqual(launches, []);
      assert.deepEqual(transitions, []);
      assert.deepEqual(relay.state().active, {});
      assert.equal(preflights, 0);
      assert.equal(enrichments, 0);
    } finally { relay.stop(); }
  });
}

test("third-cycle verifier rejection holds the BIU before a fourth IMPLEMENT transition", async () => {
  let status = "IMPLEMENT";
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1" };
  const f = subject({ biuLimits: { "ExampleOrg/sample-project#303": { maxCycles: 3, maxReplacementsPerPhase: 1 } } });
  f.relay.options.authority.currentStatus = async () => status;
  f.relay.options.authority.transition = async (_item, target) => { f.transitions.push(target); status = target; };
  let relay = f.relay;
  async function runPhase(role, result) {
    assert.equal(await relay.start(item, role, status), true);
    const claim = [...relay.active.values()][0];
    assert.equal(await relay.routeResult(claim, result), true);
    claim.child.exitCode = 0;
    await relay.complete(claim);
  }
  for (let cycle = 1; cycle <= 3; cycle++) {
    await runPhase("PRODUCER", "VERIFY");
    if (cycle < 3) await runPhase("VERIFIER", "REJECT");
    if (cycle === 2) { relay.stop(); relay = new EventRelay({ ...relay.options }); }
  }
  assert.equal(await relay.start(item, "VERIFIER", status), true);
  const verifier = [...relay.active.values()][0];
  assert.equal(await relay.routeResult(verifier, "REJECT"), false);
  assert.equal(status, "VERIFY");
  assert.deepEqual(f.transitions, ["VERIFY", "IMPLEMENT", "VERIFY", "IMPLEMENT", "VERIFY"]);
  assert.equal(relay.state().executionLimits["ExampleOrg/sample-project#303"].cycle, 3);
  assert.equal(relay.state().diagnostics[verifier.lane].outcome, "EXECUTION_CYCLE_LIMIT");
  assert.equal(relay.state().diagnostics[verifier.lane].rejectedSignal, "REJECT");
  relay.stop();
});

test("one same-phase replacement survives restart; repeated liveness and delivery cannot grant another", async () => {
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1" };
  const f = subject({ isProcessAlive: () => false, biuLimits: { "ExampleOrg/sample-project#303": { maxCycles: 3, maxReplacementsPerPhase: 1 } } });
  assert.equal(await f.relay.start(item, "PRODUCER", "IMPLEMENT"), true);
  let claim = [...f.relay.active.values()][0];
  claim.child.exitCode = 124;
  await f.relay.complete(claim);
  assert.equal(await f.relay.start(item, "PRODUCER", "IMPLEMENT"), true);
  claim = [...f.relay.active.values()][0];
  claim.child.exitCode = 124;
  await f.relay.complete(claim);
  const restarted = new EventRelay({ ...f.relay.options });
  assert.equal(await restarted.start(item, "PRODUCER", "IMPLEMENT"), false);
  assert.equal(await restarted.inspectLiveness(claim.invocationId), "PROCESS_GONE");
  await restarted.acceptEvent(event("IMPLEMENT", "repeat-after-restart"));
  assert.deepEqual(f.launches, ["PRODUCER", "PRODUCER"]);
  assert.equal(restarted.state().executionLimits["ExampleOrg/sample-project#303"].cycle, 1);
  assert.equal(restarted.state().limitEscalations["ExampleOrg/sample-project#303"].outcome, "PHASE_REPLACEMENT_LIMIT");
  assert.equal(await restarted.start({ ...item, issue: 304 }, "PRODUCER", "IMPLEMENT"), true);
  assert.deepEqual(f.launches, ["PRODUCER", "PRODUCER", "PRODUCER"]);
  f.relay.stop(); restarted.stop();
});

test("persisted cycle-limit escalation fences verifier admission through direct, event and startup paths", async () => {
  const item = { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1", status: "VERIFY" };
  const key = "ExampleOrg/sample-project#303";
  const f = subject({ biuLimits: { [key]: { maxCycles: 3, maxReplacementsPerPhase: 1 } } });
  f.relay.save({ deliveries: {}, active: {}, executionLimits: {
    [key]: { cycle: 3, phase: "VERIFY", phaseInvocations: ["held-verifier"] },
  }, limitEscalations: { [key]: { biu: key, outcome: "EXECUTION_CYCLE_LIMIT", cycle: 3, rejectedSignal: "REJECT" } } });
  f.relay.options.authority.listItems = async () => [item];
  const restarted = new EventRelay({ ...f.relay.options });
  assert.equal(await restarted.start(item, "VERIFIER", "VERIFY"), false);
  const lane = restarted.lane(item, "VERIFIER");
  const claim = { item, lane, role: "VERIFIER", status: "VERIFY", invocationId: "held-verifier", startedAt: "2026-09-23T00:00:00.000Z" };
  const persisted = restarted.state(); persisted.active[lane] = claim; restarted.save(persisted);
  assert.equal(await restarted.routeResult(claim, "ACCEPT"), false);
  assert.deepEqual(f.transitions, []);
  const cleared = restarted.state(); delete cleared.active[lane]; restarted.save(cleared);
  await restarted.acceptEvent(event("VERIFY", "held-event"));
  await restarted.startupReconcile();
  assert.deepEqual(f.launches, []);
  assert.equal(restarted.state().executionLimits[key].cycle, 3);
  assert.equal(await restarted.start({ ...item, issue: 304 }, "VERIFIER", "VERIFY"), true);
  assert.deepEqual(f.launches, ["VERIFIER"]);
  restarted.stop();
});

// An ordinary Issue comment is not a worker result. Emitting INVALID_RESULT_COMMENT
// for every comment that is not one turned routine authorized Director comments
// into apparent worker-result errors (AlienLogicLab/alienintent#83). A comment
// only claims to signal when it carries a B-DISP marker.
test("an ordinary operator comment is not reported as an invalid worker result", async () => {
  const { relay } = subject();
  await relay.acceptEvent(resultEvent({ body: "Program Director recovery: resume closure under the approved activation.", login: "sanookdu", id: "operator-comment" }));
  assert.equal(relay.events.some(e => e.outcome === "INVALID_RESULT_COMMENT"), false);
  assert.equal(relay.events.at(-1).outcome, "NON_RESULT_COMMENT");
});

test("a result marker that fails validation is still reported as an invalid worker result", async () => {
  const { relay } = subject();
  await relay.acceptEvent(resultEvent({ invocationId: "no-such-invocation", id: "unmatched-marker" }));
  assert.equal(relay.events.at(-1).outcome, "INVALID_RESULT_COMMENT");
});

test("a worker comment carrying a marker from the wrong author is still reported", async () => {
  const { relay } = subject();
  await relay.acceptEvent(event("IMPLEMENT", "start-for-author-check"));
  const invocationId = Object.values(relay.state().active)[0].invocationId;
  await relay.acceptEvent(resultEvent({ invocationId, login: "someone-else", id: "wrong-author-marker" }));
  assert.equal(relay.events.some(e => e.outcome === "INVALID_RESULT_COMMENT"), true);
});

// AlienIntent does not use pull requests: PRs are for humans, the factory is for models.
// SWF-19 fixes the canonical closure landing as "a normal merge preserving the accepted
// candidate SHA". Wave 1 landed exactly that way ("Merge accepted PY-02 candidate (Issue
// #50)"). Wave 2 workers read the ambiguous "account for landing/merge" as permission to
// open pull requests (#70, #73, #77, #84). The instruction has to name the mechanism.
test("closure instructions name the merge landing mechanism and forbid pull requests", async () => {
  const { relay, launches } = subject({ launch: (options) => { launches.push(options.bootstrap); return child(); } });
  relay.options.authority.currentStatus = async () => "ACCEPT";
  await relay.acceptEvent(event("ACCEPT", "closure-landing"));
  const bootstrap = launches.at(-1);
  assert.match(bootstrap, /merge/i);
  assert.match(bootstrap, /accepted candidate/i);
  assert.match(bootstrap, /do not open (a )?pull request/i);
});

test("implementation instructions also forbid opening pull requests", async () => {
  const { relay, launches } = subject({ launch: (options) => { launches.push(options.bootstrap); return child(); } });
  await relay.acceptEvent(event("IMPLEMENT", "implement-no-pr"));
  assert.match(launches.at(-1), /do not open (a )?pull request/i);
});

// Adversarial review finding 1: a comment that *attempts* a B-DISP result but malforms it
// was downgraded to NON_RESULT_COMMENT, so a broken worker result looked like chat and
// bypassed identity-mismatch reporting. Classification must key on the attempt, not on a
// successful parse.
test("a truncated result marker is still reported as an invalid worker result", async () => {
  const { relay } = subject();
  await relay.acceptEvent(event("IMPLEMENT", "start-truncated"));
  const invocationId = Object.values(relay.state().active)[0].invocationId;
  await relay.acceptEvent(resultEvent({ body: `<!-- B-DISP: INVOCATION=${invocationId} RESULT=VERIFY`, id: "truncated-marker" }));
  assert.equal(relay.events.at(-1).outcome, "INVALID_RESULT_COMMENT");
});

test("two result markers in one comment are reported as invalid, not routine", async () => {
  const { relay } = subject();
  await relay.acceptEvent(event("IMPLEMENT", "start-double"));
  const invocationId = Object.values(relay.state().active)[0].invocationId;
  const marker = `<!-- B-DISP: INVOCATION=${invocationId} RESULT=VERIFY -->`;
  await relay.acceptEvent(resultEvent({ body: `${marker}\n${marker}`, id: "double-marker" }));
  assert.equal(relay.events.at(-1).outcome, "INVALID_RESULT_COMMENT");
});

test("an unknown B-DISP directive is reported as invalid rather than ignored", async () => {
  const { relay } = subject();
  await relay.acceptEvent(resultEvent({ body: "<!-- B-DISP: INVOCATION=x RESULT=BANANA -->", id: "bogus-directive" }));
  assert.equal(relay.events.at(-1).outcome, "INVALID_RESULT_COMMENT");
});

// Lifecycle refill and the control tick: a Project board fake whose Status the dispatcher moves.
const REPO = "ExampleOrg/sample-project";
function boardSubject({ board, eligible, ...overrides } = {}) {
  const items = new Map(board.map(entry => [entry.issue, { repository: REPO, itemId: `PVTI_${entry.issue}`, ...entry }]));
  const asked = [];
  const fixture = subject({ authority: {
    listItems: async () => [...items.values()].map(item => ({ ...item })),
    resolveItem: async item => ({ repository: item.repository, issue: item.issue, itemId: item.itemId }),
    currentStatus: async item => items.get(item.issue).status,
    transition: async (item, status) => { fixture.transitions.push(`${item.issue}:${status}`); items.get(item.issue).status = status; },
    enrichContentNode: async (_content, itemId) => { const item = [...items.values()].find(value => value.itemId === itemId); return item && { repository: REPO, issue: item.issue, itemId }; },
    durableResult: async () => null,
  }, eligibility: async request => { asked.push([request.item.issue, request.activeClaims]); return eligible(request); }, ...overrides });
  return { ...fixture, items, asked };
}
// The gate's typed result for one BIU: `failures` are check names; capacity checks are the gate's own.
const capacity = new Set(["status_ready", "no_active_invocation", "wip_limit_known", "wip_capacity_known", "wip_capacity_available"]);
function gate({ agentReady = "READY", checks = [] } = {}) {
  const failures = checks.map(check => ({ check, why: check }));
  return { agentReady, prepared: failures.every(failure => capacity.has(failure.check)), admitted: failures.length === 0, failures };
}
// A gate over structured facts: READY receipt, WIP limit, per-Issue refusals and Project status.
function facts({ wipLimit = 1, agentReady = {}, refuse = {} } = {}) {
  return ({ item, activeClaims }) => gate({ agentReady: agentReady[item.issue] ?? "READY", checks: [
    ...(item.status === "READY" ? [] : ["status_ready"]), ...(agentReady[item.issue] && agentReady[item.issue] !== "READY" ? ["agent_ready"] : []),
    ...(refuse[item.issue] ?? []), ...(activeClaims >= wipLimit ? ["wip_capacity_available"] : [])] });
}
const settle = () => new Promise(resolve => setTimeout(resolve, 20));
const liveLane = (issue, pid, role = "PRODUCER", status = "IMPLEMENT") => ({ [`${REPO}#${issue}:${role}`]: {
  invocationId: `inv-${issue}`, item: { repository: REPO, issue, itemId: `PVTI_${issue}` }, role, status, startedAt: "2026-09-25T00:00:00.000Z", pid } });

test("(1) a TASKS BIU with a READY receipt and satisfied prerequisites becomes READY, then IMPLEMENT", async () => {
  const { relay, transitions, launches } = boardSubject({ eligible: facts(), board: [{ issue: 147, status: "TASKS", priority: "P1" }] });
  await relay.requestRefill();
  assert.deepEqual(transitions, ["147:READY", "147:IMPLEMENT"]);
  assert.deepEqual(launches, ["PRODUCER"]);
  assert.deepEqual(relay.events.filter(event => /PREPARED|ADMITTED/.test(event.outcome)).map(event => event.outcome), ["TASKS_PREPARED", "READY_ADMITTED"]);
});

test("(1) HOLD, CLARIFY and SPLIT receipts are never READY supply and record no refusal", async () => {
  const { relay, transitions } = boardSubject({ eligible: facts({ agentReady: { 401: "HOLD", 402: "CLARIFY", 403: "SPLIT" } }),
    board: [{ issue: 401, status: "TASKS" }, { issue: 402, status: "TASKS" }, { issue: 403, status: "TASKS" }] });
  await relay.requestRefill();
  assert.deepEqual(transitions, []);
  assert.equal(relay.state().admissionRefusals, undefined);
});

test("(1) prepared supply advances to READY even while WIP is full; admission waits for capacity", async () => {
  const { relay, statePath, transitions, launches } = boardSubject({ isProcessAlive: pid => pid === 4455, eligible: facts(),
    board: [{ issue: 138, status: "IMPLEMENT" }, { issue: 147, status: "TASKS", priority: "P0" }] });
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: liveLane(138, 4455) }));
  await relay.requestRefill();
  assert.deepEqual(transitions, ["147:READY"]);
  assert.deepEqual(launches, []);
  assert.deepEqual(relay.state().admissionRefusals[`${REPO}#147`], { issue: 147, status: "READY", checks: ["wip_capacity_available"], at: relay.state().admissionRefusals[`${REPO}#147`].at });
});

test("(2)(3) READY refills WIP in priority order: P0 before P1, then lower Issue number", async () => {
  const { relay, asked, transitions, launches } = boardSubject({ eligible: facts({ wipLimit: 1 }), board: [
    { issue: 310, status: "READY", priority: "P2" }, { issue: 312, status: "READY", priority: "P1" },
    { issue: 311, status: "READY", priority: "P1" }, { issue: 313, status: "READY" }, { issue: 309, status: "READY", priority: "P0" }] });
  await relay.requestRefill();
  assert.deepEqual(asked, [[309, 0], [311, 1]]);
  assert.deepEqual(transitions, ["309:IMPLEMENT"]);
  assert.deepEqual(launches, ["PRODUCER"]);
  assert.deepEqual(Object.values(relay.state().admissionRefusals).map(refusal => [refusal.issue, refusal.checks]).sort(),
    [[310, ["wip_capacity_available"]], [311, ["wip_capacity_available"]], [312, ["wip_capacity_available"]], [313, ["wip_capacity_available"]]]);
});

test("(3) a blocked higher-priority BIU keeps its typed checks while the next eligible BIU is admitted", async () => {
  const { relay, transitions } = boardSubject({ eligible: facts({ wipLimit: 2, refuse: { 320: ["dependencies_satisfied"] } }),
    board: [{ issue: 320, status: "READY", priority: "P0" }, { issue: 321, status: "READY", priority: "P3" }] });
  await relay.requestRefill();
  assert.deepEqual(transitions, ["321:IMPLEMENT"]);
  const refusal = relay.state().admissionRefusals[`${REPO}#320`];
  assert.deepEqual(refusal.checks, ["dependencies_satisfied"]);
  await relay.requestRefill();
  assert.equal(relay.state().admissionRefusals[`${REPO}#320`].at, refusal.at);
  assert.equal(relay.events.filter(event => event.outcome === "LIFECYCLE_REFUSED" && event.issue === 320).length, 1);
});

test("(9) unrelated runtime uncertainty never moves READY or IMPLEMENT backward", async () => {
  // A stale PROCESSING delivery, a dead RUNNING record of another BIU, an unreconciled priority
  // and a gate that cannot read GitHub: each is a typed refusal; nothing moves backward.
  const { relay, statePath, transitions } = boardSubject({ isProcessAlive: () => false,
    eligible: request => { if (request.item.issue === 126) throw new Error("gh: HTTP 502"); return facts({ refuse: { 125: ["priority_inheritance_reconciled"] } })(request); },
    board: [{ issue: 125, status: "READY", priority: "P0" }, { issue: 126, status: "READY", priority: "P1" },
      { issue: 127, status: "READY", priority: "P2" }, { issue: 147, status: "TASKS", priority: "P0" }] });
  writeFileSync(statePath, JSON.stringify({ deliveries: { "stuck-since-09-25": { state: "PROCESSING", at: "2026-09-25T00:00:00.000Z" } },
    active: liveLane(138, 9999) }));
  await relay.requestRefill();
  await relay.reconcile();
  assert.deepEqual(transitions, ["147:READY", "147:IMPLEMENT"]);
  const refusals = relay.state().admissionRefusals;
  assert.deepEqual(refusals[`${REPO}#125`].checks, ["priority_inheritance_reconciled"]);
  assert.deepEqual(refusals[`${REPO}#126`].checks, ["eligibility_unavailable"]);
  assert.deepEqual(refusals[`${REPO}#127`].checks, ["wip_capacity_available"]);
  for (const issue of [125, 126, 127]) assert.equal(await relay.options.authority.currentStatus({ issue }), "READY");
});

test("(10) restart with no active claim resumes eligible IMPLEMENT, VERIFY and ACCEPT work and READY supply", async () => {
  const { relay, transitions, launches } = boardSubject({ eligible: facts({ wipLimit: 4 }), board: [
    { issue: 501, status: "IMPLEMENT" }, { issue: 502, status: "VERIFY" }, { issue: 503, status: "ACCEPT" }, { issue: 504, status: "READY", priority: "P0" }] });
  await relay.startupReconcile();
  assert.deepEqual(launches, ["PRODUCER", "VERIFIER", "PRODUCER", "PRODUCER"]);
  assert.deepEqual(transitions, ["504:IMPLEMENT"]);
  relay.stop();
});

test("(7) restart where runtime and Project disagree converges: a dead IMPLEMENT claim on a TASKS/READY card is released", async () => {
  const { relay, statePath, transitions, launches } = boardSubject({ isProcessAlive: () => false, eligible: facts(),
    board: [{ issue: 125, status: "READY", priority: "P0" }, { issue: 147, status: "TASKS" }] });
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: { ...liveLane(125, 4455), ...liveLane(147, 4456) } }));
  await relay.startupReconcile();
  relay.stop();
  assert.deepEqual(relay.events.filter(event => event.outcome === "STALE_CLAIM_RELEASED").map(event => event.issue).sort(), [125, 147]);
  assert.deepEqual(transitions, ["125:IMPLEMENT", "147:READY"]);
  assert.deepEqual(Object.keys(relay.state().active), [`${REPO}#125:PRODUCER`]);
  assert.deepEqual(launches, ["PRODUCER"]);
});

test("(12) a live claim on a READY card is kept and counts against WIP; the card is not re-admitted", async () => {
  const { relay, statePath, asked, transitions } = boardSubject({ isProcessAlive: pid => pid === 4455, eligible: facts(),
    board: [{ issue: 340, status: "READY", priority: "P0" }, { issue: 341, status: "READY", priority: "P1" }] });
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: liveLane(340, 4455) }));
  await relay.reconcile();
  await relay.requestRefill();
  assert.deepEqual(asked, [[341, 1]]);
  assert.deepEqual(transitions, []);
  assert.ok(relay.state().active[`${REPO}#340:PRODUCER`]);
  assert.deepEqual(relay.state().admissionRefusals[`${REPO}#340`].checks, ["no_active_invocation"]);
});

test("(12) a persisted record whose worker is gone does not occupy WIP", async () => {
  const { relay, statePath, asked, transitions } = boardSubject({ isProcessAlive: () => false, eligible: facts(),
    board: [{ issue: 330, status: "READY", priority: "P1" }] });
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: liveLane(138, 4455) }));
  await relay.requestRefill();
  assert.deepEqual(asked, [[330, 0]]);
  assert.deepEqual(transitions, ["330:IMPLEMENT"]);
});

test("a halting refusal such as pause ends the pass without asking about lower-priority work", async () => {
  const { relay, asked, transitions } = boardSubject({ eligible: () => gate({ checks: ["factory_paused"] }),
    board: [{ issue: 350, status: "READY", priority: "P0" }, { issue: 351, status: "TASKS", priority: "P1" }] });
  await relay.requestRefill();
  assert.deepEqual(asked, [[350, 0]]);
  assert.deepEqual(transitions, []);
});

test("refill leaves a BIU another actor moved after the gate read it", async () => {
  const fixture = boardSubject({ eligible: () => { fixture.items.get(360).status = "IMPLEMENT"; return gate(); },
    board: [{ issue: 360, status: "READY", priority: "P0" }] });
  await fixture.relay.requestRefill();
  assert.deepEqual(fixture.transitions, []);
  assert.deepEqual(fixture.launches, []);
});

test("refill is inert without the eligibility gate or with execution disabled", async () => {
  for (const overrides of [{ eligibility: undefined }, { executionEnabled: false }]) {
    let listed = 0;
    const { relay, transitions } = boardSubject({ eligible: () => gate(), board: [{ issue: 370, status: "READY" }], ...overrides });
    relay.options.authority.listItems = async () => { listed++; return []; };
    await relay.requestRefill();
    assert.equal(listed, 0); assert.deepEqual(transitions, []);
  }
});

test("(11) duplicate refill requests, a replayed tick and the IMPLEMENT webhook echo launch exactly one worker", async () => {
  const { relay, transitions, launches } = boardSubject({ eligible: facts(), board: [{ issue: 303, status: "READY", priority: "P0" }] });
  await Promise.all([relay.requestRefill(), relay.requestRefill(), relay.requestRefill()]);
  await relay.acceptEvent({ ...event("IMPLEMENT", "refill-echo"), payload: { ...event("IMPLEMENT").payload, projects_v2_item: { id: "PVTI_303", content_node_id: "I_303" } } });
  await relay.acceptEvent({ ...event("IMPLEMENT", "refill-echo"), payload: { ...event("IMPLEMENT").payload, projects_v2_item: { id: "PVTI_303", content_node_id: "I_303" } } });
  await relay.reconcile();
  await relay.requestRefill();
  assert.deepEqual(transitions, ["303:IMPLEMENT"]);
  assert.deepEqual(launches, ["PRODUCER"]);
});

test("(4)(5)(6)(2) the full lifecycle runs to DONE and each terminal result refills the freed WIP slot", async () => {
  const results = new Map();
  const { relay, children, transitions, launches, items } = boardSubject({ eligible: facts({ wipLimit: 1 }),
    board: [{ issue: 601, status: "TASKS", priority: "P0" }, { issue: 602, status: "READY", priority: "P1" }] });
  relay.options.authority.durableResult = async claim => results.get(`${claim.item.issue}:${claim.role}:${claim.status}`) ?? null;
  await relay.requestRefill();
  assert.deepEqual(transitions, ["601:READY", "601:IMPLEMENT"]);
  // IMPLEMENT producer success with a candidate -> VERIFY, and the verifier starts on the Status webhook.
  results.set("601:PRODUCER:IMPLEMENT", "VERIFY"); children[0].emit("close", 0); await settle();
  assert.deepEqual(transitions.slice(2), ["601:VERIFY", "602:IMPLEMENT"]);
  await relay.acceptEvent({ ...event("VERIFY", "v-601"), payload: { ...event("VERIFY").payload, projects_v2_item: { id: "PVTI_601", content_node_id: "I_601" } } });
  // VERIFY ACCEPT -> ACCEPT, then closure DONE -> DONE.
  results.set("601:VERIFIER:VERIFY", "ACCEPT"); children[2].emit("close", 0); await settle();
  assert.equal(items.get(601).status, "ACCEPT");
  await relay.acceptEvent({ ...event("ACCEPT", "a-601"), payload: { ...event("ACCEPT").payload, projects_v2_item: { id: "PVTI_601", content_node_id: "I_601" } } });
  results.set("601:PRODUCER:ACCEPT", "DONE"); children[3].emit("close", 0); await settle();
  assert.equal(items.get(601).status, "DONE");
  assert.deepEqual(launches, ["PRODUCER", "PRODUCER", "VERIFIER", "PRODUCER"]);
  assert.deepEqual(Object.keys(relay.state().active), [`${REPO}#602:PRODUCER`]);
});

test("(7) verifier REJECT returns to IMPLEMENT within the configured cycle budget, then blocks typed", async () => {
  const { relay, children, transitions, launches, items } = boardSubject({ eligible: facts({ wipLimit: 1 }),
    biuLimits: { [`${REPO}#701`]: { maxCycles: 2, maxReplacementsPerPhase: 1 } },
    board: [{ issue: 701, status: "READY", priority: "P0" }] });
  let result = "VERIFY";
  relay.options.authority.durableResult = async () => result;
  const verifyEvent = id => ({ ...event("VERIFY", id), payload: { ...event("VERIFY").payload, projects_v2_item: { id: "PVTI_701", content_node_id: "I_701" } } });
  const implementEvent = id => ({ ...event("IMPLEMENT", id), payload: { ...event("IMPLEMENT").payload, projects_v2_item: { id: "PVTI_701", content_node_id: "I_701" } } });
  await relay.requestRefill();
  children.at(-1).emit("close", 0); await settle();
  await relay.acceptEvent(verifyEvent("v1")); result = "REJECT"; children.at(-1).emit("close", 0); await settle();
  assert.equal(items.get(701).status, "IMPLEMENT");
  await relay.acceptEvent(implementEvent("i2")); result = "VERIFY"; children.at(-1).emit("close", 0); await settle();
  await relay.acceptEvent(verifyEvent("v2")); result = "REJECT"; children.at(-1).emit("close", 0); await settle();
  // The second REJECT would start cycle 3 of 2: the lane is held as a typed technical blocker in VERIFY.
  assert.deepEqual(transitions, ["701:IMPLEMENT", "701:VERIFY", "701:IMPLEMENT", "701:VERIFY"]);
  assert.equal(items.get(701).status, "VERIFY");
  assert.equal(relay.state().limitEscalations[`${REPO}#701`].outcome, "EXECUTION_CYCLE_LIMIT");
  assert.equal(relay.state().founderExceptions, undefined);
  await relay.reconcile();
  assert.deepEqual(launches, ["PRODUCER", "VERIFIER", "PRODUCER", "VERIFIER"]);
  assert.deepEqual(transitions.filter(value => value.endsWith(":TASKS")), []);
});

test("(8) a failed preflight is a typed diagnostic the next control tick re-drives, never a Founder hold", async () => {
  let preflights = 0;
  const { relay, launches } = boardSubject({ eligible: facts(), board: [{ issue: 801, status: "IMPLEMENT" }],
    preflight: async () => (++preflights === 1 ? { ok: false, reason: "GITHUB_VERIFICATION_UNAVAILABLE" } : { ok: true }) });
  await relay.reconcile();
  assert.deepEqual(launches, []);
  const diagnostic = relay.state().diagnostics[`${REPO}#801:PRODUCER`];
  assert.equal(diagnostic.outcome, "PREFLIGHT_FAILED");
  assert.equal(diagnostic.reason, "GITHUB_VERIFICATION_UNAVAILABLE");
  assert.equal(relay.state().active[`${REPO}#801:PRODUCER`], undefined);
  await relay.reconcile();
  assert.deepEqual(launches, ["PRODUCER"]);
});

test("(10) a lost IMPLEMENT webhook and a worker that exited without a result are both re-driven by the tick", async () => {
  const timers = [];
  const { relay, statePath, launches } = boardSubject({ isProcessAlive: () => false, eligible: facts(), tickIntervalMs: 45000,
    setTimeout: (callback, ms) => { const timer = { callback, ms, cleared: false }; timers.push(timer); return timer; },
    clearTimeout: timer => { timer.cleared = true; },
    board: [{ issue: 901, status: "IMPLEMENT" }, { issue: 902, status: "VERIFY" }] });
  writeFileSync(statePath, JSON.stringify({ deliveries: {}, active: {}, diagnostics: { [`${REPO}#902:VERIFIER`]: {
    invocationId: "exited", item: { repository: REPO, issue: 902, itemId: "PVTI_902" }, role: "VERIFIER", status: "VERIFY", startedAt: "2026-09-25T00:00:00.000Z", outcome: "DURABLE_RESULT_MISSING" } } }));
  const ticks = () => timers.filter(timer => timer.ms === 45000);
  relay.started = true;
  relay.scheduleTick();
  assert.equal(ticks().length, 1);
  await ticks()[0].callback();
  assert.deepEqual(launches.sort(), ["PRODUCER", "VERIFIER"]);
  assert.equal(ticks().length, 2);
  relay.stop();
  assert.equal(ticks().at(-1).cleared, true);
});

test("(11)(12) the control tick leaves a lane this process owns to its owner: no re-read, no second worker", async () => {
  let reads = 0;
  const { relay, launches } = boardSubject({ eligible: facts(), board: [{ issue: 303, status: "IMPLEMENT" }] });
  relay.options.authority.durableResult = async () => { reads++; return null; };
  await relay.acceptEvent({ ...event("IMPLEMENT", "owned"), payload: { ...event("IMPLEMENT").payload, projects_v2_item: { id: "PVTI_303", content_node_id: "I_303" } } });
  const events = relay.events.length;
  await relay.reconcile();
  await relay.reconcile();
  assert.deepEqual(launches, ["PRODUCER"]);
  assert.equal(reads, 0);
  assert.deepEqual(relay.events.slice(events), []);
});
