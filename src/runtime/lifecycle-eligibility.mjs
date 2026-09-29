import { execFile } from "node:child_process";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const defaultScript = fileURLToPath(new URL("../../scripts/lifecycle-eligibility", import.meta.url));

// The dispatcher's one lifecycle eligibility source is the existing release-admission gate,
// run as a child process; this adapter only validates the typed result it prints.
export function createLifecycleEligibility({ python, directorHostConfig, environment, script = defaultScript,
  execute = promisify(execFile), timeoutMs = 120000 }) {
  return async ({ item, activeClaims }) => {
    if (!Number.isSafeInteger(item?.issue) || item.issue <= 0 || !Number.isSafeInteger(activeClaims) || activeClaims < 0) {
      throw new Error("LIFECYCLE_ELIGIBILITY_REQUEST_INVALID");
    }
    const { stdout } = await execute(python, [script, "--issue", String(item.issue),
      "--director-host-config", directorHostConfig, "--active-claims", String(activeClaims)],
    { cwd: dirname(dirname(script)), env: environment(), encoding: "utf8", timeout: timeoutMs, maxBuffer: 4 * 1024 * 1024 });
    let result;
    try { result = JSON.parse(stdout); } catch { throw new Error("LIFECYCLE_ELIGIBILITY_RESULT_INVALID"); }
    const failures = result?.failures;
    if (typeof result?.admitted !== "boolean" || typeof result.prepared !== "boolean" || !Array.isArray(failures)
        || failures.some(failure => typeof failure?.check !== "string" || !failure.check)
        || result.admitted !== (failures.length === 0) || (result.admitted && !result.prepared)
        || (result.agentReady !== null && typeof result.agentReady !== "string")) {
      throw new Error("LIFECYCLE_ELIGIBILITY_RESULT_INVALID");
    }
    return result;
  };
}
