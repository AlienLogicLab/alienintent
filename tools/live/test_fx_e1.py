"""Offline regression for the FX-E1 evaluator and no-Node instrument (WO-220502).

The live proof itself needs the sandbox and its authority; these tests pin what
judges it: every predicate passes only on present evidence, each fault holds its
own predicate, and the no-Node instrument detects Node by name and by path.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fx_e1_evaluate import CONTROLS, PREDICATES, controls, evaluate  # noqa: E402
from fx_e1_no_node import real_node_binaries, self_test  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[2] / "docs/evidence/wave2-proof-fixtures/FX-E1"
MANIFEST = FIXTURE / "manifest.json"
A, B = "E1-000000-A", "E1-000000-B"


def listener(pid: int) -> dict:
    return {"port": 8789, "owners": [{"pid": pid, "executable_name": "python3", "argv": ["python3"]}]}


def aggregate(identity: str, correlation: str) -> dict:
    return {"stage": "DONE", "accepted": True, "correlation": correlation,
            "candidate": {"independent_read_back_proven": True}}


def passing_record() -> dict:
    node_writer = {"runtime_pids": [42], "bootstrap_ports_listening": ["8787", "8788"],
                   "bootstrap_port_answers": {"8787": "404", "8788": "401"}, "root_tunnel_config_mtime": 1}
    return {
        "repository": "AlienLogicLab/alienintent-sandbox", "identities": [A, B],
        "pinned": {"fixture_plan_committed_before_run": True, "identification_committed_before_run": True,
                   "fixture_plan_digest": "sha256:1", "identification_digest": "sha256:2", "source_clean": True,
                   "source_revision": "abc"},
        "instrument_self_test": {"ok": True, "probes": [
            {"probe": name, "applied": True, "discriminates": True}
            for name in ("intact", "fault-shimmed-node-by-name", "fault-absolute-node-bypassing-shims", "restored")]},
        "no_node": {"samples": 10, "processes_observed": 5, "node_observed": False, "shim_invocations": [], "node_observations": []},
        "dependency_path": {"exit_status": 0, "modules_loaded": 100, "modules_outside_stdlib_and_alienintent": [],
                            "node_references_in_python_source": []},
        "isolation": {"findings": [], "repository_scope": ["AlienLogicLab/alienintent-sandbox"]},
        "substitutions": [{"what": "worker", "claims_nothing_about": "providers"}],
        "before": {"node_writer": dict(node_writer)}, "after": {"node_writer": dict(node_writer)},
        "phases": [
            {"phase": "process-loss", "pid": 100, "signal": "SIGKILL", "effect_unresolved_at_kill": True,
             "held_reservation": {"owner": f"launch:{A}:0"}, "ingress_listener": listener(100)},
            {"phase": "restart", "exit_status": 0},
            {"phase": "ingress-restart", "pid": 200, "ingress_listener": listener(200),
             "replay": {"available": True, "redelivery_status_code": 202, "receipt_unchanged": True,
                        "receipt_before": {"event_id": "g"}, "effect_before": [1], "effect_after": [1],
                        "notification_lines_before": 3, "notification_lines_after": 3, "originally_admitted_by": "A"},
             "scope_controls": [
                 {"control": "unsigned", "http_status": 401, "durable_receipt_created": False, "label": "LOCAL"},
                 {"control": "wrong", "http_status": 401, "durable_receipt_created": False, "label": "LOCAL"},
                 {"control": "foreign", "http_status": 401, "durable_receipt_created": False, "label": "LOCAL"},
                 {"control": "foreign_project_address_resolution", "refused": True}]},
        ],
        "readback": {
            "store": {"state": {"aggregates": {f"factory:{A}": aggregate(A, f"launch:{A}:1"),
                                               f"factory:{B}": aggregate(B, f"launch:{B}:0")}},
                      "effects": [{"identity": f"launch:{A}:0", "status": "authority-authorized"},
                                  {"identity": f"launch:{A}:1", "status": "confirmed"},
                                  {"identity": f"launch:{B}:0", "status": "confirmed"}]},
            "project": [{"identity": A, "status": "DONE"}, {"identity": B, "status": "DONE"}],
            "candidates": [{"identity": A, "revision": "r1", "note_read_back": True},
                           {"identity": B, "revision": "r2", "note_read_back": True}],
            "deliveries": [{"status_code": 202, "redelivery": False, "durable_receipt": True, "process": "A"}],
        },
    }


class EvaluatorTests(unittest.TestCase):
    def test_complete_evidence_passes_every_predicate(self) -> None:
        verdict = evaluate(passing_record())
        self.assertEqual(verdict["disposition"], "PASS", verdict)
        self.assertEqual(len(verdict["predicates"]), len(PREDICATES))

    def test_every_control_holds_its_own_predicate_and_restores(self) -> None:
        result = controls(passing_record())
        self.assertTrue(result["ok"], json.dumps(result, indent=1))
        self.assertEqual({control["predicate"] for control in result["controls"]}, {identity for identity, _, _ in PREDICATES})
        self.assertEqual(len(result["controls"]), len(CONTROLS))

    def test_missing_measurement_holds_never_passes(self) -> None:
        for section in ("pinned", "no_node", "readback", "phases", "before", "substitutions", "instrument_self_test"):
            record = passing_record()
            del record[section]
            with self.subTest(section=section):
                self.assertEqual(evaluate(record)["disposition"], "HOLD")

    def test_local_fake_without_github_delivery_log_holds(self) -> None:
        record = passing_record()
        record["readback"]["deliveries"] = []
        held = [p["id"] for p in evaluate(record)["predicates"] if p["outcome"] == "HOLD"]
        self.assertIn("E1-4", held)

    def test_ingress_held_by_a_non_python_process_holds(self) -> None:
        record = passing_record()
        record["phases"][0]["ingress_listener"]["owners"][0]["executable_name"] = "node"
        held = [p["id"] for p in evaluate(record)["predicates"] if p["outcome"] == "HOLD"]
        self.assertIn("E1-3", held)

    def test_restart_without_killed_in_flight_work_holds(self) -> None:
        record = passing_record()
        record["phases"][0]["held_reservation"] = None
        held = [p["id"] for p in evaluate(record)["predicates"] if p["outcome"] == "HOLD"]
        self.assertIn("E1-7", held)

    @unittest.skipUnless(MANIFEST.is_file(), "no retained FX-E1 run in this checkout")
    def test_every_retained_run_reproduces_its_recorded_disposition(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(manifest["runs"])
        for run in manifest["runs"]:
            record = json.loads((FIXTURE / run["record"]).read_text(encoding="utf-8"))
            with self.subTest(run=run["run_id"]):
                self.assertEqual(evaluate(record)["disposition"], run["disposition"])
                self.assertEqual(record["verdict"]["disposition"], run["disposition"])
        accepted = [run for run in manifest["runs"] if run["run_id"] == manifest["accepted_run"]]
        self.assertEqual([run["disposition"] for run in accepted], ["PASS"])
        record = json.loads((FIXTURE / accepted[0]["record"]).read_text(encoding="utf-8"))
        self.assertTrue(controls(copy.deepcopy(record))["ok"])


class InstrumentTests(unittest.TestCase):
    @unittest.skipUnless(real_node_binaries() and shutil.which("sh"), "no Node binary to exercise the fault probes")
    def test_instrument_detects_node_by_name_and_by_path_and_restores(self) -> None:
        result = self_test()
        self.assertTrue(result["ok"], json.dumps(result, indent=1))
        observed = {probe["probe"]: probe["node_observed"] for probe in result["probes"]}
        self.assertFalse(observed["intact"])
        self.assertTrue(observed["fault-shimmed-node-by-name"])
        self.assertTrue(observed["fault-absolute-node-bypassing-shims"])
        self.assertTrue(observed["fault-stated-environment-detached"])
        self.assertFalse(observed["restored"])


if __name__ == "__main__":
    unittest.main()
