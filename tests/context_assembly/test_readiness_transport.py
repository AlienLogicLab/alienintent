"""FX-U10 probes: the Agent Ready CLI/MCP transport boundary into the retained consumer (WO-220210, U10).

Composed through UpstreamProfile over a real temporary SQLite store, local evidence, the U5 design gate and the
FactoryCoordinator lifecycle, with the producer adapter constructed from the resolved binding. The deterministic
probes launch a labelled stand-in executable (FIXTURE_EXECUTABLE_NOT_AGENT_READY) as a real subprocess over the
pinned public contract; it proves transport, custody and refusal mechanics, never native-producer identity. The
native probes launch the configured Agent Ready product itself and run only when FX_U10_AGENT_READY_BIN names its
environment's bin directory; full provider-backed assessments additionally need FX_U10_NATIVE_ASSESS=1.
"""
from dataclasses import replace
import json
import os
from pathlib import Path
import sys

import pytest

from alienintent.composition.readiness import compose_producer
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.execution_coordination.adapters.agent_ready_producer import (
    MCP_PROTOCOL_VERSION, MCP_TOOL, AgentReadyCliAssessment, AgentReadyMcpAssessment)
from alienintent.execution_coordination.domain import release as release_domain
from alienintent.execution_coordination.domain.readiness import (
    ATTEMPT_FAILURE, CAPABILITY_PROVENANCE_HOLD, CONFLICTING, CONTRACT_VERSION, DISPOSITIONS, MALFORMED, MCP,
    MCP_ERROR, NO_TERMINAL_RESULT, PROVENANCE, PROVIDER_FAILURE, READY, TIMEOUT, UNKNOWN, AttemptFailure, Hold,
    ReadinessEligibility, SemanticAssessment, digest, recognize)
from tests.context_assembly.test_readiness_consumer import (
    P1, PLAN, X, Harness, body, candidate, encode, envelope, record)

ROOT = Path(__file__).resolve().parents[2]
CONFORMANCE = json.loads((ROOT / "docs/evidence/wave2-proof-fixtures/FX-U10/agent-ready-public-contract.json")
                         .read_text())
FIXTURE_EXECUTABLE = "FIXTURE_EXECUTABLE_NOT_AGENT_READY"
SCRIPTS = {"cli": "agent-ready", "mcp": "agent-ready-mcp"}

STAND_IN = r'''#!{python}
# FIXTURE_EXECUTABLE_NOT_AGENT_READY: an FX-U10 stand-in speaking the pinned public contract; not Agent Ready.
import hashlib, json, sys, time
from pathlib import Path
HOME = Path(__file__).resolve().parent.parent
behavior = json.loads((HOME / "behavior.json").read_text())
def log(entry):
    with (HOME / "calls.jsonl").open("a") as stream:
        stream.write(json.dumps(entry) + "\n")
def send(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
if Path(sys.argv[0]).name == "agent-ready":
    text = Path(sys.argv[2]).read_bytes()
    log({"argv": sys.argv, "text_sha256": hashlib.sha256(text).hexdigest(), "text_chars": len(text.decode())})
    time.sleep(behavior.get("sleep", 0))
    sys.stdout.buffer.write(bytes.fromhex(behavior["stdout_hex"]))
    sys.exit(behavior.get("exit", 0))
for line in sys.stdin:
    message = json.loads(line)
    if message.get("method") == "initialize":
        send(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": {
            "protocolVersion": message["params"]["protocolVersion"], "capabilities": {"tools": {}},
            "serverInfo": {"name": "agent-ready", "version": "1.29.1"}}}))
    elif message.get("method") == "tools/call":
        arguments = message["params"]["arguments"]
        log({"name": message["params"]["name"], "keys": sorted(arguments), "provider": arguments.get("provider"),
             "text_sha256": hashlib.sha256(arguments["text"].encode()).hexdigest(),
             "text_chars": len(arguments["text"])})
        time.sleep(behavior.get("sleep", 0))
        if behavior.get("exit_without_reply"):
            sys.exit(0)
        send(json.dumps({"jsonrpc": "2.0", "method": "notifications/message", "params": {"level": "info"}}))
        send(behavior["line"].replace("__ID__", json.dumps(behavior.get("answer_id", message["id"]))))
'''


