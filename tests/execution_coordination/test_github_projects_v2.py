"""Live Projects v2 read and fenced projection write, driven by recorded answers.

The adapter under test is the one the sandbox composition binds; only the
transport is recorded, so protocol and fencing logic run exactly as they run
live.
"""

from __future__ import annotations

import pytest

from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory
from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.execution_coordination.ports.project_directory import ProjectRejected, ProjectUnavailable
from alienintent.execution_coordination.ports.work_management import WorkRejected, WorkUnavailable
from alienintent.installation.domain.project_identity import ProjectAddress, ProjectAddressRejected
from tests.execution_coordination.test_github_work_management import contract
from tests.support.live_github import (
    FOREIGN_PROJECT,
    PRIORITY_FIELD,
    SANDBOX_PROJECT,
    SANDBOX_REPOSITORY,
    STATUS_FIELD,
    RecordedTransport,
    project_graphql,
)


def address() -> ProjectAddress:
    return ProjectAddress(SANDBOX_PROJECT, 2, "AlienLogicLab", STATUS_FIELD, PRIORITY_FIELD)


def directory(**recorded) -> GitHubProjectsV2Directory:
    transport = RecordedTransport({}, project_graphql(**recorded))
    return GitHubProjectsV2Directory(address(), transport, lambda: {"Authorization": "token recorded"})


# --- AC 4: live Project, field and option identities -------------------------


def test_status_and_priority_fields_resolve_with_their_option_identities() -> None:
    schema = directory().schema()

    assert (schema.project_id, schema.project_number) == (SANDBOX_PROJECT, 2)
    assert schema.status_field_id == STATUS_FIELD
    assert schema.status_options["IMPLEMENT"] == "b39bda1a"
    assert schema.priority_field_id == PRIORITY_FIELD
    assert schema.priority_options["P0"] == "275d961a"


def test_a_project_answering_with_a_different_field_identity_is_refused() -> None:
    """Removing the field-identity comparison must make this fail."""
    with pytest.raises(ProjectRejected):
        directory(status_field="PVTSSF_somewhere_else").schema()


def test_a_project_missing_a_configured_field_is_refused_rather_than_partly_used() -> None:
    transport = RecordedTransport({}, lambda query, variables: {"data": {"node": {
        "id": SANDBOX_PROJECT, "number": 2, "title": "x", "fields": {"nodes": [{"id": STATUS_FIELD, "name": "Status", "options": []}]},
    }}})

    with pytest.raises(ProjectRejected):
        GitHubProjectsV2Directory(address(), transport, lambda: {}).schema()


def test_project_resolution_through_the_work_management_port_validates_the_mapping() -> None:
    """AC 4: the Project is resolved through the port the control plane already uses."""
    work = GitHubProjectsWorkManagement(
        "py10-sandbox", SANDBOX_REPOSITORY, {"READY": "READY"}, {"IMPLEMENT": "Status", "VERIFY": "Status"},
        lambda: (), contract(), directory=directory(),
    )

    assert work.resolve_project().status_options["VERIFY"] == "64fca347"


def test_a_lifecycle_state_the_project_cannot_carry_is_rejected_before_any_write() -> None:
    work = GitHubProjectsWorkManagement(
        "py10-sandbox", SANDBOX_REPOSITORY, {"READY": "READY"}, {"PARKED": "Status"},
        lambda: (), contract(), directory=directory(),
    )

    with pytest.raises(WorkRejected):
        work.resolve_project()


def test_a_profile_with_no_bound_directory_is_unavailable_rather_than_silently_offline() -> None:
    work = GitHubProjectsWorkManagement(
        "py10-sandbox", SANDBOX_REPOSITORY, {"READY": "READY"}, {"IMPLEMENT": "Status"}, lambda: (), contract(),
    )

    with pytest.raises(WorkUnavailable):
        work.resolve_project()


# --- AC 10b: every read and every write targets the configured Project -------


