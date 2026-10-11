"""Subprocess proof for the public operator CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_cli_status_reports_real_execution_when_upstream_is_unavailable(tmp_path: Path) -> None:
    """Removing the CLI adapter or leaking an upstream secret breaks this proof."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile

class Work:
    def import_ready_snapshot(self):
        raise RuntimeError('token=SENTINEL-CLI-SECRET unavailable')
class Worker:
    def cancel(self, *_): return 'cancelled'
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    return profile
"""
    )
    environment = os.environ | {"PYTHONPATH": f"src:{tmp_path}"}
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "status", "--json"],
        text=True, capture_output=True, env=environment, check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["execution"]["status"] == "known"
    assert payload["upstream"]["status"] == "unavailable"
    assert "SENTINEL-CLI-SECRET" not in result.stdout + result.stderr


def test_cli_returns_json_error_without_traceback_when_factory_leaks_secret(tmp_path: Path) -> None:
    """Removing the top-level sanitization must fail rather than expose diagnostics."""
    factory = tmp_path / "broken_factory.py"
    factory.write_text("def make(): raise RuntimeError('secret=SENTINEL-LEAK')")
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "broken_factory:make", "status", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout)["error"]
    assert "SENTINEL-LEAK" not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr


def test_cli_sanitizes_invalid_arguments(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "status", "--bad=secret=SENTINEL-ARG"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": "src"}, check=False,
    )

    assert result.returncode != 0
    assert "SENTINEL-ARG" not in result.stdout + result.stderr


def test_cli_redacts_bearer_and_provider_diagnostics(tmp_path: Path) -> None:
    factory = tmp_path / "broken_factory.py"
    factory.write_text("def make(): raise RuntimeError('Authorization: Bearer SENTINEL-BEARER provider stderr: ghp_SENTINEL-PAT')")
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "broken_factory:make", "status", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert "SENTINEL-BEARER" not in result.stdout + result.stderr
    assert "SENTINEL-PAT" not in result.stdout + result.stderr
    assert "provider stderr" not in result.stdout.lower() + result.stderr.lower()


def test_cli_sanitizes_subcommand_parse_errors() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "decisions", "secret=SENTINEL-SUBPARSER"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": "src"}, check=False,
    )

    assert result.returncode != 0
    assert "SENTINEL-SUBPARSER" not in result.stdout + result.stderr


def test_cli_accepts_a_distinct_biu_version_for_decisions() -> None:
    from alienintent.control_plane.adapters.cli import _parser

    args = _parser().parse_args([
        "decisions", "decide", "PY-08", "--choice", "authorize", "--biu-version", "0",
        "--actor", "morty", "--authority", "operator", "--intent", "authorize",
        "--expected-version", "1", "--reason", "approved", "--idempotency-key", "decision-1",
    ])
    assert args.biu_version == 0


def test_cli_decision_uses_kernel_biu_version_after_row_revision_advances(tmp_path: Path) -> None:
    """Passing the store row revision to the kernel decision must fail this proof."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
from alienintent.execution_coordination.ports.worker_provider import WorkerOutcome
from tests.execution_coordination.test_factory_coordinator import _item

class Work:
    def __init__(self): self.items = (_item('PY-08', 0, 1),)
    def import_ready_snapshot(self): return self.items
    def propose_release(self, _): pass
    def project_execution_state(self, *_): pass
class Worker:
    def start(self, *_): return WorkerOutcome('authority-block')
    def read_back(self, *_): return WorkerOutcome('authority-block')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    assert profile.coordinator.start().authority_blocked == ('PY-08',)
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "decisions", "decide", "PY-08", "--choice", "authorize", "--biu-version", "0", "--actor", "morty", "--authority", "SWF-21", "--intent", "authorize", "--expected-version", "2", "--reason", "approved", "--idempotency-key", "decision-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["event"]["work_item"] == "PY-08"


def test_cli_returns_a_sanitized_readiness_reason(tmp_path: Path) -> None:
    """Replacing the safe diagnostic vocabulary with an opaque constant must fail."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def start(self, *_): raise AssertionError('readiness gate must prevent start')
def make(): return OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "run", "--actor", "morty", "--authority", "SWF-21", "--intent", "start", "--expected-version", "0", "--reason", "approved", "--idempotency-key", "run-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout) == {"error": "readiness-gate-failed"}


def test_cli_rejects_a_stale_mutation_version(tmp_path: Path) -> None:
    """A stale CLI write must be denied before the cancellation protocol runs."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def cancel(self, *_): raise AssertionError('stale command reached cancellation')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "cancel", "PY-08", "--actor", "morty", "--authority", "SWF-21", "--intent", "cancel", "--expected-version", "0", "--reason", "stale", "--idempotency-key", "cancel-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout) == {"error": "stale-expected-version"}


def test_cli_stop_rejects_a_stale_profile_fence(tmp_path: Path) -> None:
    """Dropping stop's expected-version fence would let this subprocess cancel work."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def cancel(self, *_): raise AssertionError('stale stop reached cancellation')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "stop", "--actor", "morty", "--authority", "SWF-21", "--intent", "stop", "--expected-version", "0", "--reason", "stale", "--idempotency-key", "stop-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode != 0
    assert json.loads(result.stdout) == {"error": "stale-expected-version"}


def test_cli_sanitizer_labels_domain_conflicts_without_exposing_messages() -> None:
    """Generic ValueError/RuntimeError buckets misdescribe normal domain outcomes."""
    from alienintent.control_plane.adapters.cli import _sanitize
    from alienintent.execution_coordination.application.factory_coordinator import TerminalWork
    from alienintent.execution_coordination.domain.escalation import SupersededDecision
    from alienintent.execution_coordination.ports.operational_store import VersionConflict

    assert _sanitize(TerminalWork("terminal work contains token=SENTINEL")) == "terminal-work"
    assert _sanitize(SupersededDecision("decision token=SENTINEL")) == "superseded-decision"
    assert _sanitize(VersionConflict("revision token=SENTINEL")) == "stale-expected-version"


def test_cli_cancel_cannot_write_through_its_store_view(tmp_path: Path) -> None:
    """Replacing the application-service cancellation with a store write must fail."""
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def cancel(self, *_): return 'cancelled'
class ReadOnlyStore:
    def __init__(self, store): self._store = store
    def read_state(self, *args): return self._store.read_state(*args)
    def commit(self, *_): raise AssertionError('CLI attempted a direct store write')
def make():
    profile = OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts')
    profile.store.commit('offline', 'factory:PY-08', 0, {'stage': 'IMPLEMENT', 'version': 0, 'accepted': False, 'closure': []})
    profile.store = ReadOnlyStore(profile.store)
    return profile
"""
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "cancel", "PY-08", "--actor", "morty", "--authority", "SWF-21", "--intent", "cancel", "--expected-version", "1", "--reason", "operator stop", "--idempotency-key", "cancel-1", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "cancelled"


