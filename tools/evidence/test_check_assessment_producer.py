"""Tests for the readiness-assessment producer-identity checker.

Wave 1's PY-01..PY-10 readiness assessments were not produced by the Agent Ready product. A
coordinator ran raw Codex (later Claude) prompts shaped to Agent Ready's contract, and the
resulting artifacts carried a `provider_evidence` block that *copied Agent Ready's host-measured
vocabulary* (`compatibility`, `capability_probe`) as asserted text. Nothing checked who produced
them; the release gate read only `disposition`.

The invariant this enforces, from the Founder (2026-09-22):

    A compatible output shape is not evidence that the authoritative capability produced the
    result.

So every retained assessment must be covered by a provenance manifest that declares its
producer, and the declaration must be consistent with what a native Agent Ready result actually
looks like: an MCP envelope, or a CLI object with exactly the twelve contract fields plus, at
most, Agent Ready's own four-key `provider_evidence`, and a disposition from
`READY / CLARIFY / SPLIT / HOLD`. Anything carrying an `invocation`, `adapter`, `model`,
`provider_failover` or `permission_denials`, or provider evidence Agent Ready does not emit, or a
bootstrap-assessor disposition, was not produced by Agent Ready — whatever it says about itself.

ARP-01 made the provider evidence rule provider-generic: every provider Agent Ready supports is
accepted with its own version format, and nothing else is. Each rejection is shown killable by a
deliberately permissive variant of the rule.

Proven red against the real shapes: a real surrogate (PY-02) and a real native (PG-01) artifact.
"""
import copy
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "orchestration"))

import check_assessment_producer as cap  # noqa: E402
from check_assessment_producer import (AGENT_READY_COMPATIBILITY_PAIRS,  # noqa: E402
                                       AGENT_READY_PROVIDER_VERSION_FORMATS, CHECKS,
                                       NATIVE_PROVIDER_EVIDENCE_KEYS, check_manifest,
                                       looks_native_agent_ready, main, native_provenance_only)
from readiness_assessment import PROVIDERS  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
REAL_SURROGATE = json.loads((REPO / "docs/work-units/python/PY-02.assessment.json").read_text())
REAL_NATIVE = json.loads(
    (REPO / "docs/work-units/pre-python-gate/assessments/PG-01.assessment.json").read_text())

_CONTRACT = {"disposition": "READY", "governing_intent": "x", "summary": "x",
             "owner_clarifications": [], "implementation_unknowns": [],
             "independent_decision_centers": [], "semantic_split_recommendation": [],
             "verification_assessment": "x", "expected_rework_locality": "HIGH",
             "material_risks": [], "next_action": "x", "rationale": "x"}


# --- shape recognition, proven against real artifacts -----------------------------------


def test_the_real_pre_python_gate_artifact_looks_native():
    assert looks_native_agent_ready(REAL_NATIVE) is True


def test_the_real_wave1_surrogate_artifact_does_not_look_native():
    """PY-02 asserts compatibility=COMPATIBLE_UNVERIFIED and capability_probe=PASSED, the
    words Agent Ready generates host-side. It also carries `invocation`. Shape is not proof."""
    assert looks_native_agent_ready(REAL_SURROGATE) is False


def test_a_bare_cli_object_with_exactly_the_contract_fields_looks_native():
    assert looks_native_agent_ready(dict(_CONTRACT)) is True


def test_agent_readys_own_codex_provider_evidence_is_accepted():
    a = dict(_CONTRACT)
    a["provider_evidence"] = {"provider": "codex", "version": "codex-cli 0.153.4",
                              "compatibility": "SUPPORTED", "capability_probe": "REVIEWED_VERSION"}
    assert looks_native_agent_ready(a) is True


def test_a_bootstrap_assessor_disposition_is_not_native():
    a = dict(_CONTRACT)
    a["disposition"] = "BLOCKED"
    assert looks_native_agent_ready(a) is False


# --- provider-generic provider evidence (ARP-01) -----------------------------------------


def _pe(provider, version, compatibility="SUPPORTED", capability_probe="REVIEWED_VERSION"):
    return {"provider": provider, "version": version, "compatibility": compatibility,
            "capability_probe": capability_probe}


def _full(pe):
    a = dict(_CONTRACT)
    a["provider_evidence"] = pe
    return a


def _partial(pe, disposition="READY"):
    return {"disposition": disposition, "summary": "x", "record_kind": "Receipt excerpt",
            "provider_evidence": pe}


