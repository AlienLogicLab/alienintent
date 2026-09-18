import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { syntheticProfile } from "./helpers/profile.mjs";

test("missing App authentication fails before creating any workflow state", () => {
  const directory = mkdtempSync(join(tmpdir(), "b-disp-app-cli-"));
  try {
    const config = syntheticProfile(directory);
    delete config.githubApp;
    const path = join(directory, "config.json"); writeFileSync(path, JSON.stringify(config));
    const child = spawnSync(process.execPath, ["bin/b-disp.mjs", "--config", path, "--preflight-only"], { encoding: "utf8", timeout: 5000 });
    assert.notEqual(child.status, 0);
    assert.equal(existsSync(join(directory, "state")), false);
    assert.match(child.stderr, /githubApp/);
    assert.doesNotMatch(child.stdout + child.stderr, /FAKE_WEBHOOK_SECRET_NOT_FOR_OUTPUT/);
  } finally { rmSync(directory, { recursive: true, force: true }); }
});

test("malformed configuration fails without echoing secrets from JSON", () => {
  const directory = mkdtempSync(join(tmpdir(), "b-disp-app-cli-"));
  try {
    const path = join(directory, "config.json"); writeFileSync(path, '{"webhookSecret": FAKE_SECRET_SENTINEL}');
    const child = spawnSync(process.execPath, ["bin/b-disp.mjs", "--config", path, "--preflight-only"], { encoding: "utf8", timeout: 5000 });
    assert.notEqual(child.status, 0);
    assert.doesNotMatch(child.stdout + child.stderr, /FAKE_SECRET_SENTINEL/);
  } finally { rmSync(directory, { recursive: true, force: true }); }
});
