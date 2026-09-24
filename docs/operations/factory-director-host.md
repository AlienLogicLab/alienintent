# Factory Director Host

Status: **KEEP_UNTIL_REPLACED.** Non-cognizant host infrastructure (FDH-01, Issue #89,
SF-REQ-053) for the canonical Factory Director. It is not a Product Requirement, a Wave 2
DAG node, a policy engine or a second cognizant Director.

- Runtime contract, including source paths and schemas, the predicate mapping and the
  idle-reason precedence: `docs/operations/factory-director-runtime-contract.md`.
- Live-proof procedure: `docs/operations/factory-director-host-live-proof.md`.

## What it does

The user-level service holds an exclusive `flock` and a durable lease at
`~/.local/state/alienintent/factory-director-host/lease.json`. On every reconcile, the
read-only adapter `tools/orchestration/factory_director_inputs.py` does three things:

1. It reads Project #1 through the fail-closed read path in
   `tools/live/project_materialization.py`.
2. It reads the Node runtime state, the Founder-hold record, the Director inbox and the
   pause flag.
3. It atomically writes the nine-boolean projection to `inputs.json`, with reasons in
   `inputs.diagnostics.json`.

Any missing, partial or inconsistent source becomes `AUTHORITATIVE_STATE_UNAVAILABLE`,
and nothing is launched.

When control is required and no live episode holds the lease, the host starts one fresh
episode with the configured provider:

- `claude -p --no-session-persistence ...`
- `codex exec --ephemeral ...`

Switching provider or model is a change to `~/.config/alienintent/factory-director-host.json`,
not to code. The prompt is a short pointer to the runtime contract. When the episode
exits, the host wakes within a second and records the exit with provider, model and
provider-reported usage. It then re-evaluates and starts a successor if control remains.

The host does not judge work, select product architecture, change lifecycle state,
modify WIP, resolve Founder questions or change Wave 2 priorities. Its only durable
outputs are:

- the lease;
- the append-only `history.jsonl`;
- the projection and diagnostics files;
- provider output under `episodes/`.

## Installation and inspection

Follow the live-proof procedure. Installation alone is:

```bash
tools/orchestration/install_factory_director_host.sh
```

The script copies repository-owned source into
`~/.local/share/alienintent-bootstrap/factory-director-host/`, installs the unit and the
example host configuration if none exists, and runs `systemctl --user daemon-reload`. It
does not enable or start the service. It never creates the Director-owned hold record or
inbox. Until the Factory Director writes them, the host stays failed closed.

The unit reads its environment from `~/.config/alienintent/factory-director-host.env`. The
installer seeds that file with commented guidance only when it does not exist, and never
overwrites it. The file must set `FACTORY_DIRECTOR_WORKTREE`, `GH_CONFIG_DIR` and `PATH`.
`PATH` is required because the systemd user unit does not inherit the login shell's `PATH`,
and its default does not include `~/.local/bin`. It must resolve every executable the host
runs: `gh` and `python3` (adapter), `git`, and the configured provider CLI (`claude` or
`codex`). Use absolute directories, because systemd does not expand `$HOME` or `~` there,
for example `PATH=/home/netmarine/.local/bin:/usr/local/bin:/usr/bin:/bin`. When `gh`
cannot be resolved, the adapter fails closed (`AUTHORITATIVE_STATE_UNAVAILABLE`) with a
failure that names `gh` and the `PATH` it searched.

Inspect with `systemctl --user status alienintent-factory-director-host` and:

```bash
python3 ~/.local/share/alienintent-bootstrap/factory-director-host/factory_director_host.py \
  --state-root ~/.local/state/alienintent/factory-director-host \
  --config ~/.config/alienintent/factory-director-host.json \
  --workdir "$FACTORY_DIRECTOR_WORKTREE" \
  --prompt ~/.local/share/alienintent-bootstrap/factory-director-host/factory-director-episode.md \
  --inspect
```

## Retirement gate

Do not retire this host, or any existing continuity mechanism, because SF-REQ-053 code
or unit tests exist. The replacement-safety rule (runtime contract §11) requires the
twelve-step live proof under real workload first.
