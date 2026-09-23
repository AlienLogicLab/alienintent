import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
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



test("a reserved delivery blocks concurrent duplicate processing", async () => { let release; const blocked = new Promise((resolve) => { release = resolve; }); let enrichments = 0; const { relay, launches } = subject({ authority: { enrichContentNode: async () => { enrichments++; await blocked; return { repository: "ExampleOrg/sample-project", issue: 303, itemId: "PVT_1" }; }, durableResult: async () => null, transition: async () => {}, listItems: async () => [] } }); const first = relay.acceptEvent(event("IMPLEMENT", "same")); await new Promise((resolve) => setImmediate(resolve)); const duplicate = await relay.acceptEvent(event("IMPLEMENT", "same")); assert.equal(duplicate.duplicate, true); release(); await first; assert.equal(enrichments, 1); assert.deepEqual(launches, ["PRODUCER"]); });

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

test("failed state write leaves the previous complete snapshot readable", async () => {
  const f = subject();
  f.relay.save({ deliveries: {}, active: {}, proof: "previous" });
  const fs = (await import("node:fs")).default;
  const { syncBuiltinESMExports } = await import("node:module");
  const originalWrite = fs.writeFileSync;
  fs.writeFileSync = (path, ...args) => {
    if (String(path).startsWith(f.statePath)) { originalWrite(path, "{partial"); throw new Error("ENOSPC"); }
    return originalWrite(path, ...args);
  };
  syncBuiltinESMExports();
  try { assert.throws(() => f.relay.save({ deliveries: {}, active: {}, proof: "next" }), /ENOSPC/); }
  finally { fs.writeFileSync = originalWrite; syncBuiltinESMExports(); }
  assert.equal(f.relay.state().proof, "previous");
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