VALID_PROVIDER_EVIDENCE = {
    "codex_supported_reviewed": _pe("codex", "codex-cli 0.153.4"),
    "codex_compatible_unverified_passed": _pe("codex", "codex-cli 0.155.1",
                                              "COMPATIBLE_UNVERIFIED", "PASSED"),
    "codex_suffixed_version": _pe("codex", "codex-cli 0.156.0-alpha.2",
                                  "COMPATIBLE_UNVERIFIED", "PASSED"),
    "claude_supported_reviewed": _pe("claude", "2.1.258 (Claude Code)"),
    "claude_compatible_unverified_passed": _pe("claude", "2.1.281 (Claude Code)",
                                               "COMPATIBLE_UNVERIFIED", "PASSED"),
    "claude_suffixed_version": _pe("claude", "2.2.0+build.7 (Claude Code)"),
}

_missing_key = _pe("claude", "2.1.281 (Claude Code)")
del _missing_key["capability_probe"]

# Each rejection names the permissive variant (below) that would wrongly accept it, so every
# rejection test is shown able to fail. A check that cannot fail is not evidence.
INVALID_PROVIDER_EVIDENCE = {
    "unknown_provider": (_pe("gemini", "codex-cli 0.153.4"), "provider_not_checked"),
    "non_string_provider": (_pe(["claude"], "2.1.281 (Claude Code)"), "provider_not_checked"),
    "codex_with_claude_version_format": (_pe("codex", "2.1.281 (Claude Code)"),
                                         "provider_not_checked"),
    "claude_with_codex_version_format": (_pe("claude", "codex-cli 0.153.4"),
                                         "provider_not_checked"),
    "claude_version_x": (_pe("claude", "x"), "version_not_checked"),
    "codex_version_trailing_text": (_pe("codex", "codex-cli 0.153.4 extra"),
                                    "version_not_checked"),
    "non_string_version": (_pe("claude", ["2.1.281 (Claude Code)"]), "version_not_checked"),
    "supported_with_passed": (_pe("claude", "2.1.281 (Claude Code)", "SUPPORTED", "PASSED"),
                              "pair_not_checked"),
    "unverified_with_reviewed_version": (_pe("codex", "codex-cli 0.153.4",
                                             "COMPATIBLE_UNVERIFIED", "REVIEWED_VERSION"),
                                         "pair_not_checked"),
    "incompatible_failed": (_pe("codex", "codex-cli 0.153.4", "INCOMPATIBLE", "FAILED"),
                            "pair_not_checked"),
    # Found by the ARP-01 verifier (F1): these crashed both readers instead of rejecting.
    "compatibility_list": (_pe("claude", "2.1.281 (Claude Code)", [], "PASSED"),
                           "pair_not_checked"),
    "compatibility_dict": (_pe("codex", "codex-cli 0.155.1", {}, "PASSED"), "pair_not_checked"),
    "capability_probe_list": (_pe("codex", "codex-cli 0.153.4", "SUPPORTED", []),
                              "pair_not_checked"),
    "capability_probe_dict": (_pe("claude", "2.1.258 (Claude Code)", "SUPPORTED", {}),
                              "pair_not_checked"),
    "missing_key": (_missing_key, "keys_not_exact"),
    "extra_key": (dict(_pe("claude", "2.1.281 (Claude Code)"), model="claude-opus-5"),
                  "keys_not_exact"),
    "non_dict_list": (["claude", "2.1.281 (Claude Code)", "SUPPORTED", "REVIEWED_VERSION"],
                      "non_dict_accepted"),
    "non_dict_string": ("claude 2.1.281 (Claude Code)", "non_dict_accepted"),
}


def _real(pe):
    return cap.is_native_provider_evidence(pe)


def _provider_not_checked(pe):
    """Any version format, for any provider name."""
    if not isinstance(pe, dict) or set(pe) != NATIVE_PROVIDER_EVIDENCE_KEYS:
        return False
    v = pe.get("version")
    return isinstance(v, str) and any(f.fullmatch(v) for f in
                                      AGENT_READY_PROVIDER_VERSION_FORMATS.values()) \
        and (pe["compatibility"], pe["capability_probe"]) in AGENT_READY_COMPATIBILITY_PAIRS


