"""Context assembly's role vocabulary agrees with the worker port."""

from alienintent.context_assembly.domain import work_context
from alienintent.execution_coordination.ports import worker_provider


def test_context_role_names_match_worker_roles():
    assert (work_context.PRODUCER, work_context.VERIFIER, work_context.CLOSURE) == (
        worker_provider.PRODUCER, worker_provider.VERIFIER, worker_provider.CLOSURE)