def test_cli_sanitizes_realistic_secret_shapes(tmp_path: Path) -> None:
    factory = tmp_path / "broken_factory.py"
    sentinel = "SENTINELSECRET"
    factory.write_text(
        "def make(): raise RuntimeError('AKIAIOSFODNN" + sentinel + " xoxb-1-" + sentinel
        + " postgres://factory:" + sentinel + "@db /home/a/.ssh/config Authorization=Basic " + sentinel + "')"
    )
    result = subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "broken_factory:make", "status", "--json"],
        text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False,
    )
    assert result.returncode != 0
    assert sentinel not in result.stdout + result.stderr


def _work_factory(tmp_path: Path) -> Path:
    """A profile factory whose project work registry has one configured profile (fx) and no Git activity."""
    factory = tmp_path / "work_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.work_registry import WorkRegistry, project_configuration
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

ROOT = Path(__file__).parent
class Profile:
    def __init__(self):
        SQLiteOperationalStore(ROOT / 'fx.sqlite')
        self.work_registry = WorkRegistry(project_configuration({'schema_version': 1, 'projects': {'P': {
            'database': str(ROOT / 'work.sqlite'),
            'repositories': {'r': {'clone': str(ROOT / 'clone'), 'remote': 'origin', 'default_branch': 'main',
                                   'packets_branch': 'packets'}},
            'packets': {'repository': 'r', 'directory': 'work-packets'},
            'profiles': {'fx': str(ROOT / 'fx.sqlite')}}}}, 'P'))
def make():
    return Profile()