def _version_not_checked(pe):
    if not isinstance(pe, dict) or set(pe) != NATIVE_PROVIDER_EVIDENCE_KEYS:
        return False
    return pe["provider"] in AGENT_READY_PROVIDER_VERSION_FORMATS \
        and (pe["compatibility"], pe["capability_probe"]) in AGENT_READY_COMPATIBILITY_PAIRS


def _pair_not_checked(pe):
    if not isinstance(pe, dict) or set(pe) != NATIVE_PROVIDER_EVIDENCE_KEYS:
        return False
    f = AGENT_READY_PROVIDER_VERSION_FORMATS.get(pe["provider"])
    return f is not None and isinstance(pe["version"], str) and bool(f.fullmatch(pe["version"]))


def _keys_not_exact(pe):
    """Judges only the four keys it knows, ignoring extra and treating absent as passing."""
    if not isinstance(pe, dict):
        return False
    f = AGENT_READY_PROVIDER_VERSION_FORMATS.get(pe.get("provider"))
    v = pe.get("version")
    if f is None or not isinstance(v, str) or not f.fullmatch(v):
        return False
    c, p = pe.get("compatibility"), pe.get("capability_probe")
    return c is None or p is None or (c, p) in AGENT_READY_COMPATIBILITY_PAIRS


def _non_dict_accepted(pe):
    return not isinstance(pe, dict) or _real(pe)


PERMISSIVE_VARIANTS = {"provider_not_checked": _provider_not_checked,
                       "version_not_checked": _version_not_checked,
                       "pair_not_checked": _pair_not_checked,
                       "keys_not_exact": _keys_not_exact,
                       "non_dict_accepted": _non_dict_accepted}

def _pair_type_not_checked(pe):
    """The first ARP-01 candidate (04b082c): pair membership on unchecked JSON values."""
    if not isinstance(pe, dict) or set(pe) != NATIVE_PROVIDER_EVIDENCE_KEYS:
        return False
    f = AGENT_READY_PROVIDER_VERSION_FORMATS.get(pe["provider"]) \
        if isinstance(pe["provider"], str) else None
    if f is None or not isinstance(pe["version"], str) or not f.fullmatch(pe["version"]):
        return False
    return (pe["compatibility"], pe["capability_probe"]) in AGENT_READY_COMPATIBILITY_PAIRS


UNHASHABLE_PAIR_CASES = ("compatibility_list", "compatibility_dict", "capability_probe_list",
                         "capability_probe_dict")

READERS = {"looks_native_agent_ready": lambda pe: looks_native_agent_ready(_full(pe)),
           "native_provenance_only": lambda pe: native_provenance_only(_partial(pe))}


def test_the_declared_providers_agree_with_the_readiness_adapter():
    """One declared source: the reader's providers are exactly the ones the adapter runs."""
    assert set(AGENT_READY_PROVIDER_VERSION_FORMATS) == set(PROVIDERS)
    assert all(isinstance(f, re.Pattern) for f in AGENT_READY_PROVIDER_VERSION_FORMATS.values())


def test_the_compatibility_pairs_are_exactly_agent_readys_two():
    assert AGENT_READY_COMPATIBILITY_PAIRS == {("SUPPORTED", "REVIEWED_VERSION"),
                                               ("COMPATIBLE_UNVERIFIED", "PASSED")}


@pytest.mark.parametrize("reader", sorted(READERS))
@pytest.mark.parametrize("case", sorted(VALID_PROVIDER_EVIDENCE))
def test_genuine_provider_evidence_is_native_for_every_supported_provider(reader, case):
    assert READERS[reader](copy.deepcopy(VALID_PROVIDER_EVIDENCE[case])) is True


def test_every_supported_provider_has_an_accepted_case_for_both_pairs():
    seen = {(pe["provider"], pe["compatibility"], pe["capability_probe"])
            for pe in VALID_PROVIDER_EVIDENCE.values()}
    for provider in AGENT_READY_PROVIDER_VERSION_FORMATS:
        for pair in AGENT_READY_COMPATIBILITY_PAIRS:
            assert (provider, *pair) in seen


@pytest.mark.parametrize("reader", sorted(READERS))
@pytest.mark.parametrize("case", sorted(INVALID_PROVIDER_EVIDENCE))
def test_malformed_or_unknown_provider_evidence_is_not_native(reader, case):
    pe, _variant = INVALID_PROVIDER_EVIDENCE[case]
    assert READERS[reader](copy.deepcopy(pe)) is False


