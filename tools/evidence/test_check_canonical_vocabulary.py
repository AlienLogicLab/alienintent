"""Tests for the canonical-vocabulary boundary checker.

Founder decision (2026-09-22, canonicalized): Agent Ready has exactly four dispositions —
READY, CLARIFY, SPLIT, HOLD. `BLOCKED`, `NEEDS_CLARIFICATION` and `SPLIT_RECOMMENDED` were the
AlienIntent *bootstrap assessor's* vocabulary; they are retained verbatim in historical evidence
and must never be presented as Agent Ready dispositions in active canonical authority.

Also enforced: no AlienIntent artifact claims ownership of Agent Ready's CLI, MCP server,
engine or schema; `Gap Trap` is not an AlienIntent Ubiquitous Language term; SF-REQ-039 keeps
its identity through its rename; core port definitions do not name a specific vendor as required.

Every check is proven red against the real shape it was written to catch — the actual SF-REQ-015
Wave 2 specification text as it stood before repair — not only against synthetic fixtures.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_canonical_vocabulary import CHECKS, check_texts  # noqa: E402

# The real string from docs/evidence/wave2-specified-requirements.json, SF-REQ-015 scope,
# as it stood before canonicalization.
REAL_PRE_REPAIR_SCOPE = (
    "Process semantics for READY, BLOCKED, NEEDS_CLARIFICATION, SPLIT_RECOMMENDED; "
    "immutable assessment evidence and reassessment lineage."
)
# The real string from docs/evidence/wave2-design-contracts.json, SF-REQ-015 contract.
REAL_PRE_REPAIR_CONTRACT = (
    '"Disposition": "Observed READY/BLOCKED/NEEDS_CLARIFICATION/SPLIT_RECOMMENDED semantics."'
)


def _clean():
    return {
        "docs/architecture/alienintent-ubiquitous-language-v0.1.md": (
            "## Readiness Assessment\nAlienIntent's immutable record of an Agent Ready "
            "Assessment. Agent Ready dispositions: READY, CLARIFY, SPLIT, HOLD.\n"
            "## Deterministic failure-class promotion\nConverts suitable REVIEW discoveries "
            "into VERIFY capability.\n"),
        "docs/decisions/alienintent-software-factory-plan.md": (
            "## SF-REQ-039 — Deterministic Test Worker\n**Priority:** P1\n\n"
            "Formerly titled *Fake-agent/offline factory proof*; identity retained.\n"),
        "docs/architecture/pre-python-gate/hexagonal-contracts.md": (
            "| RequirementSource | scoped source reference -> provenance-bearing Source Record |\n"),
    }


def test_clean_active_authority_passes():
    ok, failures = check_texts(_clean())
    assert ok, failures


def test_the_real_pre_repair_specification_text_is_rejected():
    """Proven red against the actual Wave 2 SF-REQ-015 scope string, not a synthetic one."""
    texts = _clean()
    texts["docs/evidence/wave2-specified-requirements.json"] = REAL_PRE_REPAIR_SCOPE
    ok, failures = check_texts(texts)
    assert not ok
    assert any("agent_ready_dispositions_exact" in f for f in failures)


def test_the_real_pre_repair_design_contract_text_is_rejected():
    texts = _clean()
    texts["docs/evidence/wave2-design-contracts.json"] = REAL_PRE_REPAIR_CONTRACT
    ok, failures = check_texts(texts)
    assert not ok
    assert any("agent_ready_dispositions_exact" in f for f in failures)


def test_legacy_vocabulary_marked_as_historical_bootstrap_assessor_is_allowed():
    """Historical records remain historical; the marker is what distinguishes them."""
    texts = _clean()
    texts["docs/decisions/alienintent-software-factory-plan.md"] += (
        "Historical bootstrap-assessor vocabulary (READY, BLOCKED, NEEDS_CLARIFICATION, "
        "SPLIT_RECOMMENDED) is retained in Wave 1 evidence and is not an Agent Ready "
        "disposition set.\n")
    ok, failures = check_texts(texts)
    assert ok, failures


def test_a_document_level_terminology_note_exempts_a_historical_record():
    """SWF-33 records the assessment it acted on, in the vocabulary of the time. A decision
    record is not rewritten; it carries one note declaring that vocabulary historical."""
    texts = _clean()
    texts["docs/decisions/2026-09-21-py10-transport-split.md"] = (
        "> **Terminology note (2026-09-22).** Dispositions quoted below are the historical "
        "bootstrap-assessor vocabulary, not Agent Ready dispositions.\n\n"
        "PY-10's fresh reassessment returned **`SPLIT_RECOMMENDED`**.\n"
        "Neither the earlier `BLOCKED` nor the current `SPLIT_RECOMMENDED` disposition is "
        "treated as READY.\n")
    ok, failures = check_texts(texts)
    assert ok, failures


def test_a_document_level_note_does_not_launder_a_design_artifact():
    """The note exempts records, not designs: a Wave 2 artifact that merely mentions the
    history while still specifying legacy semantics normatively is still contaminated."""
    texts = _clean()
    texts["docs/evidence/wave2-specified-requirements.json"] = (
        '["historical bootstrap-assessor vocabulary is retained in Wave 1 evidence", '
        '"Process semantics for READY, BLOCKED, NEEDS_CLARIFICATION, SPLIT_RECOMMENDED."]')
    ok, failures = check_texts(texts)
    assert not ok


def test_the_sentence_that_denies_blocked_is_a_disposition_is_not_flagged():
    """False positive found live: the SF-REQ-015 amendment says BLOCKED is NOT an Agent Ready
    disposition, on a line that also names READY. Denial is not contamination."""
    texts = _clean()
    texts["docs/decisions/alienintent-software-factory-plan.md"] += (
        "Agent Ready returns exactly one of **`READY`, `CLARIFY`, `SPLIT`, `HOLD`**. A "
        "disposition is an assessment result, never a lifecycle state; `BLOCKED` is an "
        "AlienIntent planning/verdict state and is not an Agent Ready disposition.\n")
    ok, failures = check_texts(texts)
    assert ok, failures


def test_blocked_enumerated_beside_ready_as_a_disposition_set_is_flagged():
    """The contaminated shape is an enumeration: READY and BLOCKED joined by list punctuation."""
    texts = _clean()
    texts["docs/decisions/alienintent-software-factory-plan.md"] += (
        "Dispositions: READY / BLOCKED / HOLD.\n")
    ok, failures = check_texts(texts)
    assert not ok
    assert any("agent_ready_dispositions_exact" in f for f in failures)


def test_blocked_alone_as_a_lifecycle_or_verdict_state_is_allowed():
    """BLOCKED is a legitimate AlienIntent planning/verdict state; only the disposition-set
    shape is contaminated."""
    texts = _clean()
    texts["docs/decisions/alienintent-software-factory-plan.md"] += (
        "Missing evidence yields UNVERIFIED/BLOCKED/REJECT, not DONE.\n")
    ok, failures = check_texts(texts)
    assert ok, failures


def test_a_claim_of_owning_agent_ready_internals_is_rejected():
    texts = _clean()
    texts["docs/decisions/alienintent-software-factory-plan.md"] += (
        "## SF-REQ-099 — Readiness engine\nAlienIntent owns the Agent Ready assessment engine "
        "and its CLI.\n")
    ok, failures = check_texts(texts)
    assert not ok
    assert any("no_agent_ready_internals_ownership" in f for f in failures)


def test_gap_trap_as_a_defined_ul_term_is_rejected():
    texts = _clean()
    texts["docs/architecture/alienintent-ubiquitous-language-v0.1.md"] += (
        "## Gap Trap\nThe learning mechanism that converts REVIEW discoveries.\n")
    ok, failures = check_texts(texts)
    assert not ok
    assert any("gap_trap_not_ul" in f for f in failures)


def test_gap_trap_as_attribution_prose_is_allowed():
    texts = _clean()
    texts["docs/architecture/alienintent-ubiquitous-language-v0.1.md"] += (
        "Attribution: the concept was informed by the external Gap Trap project.\n")
    ok, failures = check_texts(texts)
    assert ok, failures


def test_losing_sf_req_039_identity_is_rejected():
    texts = _clean()
    texts["docs/decisions/alienintent-software-factory-plan.md"] = (
        "## SF-REQ-057 — Deterministic Test Worker\n**Priority:** P1\n")
    ok, failures = check_texts(texts)
    assert not ok
    assert any("sf_req_039_identity" in f for f in failures)


def test_a_core_port_that_requires_a_specific_vendor_is_rejected():
    texts = _clean()
    texts["docs/architecture/pre-python-gate/hexagonal-contracts.md"] = (
        "| RequirementSource | GitHub Issue (required) -> Requirement |\n")
    ok, failures = check_texts(texts)
    assert not ok
    assert any("ports_are_vendor_neutral" in f for f in failures)


NEGATIVE_CONTROLS = {
    "agent_ready_dispositions_exact": lambda t: t.__setitem__(
        "docs/evidence/wave2-specified-requirements.json", REAL_PRE_REPAIR_SCOPE),
    "no_agent_ready_internals_ownership": lambda t: t.__setitem__(
        "docs/decisions/alienintent-software-factory-plan.md",
        "AlienIntent owns the Agent Ready MCP server.\n## SF-REQ-039 — x\n"),
    "gap_trap_not_ul": lambda t: t.__setitem__(
        "docs/architecture/alienintent-ubiquitous-language-v0.1.md", "## Gap Trap\ndefined\n"),
    "sf_req_039_identity": lambda t: t.__setitem__(
        "docs/decisions/alienintent-software-factory-plan.md", "## SF-REQ-057 — renamed\n"),
    "ports_are_vendor_neutral": lambda t: t.__setitem__(
        "docs/architecture/pre-python-gate/hexagonal-contracts.md",
        "| RequirementSource | Jira Epic (required) -> Requirement |\n"),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        texts = copy.deepcopy(_clean())
        mutate(texts)
        ok, failures = check_texts(texts)
        if ok or not any(name in f for f in failures):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)


# --- Markdown renderings are active artifacts too (DV-2, 2026-09-22) ------------------------

REAL_STALE_MARKDOWN_LANE_LINE = (
    "- **failure:** BLOCKED, NEEDS_CLARIFICATION, SPLIT_RECOMMENDED, stale verdict or failed "
    "attempt holds affected work and routes the appropriate decision/reassessment.")


def test_the_wave2_markdown_renderings_are_active_artifacts():
    from check_canonical_vocabulary import ACTIVE_ARTIFACTS
    assert "docs/evidence/wave2-specified-requirements.md" in ACTIVE_ARTIFACTS
    # The design-contracts prose companion is a Phase 9 rendering superseded by the JSON and
    # carries a historical banner instead (DV-2); it is deliberately not active.


def test_the_real_stale_markdown_lane_line_is_rejected():
    """Proven red against the actual line the DV reviewer found at
    wave2-specified-requirements.md:826 — bootstrap vocabulary presented as current READY-lane
    failure handling, with no historical marker."""
    texts = _clean()
    texts["docs/evidence/wave2-specified-requirements.md"] = REAL_STALE_MARKDOWN_LANE_LINE
    ok, failures = check_texts(texts)
    assert not ok
    assert any("agent_ready_dispositions_exact" in f for f in failures)
