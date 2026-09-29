import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { NodeStateLedger } from "../src/runtime/node-state-ledger.mjs";

function subject(hooks = {}) {
  const statePath = join(mkdtempSync(join(tmpdir(), "claim-transfer-ledger-")), "state.json");
  const ledger = new NodeStateLedger(statePath, undefined, hooks);
  ledger.read();
  return ledger;
}

test("expected-head save commits only against the exact writer head", () => {
  const ledger = subject();
  const expected = ledger.assertFence();
  const next = { ...ledger.read(), transfer: { operationId: "one" } };
  const committed = ledger.saveIfHead(expected, next);
  assert.equal(committed.sequence, expected.sequence + 1);
  assert.deepEqual(ledger.read(), next);
  assert.deepEqual(ledger.assertFence(), {
    revision: committed.revision, sequence: committed.sequence, digest: committed.digest,
  });
  assert.throws(() => ledger.saveIfHead(expected, next), /LEDGER_EXPECTED_HEAD_CHANGED/);
  assert.equal(readFileSync(ledger.path, "utf8").trimEnd().split("\n").length, 2);
});

test("expected-head save refuses another committed head before append", () => {
  const ledger = subject();
  const expected = ledger.assertFence();
  const next = { ...ledger.read(), transfer: { operationId: "one" } };
  ledger.save({ deliveries: { other: { state: "PROCESSING" } }, active: {} });
  assert.throws(() => ledger.saveIfHead(expected, next), /LEDGER_EXPECTED_HEAD_CHANGED/);
  assert.equal(ledger.read().transfer, undefined);
});

test("expected-head save refuses each incorrect head field and a divergent projection", () => {
  const ledger = subject();
  const expected = ledger.assertFence();
  const next = { ...ledger.read(), transfer: { operationId: "one" } };
  for (const field of ["revision", "sequence", "digest"]) {
    const incorrect = { ...expected, [field]: field === "sequence" ? expected.sequence + 1 : "incorrect" };
    assert.throws(() => ledger.saveIfHead(incorrect, next), /LEDGER_EXPECTED_HEAD_CHANGED/);
  }
  writeFileSync(ledger.statePath, `${JSON.stringify({ deliveries: {}, active: { unexpected: {} } })}\n`);
  assert.throws(() => ledger.saveIfHead(expected, next), /LEDGER_PROJECTION_FENCE_UNAVAILABLE/);
  assert.equal(readFileSync(ledger.path, "utf8").trimEnd().split("\n").length, 1);
});

test("expected-head save reconciles interrupted append before any retry", () => {
  const ledger = subject();
  const expected = ledger.assertFence();
  const next = { ...ledger.read(), transfer: { operationId: "one" } };
  ledger.hooks.afterAppend = () => { throw new Error("INTERRUPTED_AFTER_APPEND"); };
  assert.throws(() => ledger.saveIfHead(expected, next), /INTERRUPTED_AFTER_APPEND/);
  delete ledger.hooks.afterAppend;
  assert.deepEqual(ledger.read(), next);
  assert.throws(() => ledger.saveIfHead(expected, next), /LEDGER_EXPECTED_HEAD_CHANGED/);
  assert.equal(readFileSync(ledger.path, "utf8").trimEnd().split("\n").length, 2);
});