def stand_in(home: Path, name: str = "agent-ready", version: str = "0.1.0rc1", metadata: bool = True) -> Path:
    """A disposable distribution whose console scripts are the labelled stand-in; returns its bin directory."""
    binaries = home / "bin"
    binaries.mkdir(parents=True)
    for script in SCRIPTS.values():
        path = binaries / script
        path.write_text(STAND_IN.replace("{python}", sys.executable))
        path.chmod(0o700)
    if metadata:
        info = home / "lib" / "python3.12" / "site-packages" / f"{name.replace('-', '_')}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
        (info / "entry_points.txt").write_text("[console_scripts]\n" + "".join(
            f"{script} = fixture_only:main\n" for script in SCRIPTS.values()))
    return binaries


def cli(stdout: bytes, exit_status: int = 0, sleep: float = 0) -> dict:
    return {"stdout_hex": stdout.hex(), "exit": exit_status, "sleep": sleep}


def mcp(result: object = None, error: object = None, **options) -> dict:
    """One JSON-RPC response line; __ID__ becomes the id the stand-in answers (the request's unless overridden)."""
    member = {"error": error} if error is not None else {}
    if result is not None:
        member["result"] = result
    line = '{"jsonrpc": "2.0", "id": __ID__, ' + json.dumps(member)[1:]
    return {"line": line, **options}


def ready_bytes() -> bytes:
    return encode(record("ready")["assessment"])


class Composed:
    def __init__(self, harness: Harness, vector: dict, home: Path, transport: str) -> None:
        self.h, self.vector, self.home, self.transport = harness, vector, home, transport

    @property
    def executable(self) -> str:
        return str(self.home / "bin" / SCRIPTS[self.transport])

    def calls(self) -> list[dict]:
        log = self.home / "calls.jsonl"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


@pytest.fixture
def compose(tmp_path):
    count = iter(range(1000))

    def factory(transport: str = "cli", behavior: dict | None = None, package: dict | None = None,
                bound: bool = True) -> Composed:
        n = next(count)
        home = tmp_path / f"stand-in{n}"
        binaries = stand_in(home, **(package or {}))
        (home / "behavior.json").write_text(json.dumps(behavior or {}))
        h = Harness(tmp_path / f"h{n}", None, executable=binaries / SCRIPTS[transport] if bound else None,
                    provider="claude", transport=transport)
        h.lifecycle(P1, "DONE")
        return Composed(h, h.design("verified"), home, transport)
    return factory


def failure(c: Composed) -> dict:
    return c.h.outcome(X)


# --- Class 1: a configured public binding reaches the consumer with raw response and invocation provenance ---------


def test_cli_binding_reaches_consumer_with_raw_response_and_custody(compose):
    stdout = ready_bytes()
    c = compose("cli", cli(stdout))
    unit = candidate(c.vector)
    result = c.h.service.assess(unit, PLAN)
    assert isinstance(result, ReadinessEligibility)
    producer = c.h.profile.readiness_producer
    assert type(producer) is AgentReadyCliAssessment and producer.binding is c.h.profile.readiness_binding
    [call] = c.calls()
    template = CONFORMANCE["cli"]["argv"]
    assert call["argv"][0] == c.executable and call["argv"][1] == template[1]
    assert call["argv"][3:] == [template[3], "claude", template[5]]
    assert "sha256:" + call["text_sha256"] == digest(unit["text"])
    [entry] = c.h.consumer.history(X)
    assert c.h.raw(entry) == stdout.decode()  # Byte-for-byte, before any normalization.
    outcome = c.h.outcome(X)
    assert outcome["record_kind"] == "ReadinessObservation" and outcome["raw_digest"] == digest(stdout)
    provenance = outcome["provenance"]
    assert (provenance["producer"], provenance["product_version"], provenance["transport"]) == \
        ("agent-ready", "0.1.0rc1", "cli")
    assert provenance["executable"] == c.executable and provenance["exit_status"] == 0
    assert provenance["contract_version"] == CONTRACT_VERSION == CONFORMANCE["bound_release"]["contract_version"]
    assert provenance["model"] == UNKNOWN and provenance["provider"] == "claude"
    invocation = provenance["invocation"]
    assert invocation["attempt_id"] == entry["attempt_id"] and invocation["input_sha256"] == digest(unit["text"])
    assert invocation["arguments"][0] == c.executable and invocation["arguments"][1:2] == ["assess"]
    assert invocation["started_at"] and invocation["ended_at"] and invocation["sdk_version"] is None


