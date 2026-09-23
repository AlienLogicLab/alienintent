"""CAS applicability pointers only after durable immutable evidence installation."""
from dataclasses import asdict, dataclass

from alienintent.evidence_learning.domain.admission import AuthoritySnapshot, validate
from alienintent.evidence_learning.domain.catalog import Catalog
from alienintent.evidence_learning.domain.records import Definition, Observation, Record, Verdict, canonical_bytes, kind_of, record_ref, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository, VerdictAdmission
from alienintent.execution_coordination.ports.operational_store import OperationalStore, SchemaIncompatible, VersionConflict


@dataclass(frozen=True)
class Admitted:
    ref: Ref
    version: int


def _conflicts(records: tuple[Record, ...]) -> tuple[Ref, ...]:
    seen: dict[tuple[Ref, str], set[bytes]] = {}
    held = []
    for record in records:
        if not isinstance(record, Observation):
            continue
        key = (record.definition_ref, record.evidence_id)
        seen.setdefault(key, set()).add(canonical_bytes(record.value))
        if len(seen[key]) > 1 and record.definition_ref not in held:
            held.append(record.definition_ref)
    return tuple(held)


class EvidenceService:
    aggregate = "upstream:evidence:catalog"

    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 authority: AuthoritySnapshot, access_scope: frozenset[str]) -> None:
        self.repository, self.store = repository, store
        self.project, self.profile, self.authority, self.access_scope = project, profile, authority, access_scope
        self.verdict_admission: VerdictAdmission | None = None

    def read(self) -> Catalog:
        version, state = self.store.read_state(self.profile, self.aggregate)
        if version == 0 and not state:
            return Catalog(0, (), (), ())
        if type(state.get("schema_version")) is not int or state.get("schema_version") != 1:
            raise SchemaIncompatible("evidence pointer requires schema_version=1")
        if set(state) != {"schema_version", "refs", "held_definitions"} or not isinstance(state["refs"], list):
            raise EvidenceHold("INVALID_POINTER")
        refs = tuple(ref_from_document(r) for r in state["refs"])
        if len(set(refs)) != len(refs):
            raise EvidenceHold("INVALID_POINTER")
        records: dict[Ref, Record] = {}
        current: dict[str, Ref] = {}
        for ref in refs:
            record = self.repository.get(ref, self.access_scope)
            self._scope(record)
            validate(record, self.authority, records, current)
            self._check_verdict(record, Catalog(version, tuple(records), tuple(records.values()), _conflicts(tuple(records.values()))))
            records[ref] = record
            if isinstance(record, Definition):
                current[record.header.logical_id] = ref
        values = tuple(records.values())
        held = _conflicts(values)
        if state["held_definitions"] != [asdict(ref) for ref in held]:
            raise EvidenceHold("INVALID_APPLICABILITY_POINTER")
        return Catalog(version, refs, values, held)

    def _check_verdict(self, record: Record, catalog: Catalog) -> None:
        if isinstance(record, Verdict):
            if self.verdict_admission is None:
                raise EvidenceHold("VERDICT_POLICY_UNAVAILABLE")
            self.verdict_admission.check(record, catalog)

    def _scope(self, record: Record) -> None:
        if (record.header.project, record.header.profile) != (self.project, self.profile):
            raise EvidenceHold("REF_SCOPE", (record_ref(record),))
        if record.header.access_label not in self.access_scope:
            raise EvidenceHold("ACCESS_DENIED", (record_ref(record),))

    def admit(self, record: Record, expected_version: int) -> Admitted:
        catalog = self.read()
        if catalog.version != expected_version:
            raise EvidenceHold("VERSION_CONFLICT", required_action="read the current version and reevaluate; do not retry the old decision")
        self._scope(record)
        ref = record_ref(record)
        # read() already revalidated the entire retained history and authority.
        # Re-putting an old identical revision must not move its current pointer.
        if ref in catalog.refs:
            return Admitted(ref, catalog.version)
        admitted = validate(record, self.authority, dict(zip(catalog.refs, catalog.records)), catalog.current_definitions())
        self._check_verdict(record, catalog)
        identity = (kind_of(record), record.header.logical_id, record.header.revision)
        if any((kind_of(r), r.header.logical_id, r.header.revision) == identity for r in catalog.records):
            raise EvidenceHold("IDENTITY_CONFLICT", (admitted.ref,))
        ref = self.repository.put(record)
        # This readback is deliberately before the operational transaction.
        self.repository.get(ref, self.access_scope)
        refs = (*catalog.refs, ref)
        held = _conflicts((*catalog.records, record))
        state = {"schema_version": 1, "refs": [asdict(r) for r in refs],
                 "held_definitions": [asdict(r) for r in held]}
        try:
            version = self.store.commit(self.profile, self.aggregate, expected_version, state)
        except VersionConflict as error:
            raise EvidenceHold("VERSION_CONFLICT", (ref,), required_action="read current state and reevaluate; installed object remains retained") from error
        return Admitted(ref, version)
