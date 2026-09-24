from tests.evidence_learning.test_proof_planning import *
import shutil
f = ProofPlanningTests()
f.setUp()
try:
    f.remap(lambda m: f.predicate(m, "pinned-before-implementation").update(command=""))
    for _ in range(2):
        assert f.derive().reason_code == "INCOMPLETE_OBLIGATION"
    shutil.copyfile(ROOT / MAPPING, f.root / MAPPING)
    f.mapping_sha256 = MAPPING_SHA256
    assert isinstance(f.derive(), ProofPlan)
    f.remap(lambda m: m["predicates"].remove(f.predicate(m, "mapping-faithfulness-judgment")))
    assert f.derive().reason_code == "PRIOR_OBLIGATION_DROPPED"
    shutil.copyfile(ROOT / MAPPING, f.root / MAPPING)
    f.mapping_sha256 = MAPPING_SHA256
    assert isinstance(f.derive(), ProofPlan)
    proofs = f.profile().proofs
    version, original = proofs.read(REQUIREMENT)
    assert [e["event"] for e in original["history"]] == ["held", "held", "plan", "held", "plan"]
    print("valid repeated holds and interleaved plans: admitted")
    f.remap(lambda m: m["predicates"].remove(f.predicate(m, "mapping-faithfulness-judgment")))
    proofs = f.profile().proofs
    f.overwrite(dict(original, history=[], plan_ref=None, plan_digest=None))
    assert proofs.current(REQUIREMENT).reason_code == "INCOMPATIBLE_PROOF_PLAN_STATE"
    requirement = retained_requirement_revision(ROOT, SPECIFICATION, REQUIREMENT, PROJECT, PROFILE)
    design = retained_design_ref(ROOT, DESIGN, REQUIREMENT, PROJECT, PROFILE)
    assert proofs.derive(requirement, design, version).reason_code == "INCOMPATIBLE_PROOF_PLAN_STATE"
    f.overwrite(original)
    assert f.derive().reason_code == "PRIOR_OBLIGATION_DROPPED"
    print("same-version history erasure: held; restored history: deletion held")
finally:
    f.doCleanups()