"""
    )
    return factory


def _work(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "work_factory:make", "--json", "work", "migrate",
         *args], text=True, capture_output=True, env=os.environ | {"PYTHONPATH": f"src:{tmp_path}"}, check=False)


def test_cli_work_migrate_with_no_saved_assignments_is_a_repeatable_no_op(tmp_path: Path) -> None:
    """Check 7: an empty snapshot and no reservation records migrate to nothing, twice."""
    _work_factory(tmp_path)
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"identity_snapshot": {"active": [], "retired": [], "reserved": []}}))
    for _ in range(2):
        result = _work(tmp_path, "--snapshot", str(snapshot), "--profile", "fx")
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout) == {"created": [], "rekeyed": [], "unchanged": []}


def test_cli_work_migrate_creates_rows_and_reports_conflicts(tmp_path: Path) -> None:
    _work_factory(tmp_path)
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"active": ["PY-01"], "retired": ["PY-09"], "reserved": []}))  # TEST DATA
    created = _work(tmp_path, "--snapshot", str(snapshot), "--profile", "fx")
    assert created.returncode == 0 and sorted(json.loads(created.stdout)["created"]) == ["PY-01", "PY-09"]
    again = _work(tmp_path, "--snapshot", str(snapshot), "--profile", "fx")
    assert json.loads(again.stdout) == {"created": [], "rekeyed": [], "unchanged": ["PY-01", "PY-09"]}
    foreign = _work(tmp_path, "--snapshot", str(snapshot), "--profile", "fx", "--profile", "other-project")
    assert foreign.returncode == 2 and json.loads(foreign.stdout) == {"error": "migration-conflict"}
    assert "Traceback" not in foreign.stderr


def _registry_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    """`work` commands through the production profile factory, configured only by its two environment variables."""
    environment = os.environ | {"PYTHONPATH": "src", "ALIENINTENT_PROJECT": "P",
                                "ALIENINTENT_PROJECT_CONFIGURATION": str(tmp_path / "projects.json")}
    return subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory",
         "alienintent.composition.work_registry:work_registry_profile", "--json", "work", *args],
        text=True, capture_output=True, env=environment, check=False)


def _registry_project(tmp_path: Path) -> tuple[Path, str, bytes]:
    """A project with one clone and a local bare remote; one packet committed on main (TEST DATA)."""
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from tests.context_assembly.test_initial_compilation import project_clone
    from tests.context_assembly.test_work_identity_service import commit_file
    clone, _ = project_clone(tmp_path)
    SQLiteOperationalStore(tmp_path / "fx.sqlite")
    (tmp_path / "projects.json").write_text(json.dumps({"schema_version": 1, "projects": {"P": {
        "database": str(tmp_path / "work.sqlite"),
        "repositories": {"r": {"clone": str(clone), "remote": "origin", "default_branch": "main",
                               "packets_branch": "packets"}},
        "packets": {"repository": "r", "directory": "work-packets"},
        "profiles": {"fx": str(tmp_path / "fx.sqlite")}}}}))
    packet = b"# Work unit: fixture\n\nDo this.\n"
    (tmp_path / "packet.md").write_bytes(packet)
    return clone, commit_file(clone, "main", "docs/packet.md", packet), packet


def _landing(document: dict, tmp_path: Path) -> None:
    document["projects"]["P"]["github"] = {
        "repository": "AlienLogicLab/alienintent", "application_id": 1, "installation_id": 1,
        "private_key_path": str(tmp_path / "no-key.pem"),
        "project": {"project_id": "PVT_fixture", "project_number": 1, "organization": "AlienLogicLab",
                    "status_field_id": "S", "priority_field_id": "P"}, "landing": True}


def _remote_tag(remote: str, identity: str) -> str | None:
    lines = subprocess.run(["git", "ls-remote", remote, f"refs/tags/work/{identity}"], text=True,
                           capture_output=True, check=True).stdout.split()
    return lines[0] if lines else None


@pytest.mark.parametrize("command", ["register", "import"])
def test_cli_work_commands_publish_and_a_rerun_completes_a_failed_push(tmp_path: Path, command: str) -> None:
    """Check 7: each command leaves work/<id> on the remote at the row's commit; a failed push exits non-zero
    naming PUBLICATION_FAILED, the row stays, and rerunning the same command publishes and exits zero."""
    clone, commit, _ = _registry_project(tmp_path)
    args = [command, "--file", str(tmp_path / "packet.md"), "--repo", "r", "--path", "docs/packet.md",
            "--commit", commit, "--label", "PY-SELF-00", *(("--issue", "153") if command == "import" else ())]
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=clone, text=True, capture_output=True,
                            check=True).stdout.strip()
    subprocess.run(["git", "remote", "set-url", "origin", str(tmp_path / "missing.git")], cwd=clone, check=True)
    failed = _registry_cli(tmp_path, *args)
    assert failed.returncode != 0 and json.loads(failed.stdout) == {"error": "publication-failed"}
    assert "Traceback" not in failed.stderr
    shown = json.loads(_registry_cli(tmp_path, "show", "PY-SELF-00").stdout)
    identity = shown["item"]["id"]
    assert shown["item"]["pointer"]["commit"] == commit and _remote_tag(remote, identity) is None
    subprocess.run(["git", "remote", "set-url", "origin", remote], cwd=clone, check=True)
    rerun = _registry_cli(tmp_path, *args)
    assert rerun.returncode == 0, rerun.stdout + rerun.stderr
    item = json.loads(rerun.stdout)
    assert item["id"] == identity and item["state"] == ("DONE" if command == "import" else "CAPTURE")
    assert _remote_tag(remote, identity) == commit


def test_cli_work_register_refuses_a_mismatch_and_show_reads_the_pinned_packet(tmp_path: Path) -> None:
    _, commit, packet = _registry_project(tmp_path)
    (tmp_path / "edited.md").write_bytes(packet + b"uncommitted edit\n")
    base = ["--repo", "r", "--path", "docs/packet.md", "--commit", commit, "--label", "PACKET"]
    refused = _registry_cli(tmp_path, "register", "--file", str(tmp_path / "edited.md"), *base)
    assert refused.returncode != 0 and json.loads(refused.stdout) == {"error": "pointer-mismatch"}
    item = json.loads(_registry_cli(tmp_path, "register", "--file", str(tmp_path / "packet.md"), *base).stdout)
    shown = _registry_cli(tmp_path, "show", item["id"])
    assert shown.returncode == 0 and json.loads(shown.stdout)["packet"] == packet.decode()
    assert json.loads(shown.stdout)["item"] == item
    assert json.loads(_registry_cli(tmp_path, "show", "missing").stdout) == {"answer": "UNKNOWN_IDENTITY"}


def test_cli_work_assess_with_and_without_the_readiness_entry(tmp_path: Path) -> None:
    """Check 6: without a readiness entry `work assess` answers readiness-not-configured and moves nothing; with one
    it assesses once, a repeat runs nothing, and `work show` names the saved reference."""
    from tests.composition.test_work_registry import fixture_agent_ready
    from tests.context_assembly.test_work_contract import block, satisfiable_payload
    from tests.context_assembly.test_work_identity_service import commit_file
    clone, commit, packet = _registry_project(tmp_path)
    item = json.loads(_registry_cli(tmp_path, "register", "--file", str(tmp_path / "packet.md"), "--repo", "r",
                                    "--path", "docs/packet.md", "--commit", commit, "--label", "PACKET").stdout)
    revision_packet = packet + block(satisfiable_payload(item["id"],
                                                       authority_references=["docs/packet.md"])).encode()
    revised = commit_file(clone, "main", "docs/packet.md", revision_packet)
    (tmp_path / "revised.md").write_bytes(revision_packet)
    for args in ((), ("--file", str(tmp_path / "revised.md"), "--commit", revised)):
        refused = _registry_cli(tmp_path, "assess", "PACKET", *args)
        assert refused.returncode == 1 and json.loads(refused.stdout) == {"error": "readiness-not-configured"}
    shown = json.loads(_registry_cli(tmp_path, "show", "PACKET").stdout)["item"]
    assert shown == item and _remote_tag(str(tmp_path / "remote.git"), item["id"]) == commit
    for args in (("--file", "x"), ("--commit", revised), ("--file", "x", "--commit", revised, "--recover", "a")):
        invalid = _registry_cli(tmp_path, "assess", "PACKET", *args)
        assert invalid.returncode == 2 and json.loads(invalid.stdout) == {"error": "invalid-command-arguments"}
    document = json.loads((tmp_path / "projects.json").read_text())
    document["projects"]["P"]["readiness"] = {
        "database": str(tmp_path / "readiness.sqlite"), "evidence_root": str(tmp_path / "evidence"),
        "executable": str(fixture_agent_ready(tmp_path, tmp_path / "launched.env")), "provider": "claude"}
    _landing(document, tmp_path)
    (tmp_path / "projects.json").write_text(json.dumps(document))
    assessed = _registry_cli(tmp_path, "assess", "PACKET", "--file", str(tmp_path / "revised.md"),
                             "--commit", revised)
    assert assessed.returncode == 0, assessed.stdout + assessed.stderr
    value = json.loads(assessed.stdout)
    assert (value["identity"], value["disposition"], value["reused"]) == (item["id"], "READY", False)
    again = json.loads(_registry_cli(tmp_path, "assess", item["id"]).stdout)
    assert (again["attempt_id"], again["reused"]) == (value["attempt_id"], True)
    shown = json.loads(_registry_cli(tmp_path, "show", "PACKET").stdout)["item"]
    assert shown["assessment_ref"] == value["assessment_ref"] and shown["state"] == "CAPTURE"
    assert json.loads(_registry_cli(tmp_path, "assess", "missing").stdout) == {
        "answer": "UNKNOWN_IDENTITY", "identity": "missing", "attempt_id": None, "detail": ""}


def test_cli_work_authorize_with_and_without_the_readiness_entry(tmp_path: Path) -> None:
    """Release record check 7: without a readiness entry `work authorize` answers readiness-not-configured and writes
    nothing; with one it records the authorization once and a repeat changes nothing."""
    from tests.composition.test_work_registry import fixture_agent_ready
    from tests.context_assembly.test_work_contract import block, satisfiable_payload
    from tests.context_assembly.test_work_identity_service import commit_file
    clone, commit, packet = _registry_project(tmp_path)
    item = json.loads(_registry_cli(tmp_path, "register", "--file", str(tmp_path / "packet.md"), "--repo", "r",
                                    "--path", "docs/packet.md", "--commit", commit, "--label", "PACKET").stdout)
    contracted = packet + block(satisfiable_payload(item["id"],
                                                    authority_references=["docs/packet.md"])).encode()
    (tmp_path / "contracted.md").write_bytes(contracted)
    revised = commit_file(clone, "main", "docs/packet.md", contracted)
    baseline = subprocess.run(["git", "rev-parse", "main"], cwd=clone, text=True, capture_output=True,
                              check=True).stdout.strip()
    quote = "I authorize implementation of this fixture unit."
    args = ["authorize", "PACKET", "--commit", revised, "--attempt", "none", "--baseline", baseline, "--quote", quote]
    refused = _registry_cli(tmp_path, *args)
    assert refused.returncode == 1 and json.loads(refused.stdout) == {"error": "readiness-not-configured"}
    invalid = _registry_cli(tmp_path, *args[:-2])
    assert invalid.returncode == 2 and json.loads(invalid.stdout) == {"error": "invalid-command-arguments"}
    document = json.loads((tmp_path / "projects.json").read_text())
    document["projects"]["P"]["readiness"] = {
        "database": str(tmp_path / "readiness.sqlite"), "evidence_root": str(tmp_path / "evidence"),
        "executable": str(fixture_agent_ready(tmp_path, tmp_path / "launched.env")), "provider": "claude"}
    _landing(document, tmp_path)
    (tmp_path / "projects.json").write_text(json.dumps(document))
    assessed = json.loads(_registry_cli(tmp_path, "assess", "PACKET", "--file", str(tmp_path / "contracted.md"),
                                        "--commit", revised).stdout)
    args[args.index("none")] = assessed["attempt_id"]
    authorized = _registry_cli(tmp_path, *args)
    assert authorized.returncode == 0, authorized.stdout + authorized.stderr
    value = json.loads(authorized.stdout)
    assert (value["identity"], value["answer"], value["repeated"]) == (item["id"], None, False)
    assert value["authorization"]["record_ref"] == value["evidence_ref"]["revision_digest"]
    assert (value["authorization"]["baseline"], value["authorization"]["text"]) == (baseline, quote)
    again = json.loads(_registry_cli(tmp_path, *args).stdout)
    assert again == value | {"repeated": True}
    shown = json.loads(_registry_cli(tmp_path, "show", "PACKET").stdout)["item"]
    assert shown["approval_ref"] == value["evidence_ref"] and shown["state"] == "CAPTURE"
    stale = json.loads(_registry_cli(tmp_path, *[commit if a == revised else a for a in args]).stdout)
    assert (stale["answer"], stale["detail"]) == ("AUTHORIZATION_STALE", "--commit is not the pointer commit")


def test_cli_work_record_completed_passes_resolved_paths_and_exact_bytes(tmp_path: Path, monkeypatch, capsys) -> None:
    """RECORD-COMPLETED-WORK: the command reads each given file once, as its resolved absolute path and exact bytes,
    and answers the service's result; without a readiness entry it is readiness-not-configured."""
    from types import SimpleNamespace
    from alienintent.context_assembly.application.work_completion import CompletionResult
    from alienintent.control_plane.adapters import cli
    calls = []

    class Completion:
        def record(self, *args):
            calls.append(args)
            return CompletionResult(args[0], None, {"logical_id": "work-completion/UNIT"})

    registry = SimpleNamespace(completion=None)
    monkeypatch.setattr(cli, "_factory", lambda reference: SimpleNamespace(work_registry=registry))
    monkeypatch.chdir(tmp_path)
    for name, data in (("round1.md", b"REJECT\n"), ("round2.md", b"ACCEPT\r\nbytes \xff\n"), ("approval.json", b"{}")):
        (tmp_path / name).write_bytes(data)
    argv = ["--json", "--profile-factory", "x:y", "work", "record-completed", "UNIT", "--candidate", "c" * 40,
            "--landing", "d" * 40, "--record", "docs/evidence/landing.md", "--verification", "round1.md",
            "--verification", "./round2.md", "--approval", "approval.json", "--quote", "I approve."]
    assert cli.main(argv) == 1 and json.loads(capsys.readouterr().out) == {"error": "readiness-not-configured"}
    registry.completion = Completion()
    assert cli.main(argv) == 0
    assert json.loads(capsys.readouterr().out)["evidence_ref"] == {"logical_id": "work-completion/UNIT"}
    root = tmp_path.resolve()
    assert calls == [("UNIT", "c" * 40, "d" * 40, "docs/evidence/landing.md",
                      [(str(root / "round1.md"), b"REJECT\n"), (str(root / "round2.md"), b"ACCEPT\r\nbytes \xff\n")],
                      (str(root / "approval.json"), b"{}"), "I approve.")]
    assert cli.main([a for a in argv if a not in ("--verification", "round1.md", "./round2.md")]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "invalid-command-arguments"}

