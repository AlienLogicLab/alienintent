"""Explicit manifested source boundary; no work-management writes."""
from typing import Protocol
from alienintent.context_assembly.domain.inventory import Manifest, SourceRecord


class RequirementSource(Protocol):
    def read(self, manifest: Manifest) -> tuple[SourceRecord, ...]: ...
