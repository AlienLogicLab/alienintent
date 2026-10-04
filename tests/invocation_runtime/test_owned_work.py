"""WO-220404 AC-08: invocation ownership includes the work an invocation starts.

The process adapter supervises a real child. A client that exits while work it
started is still running - even work that detached into its own session and
redirected its output away from the supervisor - does not end the invocation.
The ``/proc`` observation behind it answers only from the kernel, and anything
it cannot read is unknown, never terminated.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.domain.runtime import INVOCATION_MARKER, InvocationRole

DIMENSIONS = frozenset({"wall-clock", "cancellation"})
DETACHED = "setsid bash -c 'sleep {delay}; echo finished > \"$1\"' _ \"$1\" > /dev/null 2>&1 < /dev/null &\nexit 0\n"


def worker(tmp_path: Path, delay: float) -> CliWorkerProvider:
    script = tmp_path / "client.sh"
    script.write_text(DETACHED.format(delay=delay))
    environment = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "LANG": "C.UTF-8"}
    return CliWorkerProvider("claude", "/bin/bash", (str(script), str(tmp_path / "result.txt")), "explicit", DIMENSIONS, environment=environment)


def test_client_exit_with_detached_owned_work_active_does_not_end_the_invocation(tmp_path: Path) -> None:
    provider = worker(tmp_path, 1)

    result = provider.run("launch:AC08:0", InvocationRole.PRODUCER, tmp_path, 30)

    assert result.kind == "success" and result.quiescent
    assert (tmp_path / "result.txt").exists(), "the invocation ended while owned background work was still active"
    assert ProcOwnership().owned_work("launch:AC08:0") == ()
    assert provider.cancel("launch:AC08:0", "probe").kind == "already-finished"


def test_owned_work_outliving_the_wall_clock_is_stopped_with_the_client(tmp_path: Path) -> None:
    provider = worker(tmp_path, 30)

    result = provider.run("launch:AC08:1", InvocationRole.PRODUCER, tmp_path, 1)

    assert result.kind == "timeout" and result.quiescent
    assert ProcOwnership().owned_work("launch:AC08:1") == ()
    assert not (tmp_path / "result.txt").exists()


def test_the_owner_identity_distinguishes_a_live_process_from_an_ended_or_reused_one(tmp_path: Path) -> None:
    ownership = ProcOwnership()
    me = ownership.current()
    assert me is not None and me["pid"] == os.getpid()

    child = subprocess.run([sys.executable, "-c", "import json,os; from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership; print(json.dumps(ProcOwnership().current()))"],
                           capture_output=True, text=True, check=True, env=os.environ | {"PYTHONPATH": os.pathsep.join(sys.path)})
    ended = json.loads(child.stdout)

    assert ownership.owner_state(me) == "alive"
    assert ownership.owner_state(ended) == "terminated"
    assert ownership.owner_state(dict(me) | {"start": int(me["start"]) + 1}) == "terminated", "a reused pid read as the owner"
    assert ownership.owner_state(dict(me) | {"boot": "another-boot"}) == "terminated"
    assert ownership.owner_state({"pid": "1"}) == "unknown"
    assert ProcOwnership(tmp_path / "no-proc").owner_state(me) == "unknown"
    assert ProcOwnership(tmp_path / "no-proc").owned_work("x") is None


def test_owned_work_is_found_by_its_marker_even_in_another_session(tmp_path: Path) -> None:
    survivor = subprocess.Popen(["setsid", "sleep", "30"], env={"PATH": os.environ["PATH"], INVOCATION_MARKER: "launch:AC08:2"})
    try:
        deadline = time.monotonic() + 5
        while not ProcOwnership().owned_work("launch:AC08:2") and time.monotonic() < deadline:
            time.sleep(0.05)
        assert ProcOwnership().owned_work("launch:AC08:2") == (survivor.pid,)
        assert ProcOwnership().owned_work("launch:AC08:20") == ()
    finally:
        survivor.kill()
        survivor.wait()
    assert ProcOwnership().owned_work("launch:AC08:2") == ()


def test_another_owners_work_with_the_same_invocation_identity_is_neither_awaited_nor_stopped(tmp_path: Path) -> None:
    """Correlation ids repeat across profiles; ownership is bound to the owning provider, not the id alone."""
    from threading import Thread

    other_root, own_root = tmp_path / "other", tmp_path / "own"
    other_root.mkdir()
    own_root.mkdir()
    other = worker(other_root, 3)
    finished: list[object] = []
    thread = Thread(target=lambda: finished.append(other.run("launch:SHARED:0", InvocationRole.PRODUCER, other_root, 30)))
    thread.start()
    deadline = time.monotonic() + 5
    while not ProcOwnership().owned_work("launch:SHARED:0") and time.monotonic() < deadline:
        time.sleep(0.05)
    quick = own_root / "quick.sh"
    quick.write_text("exit 0\n")
    own = CliWorkerProvider("claude", "/bin/bash", (str(quick),), "explicit", DIMENSIONS,
                            environment={"PATH": os.environ["PATH"], "HOME": str(own_root), "LANG": "C.UTF-8"})

    began = time.monotonic()
    result = own.run("launch:SHARED:0", InvocationRole.PRODUCER, own_root, 1)
    elapsed = time.monotonic() - began
    thread.join(10)

    assert result.kind == "success" and elapsed < 1, f"another owner's work was awaited ({elapsed:.1f}s, {result.kind})"
    assert finished and finished[0].kind == "success" and (other_root / "result.txt").exists(), "another owner's work was stopped"


def test_only_a_worker_whose_owned_work_is_marked_journals_an_attestable_owner(tmp_path: Path) -> None:
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
    from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider

    def started_owner(environment) -> object:
        journal = JsonlInvocationJournal(tmp_path / f"journal-{environment is None}.jsonl", lambda: 0.0)
        process = CliWorkerProvider("claude", "/bin/true", (), "explicit", DIMENSIONS, environment=environment)
        provider = RealWorkerProvider(process, None, tmp_path, "origin", "b", tmp_path, None, "t", None, now=lambda: 0.0, sleep=lambda _: None,  # type: ignore[arg-type]
                                      journal=journal, ownership=ProcOwnership())
        invocation = WorkerInvocation("W", "launch:W:0", None, "OTHER")
        provider.start(invocation, None, frozenset(), BudgetPolicy())
        return journal.records()[0].get("owner"), provider.attest_ownership(invocation).kind

    # An inherited environment carries no marker, so surviving work could not be seen: never attestable.
    assert started_owner(None) == (None, "owner-unattested")
    owner, kind = started_owner({"PATH": os.environ["PATH"]})
    assert isinstance(owner, dict) and kind == "owner-alive"


def test_an_owner_recorded_in_another_pid_namespace_is_unknown() -> None:
    ownership = ProcOwnership()
    me = ownership.current()

    assert me is not None and ownership.owner_state(dict(me) | {"pidns": -1}) == "unknown"


# --- WORKER-CREDENTIAL-BOUNDARY acceptance check 5: ownership and stopping across users ------------------------------
import pytest  # noqa: E402

from alienintent.invocation_runtime.domain.runtime import INVOCATION_OWNER_MARKER  # noqa: E402

WORKER_UID = 4321


def fake_proc(root: Path, processes: dict[int, dict]) -> Path:
    """A fake /proc: each pid's status (real uid), stat (state, session) and, when readable, environ."""
    for pid, spec in processes.items():
        entry = root / str(pid)
        entry.mkdir(parents=True)
        (entry / "status").write_text(f"Name:\tx\nUid:\t{spec['uid']}\t{spec['uid']}\t{spec['uid']}\t{spec['uid']}\n")
        (entry / "stat").write_text(f"{pid} (x) {spec.get('state', 'S')} 1 {spec['session']} {spec['session']} "
                                    + " ".join(["0"] * 30) + "\n")
        if "environ" in spec:
            (entry / "environ").write_bytes(b"\0".join(v.encode() for v in spec["environ"]) + b"\0")
        else:
            (entry / "environ").mkdir()  # unreadable as a file, as another user's environ is
    return root


