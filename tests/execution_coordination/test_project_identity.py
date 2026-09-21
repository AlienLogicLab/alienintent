"""Configuration-enforced Project addressing (SWF-34, binding rule 6b, AC 10b).

Nothing here asserts token-level Project isolation: `organization_projects` is
organization scoped and cannot provide it. These tests prove the control that
does operate — deterministic, exclusive, fail-closed addressing.
"""

from __future__ import annotations

import pytest

from alienintent.installation.domain.project_identity import (
    ProjectAddress,
    ProjectAddressRejected,
    foreign_project_identities,
    foreign_repositories,
)
from tests.support.live_github import FOREIGN_PROJECT, PRIORITY_FIELD, SANDBOX_PROJECT, SANDBOX_REPOSITORY, STATUS_FIELD


def address() -> ProjectAddress:
    return ProjectAddress(SANDBOX_PROJECT, 2, "AlienLogicLab", STATUS_FIELD, PRIORITY_FIELD)


def test_the_configured_project_resolves_to_itself_and_to_nothing_else() -> None:
    assert address().resolve(SANDBOX_PROJECT, 2) == SANDBOX_PROJECT


@pytest.mark.parametrize(
    ("observed_id", "observed_number"),
    [(FOREIGN_PROJECT, 1), (FOREIGN_PROJECT, None), (None, 2), ("", 2), (SANDBOX_PROJECT, 1)],
)
def test_resolution_fails_closed_on_mismatch_and_on_ambiguity(observed_id, observed_number) -> None:
    """Removing either comparison must make this fail: a foreign answer must never resolve."""
    with pytest.raises(ProjectAddressRejected):
        address().resolve(observed_id, observed_number)


def test_the_non_raising_form_answers_the_same_single_comparison() -> None:
    assert address().targets(SANDBOX_PROJECT)
    assert not address().targets(FOREIGN_PROJECT)
    assert not address().targets(None)


def test_only_the_configured_status_and_priority_fields_are_addressable() -> None:
    assert address().field_for("Status") == STATUS_FIELD
    assert address().field_for("Priority") == PRIORITY_FIELD
    with pytest.raises(ProjectAddressRejected):
        address().field_for("Estimate")


@pytest.mark.parametrize(
    "broken",
    [
        (SANDBOX_PROJECT, 0, "AlienLogicLab", STATUS_FIELD, PRIORITY_FIELD),
        ("not-a-project-node", 2, "AlienLogicLab", STATUS_FIELD, PRIORITY_FIELD),
        (SANDBOX_PROJECT, 2, "", STATUS_FIELD, PRIORITY_FIELD),
        (SANDBOX_PROJECT, 2, "AlienLogicLab", "", PRIORITY_FIELD),
        (SANDBOX_PROJECT, 2, "AlienLogicLab", STATUS_FIELD, ""),
    ],
)
def test_an_incomplete_project_identity_is_refused_at_construction(broken: tuple) -> None:
    with pytest.raises(ProjectAddressRejected):
        ProjectAddress(*broken)


def test_any_project_identity_other_than_the_configured_one_is_reported() -> None:
    """Stated as an allowlist, so no production identifier has to be written here."""
    configuration = f'{{"project_reference":"{SANDBOX_PROJECT}","stray":"{FOREIGN_PROJECT}"}}'

    assert foreign_project_identities(configuration, SANDBOX_PROJECT) == (FOREIGN_PROJECT,)
    assert foreign_project_identities(f'{{"project_reference":"{SANDBOX_PROJECT}"}}', SANDBOX_PROJECT) == ()


def test_any_repository_other_than_the_configured_one_is_reported() -> None:
    assert foreign_repositories((SANDBOX_REPOSITORY,), SANDBOX_REPOSITORY) == ()
    assert foreign_repositories((SANDBOX_REPOSITORY, "AlienLogicLab/elsewhere"), SANDBOX_REPOSITORY) == ("AlienLogicLab/elsewhere",)
