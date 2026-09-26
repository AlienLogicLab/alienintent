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