@pytest.mark.parametrize("reader", sorted(READERS))
@pytest.mark.parametrize("case", sorted(INVALID_PROVIDER_EVIDENCE))
def test_each_rejection_fails_against_a_permissive_variant(reader, case, monkeypatch):
    """The rejection above is discriminating: under the named permissive variant the same
    reader accepts the same evidence, so the rejection test would fail."""
    pe, variant = INVALID_PROVIDER_EVIDENCE[case]
    monkeypatch.setattr(cap, "is_native_provider_evidence", PERMISSIVE_VARIANTS[variant])
    assert READERS[reader](copy.deepcopy(pe)) is True


@pytest.mark.parametrize("reader", sorted(READERS))
@pytest.mark.parametrize("case", UNHASHABLE_PAIR_CASES)
def test_unhashable_pair_values_crash_the_unguarded_rule(reader, case, monkeypatch):
    """The rejection of a list/object compatibility or probe is also shown failing against the
    rule it repairs: unguarded, the reader raises instead of returning False."""
    monkeypatch.setattr(cap, "is_native_provider_evidence", _pair_type_not_checked)
    with pytest.raises(TypeError):
        READERS[reader](copy.deepcopy(INVALID_PROVIDER_EVIDENCE[case][0]))


@pytest.mark.parametrize("inner", [None, [], "READY", ["disposition", "READY"]])
def test_a_non_object_structured_content_is_rejected_not_raised(inner):
    envelope = {"content": [], "structuredContent": inner, "isError": False}
    assert looks_native_agent_ready(envelope) is False
    assert native_provenance_only(envelope) is False


@pytest.mark.parametrize("case", sorted(VALID_PROVIDER_EVIDENCE))
def test_valid_evidence_with_runner_asserted_fields_is_still_not_native(case):
    pe = VALID_PROVIDER_EVIDENCE[case]
    for field in ("invocation", "adapter", "model", "provider_failover", "permission_denials"):
        full = _full(copy.deepcopy(pe))
        full[field] = "asserted"
        assert looks_native_agent_ready(full) is False
        part = _partial(copy.deepcopy(pe))
        part[field] = "asserted"
        assert native_provenance_only(part) is False


@pytest.mark.parametrize("case", sorted(VALID_PROVIDER_EVIDENCE))
def test_valid_evidence_with_a_bootstrap_assessor_disposition_is_still_not_native(case):
    pe = VALID_PROVIDER_EVIDENCE[case]
    for disposition in ("BLOCKED", "NEEDS_CLARIFICATION"):
        full = _full(copy.deepcopy(pe))
        full["disposition"] = disposition
        assert looks_native_agent_ready(full) is False
        assert native_provenance_only(_partial(copy.deepcopy(pe), disposition)) is False


def test_a_partial_record_still_requires_provider_evidence():
    part = _partial(None)
    del part["provider_evidence"]
    assert native_provenance_only(part) is False


def test_a_full_record_without_provider_evidence_is_unchanged():
    assert looks_native_agent_ready(dict(_CONTRACT)) is True


RETAINED_WAVE1_SURROGATES = ("docs/work-units/python/PY-09B.assessment.json",
                             "docs/work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json",
                             "docs/work-units/python/PY-10.assessment.json")


@pytest.mark.parametrize("path", RETAINED_WAVE1_SURROGATES)
def test_the_retained_claude_surrogates_are_still_not_native(path):
    """Their 16- or 17-key claude provider_evidence copies Agent Ready's words; it is not
    Agent Ready's evidence, and a supported claude provider does not change that."""
    artifact = json.loads((REPO / path).read_text())
    assert artifact["provider_evidence"]["provider"] == "claude"
    assert set(artifact["provider_evidence"]) > NATIVE_PROVIDER_EVIDENCE_KEYS
    assert looks_native_agent_ready(artifact) is False
    assert native_provenance_only(artifact) is False


def test_the_committed_provenance_manifest_passes_unchanged(monkeypatch, capsys):
    monkeypatch.chdir(REPO)
    assert main(["docs/evidence/wave1-readiness-assessment-provenance.json"]) == 0
    assert "result    : PASS" in capsys.readouterr().out


# --- manifest checks ---------------------------------------------------------------------


def _manifest(entries):
    return {"entries": entries}


def _entry(**over):
    e = {"path": "docs/work-units/python/PY-02.assessment.json", "producer": "surrogate",
         "engine": "codex exec (bootstrap assessor)", "native_agent_ready": False}
    e.update(over)
    return e


