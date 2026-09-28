"""Offline checks for the FX-B3/FX-B4 release-admission proof harness (WO-220506, Issue #126).

The live fixture runs against GitHub. These tests drive the same ``run_phase`` sequence over an
in-memory board and a local git remote, so the case table, the refusal attribution, the mutation
scope check, cleanup and the non-interference diff are exercised without any network, and the
harness's own discrimination is shown: with the release gate faulted, the gate cases launch and
the run fails; restored, it passes again.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fx_b3_release_admission_proof as fixture  # noqa: E402
from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate  # noqa: E402

PROJECT = "PVT_fixtureProject"


class Identity:
    def __call__(self, value):
        return value

    def text(self, value: str) -> str:
        return value


class FakeBoard:
    """An in-memory Project with the LiveBoard surface; it keeps one unrelated item to watch."""

    def __init__(self) -> None:
        self.transport = SimpleNamespace(mutations=[])
        self._next = 0
        self.items: dict[str, dict] = {"PVTI_unrelated": self._item("PVTI_unrelated", "SB-01 — unrelated", "biu: SB-01", "DONE")}

    @staticmethod
    def _item(item: str, title: str, body: str, status: str | None) -> dict:
        fields = {} if status is None else {"Status": {"value": status, "updatedAt": "2026-09-28T00:00:00Z"}}
        return {"id": item, "type": "DRAFT_ISSUE", "isArchived": False, "updatedAt": "2026-09-28T00:00:00Z",
                "content": {"typename": "DraftIssue", "id": "DI_" + item, "number": None, "title": title,
                            "body_sha256": fixture.sha256(body), "state": None, "updatedAt": None, "closedAt": None},
                "fields": fields, "_body": body}

    def _mutate(self, operation: str, item: str | None) -> None:
        self.transport.mutations.append({"operation": operation, "project": PROJECT, "item": item, "field": None, "title": None})

    def schema_statuses(self):
        return ("READY", "IMPLEMENT", "DONE")

    def read_items(self, detailed: bool = False):
        return copy.deepcopy(list(self.items.values()))

    def create(self, title: str, body: str) -> str:
        self._next += 1
        item = f"PVTI_probe{self._next}"
        self._mutate("addProjectV2DraftIssue", None)
        self.items[item] = self._item(item, title, body, None)
        return item

    def make_ready(self, item: str) -> None:
        self._mutate("updateProjectV2ItemFieldValue", item)
        self._mutate("updateProjectV2ItemFieldValue", item)
        self.items[item]["fields"] = {"Priority": {"value": "P5", "updatedAt": "2026-09-28T00:00:01Z"},
                                      "Status": {"value": "READY", "updatedAt": "2026-09-28T00:00:01Z"}}

    def read_back(self, item: str) -> dict:
        entry = self.items[item]
        return {"item": item, "status": entry["fields"]["Status"]["value"], "priority": entry["fields"]["Priority"]["value"],
                "title": entry["content"]["title"], "body_sha256": fixture.sha256(entry["_body"]), "status_updated_at": None}

    def delete(self, item: str) -> str:
        self._mutate("deleteProjectV2Item", item)
        del self.items[item]
        return item

    def absent(self, item: str) -> bool:
        return item not in self.items


def _target(tmp_path: Path, phase: int) -> fixture.Target:
    secret, key = tmp_path / "webhook", tmp_path / "app.pem"
    secret.write_text("fixture-webhook-secret")
    key.write_text("not a key")
    secret.chmod(0o600)
    key.chmod(0o600)
    document = {
        "profile": "fx-b3-offline", "repository": "AlienLogicLab/alienintent-sandbox", "project_reference": PROJECT,
        "project_number": 2, "project_status_field": "PVTSSF_status", "project_priority_field": "PVTSSF_priority",
        "lifecycle_statuses": {"READY": "READY"}, "projection_fields": {"IMPLEMENT": "Status"},
        "webhook_secret_reference": "webhook", "secret_references": {"webhook": str(secret)}, "automatic_release": True,
        "githubApp": {"applicationId": 1, "installationId": 2, "privateKeyPath": str(key)},
    }
    return fixture.Target("sandbox" if phase == 1 else "production", "FX-B3" if phase == 1 else "FX-B4", phase, document)


def _remote(tmp_path: Path) -> Path:
    remote, seed = tmp_path / "remote.git", tmp_path / "seed"
    subprocess.run(["git", "init", "-q", "--bare", "--initial-branch=main", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "--initial-branch=main", str(seed)], check=True)
    identity = ["-c", "user.name=fx", "-c", "user.email=fx@example.invalid"]
    subprocess.run(["git", *identity, "commit", "-q", "--allow-empty", "-m", "baseline"], cwd=seed, check=True)
    subprocess.run(["git", "push", "-q", str(remote), "main"], cwd=seed, check=True)
    return remote


def _run(tmp_path: Path, phase: int, watched: dict | None = None) -> tuple[int, dict, FakeBoard]:
    board = FakeBoard()
    run_root, out = tmp_path / "run", tmp_path / "out"
    run_root.mkdir()
    remote = _remote(tmp_path)
    status = fixture.run_phase(_target(tmp_path, phase), board, watched or {}, out, run_root, Identity(),
                               lambda: fixture.prepare_checkout(run_root, str(remote), None))
    return status, json.loads((out / "result.json").read_text()), board


def test_every_pinned_step_is_present_once():
    steps = [case.step for case in fixture.CASES]
    for step in ("step 2", "step 3", "step 4", "step 5", "step 6", "step 7", "step 8 (re-pinned)", "step 9", "step 10",
                 "step 11", "step 12", "step 13", "step 14"):
        assert step in steps
    assert sum(case.expected_starts for case in fixture.cases_for(2)) == 1
    assert sum(case.expected_starts for case in fixture.cases_for(1)) == 2
    assert all(case.expected_starts == (0 if case.refused_by else 1) for case in fixture.CASES)


def test_probe_text_never_reads_as_denial_but_the_denial_case_does():
    identity = fixture.probe_identity("FX-B4-PROBE", "L", "POS")
    assert not fixture.UNAUTHORIZED_WORDING.search(fixture.probe_title(identity))
    target = SimpleNamespace(fixture="FX-B4", repository="AlienLogicLab/alienintent")
    valid = json.dumps(fixture.contract_document(identity, target, {}, "P"))
    assert not fixture.UNAUTHORIZED_WORDING.search(valid)
    assert fixture.UNAUTHORIZED_WORDING.search(fixture.DENIAL)
    assert not fixture.probe_title(identity).startswith("WO-")


def test_board_diff_reports_every_kind_of_change():
    base = FakeBoard().read_items()
    before = fixture.board_digest(base)
    assert fixture.board_diff(before, fixture.board_digest(copy.deepcopy(base)))["unchanged"]
    moved = copy.deepcopy(base)
    moved[0]["fields"]["Status"]["value"] = "READY"
    diff = fixture.board_diff(before, fixture.board_digest(moved))
    assert not diff["unchanged"] and diff["changed"][0]["keys"] == ["fields"]
    assert fixture.board_diff(before, {})["removed"] == ["PVTI_unrelated"]


def test_recording_transport_names_the_mutated_item():
    inner = SimpleNamespace(request=lambda *args: SimpleNamespace(status=200, body=b"{}"))
    transport = fixture.RecordingTransport(inner)
    body = json.dumps({"query": "mutation($project:ID!,$item:ID!){ deleteProjectV2Item(input:{projectId:$project,itemId:$item}){ deletedItemId } }",
                       "variables": {"project": PROJECT, "item": "PVTI_x"}}).encode()
    transport.request("POST", "u", {}, body)
    transport.request("POST", "u", {}, json.dumps({"query": "query{ viewer{ login } }"}).encode())
    assert transport.mutations[0]["operation"] == "deleteProjectV2Item" and transport.mutations[0]["item"] == "PVTI_x"
    assert transport.reads == 1


def test_phase2_sequence_passes_offline_and_cleans_up(tmp_path):
    status, record, board = _run(tmp_path, 2)
    assert status == 0, record["checks"] | {"failure": record["failure"]}
    assert record["totals"]["observed_worker_starts"] == 1
    assert {case["case"]: case["observed_refused_by"] for case in record["cases"]}["13-unreachable-baseline"] == "gate:baseline-reachable"
    assert list(board.items) == ["PVTI_unrelated"]
    assert record["non_interference"]["target"]["unchanged"]


def test_phase1_contrast_admits_and_watched_board_is_compared(tmp_path):
    watched = FakeBoard()
    status, record, _ = _run(tmp_path, 1, {"production": watched})
    assert status == 0, record["checks"]
    assert record["totals"]["observed_worker_starts"] == 2
    assert record["non_interference"]["production"]["unchanged"]


def test_faulted_gate_is_detected_then_restored(tmp_path, monkeypatch):
    monkeypatch.setattr(ReleasePreconditionGate, "check", lambda self, item: None)
    (tmp_path / "fault").mkdir()
    status, record, board = _run(tmp_path / "fault", 2)
    assert status == 1
    faulted = {case["case"]: case for case in record["cases"]}
    assert faulted["09-no-release-record"]["observed_worker_starts"] == 1 and not faulted["09-no-release-record"]["matches_expected"]
    assert record["checks"]["cleanup_verified"] and list(board.items) == ["PVTI_unrelated"]
    monkeypatch.undo()
    (tmp_path / "restored").mkdir()
    status, record, _ = _run(tmp_path / "restored", 2)
    assert status == 0, record["checks"]
