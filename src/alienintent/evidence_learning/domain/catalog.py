"""Versioned applicability view, separate from immutable evidence records."""
from dataclasses import dataclass

from alienintent.evidence_learning.domain.records import Definition, Record
from alienintent.evidence_learning.domain.refs import Ref


@dataclass(frozen=True)
class Catalog:
    version: int
    refs: tuple[Ref, ...]
    records: tuple[Record, ...]
    held_definitions: tuple[Ref, ...]

    def current_definitions(self) -> dict[str, Ref]:
        return {r.header.logical_id: ref for ref, r in zip(self.refs, self.records) if isinstance(r, Definition)}
