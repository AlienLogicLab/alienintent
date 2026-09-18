import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { createWorkerLauncher, spawnWorker, workerLogPath, workerEnvironment } from "../src/runtime/worker-runner.mjs";
const fixture = (adapter) => ({ adapter, command: adapter, worktree: "/tmp", permissionMode: adapter === "claude" ? "manual" : "danger-full-access", fundingProfile: adapter === "claude" ? "claude-subscription" : "configured", ghConfigDir: `/tmp/${adapter}-config`, ghShimDir: `/tmp/b-disp-gh/${adapter === "claude" ? "verifier" : "producer"}`, runtimePath: "/usr/bin:/bin", executables: { githubCli: "/usr/bin/gh" } });
test("VERIFIER fails closed for API, unavailable, or unknown authentication before spawning", () => {
  for (const status of [{ loggedIn: true, authMethod: "api_key" }, { loggedIn: false }, { loggedIn: true, authMethod: "claude.ai", subscriptionType: null }]) {
    let launches = 0;
    assert.throws(() => spawnWorker({ logDirectory: mkdtempSync(join(tmpdir(), "b-disp-runner-test-")), role: "VERIFIER", worker: fixture("claude"), authenticate: () => status, execute: () => { launches++; return new EventEmitter(); } }), /CLAUDE_SUBSCRIPTION_AUTH_REQUIRED/);
    assert.equal(launches, 0);
  }
});
test("VERIFIER auth inspection and launch both receive the same API-free environment", () => {
  let inspected, launched;
  const child = new EventEmitter();
  spawnWorker({ logDirectory: mkdtempSync(join(tmpdir(), "b-disp-runner-test-")), role: "VERIFIER", worker: fixture("claude"),
    environment: { HOME: "/worker", ANTHROPIC_API_KEY: "payg", ANTHROPIC_AUTH_TOKEN: "payg", CLAUDE_CODE_USE_BEDROCK: "1", AWS_ACCESS_KEY_ID: "payg", GH_TOKEN: "wrong" },
    authenticate: (_command, options) => { inspected = options; return { loggedIn: true, authMethod: "claude.ai", subscriptionType: "max" }; },
    execute: (_command, _args, options) => { launched = options; return child; } });
  assert.deepEqual(inspected.env, launched.env);
  for (const key of ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "AWS_ACCESS_KEY_ID", "GH_TOKEN"]) assert.equal(launched.env[key], undefined);
});
test("runner returns a child for runtime close-event ownership", () => { const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter(); const got = spawnWorker({ logDirectory: mkdtempSync(join(tmpdir(), "b-disp-runner-test-")), authenticate: () => ({ loggedIn: true, authMethod: "claude.ai", subscriptionType: "max" }), role: "PRODUCER", worker: fixture("codex"), bootstrap: "work", execute: () => child }); assert.equal(got, child); });

test("Producer output is persisted under its exact invocation log identity", () => {
  const logDirectory = mkdtempSync(join(tmpdir(), "b-disp-worker-logs-"));
  const invocationId = "sample/widget#101:PRODUCER:founder exception";
  const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter();
  spawnWorker({ authenticate: () => ({ loggedIn: true, authMethod: "claude.ai", subscriptionType: "max" }), role: "PRODUCER", worker: fixture("codex"), invocationId, bootstrap: "work", logDirectory, execute: () => child });
  child.stdout.emit("data", "rationale on stdout\n"); child.stderr.emit("data", "rationale on stderr\n"); child.emit("close");
  assert.equal(readFileSync(workerLogPath(invocationId, logDirectory), "utf8"), "rationale on stdout\nrationale on stderr\n");
});

