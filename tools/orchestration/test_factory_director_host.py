"""Contract tests for the non-cognizant Factory Director Host (FDH-01)."""
from pathlib import Path
import json
import sys

import pytest
import time

sys.path.insert(0, str(Path(__file__).parent))

from factory_director_host import (  # noqa: E402
    DirectorInputs,
    FactoryDirectorHost,
    HostState,
    InMemoryDirectorLauncher,
    JsonDirectorInputs,
    ProcessDirectorLauncher,
)


def required(**overrides):
    values = dict(
        authoritative_state=True,
        eligible_authorized_work=True,
        executable_capacity=True,
        attention_required=False,
        pending_director_inbox=False,
        lifecycle_requires_selection=False,
        wip_intentionally_full=False,
        founder_decision_pending=False,
        explicit_pause=False,
    )
    values.update(overrides)
    return DirectorInputs(**values)


def process_launcher(tmp_path, prompt, *, provider="codex", executable="unused", model="test-model",
                     permission_mode=None, **kwargs):
    if permission_mode is None:
        permission_mode = {"claude": "bypassPermissions"}.get(provider, "workspace-write")
    return ProcessDirectorLauncher(tmp_path, prompt, provider=provider, executable=executable, model=model,
                                   permission_mode=permission_mode, output_dir=tmp_path / "episodes", **kwargs)


def host(tmp_path, inputs=None):
    launcher = InMemoryDirectorLauncher()
    return FactoryDirectorHost(tmp_path, lambda: inputs or required(), launcher), launcher


def test_continuity_fault_launches_one_fresh_director_episode(tmp_path):
    service, launcher = host(tmp_path)

    result = service.reconcile()

    assert result.reason == "DIRECTOR_CONTINUITY_FAULT"
    assert len(launcher.launched) == 1
    assert service.inspect().episode_active is True


def test_exit_with_remaining_control_work_launches_successor_without_prompt(tmp_path):
    service, launcher = host(tmp_path)
    service.reconcile()
    first = launcher.launched[0]
    launcher.finish(first.episode_id, exit_code=0)

    result = service.reconcile()

    assert result.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    assert len(launcher.launched) == 2
    assert launcher.launched[1].episode_id != first.episode_id


@pytest.mark.parametrize("inputs,reason", [
    (required(eligible_authorized_work=False), "NO_ELIGIBLE_AUTHORIZED_WORK"),
    (required(wip_intentionally_full=True), "WIP_INTENTIONALLY_FULL"),
    (required(founder_decision_pending=True), "FOUNDER_DECISION_PENDING"),
    (required(explicit_pause=True), "FACTORY_PAUSED"),
])
def test_legitimate_idle_states_never_launch(tmp_path, inputs, reason):
    service, launcher = host(tmp_path, inputs)

    result = service.reconcile()

    assert result.reason == reason
    assert launcher.launched == []


def test_ambiguous_or_missing_authoritative_state_fails_closed(tmp_path):
    service, launcher = host(tmp_path, required(authoritative_state=False))

    result = service.reconcile()

    assert result.reason == "AUTHORITATIVE_STATE_UNAVAILABLE"
    assert launcher.launched == []


def test_second_host_refuses_conflicting_active_lease(tmp_path):
    first, first_launcher = host(tmp_path)
    second, second_launcher = host(tmp_path)
    first.reconcile()

    result = second.reconcile()

    assert result.reason == "CONFLICTING_HOST_OWNERSHIP"
    assert len(first_launcher.launched) == 1
    assert second_launcher.launched == []


def test_corrupt_lease_refuses_rather_than_launching_a_second_episode(tmp_path):
    service, launcher = host(tmp_path)
    (tmp_path / "lease.json").write_text("{not-json")

    assert service.reconcile().reason == "AMBIGUOUS_LEASE"
    assert launcher.launched == []


def test_parseable_but_incomplete_lease_refuses_rather_than_launching(tmp_path):
    service, launcher = host(tmp_path)
    (tmp_path / "lease.json").write_text("{}")

    assert service.reconcile().reason == "AMBIGUOUS_LEASE"
    assert launcher.launched == []


