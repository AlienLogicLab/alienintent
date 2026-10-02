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
    from tests.context_assembly.test_work_identity_service import commit_file
    clone, commit, packet = _registry_project(tmp_path)
    item = json.loads(_registry_cli(tmp_path, "register", "--file", str(tmp_path / "packet.md"), "--repo", "r",
                                    "--path", "docs/packet.md", "--commit", commit, "--label", "PACKET").stdout)
    revised = commit_file(clone, "main", "docs/packet.md", packet + b"revised\n")
    (tmp_path / "revised.md").write_bytes(packet + b"revised\n")
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
    (tmp_path / "projects.json").write_text(json.dumps(document))
    assessed = _registry_cli(tmp_path, "assess", "PACKET")
    assert assessed.returncode == 0, assessed.stdout + assessed.stderr
    value = json.loads(assessed.stdout)
    assert (value["identity"], value["disposition"], value["reused"]) == (item["id"], "READY", False)
    again = json.loads(_registry_cli(tmp_path, "assess", item["id"]).stdout)
    assert (again["attempt_id"], again["reused"]) == (value["attempt_id"], True)
    shown = json.loads(_registry_cli(tmp_path, "show", "PACKET").stdout)["item"]
    assert shown["assessment_ref"] == value["assessment_ref"] and shown["state"] == "CAPTURE"
    assert json.loads(_registry_cli(tmp_path, "assess", "missing").stdout) == {
        "answer": "UNKNOWN_IDENTITY", "identity": "missing", "attempt_id": None, "detail": ""}
