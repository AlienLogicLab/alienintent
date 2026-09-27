"""B1P live trajectory-capture composition (WO-220610) under the C5 supervision. Local only.

- `host` is the capture process. It is the C5 hosted monitor process body, unchanged: it runs
  only as the supervisor-owned unit for its exact launch id, refuses otherwise before opening
  any store, and ticks its C4 generation so the external observer sees its health. It then
  reopens the capture journal, reconciles, records its session and serves one local socket.
- `launch`, `observe` and `restart` are the C5 supervisor (`MonitorHostSupervisor`) with only
  the hosted command changed to this module: same ownership record, manager-owned observer,
  durable alert and explicitly granted restart.
- `submit` is the ingestion interface: one JSON submission per connection on
  `<root>/trajectory-capture.sock`, answered only after the entry is committed. A source that
  cannot connect has nothing accepted; this composition buffers nothing for a down capture.
- Nothing here binds an operational target, issues live trajectory receipts, or claims
  observer replacement.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import sys
import time

from alienintent.composition.monitor_host import (
    EXIT_HOLD, EXIT_REFUSED, EXIT_SUPERSEDED, HostedMonitor, MonitorHostProfile, load_config, manager_environment,
    module_environment, own_cgroup, utc_micros,
)
from alienintent.control_plane.domain.monitor_health import MonitorHold
from alienintent.control_plane.domain.monitor_host import HostGrant, HostHold, SupervisionConfig
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.adapters.trajectory_journal import DurableTrajectoryJournal
from alienintent.evidence_learning.application.trajectory_capture_service import (
    TrajectoryCaptureService, replay,
)
from alienintent.evidence_learning.domain.trajectory_capture import CaptureHold, CapturePolicy, Submission
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

MODULE = "alienintent.composition.trajectory_capture"
MAX_SUBMISSION_BYTES = 1024 * 1024
POLL_SECONDS = 0.1
# One connection may hold the single-threaded host for at most this long, well inside 2*I.
READ_SECONDS = 0.5


def load_policy(path: Path | str | None) -> CapturePolicy:
    """The `capture` section of the same supervision configuration document."""
    if path is None:
        raise CaptureHold("CAPTURE_CONFIGURATION_MISSING")
    try:
        section = json.loads(Path(path).read_text()).get("capture")
    except (OSError, ValueError, AttributeError) as error:
        raise CaptureHold("CAPTURE_CONFIGURATION_INVALID") from error
    if not isinstance(section, dict) or set(section) != {"stall_seconds"}:
        raise CaptureHold("CAPTURE_CONFIGURATION_INVALID:capture")
    return CapturePolicy(**section)


def socket_path(config: SupervisionConfig) -> Path:
    return Path(config.root) / "trajectory-capture.sock"


def capture_journal(config: SupervisionConfig, invocation: str) -> DurableTrajectoryJournal:
    """The capture stream is the supervised invocation's; one journal per stream."""
    root = Path(config.root)
    return DurableTrajectoryJournal(SQLiteOperationalStore(root / "trajectory-capture.sqlite"),
                                    LocalEvidenceRepository(root / "trajectory-capture-evidence", config.project,
                                                            config.profile),
                                    project=config.project, name=config.profile, stream=config.host_invocation,
                                    invocation=invocation)


class TrajectoryCaptureProfile(MonitorHostProfile):
    """The C5 supervisor composition hosting the capture process instead of the bare monitor."""

    def command(self, launch_id: str | None) -> tuple[tuple[str, ...], dict[str, str], str]:
        root = Path(self.config.root)
        head = (self.config.python, "-B", "-m", MODULE)
        tail = ("--config", str(self.config_path))
        if launch_id is None:
            environment = module_environment(self.config) | {"XDG_RUNTIME_DIR": manager_environment()["XDG_RUNTIME_DIR"]}
            return (*head, "observe", *tail), environment, str(root / "trajectory-capture-observer.log")
        return ((*head, "host", "--launch-id", launch_id, *tail), module_environment(self.config),
                str(root / "trajectory-capture.log"))


class HostedCapture:
    """The capture process body: the C5 hosted monitor first, then the capture it hosts."""

    def __init__(self, config: SupervisionConfig, policy: CapturePolicy, launch_id: str, *,
                 clock: Callable[[], int] = utc_micros, cgroup: Callable[[], str] = own_cgroup) -> None:
        # Every C5 refusal (ownership, owned cgroup, configuration) happens before the journal opens.
        self.hosted = HostedMonitor(config, launch_id, clock=clock, cgroup=cgroup)
        self.capture = TrajectoryCaptureService(capture_journal(config, config.host_invocation + ":" + launch_id),
                                                policy, launch_id=launch_id, clock=clock)

    def start(self) -> dict[str, object]:
        self.hosted.start()
        return self.capture.start()

    def cycle(self) -> None:
        self.hosted.cycle()


def serve(capture: TrajectoryCaptureService, connection: socket.socket,
          monotonic: Callable[[], float] = time.monotonic) -> None:
    """One submission, one reply. The reply is sent only after the entry is committed. A client
    that does not finish its submission within READ_SECONDS is dropped with nothing written."""
    with connection:
        deadline = monotonic() + READ_SECONDS
        body = b""
        try:
            while not body.endswith(b"\n") and len(body) <= MAX_SUBMISSION_BYTES:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    return
                connection.settimeout(remaining)
                chunk = connection.recv(65536)
                if not chunk:
                    break
                body += chunk
        except OSError:
            return
        try:
            if len(body) > MAX_SUBMISSION_BYTES:
                raise CaptureHold("SUBMISSION_TOO_LARGE")
            try:
                document = json.loads(body)
            except (ValueError, RecursionError) as error:
                raise CaptureHold("SUBMISSION_INVALID:json") from error
            reply: dict[str, object] = capture.submit(Submission.from_document(document))
        except CaptureHold as hold:
            if hold.reason.startswith("JOURNAL_"):
                raise
            reply = {"hold": hold.reason}
        try:
            connection.sendall(json.dumps(reply, sort_keys=True).encode() + b"\n")
        except OSError:
            pass  # A lost acknowledgement leaves the entry committed; a retry is a recorded duplicate.