def test_cli_work_link_and_display_with_and_without_the_github_entry(tmp_path: Path) -> None:
    """Check 7: without a `github` entry both commands answer github-not-configured; with one they are wired to the
    link service. Only answers reached before any GitHub request are exercised here (no network); the failing step
    is named on a credential failure, which happens before anything is sent."""
    _, commit, _ = _registry_project(tmp_path)
    item = json.loads(_registry_cli(tmp_path, "register", "--file", str(tmp_path / "packet.md"), "--repo", "r",
                                    "--path", "docs/packet.md", "--commit", commit, "--label", "PACKET").stdout)
    for args in (("link", "PACKET"), ("link", "PACKET", "--issue", "3"), ("display", "PACKET")):
        refused = _registry_cli(tmp_path, *args)
        assert refused.returncode == 1 and json.loads(refused.stdout) == {"error": "github-not-configured"}
    document = json.loads((tmp_path / "projects.json").read_text())
    document["projects"]["P"]["github"] = {
        "repository": "AlienLogicLab/alienintent-sandbox", "application_id": 1000001, "installation_id": 2000002,
        "private_key_path": str(tmp_path / "no-such-key.pem"),
        "project": {"project_id": "PVT_kwDOfixtureSandboxProject", "project_number": 2, "organization": "AlienLogicLab",
                    "status_field_id": "PVTSSF_s", "priority_field_id": "PVTSSF_p"}}
    (tmp_path / "projects.json").write_text(json.dumps(document))
    unknown = json.loads(_registry_cli(tmp_path, "link", "missing").stdout)
    assert (unknown["answer"], unknown["identity"], unknown["issue_number"]) == ("UNKNOWN_IDENTITY", "missing", None)
    shown = json.loads(_registry_cli(tmp_path, "display", "PACKET").stdout)
    assert (shown["answer"], shown["identity"]) == ("NOT_LINKED", item["id"])
    invalid = _registry_cli(tmp_path, "link", "PACKET", "--issue", "three")
    assert invalid.returncode == 2 and json.loads(invalid.stdout) == {"error": "invalid-command-arguments"}
    failed = _registry_cli(tmp_path, "link", "PACKET")
    assert failed.returncode == 2 and json.loads(failed.stdout)["step"] == "permissions"
    assert "Traceback" not in failed.stderr
    assert json.loads(_registry_cli(tmp_path, "show", "PACKET").stdout)["item"]["issue_number"] is None


