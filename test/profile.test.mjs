import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadProfile } from "../src/config/profile.mjs";

function fixture() {
  const directory = mkdtempSync(join(tmpdir(), "b-disp-profile-"));
  const value = JSON.parse(readFileSync(new URL("../config/profile.example.json", import.meta.url)));
  value.webhook.secretFile = join(directory, "webhook-secret");
  writeFileSync(value.webhook.secretFile, "synthetic-secret\n");
  const path = join(directory, "profile.json");
  return { value, path, load() { writeFileSync(path, JSON.stringify(value)); return loadProfile(path); } };
}

test("profile wires all worker identities, paths, adapters and legacy role names", () => {
  const f = fixture();
  f.value.workers.PRODUCER.compatibility.persistedRoleValue = "MORTY";
  f.value.workers.VERIFIER.compatibility.persistedRoleValue = "JC";
  const c = f.load();
  assert.deepEqual(c.roleNames, { PRODUCER: "MORTY", VERIFIER: "JC" });
  assert.equal(c.workers.MORTY.adapter, "codex");
  assert.equal(c.workers.JC.adapter, "claude");
  assert.equal(c.workerLogins.MORTY, f.value.workers.PRODUCER.githubLogin);
  assert.equal(c.workers.JC.gitEmail, f.value.workers.VERIFIER.gitIdentity.email);
  assert.equal(c.workers.JC.environment.values.HOME, f.value.workers.VERIFIER.provider.authenticationProfile.homeDirectory);
  assert.equal(c.workers.JC.logDirectory, f.value.paths.workerLogDirectory);
  assert.equal(c.workers.JC.executables.githubCli, f.value.executables.githubCli);
  assert.equal(c.webhookSecret, "synthetic-secret");
  assert.deepEqual(c.authorizedOperatorLogins, f.value.operator.authorizedGithubLogins);
});

test("profile fails closed for ambiguous role/identity, unsupported workflow and unknown fields", () => {
  for (const mutate of [
    p => { p.workers.VERIFIER.githubLogin = p.workers.PRODUCER.githubLogin; },
    p => { p.workers.VERIFIER.compatibility.persistedRoleValue = "PRODUCER"; },
    p => { p.project.statusFieldName = "Custom"; },
    p => { p.project.statusNames.MERGE = "Merge"; },
    p => { p.operator.authorizedGithubLogins = [p.workers.PRODUCER.githubLogin]; },
    p => { p.project.owner = "DifferentOrg"; },
    p => { p.workers.PRODUCER.environment.values.GH_TOKEN = "must-not-leak"; },
    p => { p.workers.PRODUCER.worktreePath = "/outside/worktree"; },
    p => { p.execution.enabled = "true"; },
    p => { p.unknownPolicy = true; },
  ]) {
    const f = fixture(); mutate(f.value);
    assert.throws(() => f.load(), /AlienIntent: invalid/);
  }
});

test("dry-run profile needs no worker/preflight configuration but keeps App/target authority", () => {
  const f = fixture(); f.value.execution.enabled = false; f.value.workers = {};
  assert.deepEqual(f.load().workers, {});
  f.value.execution.enabled = true;
  assert.throws(() => f.load(), /workers/);
});

test("configuration and secret failures do not echo input contents", () => {
  const f = fixture();
  writeFileSync(f.path, '{"webhookSecret": FAKE_SECRET_SENTINEL}');
  assert.throws(() => loadProfile(f.path), error => !error.message.includes("FAKE_SECRET_SENTINEL"));
  f.value.webhook.secretFile = "/missing/synthetic-secret";
  assert.throws(() => f.load(), /webhook secret unavailable/);
});

test("profile rejects changed namespaces and identities before any state mutation", () => {
  const f = fixture();
  f.value.paths.stateFile = join(f.path, "..", "state.json");
  const invocationId = "ExampleOrg/sample-project#701:MORTY:legacy";
  const claim = { role: "MORTY", invocationId, workerLogin: "producer-bot",
    item: { repository: "ExampleOrg/sample-project", issue: 701 }, status: "IMPLEMENT" };
  const source = JSON.stringify({ deliveries: {}, active: { "ExampleOrg/sample-project#701:MORTY": claim } });
  writeFileSync(f.value.paths.stateFile, source);
  assert.throws(() => f.load(), /state compatibility/);
  assert.equal(readFileSync(f.value.paths.stateFile, "utf8"), source);
  f.value.workers.PRODUCER.compatibility.persistedRoleValue = "MORTY";
  assert.ok(f.load());
  f.value.workers.PRODUCER.githubLogin = "different-producer";
  assert.throws(() => f.load(), /state compatibility/);
  assert.equal(readFileSync(f.value.paths.stateFile, "utf8"), source);
});