def test_a_clean_manifest_passes():
    ok, f = check_manifest(_manifest([_entry(artifact=REAL_SURROGATE),
                                      _entry(path="pg", producer="agent-ready-mcp",
                                             engine="agent-ready MCP assess_work_unit",
                                             native_agent_ready=True, artifact=REAL_NATIVE)]))
    assert ok, f


def test_a_surrogate_declared_native_is_rejected():
    """The exact misrepresentation this checker exists to refuse."""
    ok, f = check_manifest(_manifest([_entry(producer="agent-ready-cli", native_agent_ready=True,
                                             artifact=REAL_SURROGATE)]))
    assert not ok
    assert any("declared_native_must_look_native" in x for x in f)


def test_a_native_declared_surrogate_is_flagged():
    """Mislabelling in the other direction hides a real Agent Ready execution."""
    ok, f = check_manifest(_manifest([_entry(path="pg", producer="surrogate",
                                             native_agent_ready=False, artifact=REAL_NATIVE)]))
    assert not ok
    assert any("declared_surrogate_must_not_look_native" in x for x in f)


def test_any_agent_ready_producer_label_is_held_to_native_shape():
    """Found live: a generator labelled two artifacts "agent-ready (…)" with native_agent_ready
    False and a non-native shape, and the checker let it through because only the exact producer
    names counted as native declarations. A label that names Agent Ready is a native claim."""
    ok, f = check_manifest(_manifest([_entry(producer="agent-ready (CLI or MCP-unwrapped; method UNKNOWN)",
                                             native_agent_ready=False, artifact=REAL_SURROGATE)]))
    assert not ok
    assert any("declared_native_must_look_native" in x for x in f)


def test_a_declared_native_partial_record_is_held_to_provenance_not_full_shape():
    """PG-00 is a receipt excerpt of a native MCP assessment: its own record_kind says the full
    response stayed in session evidence. A partial record cannot show the full contract shape,
    but it must still carry Agent Ready's own 4-key codex provider_evidence and an Agent Ready
    disposition, or the native claim fails."""
    excerpt = {"disposition": "READY", "owner_clarifications": [], "summary": "x",
               "record_kind": "Receipt excerpt",
               "provider_evidence": {"provider": "codex", "version": "codex-cli 0.154.0",
                                     "compatibility": "COMPATIBLE_UNVERIFIED",
                                     "capability_probe": "PASSED"}}
    ok, f = check_manifest(_manifest([_entry(path="pg00", producer="agent-ready-mcp",
                                             native_agent_ready=True, partial_record=True,
                                             artifact=excerpt)]))
    assert ok, f


def test_a_partial_record_claim_does_not_launder_surrogate_provenance():
    ok, f = check_manifest(_manifest([_entry(producer="agent-ready-cli", native_agent_ready=True,
                                             partial_record=True, artifact=REAL_SURROGATE)]))
    assert not ok
    assert any("declared_native_must_look_native" in x for x in f)


def test_an_entry_without_a_producer_is_rejected():
    e = _entry(artifact=REAL_SURROGATE)
    del e["producer"]
    ok, f = check_manifest(_manifest([e]))
    assert not ok
    assert any("producer_declared" in x for x in f)


def test_an_assessment_file_missing_from_the_manifest_is_rejected(tmp_path):
    """Coverage: every retained assessment must be accounted for, or an undeclared surrogate
    can sit beside declared ones."""
    ok, f = check_manifest(_manifest([]), expected_paths=["docs/work-units/python/PY-02.assessment.json"])
    assert not ok
    assert any("every_assessment_covered" in x for x in f)


NEGATIVE_CONTROLS = {
    "producer_declared": lambda m: m["entries"][0].pop("producer"),
    "declared_native_must_look_native": lambda m: m["entries"][0].update(
        producer="agent-ready-cli", native_agent_ready=True),
    "declared_surrogate_must_not_look_native": lambda m: m["entries"][1].update(
        producer="surrogate", native_agent_ready=False),
    "every_assessment_covered": lambda m: m["entries"].clear(),
}


def test_every_check_has_a_negative_control():
    base = _manifest([_entry(artifact=REAL_SURROGATE),
                      _entry(path="pg", producer="agent-ready-mcp", native_agent_ready=True,
                             artifact=REAL_NATIVE)])
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        m = copy.deepcopy(base)
        mutate(m)
        ok, f = check_manifest(m, expected_paths=["docs/work-units/python/PY-02.assessment.json"])
        if ok or not any(name in x for x in f):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)