def test_indeterminate_process_liveness_refuses_rather_than_relaunching(tmp_path):
    class UncertainLauncher(InMemoryDirectorLauncher):
        def liveness(self, episode):
            return None
    launcher = UncertainLauncher()
    service = FactoryDirectorHost(tmp_path, required, launcher)
    service.reconcile()

    assert service.reconcile().reason == "EPISODE_LIVENESS_AMBIGUOUS"
    assert len(launcher.launched) == 1


def test_unfinished_prelaunch_lease_refuses_after_host_crash_window(tmp_path):
    service, launcher = host(tmp_path)
    (tmp_path / "lease.json").write_text(__import__("json").dumps({
        "host_id": "old", "episode_id": "reserved", "pid": None,
        "started_at": "2026-01-01T00:00:00+00:00", "process_start_ticks": None,
        "status": "ACTIVATING",
    }))

    assert service.reconcile().reason == "AMBIGUOUS_LEASE"
    assert launcher.launched == []


@pytest.mark.parametrize("pid,process_start_ticks", [
    (None, "123"),
    (True, "123"),
    (False, "123"),
    (0, "123"),
    (-1, "123"),
    (1, None),
    (1, ""),
])
def test_malformed_active_lease_refuses_without_successor_or_idle_inspection(tmp_path, pid, process_start_ticks):
    service, launcher = host(tmp_path)
    (tmp_path / "lease.json").write_text(json.dumps({
        "host_id": "old", "episode_id": "active", "pid": pid,
        "started_at": "2026-01-01T00:00:00+00:00",
        "process_start_ticks": process_start_ticks, "status": "ACTIVE",
    }))

    assert service.reconcile().reason == "AMBIGUOUS_LEASE"
    assert launcher.launched == []
    inspection = service.inspect()
    assert inspection.state is HostState.REFUSED
    assert inspection.last_reason == "AMBIGUOUS_LEASE"


@pytest.mark.parametrize("failed_operation", ["write", "close"])
def test_prompt_handoff_failure_keeps_spawned_pid_leased_and_prevents_successor(
        tmp_path, monkeypatch, failed_operation):
    class BrokenStdin:
        def write(self, prompt):
            if failed_operation == "write":
                raise OSError("simulated prompt write failure")

        def close(self):
            if failed_operation == "close":
                raise OSError("simulated prompt close failure")

    class SpawnedChild:
        pid = 12345
        stdin = BrokenStdin()

    popen_calls = []

    def spawned_then_handoff_fails(*args, **kwargs):
        popen_calls.append((args, kwargs))
        return SpawnedChild()

    monkeypatch.setattr("factory_director_host.subprocess.Popen", spawned_then_handoff_fails)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("episode {{EPISODE_ID}}")
    launcher = process_launcher(tmp_path, prompt, executable="unused")
    monkeypatch.setattr(launcher, "_process_start_ticks", lambda pid: "987654")
    monkeypatch.setattr(launcher, "liveness", lambda episode: True)
    service = FactoryDirectorHost(tmp_path / "host", required, launcher)

    first = service.reconcile()
    lease = json.loads((tmp_path / "host" / "lease.json").read_text())
    second = service.reconcile()

    assert first.reason == "DIRECTOR_LAUNCH_HANDOFF_AMBIGUOUS"
    assert lease["status"] == "ACTIVE"
    assert lease["pid"] == 12345
    assert lease["process_start_ticks"] == "987654"
    assert second.reason == "DIRECTOR_EPISODE_ACTIVE"
    assert len(popen_calls) == 1


def test_restart_reconstructs_active_lease_without_duplicate_activation(tmp_path):
    first, launcher = host(tmp_path)
    first.reconcile()
    first.shutdown()  # Models service-manager restart: old host has exited and released its lock.
    restarted = FactoryDirectorHost(tmp_path, required, launcher)

    result = restarted.reconcile()

    assert result.reason == "DIRECTOR_EPISODE_ACTIVE"
    assert len(launcher.launched) == 1
    assert restarted.inspect().state is HostState.ACTIVE


def test_episode_exit_is_recorded_and_inspection_explains_latest_decision(tmp_path):
    service, launcher = host(tmp_path)
    service.reconcile()
    launcher.finish(launcher.launched[0].episode_id, exit_code=17)
    service.reconcile()

    inspection = service.inspect()
    assert inspection.last_exit_reason == "EXIT_17"
    assert inspection.last_activation_reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    assert inspection.lease_owner and inspection.episode_id