# --- unit 6c-1: `work context` and the read-only worker profile ------------------------------------------------------

SOURCE = Path(__file__).resolve().parents[2] / "src"
WORK_CONTEXT_PROFILE = "alienintent.composition.work_registry:work_context_profile"
_ASSEMBLE = """
import json, sys
from pathlib import Path
from alienintent.composition.work_registry import WorkRegistry, load_project_configuration
configuration, project, identity, role, correlation, clone = sys.argv[1:]
registry = WorkRegistry(load_project_configuration(Path(configuration), project))
print(json.dumps(registry.context.assemble(identity, role, correlation, None, None, Path(clone) if clone else None)
                 .document(), sort_keys=True))
"""


def installed(root: Path) -> Path:
    """This checkout installed into a fresh virtual environment the way an editable pip install does: a .pth file
    naming its source and the `alienintent` console script. Returns the environment's python."""
    venv = root / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True)
    python = venv / "bin" / "python"
    purelib = subprocess.run([python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                             capture_output=True, text=True, check=True, env={}).stdout.strip()
    Path(purelib, "alienintent-checkout.pth").write_text(f"{SOURCE}\n")
    script = venv / "bin" / "alienintent"
    script.write_text(f"#!{python}\nimport sys\nfrom alienintent.control_plane.adapters.cli import main\n"
                      "sys.exit(main())\n")
    script.chmod(0o755)
    return python


def test_work_context_runs_with_only_the_worker_environment(tmp_path: Path) -> None:
    """Founder check (a) / acceptance checks 4 and 7: in a running launch (saved with `commit_with_effect` and
    claimed, as the coordinator does before the worker starts), the package's own `context_command`, run from a
    worktree (the VERIFIER's from its candidate clone) with only the stated worker environment plus its two
    variables, prints exactly the package `assemble` gives for the same work item, attempt and store version. A
    command needing PYTHONPATH, an inherited ALIENINTENT_* variable or the operator's working directory, or one
    locked out by its own launch save, fails here."""
    from alienintent.composition.sandbox_run_profile import worker_environment
    from tests.context_assembly.test_initial_compilation import PROJECT, git
    from tests.context_assembly.test_work_context import Cx, launched
    python = installed(tmp_path)
    cx = Cx(tmp_path / "cx")
    item = cx.admitted(reserve=False)
    producer = launched(cx, item, "PRODUCER")
    worktree = tmp_path / "producer-worktree"
    git(cx.clone, "worktree", "add", "-q", "--detach", str(worktree))
    other = cx.admitted("OTHER")
    _, _, clone = cx.produced(other)
    verifier = launched(cx, other, "VERIFIER")
    (tmp_path / "worker-tmp").mkdir()
    for identity, role, correlation, cwd, candidate_clone in (
            (item.id, "PRODUCER", producer, worktree, ""), (other.id, "VERIFIER", verifier, clone, str(clone))):
        operator = subprocess.run([python, "-c", _ASSEMBLE, str(cx.configuration_file), PROJECT, identity, role,
                                   correlation, candidate_clone], capture_output=True, text=True, check=True,
                                  env={"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", str(tmp_path))})
        package = json.loads(operator.stdout)
        assert package["status"] == "PACKAGE", package
        command = package["context_command"]
        assert command["argv"][0] == str(python.with_name("alienintent"))
        environment = worker_environment(tmp_path) | command["environment"]
        assert "PYTHONPATH" not in environment and set(command["environment"]) == {
            "ALIENINTENT_PROJECT_CONFIGURATION", "ALIENINTENT_PROJECT"}
        assert not any(name.startswith("ALIENINTENT_") for name in worker_environment(tmp_path))
        worker = subprocess.run(command["argv"], cwd=cwd, env=environment, capture_output=True, text=True)
        assert worker.returncode == 0, worker.stdout + worker.stderr
        assert worker.stdout.strip() == operator.stdout.strip()


@pytest.mark.parametrize("argv", [
    ["work", "assess", "UNIT"],
    ["work", "authorize", "UNIT", "--commit", "c", "--attempt", "a", "--baseline", "b", "--quote", "q"],
    ["work", "approve-plan", "--commit", "c", "--quote", "q"],
    ["work", "release", "UNIT"],
    ["work", "prepare"],
    ["work", "record-completed", "UNIT", "--candidate", "c", "--landing", "l", "--record", "r", "--verification", "v",
     "--approval", "a", "--quote", "q"],
    ["work", "link", "UNIT"],
    ["work", "register", "--file", "f", "--repo", "r", "--path", "p", "--commit", "c", "--label", "l"],
    ["work", "display", "UNIT"],
    ["work", "migrate", "--snapshot", "s", "--profile", "p"],
    ["work", "show", "UNIT"],
    ["status"],
])
def test_the_worker_profile_answers_every_other_command_with_the_stated_error(tmp_path, monkeypatch, capsys, argv):
    """Acceptance check 7: through the read-only worker profile only `work context` runs; a profile exposing the
    writing commands would run them (or fail as internal-error) instead of this stated answer."""
    from alienintent.control_plane.adapters.cli import main
    from tests.context_assembly.test_initial_compilation import PROJECT
    from tests.context_assembly.test_work_context import Cx
    cx = Cx(tmp_path / "cx")
    cx.admitted()
    monkeypatch.setenv("ALIENINTENT_PROJECT_CONFIGURATION", str(cx.configuration_file))
    monkeypatch.setenv("ALIENINTENT_PROJECT", PROJECT)
    before = cx.written()
    assert main(["--json", "--profile-factory", WORK_CONTEXT_PROFILE, *argv]) == 1
    assert json.loads(capsys.readouterr().out) == {"error": "not-available-in-worker-profile"}
    assert cx.written() == before