def test_mcp_binding_reaches_consumer_with_raw_response_and_custody(compose):
    c = compose("mcp", mcp(envelope(record("ready")["assessment"])))
    unit = candidate(c.vector)
    result = c.h.service.assess(unit, PLAN)
    assert isinstance(result, ReadinessEligibility)
    producer = c.h.profile.readiness_producer
    assert type(producer) is AgentReadyMcpAssessment and producer.binding is c.h.profile.readiness_binding
    [call] = c.calls()
    assert call["name"] == MCP_TOOL == CONFORMANCE["mcp"]["tool"]
    assert call["keys"] == CONFORMANCE["mcp"]["input_keys"] and call["provider"] == "claude"
    assert "sha256:" + call["text_sha256"] == digest(unit["text"])
    assert MCP_PROTOCOL_VERSION == CONFORMANCE["mcp"]["protocol_version"]
    [entry] = c.h.consumer.history(X)
    wire = json.loads(c.h.raw(entry))  # The JSON-RPC wrapper is preserved, not re-serialized.
    assert c.h.raw(entry) == json.loads(json.dumps(mcp(envelope(record("ready")["assessment"]))))["line"] \
        .replace("__ID__", json.dumps(entry["attempt_id"]))
    assert wire["id"] == entry["attempt_id"] and wire["result"]["structuredContent"]["disposition"] == READY
    outcome = c.h.outcome(X)
    assert outcome["shape"] == MCP and outcome["exit_status"] is None
    provenance = outcome["provenance"]
    assert (provenance["producer"], provenance["product_version"], provenance["transport"]) == \
        ("agent-ready", "0.1.0rc1", "mcp")
    invocation = provenance["invocation"]
    assert invocation["attempt_id"] == entry["attempt_id"] and invocation["input_sha256"] == digest(unit["text"])
    assert invocation["sdk_version"] == "1.29.1" != provenance["product_version"]  # agent-ready#1.
    assert invocation["arguments"][1:3] == ["tools/call", MCP_TOOL]


@pytest.mark.parametrize("transport", ["cli", "mcp"])
def test_text_over_the_published_limit_is_submitted_untruncated(compose, transport):
    limit = CONFORMANCE["cli"]["text_limit_characters"]
    c = compose(transport, cli(ready_bytes()) if transport == "cli" else mcp(envelope(record("ready")["assessment"])))
    text = "# WO-990900\n\n" + "x" * limit
    c.h.service.assess(candidate(c.vector, text=text), PLAN)
    [call] = c.calls()
    assert call["text_chars"] == len(text) > limit and "sha256:" + call["text_sha256"] == digest(text)


# --- Class 2: unbound, wrong product/version or disconnected responses refuse ---------------------------------------


REFUSED_BINDINGS = {"unbound": ({"bound": False}, "UNBOUND"),
                    "version_unknown": ({"package": {"metadata": False}}, "PRODUCT_VERSION_UNKNOWN"),
                    "wrong_package": ({"package": {"name": "agent-ready-surrogate"}}, "WRONG_PACKAGE")}