def test_durable_input_file_is_strict_and_malformed_input_fails_closed(tmp_path):
    state = tmp_path / "inputs.json"
    state.write_text('{"eligible_authorized_work": true}\n')
    service = FactoryDirectorHost(tmp_path / "host", JsonDirectorInputs(state), InMemoryDirectorLauncher())

    assert service.reconcile().reason == "AUTHORITATIVE_STATE_UNAVAILABLE"

    state.write_text(__import__("json").dumps(required().__dict__))
    assert service.reconcile().reason == "DIRECTOR_CONTINUITY_FAULT"


def test_process_launcher_treats_an_exited_child_as_inactive_even_before_reap(tmp_path):
    fake_codex = tmp_path / "codex"
    fake_codex.write_text("#!/usr/bin/env bash\ncat >/dev/null\nexit 0\n")
    fake_codex.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("episode {{EPISODE_ID}}")
    launcher = process_launcher(tmp_path, prompt, executable=str(fake_codex))

    episode = launcher.launch("episode-1")
    time.sleep(0.05)

    assert launcher.is_active(episode) is False


def test_real_child_exit_is_reconciled_to_a_successor_without_human_prompt(tmp_path):
    fake_codex = tmp_path / "codex"
    fake_codex.write_text("#!/usr/bin/env bash\ncat >/dev/null\nexit 0\n")
    fake_codex.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("episode {{EPISODE_ID}}")
    service = FactoryDirectorHost(
        tmp_path / "host", required,
        process_launcher(tmp_path, prompt, executable=str(fake_codex)),
    )

    first = service.reconcile()
    time.sleep(0.05)
    second = service.reconcile()

    assert first.reason == "DIRECTOR_CONTINUITY_FAULT"
    assert second.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    assert first.episode_id != second.episode_id


# --- FDH-01 acceptance: offline continuity (criterion 4) ------------------------------------

class MutableInputs:
    def __init__(self, values):
        self.values = values

    def __call__(self):
        return self.values


def history(root):
    return [json.loads(line) for line in (root / "history.jsonl").read_text().splitlines()]


def test_continuity_a_exits_fresh_b_launches_then_b_exits_and_host_idles(tmp_path):
    inputs = MutableInputs(required())
    launcher = InMemoryDirectorLauncher(provider="claude", model="claude-opus-5-5")
    service = FactoryDirectorHost(tmp_path, inputs, launcher)

    first = service.reconcile()
    lease_a = json.loads((tmp_path / "lease.json").read_text())
    launcher.finish(first.episode_id, exit_code=0)
    second = service.reconcile()
    lease_b = json.loads((tmp_path / "lease.json").read_text())

    assert first.reason == "DIRECTOR_CONTINUITY_FAULT"
    assert second.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    assert second.episode_id != first.episode_id
    assert (lease_a["episode_id"], lease_a["pid"]) != (lease_b["episode_id"], lease_b["pid"])
    assert lease_b["episode_id"] == second.episode_id and lease_b["status"] == "ACTIVE"

    assert service.reconcile().reason == "DIRECTOR_EPISODE_ACTIVE"
    assert service.reconcile().reason == "DIRECTOR_EPISODE_ACTIVE"
    assert len(launcher.launched) == 2

    inputs.values = required(eligible_authorized_work=False)
    launcher.finish(second.episode_id, exit_code=0)
    last = service.reconcile()

    assert last.reason == "NO_ELIGIBLE_AUTHORIZED_WORK" and last.state is HostState.IDLE
    assert len(launcher.launched) == 2
    records = history(tmp_path)
    exits = [r for r in records if r["reason"] == "DIRECTOR_EPISODE_EXITED"]
    assert [r["episode_id"] for r in exits] == [first.episode_id, second.episode_id]
    assert all(r["exit_reason"] == "EXIT_0" for r in exits)
    launches = [r for r in records if r["reason"] in {"DIRECTOR_CONTINUITY_FAULT",
                                                         "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"}]
    assert [(r["provider"], r["requested_model"]) for r in launches] == [("claude", "claude-opus-5-5")] * 2
    assert json.loads((tmp_path / "lease.json").read_text())["status"] == "EXITED"