def test_work_prepare_runs_one_preparation_and_renders_its_typed_answer(monkeypatch, capsys) -> None:
    """WORK-PREPARATION-REFILL R3a: `work prepare` calls the registry's Work Preparation once and renders its answer;
    a registry without one answers the stated error."""
    from types import SimpleNamespace
    from alienintent.composition.work_preparation import PreparationResult
    from alienintent.control_plane.adapters import cli
    calls = []
    registry = SimpleNamespace(preparation=SimpleNamespace(prepare_next=lambda: calls.append(1) or PreparationResult(
        "released", "FIXTURE", "id-1", "")))
    monkeypatch.setattr(cli, "_factory", lambda path: SimpleNamespace(work_registry=registry))
    assert cli.main(["--json", "--profile-factory", "x:y", "work", "prepare"]) == 0
    assert json.loads(capsys.readouterr().out) == {"answer": "released", "obligation": "FIXTURE", "identity": "id-1",
                                                   "detail": ""} and calls == [1]
    registry.preparation = None
    assert cli.main(["--json", "--profile-factory", "x:y", "work", "prepare"]) == 1
    assert json.loads(capsys.readouterr().out) == {"error": "readiness-not-configured"}


# --- unit 6c-2: `work launch` and `work context --contract-digest` ---------------------------------------------------


def test_work_launch_renders_one_step_and_work_context_passes_the_contract_digest(monkeypatch, capsys, tmp_path) -> None:
    """`work launch <id>` calls the registry launcher's `launch` for exactly that id and renders its answer or run
    summary; `--contract-digest` reaches `assemble` (None without it)."""
    from types import SimpleNamespace
    from alienintent.control_plane.adapters import cli
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
    from alienintent.execution_coordination.application.factory_coordinator import RunSummary, StopReason
    calls = []
    answers = iter(["closure-not-automated", RunSummary(StopReason.BLOCKED, ("ITEM",))])
    launcher = SimpleNamespace(launch=lambda identity: calls.append(("launch", identity)) or next(answers))

    class Context:
        def assemble(self, *args):
            calls.append(("assemble", args[3]))
            return SimpleNamespace(document=lambda: {"status": "HOLD"})
    registry = SimpleNamespace(launcher=lambda: launcher, context=Context(),
                               store=SQLiteOperationalStore(tmp_path / "launch.sqlite"), ownership=ProcOwnership())
    monkeypatch.setattr(cli, "_factory", lambda _: SimpleNamespace(work_registry=registry))

    assert cli.main(["--json", "--profile-factory", "x:y", "work", "launch", "ITEM"]) == 0
    assert json.loads(capsys.readouterr().out) == {"identity": "ITEM", "answer": "closure-not-automated"}
    assert cli.main(["--json", "--profile-factory", "x:y", "work", "launch", "ITEM"]) == 0
    assert json.loads(capsys.readouterr().out) == {"identity": "ITEM", "stop_reason": "dependencies-or-authority-blocked",
                                                   "dispatched": ["ITEM"], "authority_blocked": [], "failed": [],
                                                   "ran": [], "infrastructure_held": []}
    for extra, digest in ((["--contract-digest", "sha256:abc"], "sha256:abc"), ([], None)):
        assert cli.main(["--json", "--profile-factory", "x:y", "work", "context", "ITEM", "--role", "PRODUCER",
                         "--correlation", "launch:ITEM:0", *extra]) == 0
        capsys.readouterr()
    assert calls == [("launch", "ITEM"), ("launch", "ITEM"), ("assemble", "sha256:abc"), ("assemble", None)]