@pytest.mark.parametrize("transport", ["cli", "mcp"])
@pytest.mark.parametrize("case", list(REFUSED_BINDINGS))
def test_unestablished_binding_holds_before_launch(compose, case, transport):
    options, refusal = REFUSED_BINDINGS[case]
    c = compose(transport, cli(ready_bytes()) if transport == "cli" else mcp(envelope(record("ready")["assessment"])),
                **options)
    before = c.h.guarded()
    result = c.h.service.assess(candidate(c.vector), PLAN)
    assert result == Hold(CAPABILITY_PROVENANCE_HOLD, X, None, refusal)
    assert c.calls() == [] and c.h.consumer.history(X) == () and c.h.guarded() == before  # Never launched.


def test_disconnected_mcp_response_is_refused(compose):
    c = compose("mcp", mcp(envelope(record("ready")["assessment"]), answer_id="another-request"))
    result = c.h.service.assess(candidate(c.vector), PLAN)
    [entry] = c.h.consumer.history(X)
    assert result == Hold(ATTEMPT_FAILURE, X, entry["attempt_id"], PROVENANCE)
    outcome = failure(c)
    assert outcome["failure_class"] == PROVENANCE and outcome["detail"] == "RESPONSE_NOT_CORRELATED"
    assert outcome["provenance"]["invocation"]["attempt_id"] == "another-request"
    assert json.loads(c.h.raw(entry))["id"] == "another-request"  # Retained, never attributed.


# --- Class 3: malformed, conflicting, missing or provider-error results are attempt failures ------------------------


IS_ERROR = {"content": [{"type": "text", "text": "Invalid assessment request; supply text and provider only."}],
            "isError": True}
FAILURES = {
    "cli_exit_1": ("cli", cli(b"", 1), PROVIDER_FAILURE),
    "cli_usage_2_with_ready_stdout": ("cli", cli(ready_bytes(), 2), PROVIDER_FAILURE),
    "cli_zero_exit_empty": ("cli", cli(b""), NO_TERMINAL_RESULT),
    "cli_malformed": ("cli", cli(b"READY\n"), MALFORMED),
    "mcp_is_error": ("mcp", mcp(IS_ERROR), MCP_ERROR),
    "mcp_json_rpc_error": ("mcp", mcp(error={"code": -32602, "message": "Invalid params"}), MCP_ERROR),
    "mcp_json_rpc_error_beside_ready": ("mcp", mcp(envelope(record("ready")["assessment"]),
                                                   error={"code": -32603, "message": "x"}), MCP_ERROR),
    "mcp_conflicting": ("mcp", mcp({"structuredContent": body("READY"), "isError": False,
                                    "content": [{"type": "text", "text": json.dumps(body("HOLD"))}]}), CONFLICTING),
    "mcp_no_reply": ("mcp", {"exit_without_reply": True}, NO_TERMINAL_RESULT),
}


@pytest.mark.parametrize("case", list(FAILURES))
def test_failed_attempt_is_never_ready(compose, case):
    transport, behavior, expected = FAILURES[case]
    c = compose(transport, behavior)
    result = c.h.service.assess(candidate(c.vector), PLAN)
    [entry] = c.h.consumer.history(X)
    assert result == Hold(ATTEMPT_FAILURE, X, entry["attempt_id"], expected)
    assert failure(c)["record_kind"] == "AttemptFailure" and "disposition" not in failure(c)
    assert len(c.calls()) == 1


@pytest.mark.parametrize("transport", ["cli", "mcp"])
def test_timeout_is_an_attempt_failure(compose, transport):
    behavior = (cli(ready_bytes(), sleep=5) if transport == "cli"
                else mcp(envelope(record("ready")["assessment"]), sleep=5))
    c = compose(transport, behavior)
    c.h.service.producer = compose_producer(c.h.profile.readiness_binding, "claude", timeout_s=1)
    result = c.h.service.assess(candidate(c.vector), PLAN)
    [entry] = c.h.consumer.history(X)
    assert result == Hold(ATTEMPT_FAILURE, X, entry["attempt_id"], TIMEOUT)


