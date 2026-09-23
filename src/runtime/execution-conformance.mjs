const dimensions = [["wallClock", true, "systemd-owned-supervision"], ["attempts", true, "dispatcher-cycle-guard"], ["replacements", true, "dispatcher-replacement-guard"], ["concurrency", true, "dispatcher-global-concurrency-guard"], ["cancellation", false, "systemd-owned-stop"]];
function systemdActive(runtime) { const s = runtime?.supervision; return s?.mode === "systemd" && ["runtimeMilliseconds", "startupMilliseconds", "stopGraceMilliseconds"].every(key => Number.isSafeInteger(s[key]) && s[key] > 0) && runtime?.workersSupervised === true; }
export function evaluateExecutionConformance({ controls, runtime }) { const missing = [];
  for (const [dimension, numeric, mechanism] of dimensions) { const control = controls?.[dimension];
    if (!control) { missing.push({ dimension, reason: "CONTROL_MISSING" }); continue; }
    if (control.status !== "ENFORCED") { missing.push({ dimension, reason: "CONTROL_STATUS_REFUSED" }); continue; }
    if (numeric && (!Number.isSafeInteger(control.value) || control.value <= 0)) { missing.push({ dimension, reason: "NUMERIC_VALUE_REQUIRED" }); continue; }
    if (control.authority !== "AUTHORIZED") { missing.push({ dimension, reason: numeric ? "NUMERIC_AUTHORITY_REQUIRED" : "POLICY_AUTHORITY_REQUIRED" }); continue; }
    if (control.mechanism !== mechanism) { missing.push({ dimension, reason: "MECHANISM_MISSING" }); continue; }
    if (dimension === "wallClock" && control.value !== runtime?.supervision?.runtimeMilliseconds + runtime?.supervision?.startupMilliseconds + runtime?.supervision?.stopGraceMilliseconds) { missing.push({ dimension, reason: "MECHANISM_CONFIGURATION_MISMATCH" }); continue; }
    if ((mechanism.startsWith("systemd") && !systemdActive(runtime)) || (mechanism.startsWith("dispatcher") && runtime?.dispatcherControls !== controls)) missing.push({ dimension, reason: "MECHANISM_INACTIVE" });
  } return { admissible: missing.length === 0, missing }; }
export function assertExecutionConformance(input) { const result = evaluateExecutionConformance(input); if (!result.admissible) throw new Error(`EXECUTION_CONFORMANCE_REFUSED:${JSON.stringify(result.missing)}`); return result; }
