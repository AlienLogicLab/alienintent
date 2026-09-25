"""Agent Ready public-interface producers: the published CLI and the host-managed local MCP stdio server.

Each adapter is constructed from the ProducerBinding resolved at composition and launches exactly the bound
executable; it never imports Agent Ready, supplies a prompt, rubric or schema of its own, or judges the result. It
returns the raw response bytes unparsed, with custody of what it observed about its own invocation: the attempt the
response answers, the digest of the text actually submitted, the arguments or tool request, and timestamps. CLI
custody is correlated by the process launched for the attempt; MCP custody names the JSON-RPC id the response
itself carries, so a response to another request cannot be attributed to this attempt. Input limits are the
product's: text is never truncated here. Syntax, tool name and limits are pinned by the FX-U10 conformance fixture.
Each launch gets its own process group, killed at the deadline and on return, so no provider descendant outlives
its attempt.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
from tempfile import TemporaryDirectory
import threading
import time
from typing import Callable, Mapping

from alienintent.execution_coordination.domain.readiness import (
    DIRECT, MCP, CandidateWorkUnit, InvocationCustody, ProducerBinding, ProducerResponse, digest)
from alienintent.execution_coordination.ports.readiness import ReadinessAssessment

MCP_TOOL = "assess_work_unit"
MCP_PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO = {"name": "alienintent-readiness", "version": "1"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kill_group(process: subprocess.Popen) -> None:
    """Kill the launched process and every descendant still in its session's process group."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


class _Producer(ReadinessAssessment):
    def __init__(self, binding: ProducerBinding, provider: str, environment: Mapping[str, str] | None = None,
                 timeout_s: float = 900, clock: Callable[[], str] = _now) -> None:
        self.binding, self.provider, self.timeout_s, self._clock = binding, provider, timeout_s, clock
        self._environment = None if environment is None else dict(environment)

    def _custody(self, attempt_id: str, input_sha256: str, arguments: tuple[str, ...], started: str,
                 sdk_version: str | None = None) -> InvocationCustody:
        return InvocationCustody(attempt_id, input_sha256, self.binding.product, self.binding.product_version,
                                 self.binding.executable, arguments, self.provider, started, self._clock(),
                                 None, sdk_version)


class AgentReadyCliAssessment(_Producer, ReadinessAssessment):
    """`agent-ready assess <file> --provider <p> --json`: stdout bytes and exit status, never exit status alone."""

    def assess(self, candidate_work_unit: CandidateWorkUnit) -> ProducerResponse:
        unit = candidate_work_unit
        started = self._clock()
        with TemporaryDirectory(prefix="alienintent-readiness-") as directory:
            source = Path(directory) / "work-unit.md"
            source.write_bytes(unit.text.encode("utf-8"))
            submitted = digest(source.read_bytes().decode("utf-8"))  # What the product will read, read back.
            arguments = (self.binding.executable, "assess", str(source), "--provider", self.provider, "--json")
            raw, status, timed_out = None, None, False
            try:
                process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                           env=self._environment, cwd=directory, start_new_session=True)
            except OSError:
                process = None  # No process and no output: an attempt failure with nothing to attribute.
            if process is not None:
                try:
                    raw, _ = process.communicate(timeout=self.timeout_s)
                    status = process.returncode
                except subprocess.TimeoutExpired:
                    timed_out = True
                    _kill_group(process)
                    raw, _ = process.communicate()  # Partial output only; a timeout is never a result.
                finally:
                    _kill_group(process)
        return ProducerResponse(raw, status, timed_out, DIRECT,
                                self._custody(unit.attempt_id, submitted, arguments, started))