def test_json_rpc_wrapper_parity_and_malformed_wrappers():
    result = envelope(record("ready")["assessment"])
    wrapped = encode({"jsonrpc": "2.0", "id": "a", "result": result})
    bare = recognize(encode(result), None, False, MCP)
    assert isinstance(bare, SemanticAssessment) and recognize(wrapped, None, False, MCP) == bare
    for wrapper in ({"jsonrpc": "1.0", "id": "a", "result": result},
                    {"jsonrpc": "2.0", "id": "a", "result": result, "disposition": READY},
                    {"jsonrpc": "2.0", "id": "a"}):
        observed = recognize(encode(wrapper), None, False, MCP)
        assert isinstance(observed, AttemptFailure) and observed.failure_class == MALFORMED


# --- Class 4: READY is eligibility only; the separate release gate is never bypassed --------------------------------


@pytest.mark.parametrize("transport", ["cli", "mcp"])
def test_transport_ready_is_eligibility_only(compose, monkeypatch, transport):
    calls = []
    original = release_domain.admit_release
    monkeypatch.setattr(release_domain, "admit_release", lambda *a: calls.append(a) or original(*a))
    c = compose(transport, cli(ready_bytes()) if transport == "cli" else mcp(envelope(record("ready")["assessment"])))
    before = c.h.guarded()
    result = c.h.service.assess(candidate(c.vector), PLAN)
    assert isinstance(result, ReadinessEligibility)
    assert calls == [] and c.h.guarded() == before  # No release and no lifecycle write through the transport.


# --- Composition --------------------------------------------------------------------------------------------------


def test_composition_refuses_ambiguous_or_unsupported_producer_configuration(compose, tmp_path):
    c = compose("cli", cli(ready_bytes()))
    binding = c.h.profile.readiness_binding
    assert compose_producer(None, "claude") is None and compose_producer(binding, None) is None
    with pytest.raises(ValueError, match="unsupported readiness transport"):
        compose_producer(replace(binding, transport="http"), "claude")
    with pytest.raises(ValueError, match="not both"):
        UpstreamProfile(c.h.repository, c.h.store, "p", "q", c.h.definition, "i", "a", frozenset(),
                        readiness_producer=object(), readiness_provider="claude")


# --- Native Agent Ready (opt-in; the configured product itself, never a stand-in) -----------------------------------


NATIVE_BIN = os.environ.get("FX_U10_AGENT_READY_BIN")
native = pytest.mark.skipif(not NATIVE_BIN, reason="FX_U10_AGENT_READY_BIN names no Agent Ready environment")
assessing = pytest.mark.skipif(os.environ.get("FX_U10_NATIVE_ASSESS") != "1",
                               reason="FX_U10_NATIVE_ASSESS=1 not set: no provider-backed native assessment")
NATIVE_UNIT = """# WO-990900 — Add a --dry-run flag to the export command

## Intent
`tool export <dir>` writes one JSON file per record into <dir>. Add `--dry-run`, which prints the paths that would
be written, one per line, and writes nothing.

## Fixed decisions
- Output format: one absolute path per line on stdout, in the same order export already uses; exit 0.
- No other flag, file format or behaviour changes.

## Scope
`src/tool/export.py` and its tests only.

## Acceptance
- With `--dry-run`, no file or directory is created or modified; stdout lists exactly the paths a real run writes.
- Without `--dry-run`, behaviour is byte-identical to today (existing tests pass unchanged).
- New tests cover both cases.
"""


def native_harness(tmp_path: Path, transport: str, name: str, provider: str = "claude") -> Harness:
    h = Harness(tmp_path / name, None, executable=Path(NATIVE_BIN) / SCRIPTS[transport], provider=provider,
                transport=transport)
    h.lifecycle(P1, "DONE")
    return h


