import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { assertClaimTransferState, EventRelay } from "../src/runtime/dispatcher.mjs";

const invocationId = "AlienLogicLab/alienintent#149:PRODUCER:claim-1";
const lane = "AlienLogicLab/alienintent#149:PRODUCER";
const path = "/worktrees/resource-1";
const branch = "b-disp/resource-1";
const manager = { uid: 1000, bootId: "boot-1", startedAtMonotonic: "123", cgroup: "/user.slice/user-1000.slice/user@1000.service" };
const worktreeManager = { inspectOwnership: () => ({ invocationId, resourceId: "resource-1", path, branch, head: "a".repeat(40) }) };
const transferRelay = options => new EventRelay({ worktreeManager, ...options });

function fixture() {
  const request = { schemaVersion: 1, operationId: "operation-1", nextOwner: "director-episode-1",
    lane, invocationId, resourceId: "resource-1", path, branch,
    manager, unit: "worker.service", cgroup: "/user.slice/worker.service" };
  const state = { deliveries: {}, active: { [lane]: { invocationId, role: "PRODUCER", status: "IMPLEMENT",
    item: { repository: "AlienLogicLab/alienintent", issue: 149 }, worktree: path } },
  resources: { [invocationId]: { invocationId, resourceId: "resource-1", path, branch,
    role: "PRODUCER", repository: "AlienLogicLab/alienintent", issue: 149,
    lifecycle: "LAUNCHING", supervision: { mode: "systemd", invocationId,
      manager: { ...manager }, unit: "worker.service", cgroup: "/user.slice/worker.service" } } } };
  return { state, request };
}

test("transfer state preflight binds the exact processless supervised claim", () => {
  const { state, request } = fixture();
  assert.deepEqual(assertClaimTransferState(state, request), {
    lane, invocationId, resourceId: "resource-1", path, branch,
  });
  assert.equal(state.claimTransfers, undefined);
});

test("transfer state preflight refuses mismatched claim and resource identities", () => {
  const fields = ["lane", "invocationId", "resourceId", "path", "branch", "unit", "cgroup"];
  for (const field of fields) {
    const { state, request } = fixture();
    request[field] = "wrong";
    assert.throws(() => assertClaimTransferState(state, request), /CLAIM_TRANSFER_/, field);
  }
  for (const field of ["uid", "bootId", "startedAtMonotonic", "cgroup"]) {
    const { state, request } = fixture();
    request.manager = { ...manager, [field]: "wrong" };
    assert.throws(() => assertClaimTransferState(state, request), /CLAIM_TRANSFER_/, field);
  }
});

test("transfer state preflight refuses effects, conflicting owners and unresolved deliveries", () => {
  const cases = [
    state => { state.active[lane].result = "VERIFY"; },
    state => { state.resources[invocationId].lifecycle = "REMOVED"; },
    state => { state.resources[invocationId].exitedAt = "2026-09-29T00:00:00Z"; },
    state => { state.active.other = { invocationId, worktree: path }; },
    state => { state.deliveries.unresolved = { state: "PROCESSING" }; },
    state => { state.claimTransfers = { [lane]: { operationId: "prior", nextOwner: "other" } }; },
  ];
  for (const alter of cases) {
    const { state, request } = fixture();
    alter(state);
    assert.throws(() => assertClaimTransferState(state, request), /CLAIM_TRANSFER_/);
  }
});

test("transfer state preflight refuses incomplete operation and owner identity", () => {
  for (const field of ["operationId", "nextOwner", "schemaVersion"]) {
    const { state, request } = fixture();
    delete request[field];
    assert.throws(() => assertClaimTransferState(state, request), /CLAIM_TRANSFER_/, field);
  }
});