test("VERIFIER raw output remains available for invocation diagnosis", () => {
  const logDirectory = mkdtempSync(join(tmpdir(), "b-disp-worker-logs-"));
  const invocationId = "sample/widget#101:VERIFIER:current";
  const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter();
  spawnWorker({ authenticate: () => ({ loggedIn: true, authMethod: "claude.ai", subscriptionType: "max" }), role: "VERIFIER", worker: fixture("claude"), invocationId, bootstrap: "work", logDirectory, execute: () => child });
  child.stdout.emit("data", "progress\n"); child.stderr.emit("data", "warning\n"); child.stdout.emit("data", '{"total_cost_usd":0.125,"subtype":"end_turn"}\n'); child.emit("close");
  assert.equal(readFileSync(workerLogPath(invocationId, logDirectory), "utf8"), 'progress\nwarning\n{"total_cost_usd":0.125,"subtype":"end_turn"}\n');
});

test("worker log paths safely and distinctly encode exact invocation IDs", () => {
  const logDirectory = "/tmp/b-disp-worker-logs";
  const first = "sample/widget#101:PRODUCER:a/b";
  const second = "sample/widget#101:PRODUCER:a?b";
  const firstPath = workerLogPath(first, logDirectory);
  assert.equal(firstPath, join(logDirectory, "sample%2Fwidget%23101%3APRODUCER%3Aa%2Fb.log"));
  assert.ok(!firstPath.slice(logDirectory.length + 1).includes("/"));
  assert.notEqual(firstPath, workerLogPath(second, logDirectory));
});

test("launcher preserves item and invocation ID for the worker runner", () => {
  const item = { repository: "sample/widget", issue: 101 };
  const invocationId = "sample/widget#101:VERIFIER:current";
  let received;
  const launch = createWorkerLauncher({ workers: { VERIFIER: fixture("claude") }, runner: (input) => { received = input; return {}; } });
  launch({ role: "VERIFIER", item, invocationId, bootstrap: "bootstrap", worktree: "/tmp/invocation-specific" });
  assert.deepEqual(received, { role: "VERIFIER", worker: { ...fixture("claude"), worktree: "/tmp/invocation-specific" }, item, invocationId, bootstrap: "bootstrap" });
});

