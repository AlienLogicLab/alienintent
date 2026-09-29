import assert from "node:assert/strict";
import test from "node:test";
import { assertClaimTransferState } from "../src/runtime/dispatcher.mjs";

const invocationId = "AlienLogicLab/alienintent#149:PRODUCER:claim-1";
const lane = "AlienLogicLab/alienintent#149:PRODUCER";
const path = "/worktrees/resource-1";
const branch = "b-disp/resource-1";
const manager = { uid: 1000, bootId: "boot-1", startedAtMonotonic: "123", cgroup: "/user.slice/user-1000.slice/user@1000.service" };

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