def test_every_project_answer_is_resolved_against_the_configured_identity() -> None:
    """Removing the resolve call must make this fail: answers would go unchecked."""
    live = directory(read_back="IMPLEMENT")
    live.schema()
    live.items()
    live.write_status("PVTI_item", "IMPLEMENT", 3)

    assert live.addressed
    assert set(live.addressed) == {SANDBOX_PROJECT}


def test_an_answer_naming_another_project_is_refused_instead_of_being_used() -> None:
    """Only the identity differs here, so the identity comparison alone must refuse it."""
    for call in (
        lambda live: live.schema(),
        lambda live: live.items(),
        lambda live: live.read_status("PVTI_item"),
        lambda live: live.write_status("PVTI_item", "IMPLEMENT", 1),
    ):
        with pytest.raises(ProjectAddressRejected):
            call(directory(project_id=FOREIGN_PROJECT, project_number=2, read_back="IMPLEMENT"))


def test_an_answer_naming_the_configured_identity_with_another_number_is_refused() -> None:
    with pytest.raises(ProjectAddressRejected):
        directory(project_number=1).schema()


# --- AC 5: the projection write is confirmed by read-back --------------------


def test_a_confirmed_projection_returns_the_revision_it_was_asked_to_carry() -> None:
    assert directory().write_status("PVTI_item", "IMPLEMENT", 7) == 7


def test_a_projection_the_project_did_not_apply_is_never_reported_as_confirmed() -> None:
    """Removing the read-back must make this fail: an unapplied write would pass."""
    assert directory(written_status="READY").write_status("PVTI_item", "IMPLEMENT", 7) == -1


def test_a_lifecycle_state_with_no_status_option_is_refused_before_the_mutation() -> None:
    with pytest.raises(ProjectRejected):
        directory().write_status("PVTI_item", "PARKED", 1)


def test_the_stale_projection_fence_still_refuses_a_superseded_revision() -> None:
    """AC 5 fence: removing the revision comparison must make this fail."""
    live = directory(read_back="IMPLEMENT")
    work = GitHubProjectsWorkManagement(
        "py10-sandbox", SANDBOX_REPOSITORY, {"READY": "READY"}, {"IMPLEMENT": "Status"},
        lambda: (), contract(), lambda identity, field, state, revision: live.write_status(identity, state, revision),
        directory=live,
    )

    assert work.project_execution_state("PVTI_item", "IMPLEMENT", 4).confirmed
    stale = work.project_execution_state("PVTI_item", "IMPLEMENT", 2)
    assert not stale.confirmed
    assert stale.detail == "stale projection fenced"


# --- AC 6: projection stays one-way ------------------------------------------


def test_an_externally_edited_project_field_does_not_alter_canonical_state() -> None:
    """FD-01: a Project field is written from canonical state and never read as authority."""
    live = directory(read_back="IMPLEMENT")
    work = GitHubProjectsWorkManagement(
        "py10-sandbox", SANDBOX_REPOSITORY, {"READY": "READY"}, {"IMPLEMENT": "Status"},
        lambda: (), contract(), lambda identity, field, state, revision: live.write_status(identity, state, revision),
        directory=live,
    )
    work.project_execution_state("PVTI_item", "IMPLEMENT", 5)

    edited = directory(read_back="DONE")
    assert edited.read_status("PVTI_item").status == "DONE"
    # The external edit changes no canonical revision: the fence still holds at 5.
    assert not work.project_execution_state("PVTI_item", "IMPLEMENT", 4).confirmed
    assert work.project_execution_state("PVTI_item", "IMPLEMENT", 6).confirmed


# --- transport failures stay distinguishable ---------------------------------


def test_a_refusing_provider_is_unavailable_rather_than_an_empty_project() -> None:
    transport = RecordedTransport({}, lambda query, variables: {"errors": [{"message": "refused"}]})

    with pytest.raises(ProjectUnavailable):
        GitHubProjectsV2Directory(address(), transport, lambda: {}).schema()
