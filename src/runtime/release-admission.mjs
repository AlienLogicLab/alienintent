import { execFile } from "node:child_process";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const defaultScript = fileURLToPath(new URL("../../scripts/release-admission-verdict", import.meta.url));

// The dispatcher's READY admission is the existing release-admission gate, run as a
// child process; this adapter only validates the typed verdict it prints.
export function createReleaseAdmission({ python, directorHostConfig, environment, script = defaultScript,
  execute = promisify(execFile), timeoutMs = 120000 }) {
  return async ({ item, activeClaims }) => {
    if (!Number.isSafeInteger(item?.issue) || item.issue <= 0 || !Number.isSafeInteger(activeClaims) || activeClaims < 0) {
      throw new Error("RELEASE_ADMISSION_REQUEST_INVALID");
    }
    const { stdout } = await execute(python, [script, "--issue", String(item.issue),
      "--director-host-config", directorHostConfig, "--active-claims", String(activeClaims)],
    { cwd: dirname(dirname(script)), env: environment(), encoding: "utf8", timeout: timeoutMs, maxBuffer: 4 * 1024 * 1024 });
    let verdict;
    try { verdict = JSON.parse(stdout); } catch { throw new Error("RELEASE_ADMISSION_VERDICT_INVALID"); }
    if (typeof verdict?.admitted !== "boolean" || !Array.isArray(verdict.failures)
        || verdict.admitted !== (verdict.failures.length === 0)
        || verdict.failures.some(failure => typeof failure?.check !== "string" || !failure.check)) {
      throw new Error("RELEASE_ADMISSION_VERDICT_INVALID");
    }
    return verdict;
  };
}
