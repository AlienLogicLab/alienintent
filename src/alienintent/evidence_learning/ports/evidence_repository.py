"""Immutable evidence body boundary; operational applicability is separate."""
from typing import Protocol

from alienintent.evidence_learning.domain.catalog import Catalog
from alienintent.evidence_learning.domain.records import Record, Verdict
from alienintent.evidence_learning.domain.refs import Ref


class EvidenceRepository(Protocol):
    def put(self, record: Record) -> Ref: ...
    def get(self, ref: Ref, access_scope: frozenset[str]) -> Record: ...


class EvidenceCatalog(Protocol):
    def read(self) -> Catalog: ...


class VerdictAdmission(Protocol):
    def check(self, record: Verdict, catalog: Catalog) -> None: ...