test("a committed transfer is read back and replays to the same opaque grant", () => {
  const { state, request } = fixture();
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-commit-")), "state.json");
  const proof = { digest: "a".repeat(64), observedAt: new Date().toISOString() };
  const relay = transferRelay({ statePath, claimTransferHostProof: () => proof });
  relay.save(state);
  request.expectedHead = relay.fence();

  const grant = relay.commitClaimTransfer(request);
  assert.match(grant.grantId, /^[a-f0-9-]{36}$/);
  assert.equal(grant.status, "COMMITTED");
  assert.deepEqual(grant.expectedHead, request.expectedHead);
  assert.deepEqual(grant.hostProof, proof);
  assert.equal(relay.state().active[lane].invocationId, invocationId);
  assert.deepEqual(relay.commitClaimTransfer(request), grant);
  assert.deepEqual(transferRelay({ statePath, claimTransferHostProof: () => proof }).commitClaimTransfer(request), grant);
});

test("transfer commit refuses missing proof, stale head and conflicting replay", () => {
  const { state, request } = fixture();
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-refuse-")), "state.json");
  const relay = transferRelay({ statePath });
  relay.save(state);
  request.expectedHead = relay.fence();
  assert.throws(() => relay.commitClaimTransfer(request), /CLAIM_TRANSFER_HOST_PROOF_REQUIRED/);
  assert.equal(relay.state().claimTransfers, undefined);

  const proven = transferRelay({ statePath, claimTransferHostProof: () =>
    ({ digest: "a".repeat(64), observedAt: new Date().toISOString() }) });
  const stale = { ...request, expectedHead: { ...request.expectedHead, sequence: request.expectedHead.sequence + 1 } };
  assert.throws(() => proven.commitClaimTransfer(stale), /LEDGER_EXPECTED_HEAD_CHANGED/);
  assert.equal(proven.state().claimTransfers, undefined);
  const grant = proven.commitClaimTransfer(request);
  assert.throws(() => proven.commitClaimTransfer({ ...request, nextOwner: "other" }), /CLAIM_TRANSFER_REPLAY_MISMATCH/);
  assert.throws(() => proven.commitClaimTransfer({ ...request, operationId: "other" }), /CLAIM_TRANSFER_REPLAY_MISMATCH/);
  assert.deepEqual(proven.state().claimTransfers[invocationId], grant);
});

test("transfer commit requires exact read-only worktree ownership inspection", () => {
  const { state, request } = fixture();
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-owner-")), "state.json");
  const proof = { digest: "d".repeat(64), observedAt: new Date().toISOString() };
  const relay = new EventRelay({ statePath, claimTransferHostProof: () => proof });
  relay.save(state); request.expectedHead = relay.fence();
  assert.throws(() => relay.commitClaimTransfer(request), /CLAIM_TRANSFER_WORKTREE_INSPECTION_REQUIRED/);
  assert.equal(relay.state().claimTransfers, undefined);

  const wrong = transferRelay({ statePath, claimTransferHostProof: () => proof,
    worktreeManager: { inspectOwnership: () => ({ invocationId, resourceId: "different",
      path, branch, head: "a".repeat(40) }) } });
  assert.throws(() => wrong.commitClaimTransfer(request), /CLAIM_TRANSFER_WORKTREE_MISMATCH/);
  assert.equal(wrong.state().claimTransfers, undefined);
});

test("an interrupted transfer append replays one committed grant after restart", () => {
  const { state, request } = fixture();
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-interrupt-")), "state.json");
  const proof = { digest: "b".repeat(64), observedAt: new Date().toISOString() };
  const hooks = {};
  const relay = transferRelay({ statePath, claimTransferHostProof: () => proof, ledgerHooks: hooks });
  relay.save(state);
  request.expectedHead = relay.fence();
  hooks.afterAppend = () => { throw new Error("INTERRUPTED_AFTER_APPEND"); };
  assert.throws(() => relay.commitClaimTransfer(request), /INTERRUPTED_AFTER_APPEND/);
  const resumed = transferRelay({ statePath, claimTransferHostProof: () => proof });
  const grant = resumed.commitClaimTransfer(request);
  assert.equal(grant.status, "COMMITTED");
  assert.equal(resumed.state().active[lane].invocationId, invocationId);
  assert.deepEqual(resumed.commitClaimTransfer(request), grant);
});

