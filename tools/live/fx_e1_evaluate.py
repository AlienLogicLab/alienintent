#!/usr/bin/env python3
"""FX-E1 evaluator: judge a retained FX-E1 proof-run record against the E1 predicate.

Pure and offline. Every predicate is either PASS on evidence present in the record
or HOLD with the reason; a missing field is a HOLD, never a PASS and never zero.
The overall disposition is PASS only when every predicate passes.

`--controls` applies one fault per predicate to a copy of the record and requires
intact PASS, the fault HOLD on exactly its named predicate, and restored PASS —
the intact/fault/restored discrimination WO-220502 requires of mechanical controls.

    python3 tools/live/fx_e1_evaluate.py docs/evidence/wave2-proof-fixtures/FX-E1/proof-run.json
    python3 tools/live/fx_e1_evaluate.py <proof-run.json> --controls --json
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Callable

DONE = "DONE"


class Hold(Exception):
    """The evidence does not establish the predicate."""


def need(condition: object, reason: str) -> None:
    if not condition:
        raise Hold(reason)


def phase(record: dict, name: str) -> dict:
    found = [entry for entry in record.get("phases") or [] if entry.get("phase") == name]
    need(found, f"no {name} phase is recorded")
    return found[0]


def aggregate(record: dict, identity: str) -> dict:
    aggregates = ((record.get("readback") or {}).get("store") or {}).get("state", {}).get("aggregates") or {}
    found = aggregates.get(f"factory:{identity}")
    need(isinstance(found, dict), f"no durable factory aggregate for {identity}")
    return found


def identities(record: dict) -> list[str]:
    found = record.get("identities") or []
    need(len(found) >= 2, "the run names fewer than two seeded BIUs")
    return list(found)


def python_owner(listener: dict, pid: object) -> bool:
    owners = (listener or {}).get("owners") or []
    return bool(owners) and all(owner.get("executable_name", "").startswith("python") for owner in owners) \
        and any(owner.get("pid") == pid for owner in owners)


# --- predicates ---------------------------------------------------------------------


def pinned_before_live(record: dict) -> str:
    pinned = record.get("pinned") or {}
    need(pinned.get("fixture_plan_committed_before_run"), "the fixture plan was not committed before the run")
    need(pinned.get("identification_committed_before_run"), "the identification was not committed before the run")
    need(pinned.get("fixture_plan_digest") and pinned.get("identification_digest"), "pinned digests are missing")
    need(pinned.get("source_clean"), "the source under test was not the committed revision")
    need(pinned.get("source_revision"), "the source revision is not recorded")
    return f"plan and identification committed before the run at {pinned['source_revision']}"


def instrument_discriminates(record: dict) -> str:
    test = record.get("instrument_self_test") or {}
    probes = test.get("probes") or []
    need(test.get("ok") is True, "the no-Node instrument self-test did not pass")
    need(len(probes) >= 4 and all(probe.get("applied") and probe.get("discriminates") for probe in probes),
         "an instrument probe was not applied or did not discriminate")
    faults = [probe["probe"] for probe in probes if probe["probe"].startswith("fault")]
    need(len(faults) >= 2, "fewer than two fault probes were applied")
    return f"{len(probes)} probes discriminate (faults detected: {faults})"


def no_node(record: dict) -> str:
    observed = record.get("no_node") or {}
    static = record.get("dependency_path") or {}
    need(observed.get("samples", 0) > 0 and observed.get("processes_observed", 0) > 0, "the sampler recorded no processes")
    need(observed.get("node_observed") is False, f"Node was observed: {observed.get('node_observations') or observed.get('shim_invocations')}")
    need(not observed.get("shim_invocations"), "a Node shim was invoked")
    need(static.get("exit_status") == 0 and static.get("modules_loaded", 0) > 0, "the dependency path was not measured")
    need(static.get("modules_outside_stdlib_and_alienintent") == [], "the production path loads modules outside stdlib and alienintent")
    need(static.get("node_references_in_python_source") == [], "the Python source references a Node executable")
    for name in ("process-loss", "ingress-restart"):
        entry = phase(record, name)
        need(python_owner(entry.get("ingress_listener") or {}, entry.get("pid")), f"the {name} ingress port was not held by the Python process")
    return (f"{observed['processes_observed']} processes over {observed['samples']} samples, 0 Node; "
            f"{static['modules_loaded']} modules, all stdlib or alienintent")


def real_ingress(record: dict) -> str:
    log = (record.get("readback") or {}).get("deliveries")
    need(isinstance(log, list), "GitHub's delivery log was not read back")
    admitted = [entry for entry in log if entry.get("status_code") == 202 and not entry.get("redelivery")]
    need(admitted, "no real delivery was accepted during the run")
    need(all(entry.get("durable_receipt") for entry in admitted), "an accepted delivery has no durable receipt")
    need(all(entry.get("process") for entry in admitted), "an accepted delivery falls outside every control-plane process window")
    by_process = sorted({entry.get("process") for entry in admitted if entry.get("process")})
    return f"{len(admitted)} real deliveries accepted with durable receipts, by processes {by_process}"


def effect_dispatch(record: dict) -> str:
    effects = ((record.get("readback") or {}).get("store") or {}).get("effects")
    need(isinstance(effects, list), "durable effects were not read back")
    confirmed = {effect["identity"] for effect in effects if effect.get("status") == "confirmed"}
    candidates = (record.get("readback") or {}).get("candidates") or []
    for identity in identities(record):
        state = aggregate(record, identity)
        need(state.get("correlation") in confirmed, f"{identity}: its dispatch effect is not confirmed")
        candidate = state.get("candidate") or {}
        need(candidate.get("independent_read_back_proven"), f"{identity}: candidate publication was not independently read back")
        need(any(entry.get("identity") == identity and entry.get("revision") for entry in candidates),
             f"{identity}: no published candidate branch was found at the remote")
    return "every seeded BIU's dispatch effect is confirmed and its candidate published"


def durable_outcome_readback(record: dict) -> str:
    project = {entry.get("identity"): entry for entry in (record.get("readback") or {}).get("project") or []}
    candidates = (record.get("readback") or {}).get("candidates") or []
    for identity in identities(record):
        need(aggregate(record, identity).get("stage") == DONE, f"{identity}: the durable store does not record DONE")
        need((project.get(identity) or {}).get("status") == DONE, f"{identity}: the Project does not read back DONE")
        need(any(entry.get("identity") == identity and entry.get("note_read_back") for entry in candidates),
             f"{identity}: the candidate content was not read back from a fresh clone")
    return "store DONE, Project DONE and candidate content read back from a fresh clone, for every seeded BIU"


def restart(record: dict) -> str:
    loss = phase(record, "process-loss")
    need(loss.get("signal") == "SIGKILL" and loss.get("held_reservation"), "no process loss with a held reservation")
    need(loss.get("effect_unresolved_at_kill"), "the killed process held no unresolved effect")
    first = identities(record)[0]
    need(first in str((loss.get("held_reservation") or {}).get("owner")), f"the killed process was not holding {first}")
    need(phase(record, "restart").get("exit_status") == 0, "the restarted run did not exit cleanly")
    need(aggregate(record, first).get("stage") == DONE, f"{first} did not reach DONE after the restart")
    replay = phase(record, "ingress-restart").get("replay") or {}
    need(replay.get("available"), "no delivery admitted by an earlier process was available to redeliver")
    need(replay.get("redelivery_status_code") == 202, "GitHub did not record the redelivery as accepted")
    need(replay.get("receipt_unchanged") is True and replay.get("receipt_before"), "the redelivered delivery changed its durable receipt")
    need(replay.get("effect_after") == replay.get("effect_before"), "the redelivery changed its durable effect")
    need(replay.get("notification_lines_after") == replay.get("notification_lines_before"), "the redelivery produced a second notification")
    return (f"{first} killed in flight, recovered and DONE; delivery admitted by process "
            f"{replay.get('originally_admitted_by')} redelivered to a restarted ingress with its receipt unchanged")


def scope(record: dict) -> str:
    isolation = record.get("isolation") or {}
    need(isolation.get("findings") == [], "isolation findings are present")
    need(isolation.get("repository_scope") == [record.get("repository")], "the installation reaches more than the sandbox repository")
    controls = phase(record, "ingress-restart").get("scope_controls") or []
    posted = [control for control in controls if "http_status" in control]
    need(len(posted) >= 3, "fewer than three ingress scope controls were applied")
    need(all(control["http_status"] == 401 and control["durable_receipt_created"] is False for control in posted),
         "an out-of-scope or unauthenticated delivery was admitted")
    resolution = [control for control in controls if control.get("control") == "foreign_project_address_resolution"]
    need(resolution and resolution[0].get("refused") is True, "a foreign Project identity resolved")
    return f"{len(posted)} out-of-scope deliveries refused without receipt; foreign Project address refused"


def one_writer_undisturbed(record: dict) -> str:
    before = (record.get("before") or {}).get("node_writer") or {}
    after = (record.get("after") or {}).get("node_writer") or {}
    need(before.get("runtime_pids"), "the Node writer was not observed before the run")
    need(before.get("runtime_pids") == after.get("runtime_pids"), "the Node writer process changed during the run")
    for key in ("bootstrap_ports_listening", "bootstrap_port_answers", "root_tunnel_config_mtime"):
        need(key in before and before.get(key) == after.get(key), f"Node bootstrap {key} changed or was not observed")
    need(record.get("repository") not in (None, "AlienLogicLab/alienintent"), "the proof targeted the Node writer's repository")
    return f"Node writer {before['runtime_pids']} unchanged; its ports and root tunnel configuration unchanged"


def labelled(record: dict) -> str:
    substitutions = record.get("substitutions")
    need(isinstance(substitutions, list) and substitutions, "substitutions are not declared")
    need(all(entry.get("claims_nothing_about") for entry in substitutions), "a substitution does not state what it cannot claim")
    controls = phase(record, "ingress-restart").get("scope_controls") or []
    need(all("LOCAL" in control.get("label", "LOCAL") for control in controls), "a local control is not labelled")
    return f"{len(substitutions)} substitution(s) labelled; local controls labelled LOCAL"


PREDICATES: tuple[tuple[str, str, Callable[[dict], str]], ...] = (
    ("E1-1", "identification and fixture pinned before any live call", pinned_before_live),
    ("E1-2", "no-Node instrument discriminates (intact/fault/restored)", instrument_discriminates),
    ("E1-3", "no Node process or dependency on the Python path", no_node),
    ("E1-4", "real ingress with durable receipt", real_ingress),
    ("E1-5", "effect dispatch", effect_dispatch),
    ("E1-6", "durable consumer outcome read back", durable_outcome_readback),
    ("E1-7", "restart with readback", restart),
    ("E1-8", "invalid scope holds", scope),
    ("E1-9", "one writer: Node bootstrap undisturbed", one_writer_undisturbed),
    ("E1-10", "local substitutions labelled", labelled),
)


def evaluate(record: dict) -> dict:
    results = []
    for identity, title, check in PREDICATES:
        try:
            results.append({"id": identity, "title": title, "outcome": "PASS", "basis": check(record)})
        except Hold as hold:
            results.append({"id": identity, "title": title, "outcome": "HOLD", "basis": str(hold)})
        except (KeyError, TypeError, AttributeError, IndexError) as error:
            results.append({"id": identity, "title": title, "outcome": "HOLD", "basis": f"evidence malformed: {type(error).__name__}: {error}"})
    return {
        "disposition": "PASS" if all(result["outcome"] == "PASS" for result in results) else "HOLD",
        "predicates": results,
        "rule": "PASS only when every predicate passes on retained evidence; a missing measurement is HOLD, never PASS",
    }


# --- intact / fault / restored ------------------------------------------------------------


def _set(path: list, value: object) -> Callable[[dict], int]:
    def apply(record: dict) -> int:
        cursor = record
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = value
        return 1
    return apply


def _phase_set(name: str, path: list, value: object) -> Callable[[dict], int]:
    def apply(record: dict) -> int:
        applied = 0
        for entry in record["phases"]:
            if entry.get("phase") == name:
                cursor = entry
                for key in path[:-1]:
                    cursor = cursor[key]
                cursor[path[-1]] = value
                applied += 1
        return applied
    return apply


def _first_project_not_done(record: dict) -> int:
    record["readback"]["project"][0]["status"] = "IMPLEMENT"
    return 1


def _unreceipted_delivery(record: dict) -> int:
    applied = 0
    for entry in record["readback"]["deliveries"]:
        if entry.get("status_code") == 202 and not entry.get("redelivery"):
            entry["durable_receipt"] = False
            applied += 1
            break
    return applied


def _unconfirm_dispatch(record: dict) -> int:
    applied = 0
    for effect in record["readback"]["store"]["effects"]:
        if effect["identity"].startswith("launch:") and effect.get("status") == "confirmed":
            effect["status"] = "unknown"
            applied += 1
    return applied


def _admit_foreign(record: dict) -> int:
    for entry in record["phases"]:
        if entry.get("phase") == "ingress-restart":
            entry["scope_controls"][-2]["http_status"] = 202
            return 1
    return 0


def _node_writer_changed(record: dict) -> int:
    record["after"]["node_writer"]["runtime_pids"] = [0]
    return 1


def _unlabelled(record: dict) -> int:
    record["substitutions"] = []
    return 1


CONTROLS: tuple[tuple[str, str, Callable[[dict], int]], ...] = (
    ("K1", "E1-1", _set(["pinned", "fixture_plan_committed_before_run"], False)),
    ("K2", "E1-2", _set(["instrument_self_test", "ok"], False)),
    ("K3", "E1-3", _set(["no_node", "node_observed"], True)),
    ("K4", "E1-4", _unreceipted_delivery),
    ("K5", "E1-5", _unconfirm_dispatch),
    ("K6", "E1-6", _first_project_not_done),
    ("K7", "E1-7", _phase_set("ingress-restart", ["replay", "receipt_unchanged"], False)),
    ("K8", "E1-8", _admit_foreign),
    ("K9", "E1-9", _node_writer_changed),
    ("K10", "E1-10", _unlabelled),
)


def controls(record: dict) -> dict:
    intact = evaluate(record)
    results = []
    for identity, predicate, fault in CONTROLS:
        faulted = copy.deepcopy(record)
        applications = fault(faulted)
        verdict = evaluate(faulted)
        held = sorted(result["id"] for result in verdict["predicates"] if result["outcome"] == "HOLD")
        restored = evaluate(copy.deepcopy(record))
        results.append({
            "control": identity, "predicate": predicate, "applications": applications,
            "fault_disposition": verdict["disposition"], "held_predicates": held,
            "restored_disposition": restored["disposition"],
            "discriminates": applications >= 1 and intact["disposition"] == "PASS" and verdict["disposition"] == "HOLD"
                             and predicate in held and restored["disposition"] == "PASS",
        })
    return {"intact_disposition": intact["disposition"], "controls": results,
            "ok": intact["disposition"] == "PASS" and all(result["discriminates"] for result in results)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="FX-E1 evaluator")
    parser.add_argument("record", type=Path)
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args(argv)
    record = json.loads(arguments.record.read_text(encoding="utf-8"))
    result = controls(record) if arguments.controls else evaluate(record)
    if arguments.json:
        print(json.dumps(result, indent=1, sort_keys=True))
    elif arguments.controls:
        for control in result["controls"]:
            print(f"{'ok ' if control['discriminates'] else 'BAD'} {control['control']} -> {control['predicate']}: "
                  f"fault {control['fault_disposition']} {control['held_predicates']}, restored {control['restored_disposition']}")
    else:
        for predicate in result["predicates"]:
            print(f"{predicate['outcome']:4} {predicate['id']} {predicate['title']}: {predicate['basis']}")
        print(result["disposition"])
    ok = result["ok"] if arguments.controls else result["disposition"] == "PASS"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
