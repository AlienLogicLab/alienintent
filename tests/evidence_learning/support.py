from dataclasses import replace
from hashlib import sha256

from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.domain.records import Definition, Header, Observation, record_ref


def external_ref(name):
    if name == "policy":
        from pathlib import Path
        from alienintent.execution_coordination.domain import verdict
        return Ref("AlienLogicLab/alienintent", "fx-s1", "execution-verdict", "sha256:" + sha256(Path(verdict.__file__).read_bytes()).hexdigest(), "python:alienintent.execution_coordination.domain.verdict")
    return Ref("AlienLogicLab/alienintent", "fx-s1", name, "sha256:" + sha256(name.encode()).hexdigest(), "fixture:" + name)


def header(name, revision="1"):
    return Header("AlienLogicLab/alienintent", "fx-s1", name, revision, (external_ref("source"),))


def definition(revision="1"):
    return Definition(header("requirement/tests", revision), "fixture-authority", external_ref("authority"), frozenset({"tests"}))


def observation(**changes):
    return replace(Observation(header("test-result"), record_ref(definition()), "tests", "pytest", (external_ref("source"),), True, None, "fixture-runner", "invocation-1"), **changes)


def authority():
    from alienintent.evidence_learning.domain.admission import AuthoritySnapshot, DefinitionGrant, EvaluatorGrant, SourceGrant
    first = definition()
    second = replace(definition("2"), header=replace(definition("2").header, preceding_refs=(record_ref(first),)))
    return AuthoritySnapshot(
        tuple(DefinitionGrant(record_ref(d), d.issuer, d.authority_ref) for d in (first, second)),
        (SourceGrant("fixture-runner", external_ref("source"), True), SourceGrant("fixture-worker", external_ref("source"), False)),
        (EvaluatorGrant("fixture-verifier", external_ref("evaluator-authority"), external_ref("policy")),),
        frozenset(external_ref(n) for n in ("source", "authority", "evaluator-authority", "policy")),
    )


def profile(root):
    from alienintent.composition.evidence_profile import EvidenceProfile
    return EvidenceProfile(root / "evidence", permitted_root=root, project="AlienLogicLab/alienintent", name="fx-s1", authority=authority(), database=root / "state.sqlite")


def seeded(root):
    p = profile(root)
    dref = p.service.admit(definition(), 0).ref
    oref = p.service.admit(observation(), 1).ref
    return p, dref, oref
