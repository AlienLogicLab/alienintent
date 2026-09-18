// Preserve required invocation flags; only model selection is configurable here.
export function codexArguments(worker, bootstrap) {
  const extra = worker.arguments ?? [];
  if (!Array.isArray(extra)) throw new Error("UNSAFE_PROVIDER_ARGUMENTS");
  for (let index = 0; index < extra.length; index += 2) {
    if (extra[index] !== "--model" || typeof extra[index + 1] !== "string" || !/^[a-zA-Z0-9][a-zA-Z0-9._:/-]*$/.test(extra[index + 1]) || index > 0) throw new Error("UNSAFE_PROVIDER_ARGUMENTS");
  }
  if (!worker.permissionMode) throw new Error("PERMISSION_MODE_REQUIRED");
  return [...["exec", "--ephemeral", "--json", "--sandbox", worker.permissionMode, "-C", worker.worktree], ...extra, bootstrap];
}
