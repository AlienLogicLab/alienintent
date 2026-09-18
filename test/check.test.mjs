import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, copyFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";

test("canonical test command fails if any required suite is absent", () => {
  const root = mkdtempSync(join(tmpdir(), "b-disp-ci-missing-"));
  mkdirSync(join(root, "scripts"));
  copyFileSync(new URL("../scripts/check.mjs", import.meta.url), join(root, "scripts/check.mjs"));
  for (const group of ["runtime", "preflight", "rai", "policy", "all"]) {
    const child = spawnSync(process.execPath, [join(root, "scripts/check.mjs"), group], { encoding: "utf8" });
    assert.equal(child.error, undefined);
    assert.equal(child.status, 1);
    assert.match(child.stderr, /Missing required suite:/);
  }
});