def run_capture_host(config: SupervisionConfig, policy: CapturePolicy, launch_id: str, stop: Callable[[], bool],
                     monotonic: Callable[[], float] = time.monotonic) -> int:
    try:
        hosted = HostedCapture(config, policy, launch_id)
    except HostHold as hold:
        print(json.dumps({"host": "REFUSED", "reason": hold.reason}), flush=True)
        return EXIT_REFUSED
    path = socket_path(config)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # The owned unit is the only host: C5 confirmed its predecessor's cgroup empty before launch.
    # The socket is bound before the session opens, so a bind failure writes nothing.
    previous = os.umask(0o177)
    try:
        path.unlink(missing_ok=True)
        listener.bind(str(path))
        listener.listen(16)
    except OSError:
        listener.close()
        print(json.dumps({"host": "HOLD", "reason": "CAPTURE_SOCKET_UNAVAILABLE"}), flush=True)
        return EXIT_HOLD
    finally:
        os.umask(previous)
    try:
        opened = hosted.start()
    except CaptureHold as hold:
        listener.close()
        print(json.dumps({"host": "HOLD", "reason": hold.reason}), flush=True)
        return EXIT_HOLD
    selector = selectors.DefaultSelector()
    selector.register(listener, selectors.EVENT_READ)
    print(json.dumps({"host": "STARTED", "launch_id": launch_id, "session": opened["session"],
                      "entry_seq": opened["entry_seq"]}), flush=True)
    deadline = monotonic()
    try:
        while not stop():
            if monotonic() >= deadline:
                hosted.cycle()
                deadline = monotonic() + config.policy.interval_seconds
            for _ in selector.select(timeout=POLL_SECONDS):
                try:
                    connection, _ = listener.accept()
                except OSError:
                    continue  # an aborted connection is the client's; nothing was submitted
                serve(hosted.capture, connection)
            hosted.capture.check_stall()
    except MonitorHold as hold:
        if hold.reason == "STALE_INSTANCE":
            print(json.dumps({"host": "SUPERSEDED", "launch_id": launch_id}), flush=True)
            return EXIT_SUPERSEDED
        raise
    except CaptureHold as hold:
        if hold.reason == "JOURNAL_VERSION_CONFLICT":
            print(json.dumps({"host": "SUPERSEDED", "launch_id": launch_id}), flush=True)
            return EXIT_SUPERSEDED
        raise
    finally:
        selector.close()
        listener.close()
    return 0


def submit(path: Path | str, document: object, timeout: float = 10.0) -> dict[str, object]:
    """Hand one submission to a running capture; raises OSError when none is listening."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(str(path))
        client.sendall(json.dumps(document, sort_keys=True).encode() + b"\n")
        body = b""
        while not body.endswith(b"\n"):
            chunk = client.recv(65536)
            if not chunk:
                raise ConnectionError("capture closed without acknowledgement")
            body += chunk
    return json.loads(body)


def read_journal(config: SupervisionConfig) -> dict[str, object]:
    """Read-only: every committed entry and the state a restarted capture would rebuild."""
    entries = capture_journal(config, "trajectory-capture-reader").entries()
    state = replay(entries)
    return {"entries": list(entries), "state": {
        "entries": state.entries, "events": state.events, "sessions": state.sessions,
        "sources": state.sources, "last_captured_at": state.last_captured_at}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=MODULE, description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("host", "launch", "observe", "restart", "show", "submit", "journal"))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--launch-id")
    parser.add_argument("--actor")
    parser.add_argument("--authority")
    parser.add_argument("--replaces")
    parser.add_argument("--alert")
    arguments = parser.parse_args(argv)
    try:
        config = load_config(arguments.config)
        policy = load_policy(arguments.config)
        if arguments.command == "host":
            stopping = []
            signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
            return run_capture_host(config, policy, arguments.launch_id or "", lambda: bool(stopping))
        if arguments.command == "submit":
            replies = []
            for line in sys.stdin:
                if line.strip():
                    try:
                        replies.append(submit(socket_path(config), json.loads(line)))
                    except OSError as error:
                        replies.append({"hold": "CAPTURE_UNAVAILABLE", "error": type(error).__name__})
            print(json.dumps({"replies": replies}), flush=True)
            return 0 if all("hold" not in r for r in replies) else EXIT_HOLD
        if arguments.command == "journal":
            print(json.dumps(read_journal(config)), flush=True)
            return 0
        profile = TrajectoryCaptureProfile(config, arguments.config)
        binding = config.binding()
        if arguments.command in ("launch", "restart"):
            grant = HostGrant(arguments.actor or "", arguments.authority or "", binding.profile, binding.unit,
                              binding.host_invocation, arguments.replaces, arguments.alert)
            action = profile.supervisor.launch if arguments.command == "launch" else profile.supervisor.restart
            result: object = asdict(action(grant))
        elif arguments.command == "observe":
            detection, ownership = profile.supervisor.observe()
            result = {"detection": asdict(detection), "ownership": asdict(ownership)}
        else:
            _, ownership = profile.records.read(config.profile)
            result = {"ownership": None if ownership is None else asdict(ownership)}
    except (HostHold, CaptureHold) as hold:
        print(json.dumps({"hold": hold.reason}), flush=True)
        return EXIT_HOLD
    print(json.dumps(result, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