def test_with_a_worker_user_ownership_is_by_real_uid_and_session_and_unreadable_worker_work_is_alive(tmp_path):
    proc = tmp_path / "proc"
    marked = [f"{INVOCATION_MARKER}=inv", f"{INVOCATION_OWNER_MARKER}=owner/1"]
    fake_proc(proc, {
        10: {"uid": 0, "session": 99},                                  # root, unreadable: never the worker's
        11: {"uid": 1000, "session": 99, "environ": marked},            # the Founder's own marked process: not counted
        20: {"uid": WORKER_UID, "session": 500, "environ": []},         # the worker, in the launched session
        21: {"uid": WORKER_UID, "session": 500, "state": "Z"},          # a zombie in the session: ended
        30: {"uid": WORKER_UID, "session": 77, "environ": marked},      # the worker, detached but marked: owned
    })
    ownership = ProcOwnership(proc, worker_uid=WORKER_UID)
    assert ownership.owned_work("inv", "owner", session=500) == (20, 30)
    fake_proc(tmp_path / "root-only", {10: {"uid": 0, "session": 99}})
    assert ProcOwnership(tmp_path / "root-only", worker_uid=WORKER_UID).owned_work("inv", session=500) == ()
    fake_proc(tmp_path / "hidden", {40: {"uid": WORKER_UID, "session": 77}})  # outside the session, unreadable
    assert ProcOwnership(tmp_path / "hidden", worker_uid=WORKER_UID).owned_work("inv", session=500) is None
    # Without a worker user nothing changes: only the marker counts, whoever owns the process.
    assert ProcOwnership(proc).owned_work("inv", "owner") == (11, 30)