test("worker commands preserve only the current invocation bootstrap and identity-isolated environment", () => {
  const item = { repository: "sample/widget", issue: 101 };
  const currentInvocation = "sample/widget#101:PRODUCER:current";
  const oldInvocation = "sample/widget#101:PRODUCER:old";
  const captures = [];
  const execute = (command, args, options) => { captures.push({ command, args, options }); const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter(); return child; };
  const producerBootstrap = `Read AGENTS.md. Repository: ${item.repository}. GitHub Issue #${item.issue}. Invocation ID: ${currentInvocation}. Reconstruct task context from durable GitHub/repository state; complete the bounded assignment. Completion requires posting exactly one GitHub Issue comment: <!-- B-DISP: INVOCATION=${currentInvocation} RESULT=VERIFY --> or <!-- B-DISP: INVOCATION=${currentInvocation} RESULT=FOUNDER_EXCEPTION -->. stdout/chat is not a workflow result.`;
  const verifierInvocation = "sample/widget#101:VERIFIER:current";
  const verifierBootstrap = `Read AGENTS.md. Repository: ${item.repository}. GitHub Issue #${item.issue}. Invocation ID: ${verifierInvocation}. Independently reconstruct review context from durable GitHub/repository state. Completion requires posting exactly one GitHub Issue comment: <!-- B-DISP: INVOCATION=${verifierInvocation} RESULT=ACCEPT --> or <!-- B-DISP: INVOCATION=${verifierInvocation} RESULT=REJECT --> or <!-- B-DISP: INVOCATION=${verifierInvocation} RESULT=FOUNDER_EXCEPTION -->. stdout/chat is not a workflow result.`;
  spawnWorker({ logDirectory: mkdtempSync(join(tmpdir(), "b-disp-runner-test-")), authenticate: () => ({ loggedIn: true, authMethod: "claude.ai", subscriptionType: "max" }), role: "PRODUCER", worker: fixture("codex"), item, invocationId: currentInvocation, bootstrap: producerBootstrap, execute, environment: { HOME: "/worker", GH_TOKEN: "must-not-leak" } });
  spawnWorker({ logDirectory: mkdtempSync(join(tmpdir(), "b-disp-runner-test-")), authenticate: () => ({ loggedIn: true, authMethod: "claude.ai", subscriptionType: "max" }), role: "VERIFIER", worker: fixture("claude"), item, invocationId: verifierInvocation, bootstrap: verifierBootstrap, execute, environment: { HOME: "/worker", GH_TOKEN: "must-not-leak", ANTHROPIC_API_KEY: "must-not-leak" } });
  const producerCommand = captures[0].args.at(-1);
  const verifierCommand = captures[1].args.at(-1);
  assert.deepEqual(captures[0].args.slice(0, -1), ["exec", "--ephemeral", "--json", "--sandbox", "danger-full-access", "-C", "/tmp"]);
  assert.deepEqual(captures[1].args.slice(0, -1), ["-p", "--no-session-persistence", "--output-format", "json", "--permission-mode", "manual"]);
  assert.match(producerCommand, new RegExp(`INVOCATION=${currentInvocation.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")}`));
  assert.match(producerCommand, new RegExp(`<!-- B-DISP: INVOCATION=${currentInvocation.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=VERIFY -->`));
  assert.match(producerCommand, new RegExp(`<!-- B-DISP: INVOCATION=${currentInvocation.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=FOUNDER_EXCEPTION -->`));
  assert.doesNotMatch(producerCommand, new RegExp(oldInvocation));
  for (const result of ["ACCEPT", "REJECT", "FOUNDER_EXCEPTION"]) assert.match(verifierCommand, new RegExp(`<!-- B-DISP: INVOCATION=${verifierInvocation.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")} RESULT=${result} -->`));
  assert.match(producerCommand, /Repository: sample\/widget\. GitHub Issue #101\./);
  assert.equal(captures[0].options.env.GH_TOKEN, undefined);
  assert.equal(captures[1].options.env.GH_TOKEN, undefined);
  assert.equal(captures[1].options.env.ANTHROPIC_API_KEY, undefined);
  assert.equal(captures[1].options.env.HOME, "/worker");
  assert.match(captures[0].options.env.PATH, /b-disp-gh\/producer/);
  assert.match(captures[1].options.env.PATH, /b-disp-gh\/verifier/);
});

for (const stream of ["stdout", "stderr"]) test(`invocation log and ${stream} output are readable before child close`, () => {
  const logDirectory = mkdtempSync(join(tmpdir(), "b-disp-live-log-"));
  const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter();
  const invocationId = "sample/widget#102:PRODUCER:live";
  spawnWorker({ role: "PRODUCER", worker: fixture("codex"), invocationId, logDirectory, execute: () => child });
  const path = workerLogPath(invocationId, logDirectory);
  assert.ok(existsSync(path), "log exists while child is running");
  child[stream].emit("data", Buffer.from("already emitted\n"));
  assert.equal(readFileSync(path, "utf8"), "already emitted\n");
  child.emit("close", null, "SIGKILL");
  assert.equal(readFileSync(path, "utf8"), "already emitted\n");
});

test("interleaved live invocations retain isolated output even without a close event", () => {
  const logDirectory = mkdtempSync(join(tmpdir(), "b-disp-live-log-"));
  const children = [new EventEmitter(), new EventEmitter()];
  for (const [index, child] of children.entries()) {
    child.stdout = new EventEmitter(); child.stderr = new EventEmitter();
    spawnWorker({ role: "PRODUCER", worker: fixture("codex"), invocationId: `invocation-${index}`, logDirectory, execute: () => child });
  }
  children[0].stdout.emit("data", Buffer.from("first stdout\n"));
  children[1].stderr.emit("data", Buffer.from("second stderr\n"));
  children[0].stderr.emit("data", Buffer.from("first stderr\n"));
  assert.equal(readFileSync(workerLogPath("invocation-0", logDirectory), "utf8"), "first stdout\nfirst stderr\n");
  assert.equal(readFileSync(workerLogPath("invocation-1", logDirectory), "utf8"), "second stderr\n");
});


test("log creation failure prevents an unlogged worker launch", () => {
  const directory = mkdtempSync(join(tmpdir(), "b-disp-log-failure-"));
  const logDirectory = join(directory, "not-a-directory");
  writeFileSync(logDirectory, "occupied");
  let launches = 0;
  assert.throws(() => spawnWorker({ role: "PRODUCER", worker: fixture("codex"),
    invocationId: "synthetic-log-failure", logDirectory,
    execute: () => { launches++; return new EventEmitter(); } }));
  assert.equal(launches, 0);
});

test("provider selection follows adapter independently of functional role", () => {
  let args;
  spawnWorker({ role: "VERIFIER", worker: { ...fixture("codex"), logDirectory: mkdtempSync(join(tmpdir(), "b-disp-adapter-")) }, bootstrap: "bounded", invocationId: "adapter", execute: (_command, argv) => { args = argv; return new EventEmitter(); } });
  assert.equal(args[0], "exec");
});
test("non-subscription Claude profile does not impose subscription authentication", () => {
  spawnWorker({ role: "PRODUCER", worker: { ...fixture("claude"), fundingProfile: "provider-default", logDirectory: mkdtempSync(join(tmpdir(), "b-disp-adapter-")) }, bootstrap: "bounded", invocationId: "adapter", authenticate: () => { throw new Error("must not run"); }, execute: () => new EventEmitter() });
});
test("extra arguments cannot override invocation, permissions, worktree or output", () => {
  for (const adapter of ["claude", "codex"]) for (const args of [["--permission-mode", "bypassPermissions"], ["--sandbox", "read-only"], ["--resume", "old"], ["--model", "--json"], ["prompt"], ["-C", "/other"]]) {
    let launched = false;
    assert.throws(() => spawnWorker({ role: "PRODUCER", worker: { ...fixture(adapter), fundingProfile: "provider-default", arguments: args }, execute: () => { launched = true; } }), /UNSAFE_PROVIDER_ARGUMENTS/);
    assert.equal(launched, false);
  }
});
test("authentication home is explicit and ambient credential inheritance fails closed", () => {
  const worker = { ...fixture("claude"), environment: { values: { HOME: "/synthetic/auth-home" } } };
  assert.equal(workerEnvironment({ worker, environment: { HOME: "/ambient", GITHUB_TOKEN: "ambient", OPENAI_API_KEY: "ambient" } }).HOME, "/synthetic/auth-home");
  assert.throws(() => workerEnvironment({ worker: { ...worker, environment: { inheritNames: ["GITHUB_TOKEN"] } } }), /UNSAFE_INHERITED_ENVIRONMENT/);
  assert.throws(() => workerEnvironment({ worker: { ...worker, environment: { values: { GH_TOKEN: "injected" } } } }), /UNSAFE_WORKER_ENVIRONMENT/);
});

test("production launcher rejects missing assigned worktree instead of using role checkout", () => {
  let launched = false;
  const launch = createWorkerLauncher({ workers: { PRODUCER: fixture("codex") }, runner: () => { launched = true; } });
  for (const worktree of [undefined, "", "relative/path"]) assert.throws(() => launch({ role: "PRODUCER", worktree }), /INVOCATION_WORKTREE_REQUIRED/);
  assert.equal(launched, false);
});

test("assigned worktree reaches provider cwd and codex argv while authentication remains isolated", () => {
  const original = { ...fixture("codex"), logDirectory: mkdtempSync(join(tmpdir(), "b-disp-assigned-")) };
  let capture;
  const launch = createWorkerLauncher({ workers: { PRODUCER: original }, runner: input => spawnWorker({ ...input,
    environment: { GH_TOKEN: "ambient-secret", HOME: "/synthetic-home" },
    execute: (command, args, options) => { capture = { command, args, options }; return new EventEmitter(); } }) });
  launch({ role: "PRODUCER", invocationId: "assigned-test", bootstrap: "bounded", worktree: "/tmp/invocation-resource" });
  assert.equal(capture.options.cwd, "/tmp/invocation-resource");
  assert.equal(capture.args[capture.args.indexOf("-C") + 1], "/tmp/invocation-resource");
  assert.equal(capture.options.env.GH_TOKEN, undefined);
  assert.equal(capture.options.env.GH_CONFIG_DIR, original.ghConfigDir);
  assert.equal(original.worktree, "/tmp");
});
