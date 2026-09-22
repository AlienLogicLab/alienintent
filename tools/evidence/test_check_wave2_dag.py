"""Tests for the Wave 2 dependency DAG checker.

Three properties are mechanically decidable and all three failed in Wave 1.

Acyclicity. A dependency cycle is not a planning opinion.

Single ownership. "Every planned capability has one owner and dependency path" is the phase exit
gate, and PY-10's live transport was unowned until Agent-Ready found it.

The capstone rule. "A capstone must integrate previously proven capabilities. It must not
secretly become first owner of infrastructure required to perform its own proof." That is
PY-10 -> PY-09B stated as a rule: PY-10 was the capstone and turned out to be first owner of the
live transport its own proof needed, which cost a SPLIT_RECOMMENDED and a new BIU.
"""
import copy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_wave2_dag import CHECKS, check_dag  # noqa: E402


def _dag(nodes=None, capabilities=None):
    nodes = nodes if nodes is not None else [
        {"id": "W2-01", "depends_on": [], "is_capstone": False,
         "owns_capabilities": ["requirement_ir"], "proof_requires_capabilities": []},
        {"id": "W2-02", "depends_on": ["W2-01"], "is_capstone": False,
         "owns_capabilities": ["biu_compiler"], "proof_requires_capabilities": ["requirement_ir"]},
        {"id": "W2-03", "depends_on": ["W2-01", "W2-02"], "is_capstone": True,
         "owns_capabilities": [], "proof_requires_capabilities": ["requirement_ir", "biu_compiler"]},
    ]
    caps = capabilities if capabilities is not None else ["requirement_ir", "biu_compiler"]
    return {"nodes": nodes, "planned_capabilities": caps}


def test_a_clean_dag_passes():
    ok, f = check_dag(_dag())
    assert ok, f


def test_a_cycle_is_rejected():
    n = _dag()["nodes"]
    n[0]["depends_on"] = ["W2-03"]
    ok, f = check_dag(_dag(n))
    assert not ok
    assert any("acyclic" in x for x in f)


def test_a_self_dependency_is_rejected():
    n = _dag()["nodes"]
    n[1]["depends_on"] = ["W2-02"]
    ok, f = check_dag(_dag(n))
    assert not ok
    assert any("acyclic" in x for x in f)


def test_a_dependency_on_an_unknown_node_is_rejected():
    n = _dag()["nodes"]
    n[1]["depends_on"] = ["W2-99"]
    ok, f = check_dag(_dag(n))
    assert not ok
    assert any("dependencies_resolve" in x for x in f)


def test_an_unowned_planned_capability_is_rejected():
    ok, f = check_dag(_dag(capabilities=["requirement_ir", "biu_compiler", "live_transport"]))
    assert not ok
    assert any("one_owner_per_capability" in x for x in f)


def test_two_owners_for_one_capability_is_rejected():
    n = _dag()["nodes"]
    n[2]["owns_capabilities"] = ["biu_compiler"]
    ok, f = check_dag(_dag(n))
    assert not ok
    assert any("one_owner_per_capability" in x for x in f)


def test_a_capstone_that_first_owns_infrastructure_its_proof_needs_is_rejected():
    """PY-10 -> PY-09B, stated as a rule."""
    n = _dag()["nodes"]
    n[2]["owns_capabilities"] = ["live_transport"]
    n[2]["proof_requires_capabilities"] = ["requirement_ir", "live_transport"]
    ok, f = check_dag(_dag(n, capabilities=["requirement_ir", "biu_compiler", "live_transport"]))
    assert not ok
    assert any("capstone_integrates" in x for x in f)


def test_a_capstone_may_own_a_capability_its_proof_does_not_need():
    n = _dag()["nodes"]
    n[2]["owns_capabilities"] = ["release_report"]
    ok, f = check_dag(_dag(n, capabilities=["requirement_ir", "biu_compiler", "release_report"]))
    assert ok, f


def test_a_node_whose_proof_needs_a_capability_it_does_not_depend_on_is_rejected():
    """A proof obligation with no dependency path is how unowned substrate hides."""
    n = _dag()["nodes"]
    n[1]["depends_on"] = []
    ok, f = check_dag(_dag(n))
    assert not ok
    assert any("proof_inputs_reachable" in x for x in f)


NEGATIVE_CONTROLS = {
    "root_register_consistent": lambda d: d.update(authority_policy={"wave2a_completion_blocker": "GAP-NOBODY-CARRIES"}),
    "acyclic": lambda d: d["nodes"][0].__setitem__("depends_on", ["W2-03"]),
    "dependencies_resolve": lambda d: d["nodes"][1].__setitem__("depends_on", ["W2-99"]),
    "one_owner_per_capability": lambda d: d["planned_capabilities"].append("live_transport"),
    "capstone_integrates": lambda d: (
        d["nodes"][2].__setitem__("owns_capabilities", ["biu_compiler"]),
        d["nodes"][2].__setitem__("proof_requires_capabilities", ["biu_compiler"])),
    "proof_inputs_reachable": lambda d: d["nodes"][1].__setitem__("depends_on", []),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        d = copy.deepcopy(_dag())
        mutate(d)
        ok, f = check_dag(d)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)


