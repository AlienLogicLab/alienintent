import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { join } from "node:path";

const root = fileURLToPath(new URL("../", import.meta.url));
const suites = {
  runtime: ["test/dispatcher.test.mjs", "test/github-authority.test.mjs", "test/github-app.test.mjs",
    "test/worker-runner.test.mjs", "test/cli.test.mjs", "test/app-cli.test.mjs",
    "test/profile.test.mjs", "test/legacy-state.test.mjs", "test/repository-state.test.mjs", "test/check.test.mjs",
    "test/worktree-manager.test.mjs", "test/worktree-lifecycle.test.mjs", "test/self-hosting.test.mjs"],
  preflight: ["test/worker-preflight.test.sh"],
  rai: ["test/rai.test.mjs"],
  policy: ["test/governing-instructions.test.mjs"],
};
const selected = process.argv[2] ?? "all";
if (selected !== "all" && !Object.hasOwn(suites, selected)) {
  console.error("Unknown required test group"); process.exit(2);
}
const groups = selected === "all" ? Object.keys(suites) : [selected];
for (const group of groups) for (const file of suites[group]) {
  if (!existsSync(join(root, file))) {
    console.error(`Missing required suite: ${file}`); process.exit(1);
  }
}
for (const group of groups) {
  console.log(`Required test group: ${group}`);
  const command = group === "preflight" ? "bash" : process.execPath;
  const args = group === "preflight" ? suites[group] : ["--test", "--test-isolation=none", ...suites[group]];
  const result = spawnSync(command, args, { cwd: root, stdio: "inherit" });
  if (result.error || result.signal || result.status !== 0) {
    console.error(`Required test group failed: ${group}`);
    process.exit(result.status && result.status > 0 ? result.status : 1);
  }
}
