import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export function syntheticProfile(directory, { keyPath = join(directory, "key.pem"), enabled = false } = {}) {
  const value = JSON.parse(readFileSync(new URL("../../config/profile.example.json", import.meta.url)));
  value.githubApp.privateKeyPath = keyPath;
  value.webhook.secretFile = join(directory, "secret");
  writeFileSync(value.webhook.secretFile, "test-only");
  value.paths.stateFile = join(directory, "state", "state.json");
  value.workers = {};
  value.execution.enabled = enabled;
  return value;
}