def test_director_only_control_launches_even_when_worker_wip_is_full(tmp_path):
    for flag in ("attention_required", "pending_director_inbox", "lifecycle_requires_selection"):
        root = tmp_path / flag
        service, launcher = host(root, required(eligible_authorized_work=False, executable_capacity=False,
                                                 wip_intentionally_full=True, **{flag: True}))
        assert service.reconcile().reason == "DIRECTOR_CONTINUITY_FAULT", flag
        assert len(launcher.launched) == 1


def test_overfull_wip_with_only_worker_work_refuses_as_capacity_unavailable(tmp_path):
    service, launcher = host(tmp_path, required(executable_capacity=False, wip_intentionally_full=False))

    result = service.reconcile()

    assert (result.reason, result.state) == ("EXECUTION_CAPACITY_UNAVAILABLE", HostState.REFUSED)
    assert launcher.launched == []


# Each row clears the condition that won the row before, so every step proves one ordering edge.
PRECEDENCE = [
    (dict(authoritative_state=False, explicit_pause=True, founder_decision_pending=True,
          wip_intentionally_full=True, executable_capacity=False), "AUTHORITATIVE_STATE_UNAVAILABLE"),
    (dict(explicit_pause=True, founder_decision_pending=True, wip_intentionally_full=True,
          executable_capacity=False), "FACTORY_PAUSED"),
    (dict(founder_decision_pending=True, wip_intentionally_full=True, executable_capacity=False),
     "FOUNDER_DECISION_PENDING"),
    (dict(wip_intentionally_full=True, executable_capacity=False), "WIP_INTENTIONALLY_FULL"),
    (dict(eligible_authorized_work=False, executable_capacity=False), "NO_ELIGIBLE_AUTHORIZED_WORK"),
    (dict(executable_capacity=False), "EXECUTION_CAPACITY_UNAVAILABLE"),
]


@pytest.mark.parametrize("overrides,reason", PRECEDENCE)
def test_idle_reason_precedence_is_the_documented_order(tmp_path, overrides, reason):
    service, launcher = host(tmp_path, required(**overrides))

    assert service.reconcile().reason == reason
    assert launcher.launched == []


def test_wait_for_change_returns_as_soon_as_the_leased_episode_exits(tmp_path):
    service, launcher = host(tmp_path)
    episode_id = service.reconcile().episode_id
    slept = []

    def sleep(seconds):
        slept.append(seconds)
        if len(slept) == 3:
            launcher.finish(episode_id)

    assert service.wait_for_change(60, poll=1, sleep=sleep) == "EPISODE_EXITED"
    assert sum(slept) == 3


# --- FDH-01 acceptance: provider-neutral launcher (criterion 5) -----------------------------

def test_claude_command_is_a_fresh_non_persisted_print_session(tmp_path):
    launcher = process_launcher(tmp_path, tmp_path / "prompt.md", provider="claude", executable="/bin/claude",
                                model="claude-opus-5-5", permission_mode="bypassPermissions")

    assert launcher.command() == ["/bin/claude", "-p", "--no-session-persistence", "--output-format", "json",
                                  "--permission-mode", "bypassPermissions", "--model", "claude-opus-5-5"]


def test_codex_command_is_a_fresh_ephemeral_exec_session(tmp_path):
    launcher = process_launcher(tmp_path, tmp_path / "prompt.md", provider="codex", executable="/bin/codex",
                                model="gpt-6-astra", permission_mode="workspace-write")

    assert launcher.command() == ["/bin/codex", "exec", "--ephemeral", "--json", "--sandbox", "workspace-write",
                                  "-C", str(tmp_path), "--model", "gpt-6-astra", "-"]


@pytest.mark.parametrize("provider", ["claude", "codex"])
def test_no_command_resumes_or_continues_a_conversation(tmp_path, provider):
    argv = process_launcher(tmp_path, tmp_path / "p", provider=provider).command()

    assert not {"--resume", "-r", "--continue", "-c", "resume", "--last", "--session-id"} & set(argv)


@pytest.mark.parametrize("override", [{"provider": "gemini"}, {"model": ""}, {"model": None},
                                      {"executable": ""}, {"permission_mode": ""}])
def test_launcher_refuses_unsupported_provider_or_unconfigured_model(tmp_path, override):
    with pytest.raises(ValueError):
        process_launcher(tmp_path, tmp_path / "p", **override)