test("an interruption after projection returns the existing grant on replay", () => {
  const { state, request } = fixture();
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-projection-")), "state.json");
  const proof = { digest: "c".repeat(64), observedAt: new Date().toISOString() };
  const hooks = {};
  const relay = transferRelay({ statePath, claimTransferHostProof: () => proof, ledgerHooks: hooks });
  relay.save(state);
  request.expectedHead = relay.fence();
  hooks.afterProjection = () => { throw new Error("INTERRUPTED_AFTER_PROJECTION"); };
  assert.throws(() => relay.commitClaimTransfer(request), /INTERRUPTED_AFTER_PROJECTION/);
  const resumed = transferRelay({ statePath, claimTransferHostProof: () => proof });
  const grant = resumed.commitClaimTransfer(request);
  assert.equal(grant.status, "COMMITTED");
  assert.deepEqual(resumed.state().claimTransfers[invocationId], grant);
});

test("transfer commit refuses malformed host proof and another transfer record", () => {
  const { state, request } = fixture();
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-proof-")), "state.json");
  const relay = transferRelay({ statePath, claimTransferHostProof: () => ({ digest: "missing", observedAt: "bad" }) });
  relay.save(state);
  request.expectedHead = relay.fence();
  assert.throws(() => relay.commitClaimTransfer(request), /CLAIM_TRANSFER_HOST_PROOF_INVALID/);
  assert.equal(relay.state().claimTransfers, undefined);
  const stale = transferRelay({ statePath, claimTransferHostProof: () =>
    ({ digest: "a".repeat(64), observedAt: new Date(Date.now() - 60000).toISOString() }) });
  assert.throws(() => stale.commitClaimTransfer(request), /CLAIM_TRANSFER_HOST_PROOF_INVALID/);
  assert.equal(stale.state().claimTransfers, undefined);
  state.claimTransfers = { unrelated: { operationId: "another" } };
  relay.save(state);
  request.expectedHead = relay.fence();
  assert.throws(() => relay.commitClaimTransfer(request), /CLAIM_TRANSFER_TRANSFER_EXISTS/);
});

test("a transfer record prevents release of its original active claim", () => {
  const { state } = fixture();
  state.claimTransfers = { [invocationId]: { schemaVersion: 1, operationId: "operation-1",
    lane, invocationId, resourceId: "resource-1", path, branch, status: "COMMITTED" } };
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-release-")), "state.json");
  const relay = new EventRelay({ statePath });
  relay.save(state);

  assert.throws(() => relay.release({ ...state.active[lane], lane }), /CLAIM_TRANSFER_IN_PROGRESS/);
  assert.equal(relay.state().active[lane].invocationId, invocationId);
});

test("reconciliation retains a transferred resource after an interrupted claim projection", () => {
  const { state } = fixture();
  state.active = {};
  state.claimTransfers = { [invocationId]: { schemaVersion: 1, operationId: "operation-1",
    lane, invocationId, resourceId: "resource-1", path, branch, status: "COMMITTED" } };
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-cleanup-")), "state.json");
  const relay = new EventRelay({ statePath, launch: { observe: () => ({ terminal: true }) }, worktreeManager: {
    cleanup: resource => ({ ...resource, lifecycle: "REMOVED" }),
  } });
  relay.save(state);

  relay.reconcileResources();
  assert.equal(relay.state().resources[invocationId].lifecycle, "LAUNCHING");
});

test("a transfer record blocks a competing worker reservation after restart", async () => {
  const { state } = fixture();
  state.active = {};
  state.claimTransfers = { [invocationId]: { schemaVersion: 1, operationId: "operation-1",
    lane, invocationId, resourceId: "resource-1", path, branch, status: "COMMITTED" } };
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-start-")), "state.json");
  const relay = new EventRelay({ statePath, authority: { workerLogins: {} }, preflight: async () => ({ ok: false }) });
  relay.save(state);

  assert.equal(await relay.start({ repository: "AlienLogicLab/alienintent", issue: 149 }, "PRODUCER", "IMPLEMENT"), false);
  assert.deepEqual(relay.state().active, {});
  assert.equal(relay.events.at(-1)?.outcome, "CLAIM_TRANSFER_IN_PROGRESS");
});
