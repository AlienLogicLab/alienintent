"""Tests for the Wave 2 SPECIFY checker.

Exit gate: every selected candidate is sufficiently specified for Design Contract work, and no
unresolved product intent is hidden in design.

Two Wave 1 lessons are enforced here. A requirement authored from an id that was never defined
must be flagged for ratification rather than slipped in as if it always existed (amendment
section 10: no silent new Product Requirements). And an acceptance criterion must be verifiable
-- PY-09B binding rule 6 demanded proof the platform's permission model cannot give, and SWF-34
was needed to undo it.
"""
import copy, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_wave2_specify import CHECKS, NAMED_CANDIDATES, SPEC_FIELDS, check_specify  # noqa: E402


def _req(**over):
    r = {"requirement_id": "SF-REQ-039", "selected": True, "definition_status": "DEFINED",
         "priority_or_wave_invented": False,
         "intent": "deterministic fake workers exercise the real lifecycle",
         "value": "factory proof without provider spend", "scope": "scripted worker adapter",
         "non_goals": "not a replacement for real provider runs",
         "dependencies": ["SF-REQ-016"],
         "acceptance_criteria": ["a scripted worker completes a BIU lifecycle with no credentials"],
         "authority_gaps": "none identified", "security_constraints": "no credentials in fixtures",
         "operational_constraints": "must run offline",
         "observability_evidence": "trajectory records emitted identically",
         "failure_modes": ["fake worker diverges from real adapter semantics"]}
    r.update(over)
    return r


def _doc(reqs=None, **over):
    reqs = reqs if reqs is not None else (
        [_req(requirement_id=c) for c in NAMED_CANDIDATES])
    d = {"candidates": reqs, "lane_semantics": {l: "defined" for l in
         ("CAPTURE", "SPECIFY", "DESIGN", "PLAN", "TASKS", "READY")},
         "pending_amendment_dependencies": []}
    d.update(over)
    return d


def test_a_clean_document_passes():
    ok, f = check_specify(_doc())
    assert ok, f


def test_a_selected_requirement_missing_a_spec_field_is_rejected():
    r = _req()
    del r["failure_modes"]
    ok, f = check_specify(_doc([r] + [_req(requirement_id=c) for c in NAMED_CANDIDATES[1:]]))
    assert not ok
    assert any("spec_fields_complete" in x for x in f)


def test_a_rejected_candidate_without_a_reason_is_rejected():
    reqs = [_req(requirement_id=c) for c in NAMED_CANDIDATES]
    reqs[0] = {"requirement_id": NAMED_CANDIDATES[0], "selected": False}
    ok, f = check_specify(_doc(reqs))
    assert not ok
    assert any("rejection_needs_reason" in x for x in f)


def test_a_rejected_candidate_with_a_reason_passes():
    reqs = [_req(requirement_id=c) for c in NAMED_CANDIDATES]
    reqs[0] = {"requirement_id": NAMED_CANDIDATES[0], "selected": False,
               "rejection_reason": "superseded by the Phase 5 design; no separate capability needed"}
    ok, f = check_specify(_doc(reqs))
    assert ok, f


def test_an_authored_requirement_without_a_ratification_flag_is_rejected():
    """No silent new Product Requirements."""
    reqs = [_req(requirement_id=c) for c in NAMED_CANDIDATES]
    reqs[0]["definition_status"] = "AUTHORED_IN_THIS_PHASE"
    ok, f = check_specify(_doc(reqs))
    assert not ok
    assert any("authored_needs_ratification" in x for x in f)


def test_an_authored_requirement_flagged_for_ratification_passes():
    reqs = [_req(requirement_id=c) for c in NAMED_CANDIDATES]
    reqs[0].update(definition_status="AUTHORED_IN_THIS_PHASE",
                   founder_ratification_required=True)
    ok, f = check_specify(_doc(reqs))
    assert ok, f


def test_an_unevaluated_named_candidate_is_rejected():
    ok, f = check_specify(_doc([_req(requirement_id=c) for c in NAMED_CANDIDATES[1:]]))
    assert not ok
    assert any("all_named_candidates_evaluated" in x for x in f)