# --- root register consistency (DV-1, 2026-09-22) -----------------------------------------
# Found live: the DAG's own status register (authority_policy.wave2a_completion_blocker,
# authority_gaps[*].status, statistics.*) said a settled gap still blocked Wave 2A and reported
# counts that no longer matched the nodes, while every node said otherwise. A checker that only
# reads nodes stays green while the artifact contradicts itself.

REPO = Path(__file__).resolve().parents[2]


def _registered():
    d = _dag()
    for n in d["nodes"]:
        n["completion_status"] = "PROCEEDS_REGARDLESS"
        n["authority_gap_refs"] = []
    d["nodes"][2]["completion_status"] = "GAP_BLOCKED"
    d["nodes"][2]["authority_gap_refs"] = ["GAP-A"]
    d["authority_gaps"] = [{"id": "GAP-A", "status": "RETURN_TO_SPECIFY"},
                           {"id": "GAP-B", "status": "RETURN_TO_SPECIFY",
                            "resolution_2026_09_22": {"status": "SETTLED_BY_AMENDMENT"}}]
    d["authority_policy"] = {"wave2a_completion_blocker": "GAP-A", "wave2a_completion_node": "W2-03"}
    d["statistics"] = {"nodes": 3, "gap_blocked_nodes": 1, "proceeds_regardless": 2,
                       "separate_authority_only_nodes": 0}
    return d


def test_a_consistent_root_register_passes():
    ok, f = check_dag(_registered())
    assert ok, f


def test_statistics_that_do_not_match_the_nodes_are_rejected():
    d = _registered(); d["statistics"]["proceeds_regardless"] = 1
    ok, f = check_dag(d)
    assert not ok and any("root_register_consistent" in x for x in f)


def test_a_completion_blocker_no_node_references_is_rejected():
    d = _registered(); d["authority_policy"]["wave2a_completion_blocker"] = "GAP-B"
    ok, f = check_dag(d)
    assert not ok and any("root_register_consistent" in x for x in f)


def test_an_open_gap_no_node_references_is_rejected():
    """A gap the register calls open but no node carries is either stale or unpropagated."""
    d = _registered(); d["authority_gaps"][1].pop("resolution_2026_09_22")
    ok, f = check_dag(d)
    assert not ok and any("root_register_consistent" in x for x in f)


def test_the_real_dag_root_register_is_consistent():
    """Proven red against the live artifact before the DV-1 repair (stale blocker, stale
    counts, R1-GAP-013-ALLOCATION open in the register and referenced by no node)."""
    import json
    ok, f = check_dag(json.loads((REPO / "docs/evidence/wave2-dependency-dag.json").read_text()))
    assert ok, f


# --- DV-12 (round 2): the register rule must not accept look-alike settlements ---------------

def test_a_resolution_record_without_a_terminal_status_does_not_settle_a_gap():
    d = _registered(); d["authority_gaps"][1]["resolution_2026_09_22"] = {"status": "RETURN_TO_SPECIFY"}
    ok, f = check_dag(d)
    assert not ok and any("root_register_consistent" in x for x in f)


def test_a_settled_gap_still_carried_by_a_node_is_rejected():
    d = _registered(); d["nodes"][2]["authority_gap_refs"].append("GAP-B")
    ok, f = check_dag(d)
    assert not ok and any("root_register_consistent" in x for x in f)


def test_the_completion_blocker_must_be_carried_by_the_named_completion_node():
    d = _registered()
    d["authority_policy"]["wave2a_completion_node"] = "W2-03"
    d["nodes"][1]["authority_gap_refs"] = ["GAP-C"]; d["nodes"][1]["completion_status"] = "GAP_BLOCKED"
    d["authority_gaps"].append({"id": "GAP-C", "status": "RETURN_TO_SPECIFY"})
    d["statistics"].update(gap_blocked_nodes=2, proceeds_regardless=1)
    d["authority_policy"]["wave2a_completion_blocker"] = "GAP-C"   # carried by W2-02, not by W2-03
    ok, f = check_dag(d)
    assert not ok and any("root_register_consistent" in x for x in f)


# --- DV-14 (round 3): the blocker rule must not degrade when the completion node is missing ----

def test_a_blocker_without_a_named_completion_node_is_rejected():
    d = _registered(); d["authority_policy"].pop("wave2a_completion_node", None)
    ok, f = check_dag(d)
    assert not ok and any("wave2a_completion_node" in x for x in f)


def test_a_completion_node_that_does_not_exist_is_rejected():
    d = _registered(); d["authority_policy"]["wave2a_completion_node"] = "W2-99"
    ok, f = check_dag(d)
    assert not ok and any("wave2a_completion_node" in x for x in f)
