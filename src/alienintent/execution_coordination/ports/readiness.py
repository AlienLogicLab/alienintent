"""Readiness assessment and retained-consumer ports (C#/contracts/4/ports/1,2); internal, not an Agent Ready schema."""
from typing import Protocol

from alienintent.execution_coordination.domain.readiness import (
    AttemptFailure, AttemptMetadata, CandidateWorkUnit, HistoricalAssessment, Hold, ProducerBinding, ProducerResponse,
    ReadinessEligibility, SemanticAssessment)


class ReadinessAssessment(Protocol):
    """A configured producer adapter (CLI or MCP) bound at composition; it returns what it observed, unjudged."""

    def assess(self, candidate_work_unit: CandidateWorkUnit) -> ProducerResponse: ...


class AssessmentConsumer(Protocol):
    """Immutable attempts with raw bytes retained before normalization; applicability is a separate pointer."""

    def open(self, identity: str, input_fingerprint: str, input_sha256: str, contract_digest: str | None,
             predecessor: dict | None, lint_ref: dict | None,
             binding: ProducerBinding | None) -> str | Hold: ...

    def observe(self, raw_artifact: bytes | None, attempt_metadata: AttemptMetadata,
                recognized_shape: str) -> SemanticAssessment | AttemptFailure | Hold: ...

    def consume(self, identity: str, current_input_fingerprint: str) -> ReadinessEligibility | Hold: ...

    def latest(self, identity: str) -> dict | None: ...

    def history(self, identity: str) -> tuple[dict, ...]: ...

    def raw(self, identity: str, attempt_id: str) -> tuple[dict, str] | None: ...

    def annotate(self, identity: str, attempt_id: str, key: str, value: object) -> Hold | None: ...

    def invalidate(self, identity: str, reason: str, cause: str) -> Hold | None: ...

    def retain(self, identity: str, event: str, document: dict) -> dict: ...


class SurrogateHistoryReplay(Protocol):
    """Historical bootstrap-assessor records retained verbatim; a digest mismatch holds before anything is kept."""

    def replay(self, history: tuple[HistoricalAssessment, ...]) -> tuple[dict, ...] | Hold: ...