def test_an_empty_acceptance_criterion_is_rejected():
    reqs = [_req(requirement_id=c) for c in NAMED_CANDIDATES]
    reqs[0]["acceptance_criteria"] = []
    ok, f = check_specify(_doc(reqs))
    assert not ok
    assert any("verifiable_acceptance" in x for x in f)


def test_a_self_referential_acceptance_criterion_is_rejected():
    """"The requirement is met" is not a criterion."""
    reqs = [_req(requirement_id=c) for c in NAMED_CANDIDATES]
    reqs[0]["acceptance_criteria"] = ["the requirement is satisfied"]
    ok, f = check_specify(_doc(reqs))
    assert not ok
    assert any("verifiable_acceptance" in x for x in f)


def test_inventing_priority_or_wave_is_rejected():
    reqs = [_req(requirement_id=c) for c in NAMED_CANDIDATES]
    reqs[0]["priority_or_wave_invented"] = True
    ok, f = check_specify(_doc(reqs))
    assert not ok
    assert any("never_invent_priority_or_wave" in x for x in f)


def test_a_lane_without_operational_semantics_is_rejected():
    """A lane that exists only as a name looks like coverage."""
    d = _doc()
    d["lane_semantics"]["DESIGN"] = "none"
    ok, f = check_specify(d)
    assert not ok
    assert any("lanes_have_semantics" in x for x in f)


NEGATIVE_CONTROLS = {
    "spec_fields_complete": lambda d: d["candidates"][0].pop("failure_modes"),
    "rejection_needs_reason": lambda d: d["candidates"][0].update(selected=False, rejection_reason="none"),
    "authored_needs_ratification": lambda d: d["candidates"][0].__setitem__(
        "definition_status", "AUTHORED_IN_THIS_PHASE"),
    "all_named_candidates_evaluated": lambda d: d["candidates"].pop(0),
    "verifiable_acceptance": lambda d: d["candidates"][0].__setitem__("acceptance_criteria", []),
    "never_invent_priority_or_wave": lambda d: d["candidates"][0].__setitem__(
        "priority_or_wave_invented", True),
    "lanes_have_semantics": lambda d: d["lane_semantics"].__setitem__("DESIGN", "none"),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        d = copy.deepcopy(_doc())
        mutate(d)
        ok, f = check_specify(d)
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)


# --- DV-9 (round 2): the Markdown rendering must agree with the JSON ------------------------
# Found live: after AC-05 was rescoped in the JSON, the Markdown still carried the superseded
# criterion. Vocabulary checking cannot see a semantic contradiction; a render-equivalence rule
# can, because the rendering of an acceptance criterion and an inventory row is deterministic.

from check_wave2_specify import (RENDER_CHECKS, check_render, render_acceptance_line,  # noqa: E402
                                 render_inventory_row)

REAL_STALE_AC05_LINE = ("- **SF-REQ-011-AC-05**: Through RequirementSource, translate representative Source Records "
    "for every named source kind to provider-neutral inputs while retaining all seven Requirement Provenance "
    "fields. Missing or ambiguous provenance or unsupported versions yields a typed refusal for affected input; "
    "never fabricate authority from vendor type. Same-vendor RequirementSource and WorkManagement adapters remain "
    "distinct. Verification: Versioned adapter conformance fixtures for all listed kinds, asserting exact retained "
    "provenance and typed failures. Fixtures prove the boundary contract, not live vendor integrations; delete "
    "each mandatory provenance field independently as negative controls.")


def _rendered(doc):
    lines = []
    for c in doc["candidates"]:
        lines.append(render_inventory_row(c))
        for ac in c.get("acceptance_criteria", []):
            lines.append(render_acceptance_line(ac))
    return "\n".join(lines) + "\n"