def test_launcher_refuses_a_workdir_that_is_not_a_linked_worktree(tmp_path):
    import subprocess
    plain = tmp_path / "plain"
    plain.mkdir()
    main_checkout = tmp_path / "main"
    subprocess.run(["git", "init", "-q", str(main_checkout)], check=True)
    subprocess.run(["git", "-C", str(main_checkout), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--allow-empty", "-m", "root"], check=True)
    linked = tmp_path / "linked"
    subprocess.run(["git", "-C", str(main_checkout), "worktree", "add", "-q", str(linked)], check=True)

    for refused in (plain, main_checkout):
        with pytest.raises(ValueError, match="isolated linked worktree"):
            ProcessDirectorLauncher(refused, tmp_path / "p", provider="claude", executable="x", model="m",
                                    permission_mode="bypassPermissions", output_dir=tmp_path / "o",
                                    require_isolated=True)
    assert ProcessDirectorLauncher(linked, tmp_path / "p", provider="claude", executable="x", model="m",
                                   permission_mode="bypassPermissions", output_dir=tmp_path / "o",
                                   require_isolated=True).workdir == linked


FAKE_CLAUDE = """#!/usr/bin/env bash
log="$(dirname "$0")/calls.jsonl"
prompt=$(cat)
printf '%s\\n' "$(python3 -c 'import json,os,sys; print(json.dumps({"argv": sys.argv[2:], "cwd": os.getcwd(), "prompt": sys.argv[1]}))' "$prompt" "$@")" >> "$log"
printf '%s' '{"type":"result","total_cost_usd":0.25,"usage":{"input_tokens":120,"output_tokens":45,"cache_read_input_tokens":7,"cache_creation_input_tokens":3},"modelUsage":{"claude-opus-5-5":{}}}'
exit 0
"""

FAKE_CODEX = """#!/usr/bin/env bash
cat >/dev/null
echo '{"type":"thread.started","thread_id":"t"}'
echo '{"type":"turn.completed","usage":{"input_tokens":200,"cached_input_tokens":50,"output_tokens":60}}'
exit 3
"""


def wait_until(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_real_claude_episodes_are_fresh_and_record_provider_model_and_usage(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(0o755)
    workdir = tmp_path / "work"
    workdir.mkdir()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Read docs/operations/factory-director-runtime-contract.md. Episode {{EPISODE_ID}}.")
    launcher = ProcessDirectorLauncher(workdir, prompt, provider="claude", executable=str(fake),
                                       model="claude-opus-5-5", permission_mode="bypassPermissions",
                                       output_dir=tmp_path / "host" / "episodes")
    service = FactoryDirectorHost(tmp_path / "host", required, launcher)

    first = service.reconcile()
    assert wait_until(lambda: launcher.liveness(launcher_episode(service)) is False)
    second = service.reconcile()
    assert wait_until(lambda: len((bin_dir / "calls.jsonl").read_text().splitlines()) == 2
                      if (bin_dir / "calls.jsonl").exists() else False)

    calls = [json.loads(line) for line in (bin_dir / "calls.jsonl").read_text().splitlines()]
    assert [call["prompt"] for call in calls] == [
        f"Read docs/operations/factory-director-runtime-contract.md. Episode {first.episode_id}.",
        f"Read docs/operations/factory-director-runtime-contract.md. Episode {second.episode_id}."]
    assert all(call["cwd"] == str(workdir) for call in calls)
    assert calls[0]["argv"] == calls[1]["argv"] == launcher.command()[1:]
    exited = [r for r in history(tmp_path / "host") if r["reason"] == "DIRECTOR_EPISODE_EXITED"][0]
    assert (exited["provider"], exited["requested_model"], exited["exit_reason"]) == ("claude", "claude-opus-5-5", "EXIT_0")
    assert exited["usage"] == {"measured": True, "observed_models": ["claude-opus-5-5"], "input_tokens": 120,
                               "output_tokens": 45, "cache_read_input_tokens": 7,
                               "cache_creation_input_tokens": 3, "cost_usd": 0.25}
    assert not (workdir / ".factory-director-host").exists()


def launcher_episode(service):
    lease = json.loads((service.root / "lease.json").read_text())
    return service._episode(lease)


def test_real_codex_episode_records_tokens_and_marks_model_and_cost_not_exposed(tmp_path):
    fake = tmp_path / "codex"
    fake.write_text(FAKE_CODEX)
    fake.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("episode {{EPISODE_ID}}")
    launcher = process_launcher(tmp_path, prompt, provider="codex", executable=str(fake), model="gpt-6-astra")
    inputs = MutableInputs(required())
    service = FactoryDirectorHost(tmp_path / "host", inputs, launcher)

    service.reconcile()
    assert wait_until(lambda: launcher.liveness(launcher_episode(service)) is False)
    inputs.values = required(eligible_authorized_work=False)
    assert service.reconcile().reason == "NO_ELIGIBLE_AUTHORIZED_WORK"

    exited = [r for r in history(tmp_path / "host") if r["reason"] == "DIRECTOR_EPISODE_EXITED"][0]
    assert (exited["provider"], exited["requested_model"], exited["exit_reason"]) == ("codex", "gpt-6-astra", "EXIT_3")
    assert exited["usage"] == {"measured": True, "turns": 1, "input_tokens": 200, "cached_input_tokens": 50,
                               "output_tokens": 60, "observed_models": None, "cost_usd": None}


def test_unmeasured_usage_is_recorded_as_unmeasured_never_zero(tmp_path):
    fake = tmp_path / "claude"
    fake.write_text("#!/usr/bin/env bash\ncat >/dev/null\necho 'not json'\n")
    fake.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("episode {{EPISODE_ID}}")
    launcher = process_launcher(tmp_path, prompt, provider="claude", executable=str(fake))
    inputs = MutableInputs(required())
    service = FactoryDirectorHost(tmp_path / "host", inputs, launcher)

    service.reconcile()
    assert wait_until(lambda: launcher.liveness(launcher_episode(service)) is False)
    inputs.values = required(eligible_authorized_work=False)
    service.reconcile()

    exited = [r for r in history(tmp_path / "host") if r["reason"] == "DIRECTOR_EPISODE_EXITED"][0]
    assert exited["usage"] == {"measured": False, "reason": "PROVIDER_DID_NOT_EXPOSE_USAGE"}


def test_unchanged_polls_do_not_grow_history_but_reason_changes_do(tmp_path):
    inputs = MutableInputs(required(eligible_authorized_work=False))
    service = FactoryDirectorHost(tmp_path, inputs, InMemoryDirectorLauncher())
    for _ in range(5):
        service.reconcile()
    inputs.values = required(explicit_pause=True)
    service.reconcile()

    assert [r["reason"] for r in history(tmp_path)] == ["NO_ELIGIBLE_AUTHORIZED_WORK", "FACTORY_PAUSED"]


# --- repairs from independent review 1 ----------------------------------------------------

from datetime import datetime, timedelta, timezone  # noqa: E402


class Clock:
    def __init__(self):
        self.offset = timedelta()

    def __call__(self):
        return datetime.now(timezone.utc) + self.offset


def test_repeated_fast_exits_back_off_instead_of_relaunching_every_second(tmp_path):
    clock = Clock()
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, required, launcher, clock=clock)

    first = service.reconcile()
    launcher.finish(first.episode_id, exit_code=1)
    second = service.reconcile()          # a single fast failure retries at once
    assert second.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    launcher.finish(second.episode_id, exit_code=1)

    refused = service.reconcile()         # the second consecutive one backs off
    assert (refused.reason, refused.state) == ("DIRECTOR_EPISODE_CRASH_LOOP", HostState.REFUSED)
    assert service.reconcile().reason == "DIRECTOR_EPISODE_CRASH_LOOP"
    assert len(launcher.launched) == 2
    lease = json.loads((tmp_path / "lease.json").read_text())
    assert lease["failure_streak"] == 2 and lease["retry_not_before"]

    clock.offset = timedelta(seconds=61)
    assert service.reconcile().reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    assert len(launcher.launched) == 3


def test_a_long_clean_episode_resets_the_failure_streak(tmp_path):
    clock = Clock()
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, required, launcher, clock=clock)
    launcher.finish(service.reconcile().episode_id, exit_code=1)
    episode = service.reconcile().episode_id
    clock.offset = timedelta(minutes=10)
    launcher.finish(episode, exit_code=0)

    assert service.reconcile().reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    assert json.loads((tmp_path / "lease.json").read_text())["failure_streak"] == 0


@pytest.mark.parametrize("provider,mode", [("codex", "bypassPermissions"), ("claude", "workspace-write"),
                                           ("claude", "danger-full-access"), ("codex", "plan")])
def test_permission_mode_must_belong_to_the_configured_provider(tmp_path, provider, mode):
    with pytest.raises(ValueError, match="permission"):
        process_launcher(tmp_path, tmp_path / "p", provider=provider, permission_mode=mode)


def test_pre_bind_launch_failure_kills_the_child_and_does_not_block_later_launches(tmp_path, monkeypatch):
    fake = tmp_path / "claude"
    fake.write_text("#!/usr/bin/env bash\nsleep 30\n")
    fake.chmod(0o755)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("episode {{EPISODE_ID}}")
    launcher = process_launcher(tmp_path, prompt, provider="claude", executable=str(fake))
    monkeypatch.setattr(launcher, "_process_start_ticks", lambda pid: None)
    import subprocess
    spawned, real_popen = [], subprocess.Popen

    def tracking(*args, **kwargs):
        spawned.append(real_popen(*args, **kwargs))
        return spawned[-1]
    monkeypatch.setattr("factory_director_host.subprocess.Popen", tracking)
    service = FactoryDirectorHost(tmp_path / "host", required, launcher)

    failed = service.reconcile()
    assert failed.reason == "DIRECTOR_LAUNCH_FAILED"
    assert launcher._children == {}
    assert len(spawned) == 1 and spawned[0].poll() is not None  # the unleased child is gone
    assert json.loads((tmp_path / "host" / "lease.json").read_text())["status"] == "LAUNCH_FAILED"

    monkeypatch.undo()
    retried = service.reconcile()
    assert retried.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    for child in launcher._children.values():
        child.kill()
        child.wait()


def test_inspection_of_an_activating_lease_is_refused_not_idle(tmp_path):
    service, _ = host(tmp_path)
    (tmp_path / "lease.json").write_text(json.dumps({
        "host_id": "old", "episode_id": "reserved", "pid": None, "started_at": "2026-01-01T00:00:00+00:00",
        "process_start_ticks": None, "status": "ACTIVATING"}))

    inspection = service.inspect()
    assert (inspection.state, inspection.last_reason) == (HostState.REFUSED, "AMBIGUOUS_LEASE")


def test_history_records_why_state_was_unavailable_and_each_new_cause(tmp_path):
    class Failing:
        def __init__(self):
            self.last_failure = "Founder-hold record is absent"

        def __call__(self):
            return required(authoritative_state=False)
    inputs = Failing()
    service = FactoryDirectorHost(tmp_path, inputs, InMemoryDirectorLauncher())
    service.reconcile()
    service.reconcile()
    inputs.last_failure = "Director inbox directory is absent"
    service.reconcile()

    assert [r.get("failure") for r in history(tmp_path)] == [
        "Founder-hold record is absent", "Director inbox directory is absent"]


def test_failure_streak_resets_when_the_factory_goes_idle(tmp_path):
    clock = Clock()
    inputs = MutableInputs(required())
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, inputs, launcher, clock=clock)
    launcher.finish(service.reconcile().episode_id, exit_code=1)
    launcher.finish(service.reconcile().episode_id, exit_code=1)
    assert service.reconcile().reason == "DIRECTOR_EPISODE_CRASH_LOOP"  # the exit is observed now
    clock.offset = timedelta(seconds=61)  # the pending back-off has elapsed
    inputs.values = required(eligible_authorized_work=False)
    assert service.reconcile().reason == "NO_ELIGIBLE_AUTHORIZED_WORK"
    assert json.loads((tmp_path / "lease.json").read_text())["failure_streak"] == 0

    inputs.values = required()
    third = service.reconcile()
    assert third.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    launcher.finish(third.episode_id, exit_code=1)
    assert service.reconcile().reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"  # first failure retries at once


def test_short_clean_episodes_that_changed_state_are_not_crashes(tmp_path):
    clock = Clock()
    inputs = MutableInputs(required(pending_director_inbox=True))
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, inputs, launcher, clock=clock)
    for flip in range(4):
        episode = service.reconcile()
        assert episode.reason in {"DIRECTOR_CONTINUITY_FAULT", "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"}, flip
        launcher.finish(episode.episode_id, exit_code=0)
        inputs.values = required(pending_director_inbox=flip % 2 == 0, lifecycle_requires_selection=True)
    assert len(launcher.launched) == 4


