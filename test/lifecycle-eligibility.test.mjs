import assert from "node:assert/strict";
import test from "node:test";
import { createLifecycleEligibility } from "../src/runtime/lifecycle-eligibility.mjs";

const request = { item: { issue: 147 }, activeClaims: 0 };
function eligibility(stdout, calls = []) {
  return createLifecycleEligibility({ python: "/usr/bin/python3", directorHostConfig: "/h/factory-director-host.json",
    environment: () => ({ GH_TOKEN: "t" }), script: "/repo/scripts/lifecycle-eligibility",
    execute: async (...args) => { calls.push(args); return { stdout }; } });
}
const result = (fields) => JSON.stringify({ agentReady: "READY", prepared: true, admitted: true, failures: [], ...fields });

test("lifecycle eligibility passes the live claim count to the gate and returns its typed result", async () => {
  const calls = [];
  const verdict = await eligibility(result({ admitted: false, failures: [{ check: "wip_capacity_available", why: "full" }] }), calls)(request);
  assert.deepEqual([verdict.prepared, verdict.admitted, verdict.failures.map(failure => failure.check)], [true, false, ["wip_capacity_available"]]);
  const [python, args, options] = calls[0];
  assert.equal(python, "/usr/bin/python3");
  assert.deepEqual(args, ["/repo/scripts/lifecycle-eligibility", "--issue", "147", "--director-host-config", "/h/factory-director-host.json", "--active-claims", "0"]);
  assert.equal(options.cwd, "/repo");
  assert.deepEqual(options.env, { GH_TOKEN: "t" });
});

test("lifecycle eligibility rejects malformed or self-contradictory results", async () => {
  for (const stdout of ["not json", "{}", result({ failures: [{ check: "x" }] }), result({ admitted: false }),
    result({ admitted: false, failures: [{ why: "no check" }] }), result({ prepared: false }), result({ prepared: "yes" }), result({ agentReady: 1 })]) {
    await assert.rejects(eligibility(stdout)(request), /LIFECYCLE_ELIGIBILITY_RESULT_INVALID/);
  }
  await assert.rejects(eligibility("{}")({ item: { issue: 0 }, activeClaims: 0 }), /LIFECYCLE_ELIGIBILITY_REQUEST_INVALID/);
});