class _Stated(ProcOwnership):
    def __init__(self, work):
        super().__init__()
        self.work = work

    def owned_work(self, invocation_id, owner=None, *, session=None):
        return self.work


@pytest.mark.parametrize("work", [None, (4_194_301,)])
def test_owned_treats_none_as_alive_and_every_stop_goes_through_sudo_kill(tmp_path, monkeypatch, work):
    from tests.invocation_runtime.test_git_source_control import USER, install_fake_sudo, sudo_calls
    log = install_fake_sudo(tmp_path / "bin", monkeypatch)
    command = tmp_path / "client.sh"
    command.write_text("#!/bin/sh\nexit 0\n")
    command.chmod(0o755)
    provider = CliWorkerProvider("fixture", str(command), (), "explicit", frozenset({"wall-clock", "cancellation"}),
                                 {"HOME": str(tmp_path)}, ownership=_Stated(work), worker_user=USER,
                                 results=tmp_path / "results", regression_base=lambda _: None)
    result = provider.run("inv", InvocationRole.PRODUCER, tmp_path, 0.5)
    assert result.kind == "timeout" and result.quiescent is False  # owned work (None or a pid) is never "ended"
    calls = [c["argv"] for c in sudo_calls(log)]
    [session] = [c for c in calls if "env" in c]
    kills = [c for c in calls if c[3] == "kill"]
    assert kills and all(c[:4] == ["-n", "-u", USER, "kill"] and c[5] == "--" for c in kills)
    groups = {c[6] for c in kills if c[6].startswith("-")}
    assert len(groups) == 1 and {c[4] for c in kills} == {"-15", "-9"}
    if work is not None:
        assert {c[6] for c in kills if not c[6].startswith("-")} == {str(work[0])}
    assert session[:7] == ["-n", "-u", USER, "--", "env", "-i", "PATH=/usr/bin:/bin"]