def test_work_run_renders_the_run_summary_inside_the_card_projector(monkeypatch, capsys, tmp_path) -> None:
    """BOUNDED-ROUTINE-LAUNCH: `work run` calls the launcher's `run` once, inside the card projector and the launch
    reservation, with the retry pause, and renders its summary with any projection still owed."""
    from contextlib import contextmanager
    from types import SimpleNamespace
    from alienintent.control_plane.adapters import cli
    from alienintent.control_plane.application import operator
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.execution_coordination.application.factory_coordinator import RunSummary, StopReason
    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
    events, store = [], SQLiteOperationalStore(tmp_path / "launch.sqlite")

    def run(pause):
        events.append(("run", [r.scope for r in store.recovery_reservations("registry")]))
        pause()
        return RunSummary(StopReason.EXHAUSTED, ("A",), ran=("A", "A", "A"))

    @contextmanager
    def projection():
        events.append("projector on")
        yield
        events.append("projector off")
    launcher = SimpleNamespace(run=run, projection_diagnostics={"A": "A: RuntimeError: x"})
    registry = SimpleNamespace(launcher=lambda: launcher, store=store, ownership=ProcOwnership(),
                               card_projection=projection)
    monkeypatch.setattr(cli, "_factory", lambda _: SimpleNamespace(work_registry=registry))
    monkeypatch.setattr(cli.time, "sleep", lambda seconds: events.append(("sleep", seconds)))

    assert cli.main(["--json", "--profile-factory", "x:y", "work", "run"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "stop_reason": "eligible-backlog-exhausted", "dispatched": ["A"], "authority_blocked": [], "failed": [],
        "ran": ["A", "A", "A"], "infrastructure_held": [], "projection_diagnostics": {"A": "A: RuntimeError: x"}}
    assert events == ["projector on", ("run", ["launch"]), ("sleep", operator.RETRY_PAUSE_SECONDS), "projector off"]
    assert store.recovery_reservations("registry") == ()


def test_work_run_wait_runs_again_after_each_idle_run_with_no_one_invoking_it(tmp_path) -> None:
    """`work run --wait`: an idle run (nothing ran, or another launch holds the reservation) waits, then runs again;
    a run that ran a role is reported and followed at once by the next run."""
    from types import SimpleNamespace
    from alienintent.control_plane.application.operator import LAUNCH_IN_PROGRESS, watch_work
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.execution_coordination.application.factory_coordinator import (
        LAUNCH_KEY, LAUNCH_SCOPE, RunSummary, StopReason)
    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
    store, ownership = SQLiteOperationalStore(tmp_path / "launch.sqlite"), ProcOwnership()
    owner = "launcher:" + json.dumps(dict(ownership.current()), sort_keys=True, separators=(",", ":"))
    held = store.acquire("registry", LAUNCH_SCOPE, LAUNCH_KEY, owner)  # a live launch holds it at first
    runs = iter([RunSummary(StopReason.EXHAUSTED, ()), RunSummary(StopReason.EXHAUSTED, (), ran=("B",)),
                 RunSummary(StopReason.EXHAUSTED, ())])
    reports, events = [], []

    class Stop(Exception):
        pass

    def sleep(seconds):
        events.append(("sleep", seconds))
        if len([event for event in events if event[0] == "sleep"]) == 1:
            store.release("registry", held.scope, held.key, held.owner, held.fence)
        if len([event for event in events if event[0] == "sleep"]) == 3:
            raise Stop()

    def run(pause):
        events.append(("run",))
        return next(runs)
    launcher = SimpleNamespace(run=run, projection_diagnostics={})
    with pytest.raises(Stop):
        watch_work(lambda: launcher, store, ownership, 30, reports.append, sleep)
    assert [report.get("answer") or list(report["ran"]) for report in reports] == [LAUNCH_IN_PROGRESS, ["B"]]
    assert events == [("sleep", 30), ("run",), ("sleep", 30), ("run",), ("run",), ("sleep", 30)]


def test_work_run_wait_survives_a_failed_run_and_runs_again(tmp_path) -> None:
    """A run that raises (the board unreadable, a store or git error) is reported, waited out and run again: one
    transient failure never ends the service. The launch reservation is released."""
    from types import SimpleNamespace
    from alienintent.control_plane.application.operator import watch_work
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.execution_coordination.application.factory_coordinator import RunSummary, StopReason
    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
    store = SQLiteOperationalStore(tmp_path / "launch.sqlite")
    answers = iter([OSError("board unreadable"), RunSummary(StopReason.EXHAUSTED, (), ran=("B",))])
    reports, waits = [], []

    class Stop(BaseException):
        pass

    def run(pause):
        answer = next(answers, None)
        if answer is None:
            raise Stop()
        if isinstance(answer, Exception):
            raise answer
        return answer
    with pytest.raises(Stop):
        watch_work(lambda: SimpleNamespace(run=run, projection_diagnostics={}), store, ProcOwnership(), 30,
                   reports.append, waits.append)
    assert reports[0] == {"error": "OSError", "detail": "board unreadable"} and list(reports[1]["ran"]) == ["B"]
    assert waits == [30]
    assert store.recovery_reservations("registry") == ()


def test_work_launch_runs_inside_the_card_projector_and_work_project_runs_one_pass(monkeypatch, capsys, tmp_path) -> None:
    """CARD-FOLLOWS-STAGE: the launch runs inside `card_projection`; `work project` is the projector on its own."""
    from contextlib import contextmanager
    from types import SimpleNamespace
    from alienintent.control_plane.adapters import cli
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
    calls = []

    @contextmanager
    def card_projection():
        calls.append("projection-start")
        yield
        calls.append("projection-end")
    launcher = SimpleNamespace(launch=lambda identity: calls.append("launch") or "closure-not-automated")
    registry = SimpleNamespace(launcher=lambda: launcher, card_projection=card_projection,
                               project_cards=lambda: calls.append("pass") or 2,
                               store=SQLiteOperationalStore(tmp_path / "launch.sqlite"), ownership=ProcOwnership())
    monkeypatch.setattr(cli, "_factory", lambda _: SimpleNamespace(work_registry=registry))
    assert cli.main(["--json", "--profile-factory", "x:y", "work", "launch", "ITEM"]) == 0
    assert calls == ["projection-start", "launch", "projection-end"]
    capsys.readouterr()
    assert cli.main(["--json", "--profile-factory", "x:y", "work", "project"]) == 0
    assert json.loads(capsys.readouterr().out) == {"retired": 2} and calls[-1] == "pass"

def test_two_launchers_taking_over_one_stale_launch_reservation_exactly_one_wins(tmp_path) -> None:
    """RESTART-CONTINUATION check 0: the loser of a takeover race (its release meets a stale fence) answers
    LAUNCH_IN_PROGRESS and launches nothing; the winner launches once and releases the reservation."""
    from types import SimpleNamespace
    from alienintent.control_plane.application.operator import exclusive_launch_work
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
    store = SQLiteOperationalStore(tmp_path / "launch.sqlite")
    dead = dict(ProcOwnership().current()) | {"pid": next(p for p in range(4_194_000, 1, -1)
                                                          if not Path(f"/proc/{p}").exists())}
    store.acquire("registry", "launch", "registry", "launcher:" + json.dumps(dead, sort_keys=True))
    launched, answers = [], []
    coordinator = lambda name: SimpleNamespace(launch=lambda identity: launched.append(name) or "not-eligible")

    class Racing(ProcOwnership):
        raced = False

        def owner_state(self, owner):
            state = super().owner_state(owner)
            if not Racing.raced:  # the other launcher takes the same stale reservation over meanwhile
                Racing.raced = True
                answers.append(exclusive_launch_work(lambda: coordinator("winner"), "B", store, Racing()))
            return state
    loser = exclusive_launch_work(lambda: coordinator("loser"), "A", store, Racing())
    assert loser == {"identity": "A", "answer": "LAUNCH_IN_PROGRESS", "owner_state": "terminated"}
    assert answers == [{"identity": "B", "answer": "not-eligible"}] and launched == ["winner"]
    assert store.recovery_reservations("registry") == ()


# --- WORKER-CREDENTIAL-BOUNDARY check 6d: `work context --export` reads only the bounded export -----------------
SOURCE = Path(__file__).resolve().parents[2] / "src"
OPENED: list[str] | None = None


def _audit(event: str, args: tuple) -> None:
    if OPENED is not None and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        OPENED.append(os.fsdecode(args[0]))


sys.addaudithook(_audit)


@pytest.fixture
def export(tmp_path, monkeypatch):
    """One Founder-owned export (folders 0711, file 0640) and the worker's three identity variables."""
    folder = tmp_path / "launch" / "exports" / "launch:c:1"
    folder.mkdir(parents=True, mode=0o711)
    path = folder / "context.json"
    package = {"status": "PACKAGE", "identity": "item-1", "role": "PRODUCER", "goal": "TEST DATA",
               "context_command": {"argv": ["alienintent", "--json", "work", "context", "--export", str(path)],
                                   "environment": {"ALIENINTENT_WORK_IDENTITY": "item-1",
                                                   "ALIENINTENT_ROLE": "PRODUCER",
                                                   "ALIENINTENT_CORRELATION": "launch:c:1"}}}
    path.write_text(json.dumps(package))
    path.chmod(0o640)
    for name, value in package["context_command"]["environment"].items():
        monkeypatch.setenv(name, value)
    return path, package


def _run_export(argv: list[str], capsys) -> tuple[int, object, list[str]]:
    """main() in process, recording every file it opens."""
    global OPENED
    from alienintent.control_plane.adapters import cli
    OPENED = []
    try:
        code = cli.main(argv)
    finally:
        opened, OPENED = OPENED, None
    return code, json.loads(capsys.readouterr().out), opened


def test_the_export_mode_prints_exactly_the_export_and_opens_nothing_else(export, capsys, monkeypatch):
    """Dispatched before any profile factory: it prints the exported package and opens only the export path; no
    database, evidence repository or configuration is opened, and no profile is built."""
    import sqlite3
    from alienintent.composition import work_registry
    path, package = export
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **k: pytest.fail("a database was opened"))
    for name in ("work_registry_profile", "work_context_profile", "load_project_configuration"):
        monkeypatch.setattr(work_registry, name, lambda *a, **k: pytest.fail("a profile was built"))
    monkeypatch.setattr(work_registry.WorkRegistry, "__init__", lambda *a, **k: pytest.fail("a registry was built"))
    code, answer, opened = _run_export(["--json", "work", "context", "--export", str(path)], capsys)
    assert (code, answer) == (0, package)
    assert set(opened) == {str(path.parent.parent), "launch:c:1", "context.json"}


