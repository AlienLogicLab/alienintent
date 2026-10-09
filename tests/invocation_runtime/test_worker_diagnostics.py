"""Bounded worker-process diagnostics and the cause they show (VERIFIER-INFRASTRUCTURE-RETRY-AND-DIAGNOSTICS)."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.domain.diagnostics import ARGUMENT, TAIL, cause, process_diagnostics
from alienintent.invocation_runtime.domain.runtime import InvocationRole

DIMENSIONS = frozenset({"wall-clock", "cancellation"})


def failed(stdout: str = "", stderr: str = "", exit_status: int | None = 1) -> dict[str, object]:
    return process_diagnostics("codex", ["/opt/bin/codex", "exec"], "failure", exit_status, stdout, stderr)


@pytest.mark.parametrize(("kind", "diagnostics", "expected"), [
    ("success", failed(stdout="tests for 401 Unauthorized handling passed", exit_status=0), "success"),
    ("closed", None, "closed"),
    ("accept", None, "accept"),
    ("reject", None, "reject"),
    ("timeout", None, "timeout"),
    ("cancelled", None, "cancellation"),
    ("failure", failed(exit_status=-15), "cancellation"),
    ("failure", failed(stderr="error sending request for url (https://chatgpt.com/x)"), "network-or-provider"),
    ("failure", failed(stdout='{"type":"error","message":"workspace routing discovery failed"}'), "network-or-provider"),
    ("failure", failed(stderr="getaddrinfo EAI_AGAIN api.example"), "network-or-provider"),
    ("failure", failed(stderr="error sending request (status 401), will retry"), "network-or-provider"),
    ("failure", failed(stderr="HTTP 401 Unauthorized: not logged in"), "authentication"),
    ("failure", failed(exit_status=127, stderr="codex: not found"), "launcher-or-runtime"),
    ("verdict-malformed", process_diagnostics("codex", ["codex"], "success", 0, "", ""), "malformed-verdict"),
    ("verdict-missing", process_diagnostics("codex", ["codex"], "success", 0, "", ""), "malformed-verdict"),
    ("failure", failed(stderr="500 passed in 12.0s"), "unknown"),
    ("candidate-unavailable", failed(stdout="test_x timed out", exit_status=0), "unknown"),
    ("failure", None, "unknown"),
])
def test_the_cause_is_read_from_the_outcome_and_its_process(kind, diagnostics, expected):
    assert cause(kind, diagnostics) == expected


def test_the_diagnostics_are_bounded():
    record = process_diagnostics("routed", ["/opt/bin/codex", "y " * 500], "failure", 1, "out line\n" * 1200 + "END-OUT",
                                 "session id: 01a11efe-394f-7961\n" + "err line\n" * 1200 + "END-ERR")
    assert (record["provider"], record["executable"], record["session_id"]) == ("routed", "codex", "01a11efe-394f-7961")
    assert [len(argument) for argument in record["command"]] == [len("/opt/bin/codex"), ARGUMENT]
    assert len(record["stdout_tail"]) == TAIL and record["stdout_tail"].endswith("END-OUT")
    assert len(record["stderr_tail"]) == TAIL and record["stderr_tail"].endswith("END-ERR")
    assert (record["process_kind"], record["exit_status"]) == ("failure", 1)


def test_the_session_id_is_an_id_and_redacted():
    assert failed(stderr="the session id = ABCDEFGHIJ")["session_id"] is None
    assert failed(stdout="curl -d session_id=sk-proj-ABCDEFGH-IJKLMNOPQRSTUV")["session_id"] != "sk-proj-ABCDEFGH-IJKLMNOPQRSTUV"
    assert failed(stdout='{"session_id":"01a11efe-394f-7961-afd7-0a801bb17e76"}')["session_id"] == \
        "01a11efe-394f-7961-afd7-0a801bb17e76"


def test_the_kept_text_is_redacted():
    sha = "a" * 40
    secret_text = (f"commit {sha} Authorization: Bearer abc.def token=s3cr3t sk-proj-ABCDEFGHIJKLMNOP "
                   "ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345 eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl")
    record = process_diagnostics("codex", ["codex", "--api-key=sk-proj-ABCDEFGHIJKLMNOP"], "failure", 1, secret_text,
                                 secret_text)
    for kept in (record["stdout_tail"], record["stderr_tail"], " ".join(record["command"])):
        assert "[REDACTED]" in kept
        for secret in ("abc.def", "s3cr3t", "sk-proj-ABCDEFGHIJKLMNOP", "ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
                       "eyJhbGciOiJIUzI1NiJ9"):
            assert secret not in kept
    assert sha in record["stdout_tail"]


def test_the_cli_worker_records_each_process(tmp_path: Path):
    script = "import sys; print('out'); sys.stderr.write('err line\\n' * 600 + 'LAST'); sys.exit(3)"
    cli = CliWorkerProvider("python", sys.executable, ("-c", script), "explicit", DIMENSIONS)
    result = cli.run("invocation-1", InvocationRole.PRODUCER, tmp_path, 10)
    record = cli.diagnostics["invocation-1"]
    assert (result.kind, record["process_kind"], record["exit_status"]) == ("failure", "failure", 3)
    assert record["stdout_tail"].strip() == "out" and len(record["stderr_tail"]) == TAIL
    assert record["stderr_tail"].endswith("LAST")
    assert (record["provider"], record["executable"]) == ("python", Path(sys.executable).name)


def test_the_cli_worker_keeps_what_a_timed_out_process_wrote(tmp_path: Path):
    script = ("import sys, time; print('partial', flush=True); sys.stderr.write('session id: 0a1b2c3d-4e5f\\n');"
              " sys.stderr.flush(); time.sleep(30)")
    cli = CliWorkerProvider("python", sys.executable, ("-c", script), "explicit", DIMENSIONS)
    result = cli.run("invocation-3", InvocationRole.PRODUCER, tmp_path, 2)
    record = cli.diagnostics["invocation-3"]
    assert (result.kind, record["process_kind"]) == ("timeout", "timeout")
    assert record["stdout_tail"].strip() == "partial" and record["session_id"] == "0a1b2c3d-4e5f"


def test_the_cli_worker_records_a_verifier_stopped_by_its_feature_regressions(tmp_path: Path):
    cli = CliWorkerProvider("python", sys.executable, ("-c", "pass"), "explicit", DIMENSIONS)
    result = cli.run("invocation-2", InvocationRole.VERIFIER, tmp_path, 10)
    record = cli.diagnostics["invocation-2"]
    assert result.kind == "failure" and (record["executable"], record["process_kind"]) == ("feature-regressions", "failure")
    assert record["exit_status"] == result.exit_status
