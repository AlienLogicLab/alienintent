#!/usr/bin/env python3
"""PY-09B proven-red matrix — remove each guard and observe its proof fail.

SWF-24: a check that cannot fail is not evidence. For every guard this BIU
adds, this harness copies the tree, deletes exactly that guard, runs the test
that names it, and requires the test to go red. A guard whose test still
passes without it is reported as a failure of this harness, not a success.

    python3 tools/live/py09b_proven_red.py           # human readable
    python3 tools/live/py09b_proven_red.py --json    # retained evidence

Nothing here touches the working tree: every mutation is applied to a copy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
COPIED = ("src", "tests", "tools", "pyproject.toml")

# guard name -> (file, exact source to remove, replacement, test that must go red)
GUARDS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "stale_projection_fence",
        "src/alienintent/execution_coordination/adapters/github_work_management.py",
        "        if revision < previous:\n            return ProjectionReceipt(identity, revision, False, \"stale projection fenced\")\n",
        "",
        "tests/execution_coordination/test_github_projects_v2.py::test_the_stale_projection_fence_still_refuses_a_superseded_revision",
    ),
    (
        "projection_read_back_confirmation",
        "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
        "        return expected_revision if self.read_status(item_id).status == status else -1",
        "        return expected_revision",
        "tests/execution_coordination/test_github_projects_v2.py::test_a_projection_the_project_did_not_apply_is_never_reported_as_confirmed",
    ),
    (
        "project_identity_resolution",
        "src/alienintent/installation/domain/project_identity.py",
        "        if observed_id != self.project_id:\n            raise ProjectAddressRejected(\"observed project is not the configured project\")\n",
        "",
        "tests/execution_coordination/test_github_projects_v2.py::test_an_answer_naming_another_project_is_refused_instead_of_being_used",
    ),
    (
        "project_field_identity_comparison",
        "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
        "        if status.get(\"id\") != self._address.status_field_id or priority.get(\"id\") != self._address.priority_field_id:\n            raise ProjectRejected(\"observed Status or Priority field is not the configured field identity\")\n",
        "",
        "tests/execution_coordination/test_github_projects_v2.py::test_a_project_answering_with_a_different_field_identity_is_refused",
    ),
    (
        "webhook_raw_body_signature",
        "src/alienintent/execution_coordination/adapters/github_webhook.py",
        "        if not self.signature_valid(self._secret, raw_body, authenticity):\n            raise IngressRejected(\"invalid raw-body signature\")\n",
        "",
        "tests/execution_coordination/test_github_delivery_ingress.py::test_a_delivery_signed_with_a_different_secret_is_rejected",
    ),
    (
        "foreign_project_delivery_refusal",
        "src/alienintent/execution_coordination/adapters/github_webhook.py",
        "        if reference.project != self._project_reference:\n            raise IngressRejected(\"delivery targets a project outside this profile\")\n",
        "",
        "tests/execution_coordination/test_github_delivery_ingress.py::test_a_delivery_for_another_project_is_refused_even_though_the_token_could_reach_it",
    ),
    (
        "exact_least_privilege",
        "src/alienintent/installation/domain/app_credentials.py",
        "    observed = dict(granted or {})\n    findings: list[str] = []",
        "    observed = dict(granted or {})\n    return ()\n    findings: list[str] = []",
        "tests/installation/test_installation_credentials.py::test_an_extra_a_missing_and_a_read_only_contents_grant_each_fail_the_check",
    ),
    (
        "repository_scope_enforcement",
        "src/alienintent/installation/domain/app_credentials.py",
        "    names = list(repositories or [])\n    findings: list[str] = []",
        "    names = list(repositories or [])\n    return ()\n    findings: list[str] = []",
        "tests/installation/test_installation_credentials.py::test_repository_scope_drift_is_reported_rather_than_tolerated",
    ),
    (
        "installation_token_staleness",
        "src/alienintent/installation/domain/app_credentials.py",
        "        return now + safety_seconds >= self.expires_at",
        "        return False",
        "tests/installation/test_installation_credentials.py::test_expiry_inside_the_refresh_margin_is_already_stale",
    ),
    (
        "credential_reference_fails_closed",
        "src/alienintent/installation/application/installation_credentials.py",
        "        if not isinstance(material, bytes) or not material:\n            raise CredentialRejected(\"App private key reference resolves to unusable material\")\n",
        "",
        "tests/installation/test_installation_credentials.py::test_unusable_credential_material_fails_closed_before_any_live_call",
    ),
    (
        "bearer_material_redaction",
        "src/alienintent/installation/domain/app_credentials.py",
        "        return (\n            \"InstallationToken(value=<redacted>, \"\n            f\"expires_at={self.expires_at!r}, repository_selection={self.repository_selection!r})\"\n        )",
        "        return f\"InstallationToken({self.value!r}, {self.expires_at!r}, {self.repository_selection!r})\"",
        "tests/installation/test_installation_credentials.py::test_installation_token_representation_never_carries_the_bearer_material",
    ),
    (
        "resident_ingress_marker",
        "src/alienintent/composition/doctor_probes.py",
        "    if RESIDENT_INGRESS_MARKER not in answered:\n        raise DoctorFailure(\"configured webhook route does not reach the resident ingress\")\n",
        "",
        "tests/composition/test_sandbox_profile.py::test_the_transport_probe_fails_when_the_route_answers_from_another_origin",
    ),
    (
        "app_assertion_signature",
        "src/alienintent/installation/adapters/app_jwt.py",
        "    signature = _segment(_sign(signing_input, modulus, private_exponent))",
        "    signature = _segment(sha256(signing_input).digest())",
        "tests/installation/test_app_jwt.py::test_signature_verifies_against_the_public_numbers_of_the_signing_key",
    ),
)


def _prepare(scratch: Path) -> Path:
    tree = scratch / "tree"
    tree.mkdir()
    for name in COPIED:
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, tree / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
        else:
            shutil.copy2(source, tree / name)
    return tree


def run() -> list[dict]:
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="py09b-proven-red-") as scratch_name:
        tree = _prepare(Path(scratch_name))
        originals = {path: (tree / path).read_text() for _, path, _, _, _ in GUARDS}
        for guard, path, removed, replacement, test in GUARDS:
            target = tree / path
            original = originals[path]
            if removed not in original:
                results.append({"check": guard, "ok": False, "detail": f"guard source not found in {path}; the matrix is stale"})
                continue
            intact = _pytest(tree, test)
            target.write_text(original.replace(removed, replacement, 1))
            broken = _pytest(tree, test)
            target.write_text(original)
            results.append({
                "check": guard,
                "ok": intact.returncode == 0 and broken.returncode != 0,
                "detail": (
                    f"{test.rsplit('::', 1)[1]}: exit {intact.returncode} with the guard, "
                    f"exit {broken.returncode} with the guard removed from {path.rsplit('/', 1)[1]}"
                ),
            })
    return results


def _pytest(tree: Path, test: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test],
        cwd=tree, capture_output=True, text=True, check=False,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="PY-09B proven-red matrix")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args(argv)

    results = run()
    failed = [result for result in results if not result["ok"]]
    if arguments.json:
        print(json.dumps({"ok": not failed, "checks": results}, indent=1))
    else:
        for result in results:
            print(f"{'PASS' if result['ok'] else 'FAIL'}  {result['check']}\n      {result['detail']}")
        print(f"\n{len(results) - len(failed)}/{len(results)} guards proven red" + ("" if not failed else f" — {len(failed)} NOT PROVEN"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