def test_short_clean_episodes_that_change_nothing_do_back_off(tmp_path):
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, required, launcher, clock=Clock())
    launcher.finish(service.reconcile().episode_id, exit_code=0)
    launcher.finish(service.reconcile().episode_id, exit_code=0)
    assert service.reconcile().reason == "DIRECTOR_EPISODE_CRASH_LOOP"


def test_an_exit_between_observation_and_lease_check_is_still_recorded_and_counted(tmp_path):
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, required, launcher, clock=Clock())
    first = service.reconcile()
    real_observe = service._observe_exit

    def exits_during_reconcile(values=None):
        real_observe(values)
        launcher.finish(first.episode_id, exit_code=1)  # after observation, before the lease check
    service._observe_exit = exits_during_reconcile
    service.reconcile()

    exits = [r for r in history(tmp_path) if r["reason"] == "DIRECTOR_EPISODE_EXITED"]
    assert [r["episode_id"] for r in exits] == [first.episode_id]
    assert json.loads((tmp_path / "lease.json").read_text())["failure_streak"] == 1


def test_repeated_launch_failures_back_off(tmp_path):
    class Broken(InMemoryDirectorLauncher):
        def launch(self, episode_id, on_spawned=None):
            raise OSError("prompt file missing")
    clock = Clock()
    service = FactoryDirectorHost(tmp_path, required, Broken(), clock=clock)
    assert service.reconcile().reason == "DIRECTOR_LAUNCH_FAILED"
    assert service.reconcile().reason == "DIRECTOR_LAUNCH_FAILED"
    assert service.reconcile().reason == "DIRECTOR_EPISODE_CRASH_LOOP"
    clock.offset = timedelta(seconds=61)
    assert service.reconcile().reason == "DIRECTOR_LAUNCH_FAILED"