class AgentReadyMcpAssessment(_Producer, ReadinessAssessment):
    """One stdio session per attempt: initialize, then `tools/call assess_work_unit {text, provider}`.

    The tool response is retained as the exact JSON-RPC line the server wrote, wrapper included. An MCP result has
    no process exit status of its own, so none is reported.
    """

    def assess(self, candidate_work_unit: CandidateWorkUnit) -> ProducerResponse:
        unit = candidate_work_unit
        started = self._clock()
        request = {"jsonrpc": "2.0", "id": unit.attempt_id, "method": "tools/call",
                   "params": {"name": MCP_TOOL, "arguments": {"text": unit.text, "provider": self.provider}}}
        arguments = (self.binding.executable, "tools/call", MCP_TOOL, "provider=" + self.provider,
                     "id=" + unit.attempt_id, "protocolVersion=" + MCP_PROTOCOL_VERSION)
        wire = json.dumps(request).encode("utf-8")
        submitted = digest(json.loads(wire)["params"]["arguments"]["text"])  # The text as sent, read back.
        raw, answered, sdk_version, timed_out = None, "", None, False
        try:
            process = subprocess.Popen([self.binding.executable], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, env=self._environment, start_new_session=True)
        except OSError:
            return ProducerResponse(None, None, False, MCP, self._custody("", submitted, arguments, started))
        lines: queue.Queue = queue.Queue()
        threading.Thread(target=self._pump, args=(process, lines), daemon=True).start()
        deadline = time.monotonic() + self.timeout_s
        expired = threading.Event()
        # A write to a server that stopped reading blocks; the watchdog ends the session at the deadline instead.
        watchdog = threading.Timer(self.timeout_s, lambda: (expired.set(), _kill_group(process)))
        watchdog.daemon = True
        watchdog.start()
        try:
            initialize = {"jsonrpc": "2.0", "id": "initialize:" + unit.attempt_id, "method": "initialize",
                          "params": {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {},
                                     "clientInfo": CLIENT_INFO}}
            self._send(process, json.dumps(initialize).encode("utf-8"))
            line, message = self._response(lines, deadline)
            result = message.get("result") if isinstance(message, dict) else None
            if not isinstance(result, dict):
                raw = line  # A failed handshake is retained as the terminal response; it answers no tool call.
            else:
                server = result.get("serverInfo")
                version = server.get("version") if isinstance(server, dict) else None
                sdk_version = version if isinstance(version, str) else None
                self._send(process, json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode())
                self._send(process, wire)
                raw, message = self._response(lines, deadline)
                identifier = message.get("id") if isinstance(message, dict) else None
                answered = identifier if isinstance(identifier, str) else ""
        except TimeoutError:
            timed_out = True
        except OSError:
            pass  # The server closed its input; whatever it answered is already held above.
        finally:
            watchdog.cancel()
            self._stop(process)
        timed_out = timed_out or (expired.is_set() and raw is None)  # A complete answer that raced it stands.
        return ProducerResponse(raw, None, timed_out, MCP,
                                self._custody(answered, submitted, arguments, started, sdk_version))

    @staticmethod
    def _pump(process: subprocess.Popen, lines: queue.Queue) -> None:
        try:
            for line in process.stdout:
                lines.put(line)
        except (OSError, ValueError):
            pass  # The session was ended and its output closed.
        lines.put(None)

    @staticmethod
    def _send(process: subprocess.Popen, message: bytes) -> None:
        process.stdin.write(message + b"\n")
        process.stdin.flush()

    @staticmethod
    def _response(lines: queue.Queue, deadline: float) -> tuple[bytes | None, object]:
        """The next response line, byte-for-byte less its newline framing; notifications and requests are skipped."""
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError
            try:
                line = lines.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError from None
            if line is None:
                return None, None  # The server ended without answering.
            raw = line[:-1] if line.endswith(b"\n") else line
            try:
                message = json.loads(raw)
            except ValueError:
                return raw, None  # Unparsable bytes are retained and fail recognition.
            if isinstance(message, dict) and "method" in message:
                continue
            return raw, message

    @staticmethod
    def _stop(process: subprocess.Popen) -> None:
        try:
            process.stdin.close()
        except OSError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        _kill_group(process)
        process.wait()
        process.stdout.close()
