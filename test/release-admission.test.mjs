import assert from "node:assert/strict";
import test from "node:test";
import { createReleaseAdmission } from "../src/runtime/release-admission.mjs";

const request = { item: { issue: 147 }, activeClaims: 0 };
function admission(stdout, calls = []) {
  return createReleaseAdmission({ python: "/usr/bin/python3", directorHostConfig: "/h/factory-director-host.json",
    environment: () => ({ GH_TOKEN: "t" }), script: "/repo/scripts/release-admission-verdict",
    execute: async (...args) => { calls.push(args); return { stdout }; } });
}

test("release admission passes the live claim count to the gate and returns its typed verdict", async () => {
  const calls = [];
  const verdict = await admission(JSON.stringify({ admitted: false, failures: [{ check: "agent_ready", why: "HOLD" }] }), calls)(request);
  assert.deepEqual(verdict.failures.map(failure => failure.check), ["agent_ready"]);
  const [python, args, options] = calls[0];
  assert.equal(python, "/usr/bin/python3");
  assert.deepEqual(args, ["/repo/scripts/release-admission-verdict", "--issue", "147", "--director-host-config", "/h/factory-director-host.json", "--active-claims", "0"]);
  assert.equal(options.cwd, "/repo");
  assert.deepEqual(options.env, { GH_TOKEN: "t" });
});

test("release admission rejects malformed or self-contradictory verdicts", async () => {
  for (const stdout of ["not json", "{}", JSON.stringify({ admitted: true, failures: [{ check: "x" }] }),
    JSON.stringify({ admitted: false, failures: [] }), JSON.stringify({ admitted: false, failures: [{ why: "no check" }] })]) {
    await assert.rejects(admission(stdout)(request), /RELEASE_ADMISSION_VERDICT_INVALID/);
  }
  await assert.rejects(admission("{}")({ item: { issue: 0 }, activeClaims: 0 }), /RELEASE_ADMISSION_REQUEST_INVALID/);
});