# --- repairs from independent review 3 ----------------------------------------------------

class FingerprintedInputs(MutableInputs):
    def __init__(self, values, fingerprint="f0"):
        super().__init__(values)
        self.last_fingerprint = fingerprint


def test_short_episodes_that_advance_durable_state_under_the_same_projection_are_progress(tmp_path):
    inputs = FingerprintedInputs(required(pending_director_inbox=True))
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, inputs, launcher, clock=Clock())
    for handled in range(5):  # five inbox entries, one per short episode; the booleans never change
        episode = service.reconcile()
        assert episode.reason != "DIRECTOR_EPISODE_CRASH_LOOP", handled
        launcher.finish(episode.episode_id, exit_code=0)
        inputs.last_fingerprint = f"f{handled + 1}"
    assert len(launcher.launched) == 5


def test_same_fingerprint_short_exits_back_off_even_if_worker_capacity_flips(tmp_path):
    inputs = FingerprintedInputs(required())
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, inputs, launcher, clock=Clock())
    launcher.finish(service.reconcile().episode_id, exit_code=0)
    inputs.values = required(executable_capacity=False, pending_director_inbox=True)
    launcher.finish(service.reconcile().episode_id, exit_code=0)
    inputs.values = required()
    assert service.reconcile().reason == "DIRECTOR_EPISODE_CRASH_LOOP"


def test_exit_observed_while_state_is_unavailable_counts_as_unchanged(tmp_path):
    inputs = FingerprintedInputs(required())
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, inputs, launcher, clock=Clock())
    launcher.finish(service.reconcile().episode_id, exit_code=0)
    inputs.values, inputs.last_fingerprint = required(authoritative_state=False), None
    service.reconcile()
    assert json.loads((tmp_path / "lease.json").read_text())["failure_streak"] == 1


def test_a_brief_idle_does_not_cancel_a_pending_back_off(tmp_path):
    clock = Clock()
    inputs = MutableInputs(required())
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path, inputs, launcher, clock=clock)
    launcher.finish(service.reconcile().episode_id, exit_code=1)
    launcher.finish(service.reconcile().episode_id, exit_code=1)
    inputs.values = required(explicit_pause=True)
    service.reconcile()
    inputs.values = required()
    assert service.reconcile().reason == "DIRECTOR_EPISODE_CRASH_LOOP"
    clock.offset = timedelta(seconds=61)
    inputs.values = required(explicit_pause=True)
    service.reconcile()                    # idle after the back-off elapsed: the run is over
    assert json.loads((tmp_path / "lease.json").read_text())["failure_streak"] == 0