test("legacy recovery diagnostics need exact operator identity evidence when author is absent", () => {
  const f = fixture();
  f.value.paths.stateFile = join(f.path, "..", "state.json");
  f.value.workers.PRODUCER.compatibility.persistedRoleValue = "MORTY";
  const invocationId = "ExampleOrg/sample-project#701:MORTY:legacy";
  const state = { deliveries: {}, active: {}, diagnostics: {
    "ExampleOrg/sample-project#701:MORTY": { role: "MORTY", invocationId,
      item: { repository: "ExampleOrg/sample-project", issue: 701 }, outcome: "DURABLE_RESULT_MISSING" },
  }, closures: { historical: { role: "OLD_ROLE", result: "DONE" } } };
  const source = JSON.stringify(state); writeFileSync(f.value.paths.stateFile, source);
  assert.throws(() => f.load(), /state compatibility/);
  f.value.workers.PRODUCER.compatibility.legacyInvocationIdentities = [
    { invocationId, githubLogin: "producer-bot", authority: "operator-approved migration handoff" },
  ];
  assert.ok(f.load());
  assert.equal(readFileSync(f.value.paths.stateFile, "utf8"), source);
  f.value.workers.PRODUCER.compatibility.legacyInvocationIdentities[0].githubLogin = "different-producer";
  assert.throws(() => f.load(), /state compatibility/);
});

test("minimal legacy claims derive optional identity fields from the lane without rewriting history", () => {
  const f = fixture();
  f.value.paths.stateFile = join(f.path, "..", "state.json");
  f.value.workers.PRODUCER.compatibility = { persistedRoleValue: "MORTY", legacyInvocationIdentities: [
    { invocationId: "legacy-invocation", githubLogin: "producer-bot", authority: "operator-approved migration handoff" },
  ] };
  const lane = "ExampleOrg/sample-project#701:MORTY";
  const claim = { invocationId: "legacy-invocation", startedAt: "2026-01-01T00:00:00.000Z", pid: 123 };
  const source = JSON.stringify({ active: { [lane]: claim } });
  writeFileSync(f.value.paths.stateFile, source);
  assert.ok(f.load());
  assert.equal(readFileSync(f.value.paths.stateFile, "utf8"), source);
  for (const [key, value] of [
    ["malformed-lane", claim], [lane, { ...claim, role: "VERIFIER" }],
    [lane, { ...claim, item: { repository: "OtherOrg/other-project", issue: 701 } }],
    [lane, { ...claim, item: { issue: 702 } }],
  ]) {
    const bytes = JSON.stringify({ active: { [key]: value } });
    writeFileSync(f.value.paths.stateFile, bytes);
    assert.throws(() => f.load(), /state compatibility/);
    assert.equal(readFileSync(f.value.paths.stateFile, "utf8"), bytes);
  }
});

test("execution profile requires canonical repository store and baseline without fixed worker checkouts", () => {
  const f = fixture();
  f.value.execution.enabled = true;
  f.value.paths.repositoryStore = "/srv/b-disp/repository.git";
  f.value.repository.baselineRef = "refs/remotes/origin/main";
  for (const worker of Object.values(f.value.workers)) delete worker.worktreePath;
  const config = f.load();
  assert.equal(config.repositoryStore, f.value.paths.repositoryStore);
  assert.equal(config.baselineRef, f.value.repository.baselineRef);
  assert.equal(config.worktreeRoot, f.value.paths.worktreeRoot);
  assert.equal(config.workers.PRODUCER.worktree, undefined);
  delete f.value.paths.repositoryStore;
  assert.throws(() => f.load(), /repositoryStore/);
  f.value.paths.repositoryStore = "/srv/b-disp/repository.git";
  delete f.value.repository.baselineRef;
  assert.throws(() => f.load(), /baselineRef/);
});