def test_a_faithful_rendering_passes():
    """A rows-plus-criteria rendering without candidate sections is no longer faithful (DV-13);
    the faithful case is test_a_fully_faithful_rendering_passes below. This keeps the
    row/criteria helper honest: it must fail for the missing sections, not pass vacuously."""
    doc = _doc()
    ok, f = check_render(doc, _rendered(doc))
    assert not ok and any("no section" in x for x in f)


def test_the_real_stale_ac05_rendering_is_rejected():
    doc = _doc()
    doc["candidates"][0]["acceptance_criteria"] = [{"id": "SF-REQ-011-AC-05", "criterion": "two heterogeneous kinds",
                                                    "verification": "two kinds"}]
    md = _rendered(doc).replace(render_acceptance_line(doc["candidates"][0]["acceptance_criteria"][0]),
                                REAL_STALE_AC05_LINE)
    ok, f = check_render(doc, md)
    assert not ok and any("markdown_render_equivalent" in x for x in f)


def test_a_stale_inventory_row_is_rejected():
    doc = _doc()
    md = _rendered(doc).replace(render_inventory_row(doc["candidates"][0]), "| SF-REQ-011 | Yes | Old title: old reason |")
    ok, f = check_render(doc, md)
    assert not ok and any("markdown_render_equivalent" in x for x in f)


def test_render_checks_are_named():
    assert RENDER_CHECKS == ("markdown_render_equivalent",)


# --- DV-13 (round 3): every rendered field, both directions -------------------------------
# Found live: after the JSON dedup, the Markdown still rendered the old ownership paragraph as
# SF-REQ-015's scope, dependency and authority gap, and the render rule (rows + acceptance only)
# passed it. The rule now covers every list-valued specification field within the candidate's
# own section, and an acceptance ID present only in the Markdown is rejected.

from check_wave2_specify import render_candidate_section  # noqa: E402

REAL_STALE_AUTHORITY_GAP_LINE = ("- Agent Ready product owns assessment semantics, implementation, public schema, CLI and local "
    "MCP; SF-REQ-015 owns integration in Requirements / Planning; SF-REQ-029 owns immutable retained-assessment "
    "serialization. A1 settles G1/G2 ownership; capability availability, producer identity, supported contract and "
    "independent design verification remain prerequisites.")


def _full_doc():
    doc = _doc()
    for c in doc["candidates"]:
        c["title"] = "T"; c["scope"] = ["s1", "s2"]; c["non_goals"] = ["n1"]; c["dependencies"] = ["d1"]
        c["authority_gaps"] = ["none settled-pending"]; c["security_constraints"] = ["sec"]
        c["operational_constraints"] = ["op"]; c["observability_evidence"] = ["obs"]; c["failure_modes"] = ["f1"]
        c["acceptance_criteria"] = [{"id": f"{c['requirement_id']}-AC-01", "criterion": "crit", "verification": "ver"}]
    return doc


def _full_md(doc):
    return "# x\n\n" + "\n".join(render_inventory_row(c) for c in doc["candidates"]) + "\n\n" + \
        "\n".join(render_candidate_section(c) for c in doc["candidates"]) + "\n## Pending amendments\n"


def test_a_fully_faithful_rendering_passes():
    doc = _full_doc()
    ok, f = check_render(doc, _full_md(doc))
    assert ok, f


def test_a_stale_authority_gap_line_in_the_candidates_section_is_rejected():
    doc = _full_doc()
    md = _full_md(doc).replace("- none settled-pending", REAL_STALE_AUTHORITY_GAP_LINE, 1)
    ok, f = check_render(doc, md)
    assert not ok and any("markdown_render_equivalent" in x and "authority_gaps" in x for x in f)


def test_an_acceptance_id_present_only_in_the_markdown_is_rejected():
    doc = _full_doc()
    rid = doc["candidates"][0]["requirement_id"]
    md = _full_md(doc).replace(f"- **{rid}-AC-01**", f"- **{rid}-AC-99**: ghost Verification: none\n- **{rid}-AC-01**", 1)
    ok, f = check_render(doc, md)
    assert not ok and any("markdown_render_equivalent" in x and "AC-99" in x for x in f)
