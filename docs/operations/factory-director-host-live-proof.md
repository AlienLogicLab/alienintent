# Factory Director Host live proof

This is the procedure for the twelve-step live proof in chat record §16. The runtime
contract (`docs/operations/factory-director-runtime-contract.md` §11) requires it before
any existing continuity mechanism can be retired.

**Authority.** Landing FDH-01 does not authorize this proof. Installing and enabling the
host, and running this procedure, are Factory Director actions. Each needs its own
durable authorization record on the FDH-01 Issue (#89) or a follow-up Issue. Nothing is
retired during this procedure. The Node runtime, resident or session continuity,
observers and liveness checks all keep running.

Every command is written for bash on the factory host, run as the factory user. Run them
from a shell where `PROOF` is set as in step 0. Retain every output file named here. A
measurement that is missing is recorded as an explicit **HOLD**, never as zero or PASS.

## 0. Preconditions and proof directory

```bash
# No errexit: this runs in an interactive shell. A failed wait is recorded as a HOLD instead.
set -uo pipefail
wait_for() {  # wait_for "<description>" <command...>: retry every 2s for up to 10 minutes
  local what=$1; shift
  for _ in $(seq 300); do "$@" >/dev/null 2>&1 && return 0; sleep 2; done
  echo "HOLD: timed out waiting for $what" | tee -a "$PROOF/HOLDS.txt"; return 1
}
exited() { jq -e --arg id "$1" 'select(.reason == "DIRECTOR_EPISODE_EXITED" and .episode_id == $id)' "$HOST_STATE/history.jsonl"; }
export REPO=/mnt/d/Projects/alienintent
export PROOF="$HOME/.local/state/alienintent/factory-director-live-proof/$(date -u +%Y%m%dT%H%M%SZ)"
export HOST_STATE="$HOME/.local/state/alienintent/factory-director-host"
export FD_STATE="$HOME/.local/state/alienintent/factory-director"
export FD_WORKTREE="$FD_STATE/worktree"
mkdir -p "$PROOF"
git -C "$REPO" fetch origin
git -C "$REPO" rev-parse origin/main | tee "$PROOF/00-origin-main.sha"
git -C "$REPO" merge-base --is-ancestor <FDH-01-landed-sha> origin/main && echo landed | tee "$PROOF/00-landed.txt"
systemctl --user list-units 'alienintent*' --no-pager | tee "$PROOF/00-existing-units.txt"
```

Replace `<FDH-01-landed-sha>` with the accepted SHA recorded on Issue #89 before running.
`00-existing-units.txt` is the replacement-safety baseline. Every unit listed there must
still be present, and still active, in step 13.

## 0a. Dedicated linked worktree, Director-owned sources and installation

```bash
git -C "$REPO" worktree add --detach "$FD_WORKTREE" origin/main
git -C "$FD_WORKTREE" rev-parse --absolute-git-dir --path-format=absolute --git-common-dir | tee "$PROOF/0a-worktree.txt"
mkdir -p "$FD_STATE/inbox/processed"
# The Factory Director writes the hold record explicitly; [] only if it has confirmed there are no holds.
test -e "$FD_STATE/founder-holds.json" || printf '%s\n' '{"schemaVersion": 1, "holds": []}' > "$FD_STATE/founder-holds.json"
cp "$FD_STATE/founder-holds.json" "$PROOF/0a-founder-holds.json"
( cd "$FD_WORKTREE" && tools/orchestration/install_factory_director_host.sh ) | tee "$PROOF/0a-install.txt"
```

Edit `~/.config/alienintent/factory-director-host.env` so that it contains:

```bash
FACTORY_DIRECTOR_WORKTREE=/home/netmarine/.local/state/alienintent/factory-director/worktree
GH_CONFIG_DIR=/home/netmarine/.config/gh
PATH=/home/netmarine/.local/bin:/usr/local/bin:/usr/bin:/bin
```

`PATH` is required. The systemd user unit does not inherit the login shell's `PATH`, and
its default `PATH` does not include `~/.local/bin`. The `PATH` must resolve every
executable the host runs: `gh` and `python3` (adapter), `git`, and the configured provider
CLI (`claude` or `codex`). Write it as absolute directories: systemd does not expand
`$HOME` or `~` in this file. Without it the adapter cannot run `gh`, and the host stays at
`AUTHORITATIVE_STATE_UNAVAILABLE` with a failure naming `gh` and the `PATH` it searched.
The dry run below sources this file, so it checks the same `PATH`.

`GH_CONFIG_DIR` must name a gh configuration that can read Project #1 and Issue comments.
A worker's fine-grained token cannot read Project #1, and with one the host stays at
`AUTHORITATIVE_STATE_UNAVAILABLE`. Review `~/.config/alienintent/factory-director-host.json`
(`provider`, `model`, `wipLimit: 1`) and copy it to `$PROOF/0a-host-config.json`.

Dry-run the read-only adapter. It must exit 0 and show `authoritative_state: true`:

```bash
set -a; . "$HOME/.config/alienintent/factory-director-host.env"; set +a
python3 "$HOME/.local/share/alienintent-bootstrap/factory-director-host/factory_director_inputs.py" \
  --config "$HOME/.config/alienintent/factory-director-host.json" | tee "$PROOF/0a-adapter-dry-run.json"
sha256sum "$(jq -r .paths.stateFile "$HOME/.config/alienintent/self-hosting.json")" \
  "$HOME/.config/alienintent/self-hosting.json" | tee "$PROOF/0a-readonly-before.sha256"
```

Choose a real workload in which control is required. For example, an authorized `READY`
Issue that the Director will release, or an Issue in `REVIEW`. Record it:

```bash
jq '.observations.controlRequiredBy' "$PROOF/0a-adapter-dry-run.json" | tee "$PROOF/0a-workload.json"
```

If `controlRequiredBy` is empty and there is no attention or inbox entry, stop. The proof
needs real workload.

## The twelve steps

Substitute `<issue>` and the expected states with the workload chosen in step 0a.

### 1. Start a Factory Director episode

```bash
systemctl --user enable --now alienintent-factory-director-host.service
wait_for "episode A lease" jq -e '.status == "ACTIVE"' "$HOST_STATE/lease.json"
cp "$HOST_STATE/lease.json" "$PROOF/01-lease-A.json"
A_ID=$(jq -r .episode_id "$PROOF/01-lease-A.json")
tail -n 5 "$HOST_STATE/history.jsonl" | tee "$PROOF/01-history.jsonl"
```

Evidence: Lease A (`status: ACTIVE`, episode id, pid, `process_start_ticks`, provider, model, `launch_inputs`). A history record `DIRECTOR_CONTINUITY_FAULT` with its `inputs`.

### 2. Let it advance real authorized factory work

```bash
A_PID=$(jq -r .pid "$PROOF/01-lease-A.json")
tr '\0' ' ' < "/proc/$A_PID/cmdline" | tee "$PROOF/02-cmdline-A.txt"
# after A has acted on the workload Issue:
python3 "$REPO/tools/live/project_materialization.py" verify <issue> --expect-status <new-state> | tee "$PROOF/02-readback.txt"
```

Evidence: Fresh-session argv (`-p --no-session-persistence`, or `exec --ephemeral`; no `--resume` or `--continue`). A Project read-back of the advanced Issue. The URL of the Issue comment A wrote.

### 3. Let that episode exit

```bash
while kill -0 "$A_PID" 2>/dev/null; do sleep 5; done
wait_for "exit record of A" exited "$A_ID"
exited "$A_ID" | tee "$PROOF/03-exit-A.json"
```

Evidence: An exit record with `exit_reason`, `provider`, `requested_model`, `runtime_seconds`, `failure_streak` and `usage`. Usage has tokens and cost when measured. Otherwise it shows `measured: false` with a reason, which is a HOLD for that measurement.

### 4. Provide no Founder intervention

```bash
gh api "repos/AlienLogicLab/alienintent/issues/<issue>/timeline" --paginate > "$PROOF/04-timeline.json"
ls -la "$FD_STATE/inbox" "$FD_STATE/inbox/processed" > "$PROOF/04-inbox.txt"
sha256sum "$FD_STATE/founder-holds.json" | tee "$PROOF/04-holds.sha256"
```

Evidence: No Founder or operator event between A's exit and B's launch. The inbox and hold record are unchanged since step 0a, unless timestamps and authors show that a Director episode wrote them.

### 5. Host detects that Director cognition is still required

```bash
wait_for "successor launch" jq -e --arg a "$A_ID" '.status == "ACTIVE" and .episode_id != $a' "$HOST_STATE/lease.json"
cp "$HOST_STATE/inputs.diagnostics.json" "$PROOF/05-diagnostics.json"
jq -c 'select(.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS")' "$HOST_STATE/history.jsonl" | tail -n 1 | tee "$PROOF/05-relaunch.json"
```

Evidence: Diagnostics showing why control is required (`controlRequiredBy`, inbox or escalations). The relaunch record's `at` falls within seconds of A's exit record, because the host wakes on exit.

### 6. Host launches a fresh Factory Director episode

```bash
cp "$HOST_STATE/lease.json" "$PROOF/06-lease-B.json"
diff <(jq -r '.episode_id,.pid' "$PROOF/01-lease-A.json") <(jq -r '.episode_id,.pid' "$PROOF/06-lease-B.json") | tee "$PROOF/06-lease-diff.txt" || true
```

Evidence: Lease B with a new episode id and a new pid. The diff must show both lines changed.

### 7. Fresh episode has no conversational history

```bash
B_ID=$(jq -r .episode_id "$PROOF/06-lease-B.json")
B_PID=$(jq -r .pid "$PROOF/06-lease-B.json")
tr '\0' ' ' < "/proc/$B_PID/cmdline" | tee "$PROOF/07-cmdline-B.txt"
```

Evidence: The same fresh-session argv as A, with no session id or resume flag. The prompt is the short contract pointer with B's episode id.

### 8. Fresh episode reconstructs state from durable records

```bash
while kill -0 "$B_PID" 2>/dev/null; do sleep 5; done
wait_for "exit record of B" exited "$B_ID"
cp "$HOST_STATE/episodes/$B_ID.stdout" "$PROOF/08-output-B.json"
cp "$HOST_STATE/episodes/$(jq -r .episode_id "$PROOF/01-lease-A.json").stdout" "$PROOF/08-output-A.json"
```

Evidence: B's output and Issue comments cite the durable sources it read: the Project read-back, runtime state, Issue comments, hold record and inbox. None cite a prior conversation. For Claude, `session_id` in `08-output-B.json` differs from `08-output-A.json`.

### 9. It identifies the correct next authorized action

```bash
gh issue view <issue> --repo AlienLogicLab/alienintent --comments > "$PROOF/09-issue.txt"
```

Evidence: The action B names matches the runtime contract's selection order (§5 step 6) applied to `05-diagnostics.json`.

### 10. It advances that action

```bash
python3 "$REPO/tools/live/project_materialization.py" verify <issue> --expect-status <state-after-B> | tee "$PROOF/10-readback.txt"
```

Evidence: A Project read-back, or a durable comment or evidence commit, showing the advance.

### 11. That episode exits

```bash
exited "$B_ID" | tee "$PROOF/11-exit-B.json"
```

Evidence: An exit record for B, with `provider`, `requested_model` and `usage`.

### 12. Host repeats the process successfully

```bash
sleep 70
tail -n 3 "$HOST_STATE/history.jsonl" | tee "$PROOF/12-history-tail.jsonl"
cp "$HOST_STATE/lease.json" "$PROOF/12-lease.json"
```

Evidence: Either a third fresh episode C (`PRIOR_EPISODE_EXITED_CONTROL_REMAINS`) while control remains, or an idle record whose reason is a terminal condition that agrees with `inputs.diagnostics.json`. A `DIRECTOR_EPISODE_CRASH_LOOP` or `DIRECTOR_LAUNCH_FAILED` record is neither outcome: it is a HOLD on this step, and the proof is not passed.

## 13. Closing checks

```bash
cp "$HOST_STATE/history.jsonl" "$PROOF/13-history.jsonl"
python3 "$HOME/.local/share/alienintent-bootstrap/factory-director-host/factory_director_host.py" \
  --state-root "$HOST_STATE" --config "$HOME/.config/alienintent/factory-director-host.json" \
  --workdir "$FD_WORKTREE" \
  --prompt "$HOME/.local/share/alienintent-bootstrap/factory-director-host/factory-director-episode.md" \
  --inspect | tee "$PROOF/13-inspect.json"
systemctl --user list-units 'alienintent*' --no-pager | tee "$PROOF/13-existing-units.txt"
diff <(awk '{print $1}' "$PROOF/00-existing-units.txt") <(awk '{print $1}' "$PROOF/13-existing-units.txt") > "$PROOF/13-replacement-safety.diff" || true
sha256sum "$HOME/.config/alienintent/self-hosting.json" | tee "$PROOF/13-config-after.sha256"
( cd "$PROOF" && sha256sum ./* > SHA256SUMS )
```

`13-replacement-safety.diff` may contain only the added host unit and the unit-count
footer line. `self-hosting.json`
must match its step-0a hash, because the host never writes configuration. The runtime
state file changes during the proof because the Node runtime writes it. That is expected,
and it is not a host write. Any line in `HOLDS.txt` is a HOLD on the step that wrote it.

To stop the proof at any point: `touch "$FD_STATE/PAUSE"`. New launches stop and any live
episode is left to finish. To disable the host:
`systemctl --user disable --now alienintent-factory-director-host.service`.

## Retention and verdict

Copy `$PROOF` into the repository as `docs/evidence/fdh-01-live-proof/<timestamp>/` in a
docs commit, add a short record that names each step's evidence file, and post the commit
SHA on the Issue. The proof passes only if all twelve steps have their evidence. Any
missing step is a HOLD, and the existing continuity mechanisms stay in place
(replacement-safety rule).
