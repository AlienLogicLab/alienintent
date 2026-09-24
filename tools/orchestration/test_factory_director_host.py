"""Contract tests for the temporary, non-cognizant Factory Director Host."""
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
    launcher = ProcessDirectorLauncher(tmp_path, prompt, codex="unused", model="test")
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
    launcher = ProcessDirectorLauncher(tmp_path, prompt, codex=str(fake_codex), model="test")

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
        ProcessDirectorLauncher(tmp_path, prompt, codex=str(fake_codex), model="test"),
    )

    first = service.reconcile()
    time.sleep(0.05)
    second = service.reconcile()

    assert first.reason == "DIRECTOR_CONTINUITY_FAULT"
    assert second.reason == "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"
    assert first.episode_id != second.episode_id