def assert_native_binding(h: Harness, transport: str) -> None:
    binding = h.profile.readiness_binding
    assert (binding.product, binding.transport) == ("agent-ready", transport)
    assert binding.product_version == CONFORMANCE["bound_release"]["product_version"]
    assert binding.version_source.startswith("importlib.metadata:")


@native
def test_native_mcp_error_reaches_consumer_as_attempt_failure(tmp_path):
    """Credential-free: the product itself rejects over-limit text before any provider is contacted."""
    h = native_harness(tmp_path, "mcp", "native-mcp-error")
    assert_native_binding(h, "mcp")
    text = "# WO-990900\n\n" + "x" * CONFORMANCE["cli"]["text_limit_characters"]
    result = h.service.assess(candidate(h.design("verified"), text=text), PLAN)
    [entry] = h.consumer.history(X)
    assert result == Hold(ATTEMPT_FAILURE, X, entry["attempt_id"], MCP_ERROR)
    wire = json.loads(h.raw(entry))
    assert wire["id"] == entry["attempt_id"] and wire["result"]["isError"] is True
    invocation = h.outcome(X)["provenance"]["invocation"]
    assert invocation["attempt_id"] == entry["attempt_id"] and isinstance(invocation["sdk_version"], str)


@native
def test_native_cli_usage_error_reaches_consumer_as_attempt_failure(tmp_path):
    """Credential-free: an unsupported provider is a product usage error (exit 2), never a disposition."""
    h = native_harness(tmp_path, "cli", "native-cli-usage", provider="not-a-provider")
    assert_native_binding(h, "cli")
    result = h.service.assess(candidate(h.design("verified")), PLAN)
    [entry] = h.consumer.history(X)
    assert result == Hold(ATTEMPT_FAILURE, X, entry["attempt_id"], PROVIDER_FAILURE)
    assert h.outcome(X)["exit_status"] == 2 and "2" in CONFORMANCE["cli"]["exit_status"]


@native
@assessing
@pytest.mark.parametrize("transport", ["cli", "mcp"])
def test_native_assessment_reaches_consumer(tmp_path, monkeypatch, transport):
    calls = []
    original = release_domain.admit_release
    monkeypatch.setattr(release_domain, "admit_release", lambda *a: calls.append(a) or original(*a))
    h = native_harness(tmp_path, transport, f"native-{transport}")
    assert_native_binding(h, transport)
    before = h.guarded()
    result = h.service.assess(candidate(h.design("verified"), text=NATIVE_UNIT), PLAN)
    [entry] = h.consumer.history(X)
    outcome = h.outcome(X)
    assert outcome["record_kind"] == "ReadinessObservation", outcome
    assert outcome["disposition"] in DISPOSITIONS
    raw = json.loads(h.raw(entry))
    supplied = raw if transport == "cli" else raw["result"]["structuredContent"]
    assert supplied["disposition"] == outcome["disposition"] and outcome["raw_digest"] == entry["outcome"]["raw_digest"]
    provenance = outcome["provenance"]
    assert provenance["invocation"]["attempt_id"] == entry["attempt_id"]
    assert provenance["invocation"]["input_sha256"] == digest(NATIVE_UNIT)
    assert provenance["editable_revision"] is None or provenance["editable_revision"].startswith("file://")
    assert isinstance(result, ReadinessEligibility) == (outcome["disposition"] == READY)
    assert calls == [] and h.guarded() == before
    retained = os.environ.get("FX_U10_NATIVE_RECORD")
    if retained:  # The runner keeps what the native product actually returned as an immutable observation.
        Path(retained, f"native-{transport}.json").write_text(json.dumps(
            {"transport": transport, "result": repr(result), "attempt": entry, "outcome": outcome,
             "raw": h.raw(entry), "binding": repr(h.profile.readiness_binding)}, indent=2, sort_keys=True))