@pytest.mark.parametrize("variable, value", [("ALIENINTENT_WORK_IDENTITY", "item-2"), ("ALIENINTENT_ROLE", "VERIFIER"),
                                             ("ALIENINTENT_CORRELATION", "launch:c:2")])
def test_another_work_item_role_or_correlation_is_not_in_export(export, capsys, monkeypatch, variable, value):
    path, _ = export
    monkeypatch.setenv(variable, value)
    code, answer, opened = _run_export(["--json", "work", "context", "--export", str(path)], capsys)
    assert (code, answer) == (1, {"error": "not-in-export"})
    if variable == "ALIENINTENT_CORRELATION":
        assert opened == []  # another correlation's folder is never opened


@pytest.mark.parametrize("extra", [["item-1"], ["--role", "PRODUCER"], ["--correlation", "launch:c:1"],
                                   ["--candidate", "git:r#b@" + "a" * 40], ["--contract-digest", "sha256:0"],
                                   ["--profile-factory", "os:getcwd"]])
def test_any_further_argument_is_refused_reading_nothing(export, capsys, extra):
    path, _ = export
    code, answer, opened = _run_export(["--json", "work", "context", "--export", str(path), *extra], capsys)
    assert (code, answer, opened) == (1, {"error": "not-in-export"}, [])


def test_another_path_or_evidence_object_is_not_in_export_and_reads_nothing(export, capsys, tmp_path):
    path, _ = export
    evidence = tmp_path / "evidence" / "objects" / "ab"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("EVIDENCE TEST DATA")
    for other in (evidence, path.parent / "other.json", tmp_path / "launch" / "context" / "launch:c:1" / "context.json"):
        code, answer, opened = _run_export(["--json", "work", "context", "--export", str(other)], capsys)
        assert (code, answer, opened) == (1, {"error": "not-in-export"}, []), other


def test_a_symlink_fifo_foreign_owner_or_swapped_folder_is_refused_without_reading_it(export, capsys, tmp_path):
    from alienintent.control_plane.application.operator import export_context
    path, package = export
    secret = tmp_path / "founder-secret.json"
    secret.write_text(json.dumps(package))
    path.unlink()
    path.symlink_to(secret)
    code, answer, opened = _run_export(["--json", "work", "context", "--export", str(path)], capsys)
    assert (code, answer) == (1, {"error": "export-refused"}) and str(secret) not in opened
    path.unlink()
    os.mkfifo(path)  # opened with O_NONBLOCK: refused without blocking
    code, answer, _ = _run_export(["--json", "work", "context", "--export", str(path)], capsys)
    assert (code, answer) == (1, {"error": "export-refused"})
    path.unlink()
    path.write_text(json.dumps(package))
    assert export_context(str(path), os.environ, founder_uid=os.getuid() + 1) == {"error": "export-refused"}
    assert export_context(str(path), os.environ) == package
    folder = path.parent
    folder.rename(folder.with_name("moved"))
    folder.symlink_to(folder.with_name("moved"))  # a swapped <c> folder
    assert export_context(str(path), os.environ) == {"error": "export-refused"}


def test_the_export_mode_runs_as_a_process_with_no_profile_factory(export):
    path, package = export
    result = subprocess.run([sys.executable, "-c", "import sys; from alienintent.control_plane.adapters.cli import "
                             "main; sys.exit(main())", "--json", "work", "context", "--export", str(path)],
                            capture_output=True, text=True, check=False, timeout=60,
                            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(SOURCE),
                                 **package["context_command"]["environment"]})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == package
