# PY-09B live GitHub transport and projection substrate — executable evidence

Retained engineering facts for the PY-09B implementation against baseline
`d3f54ebe120ab435b483b1cf60120b16ae3d706d`. It contains no secret, credential,
App id, installation id, ingress hostname or private installation detail, while
still proving the run used the sandbox identity.

## Local executable checks

- `python3 -m pytest -q`: 308 passed (209 at baseline; 99 added by this BIU).
- `python3 tools/fitness/check_architecture.py --root src/alienintent`: PASS.
- `npm test`: 310 + 18 + 2 Node tests passed, exit 0.
- `python3 tools/live/py09b_live_checks.py --json`: **35/35**, exit 0 —
  [`py09b-live-checks-2026-09-21.json`](py09b-live-checks-2026-09-21.json).
- `python3 tools/live/py09b_proven_red.py --json`: **13/13 guards proven red**,
  exit 0 — [`py09b-proven-red-2026-09-21.json`](py09b-proven-red-2026-09-21.json).

## What was proven live, against the provisioned sandbox

The bounded live portion drives the shipped `alienintent` modules through the
sandbox profile composition — not a transcript of them. It is small, cheap and
individually diagnosable, and a verifier re-runs it with one command.

| Criterion | Live result |
|---|---|
| 1 — token minted, used, refreshed, fails closed | Minted from the referenced private key; used for a live installation call; a credential already inside its refresh margin was **re-minted rather than reused**, and a usable one was reused; an unresolvable key reference raised `CredentialRejected` before any network call |
| 2 — least privilege exactly | Granted `contents:write`, `issues:read`, `metadata:read`, `organization_projects:write`; drift `[]`. `contents` is `write`, not `read` |
| 3 — repository read and custody | Private repository metadata and issues read with the installation token; a candidate was committed, **pushed and independently read back from a fresh clone with no shared objects**, then the probe branch was deleted |
| 4 — Project resolved live | Project number 2 resolved through the Work Management port with its Status and Priority field identities and all ten / six option identities |
| 5 — fenced projection | Revision 2 written and read back as `IMPLEMENT`; a write carrying superseded revision 1 was **refused** (`stale projection fenced`) and the Project remained `IMPLEMENT` |
| 6 — projection one-way | The Project was read after the write and contributed no execution authority; no canonical state followed the Project |
| 7 — real delivery, at most once | A real GitHub-signed `projects_v2_item` delivery reached the resident ingress through the provisioned endpoint (GitHub recorded `202`); replaying that delivery left its **durable receipt unchanged**, so no second admission occurred; unsigned, wrongly signed and wrong-secret deliveries were each refused |
| 8 — profile composition | The composition loaded from the recorded identities and secret references and bound credentials, repository, Project, ingress, store and doctor |
| 9 — doctor | Against the sandbox: `disposition=PASS`, exit 0, with `work_management`, `source_control`, `provider` and `transport` each `PASS` from live evidence |
| 10a — repository boundary | `repository_selection=selected`, scope exactly the sandbox repository, no isolation finding |
| 10b — Project boundary | Every Project operation resolved to the configured Project; a foreign identity raised `ProjectAddressRejected`; **a real recorded delivery for a Project this profile does not target was refused, and GitHub recorded `401`** |
| 11 — redaction | Verified mechanically across 130 source, test, tool and evidence files against the live App id, installation id, key path, ingress hostname, tunnel id, webhook secret, secret path and key material: **no occurrence**. The evidence still names the sandbox repository and Project |

The sandbox was left as found: the transient probe item was deleted from the
Project and the custody probe branch was deleted from the repository.

## Isolation, stated at the layer each control operates (SWF-34)

- **Repository — permission-enforced.** GitHub itself confines the installation
  to the sandbox repository, and the run read that back rather than assuming it.
- **Project — configuration-enforced.** `organization_projects` is an
  organization permission, so **this BIU makes no claim that the token reaches
  only the sandbox Project**, because the platform cannot provide that. What is
  proven instead: the profile names one Project; every read and every write
  resolved to it; resolution fails closed on mismatch, on a mismatched number
  and on ambiguity; no code path enumerates or opportunistically selects another
  Project; no foreign Project identity appears in the configuration — stated as
  an allowlist, so no production identifier had to be written into this
  repository at all; and a real delivery for another Project was refused.
- The organization-wide grant remains an accepted residual risk of the chosen
  organization topology. PY-10 AC 16 is the compensating end-to-end control.

## Verification-first sequencing (SWF-23 section 4b), and what it caught

The harness was built before the implementation was widened, and the
proven-red matrix was run against it rather than asserted. **It found two tests
that passed for the wrong reason**, which is the whole point of the exercise:

1. `test_an_answer_naming_another_project_is_refused_instead_of_being_used`
   used a foreign Project whose *number* also differed, so the number comparison
   alone could carry it. The identity comparison is now isolated, and removing
   it turns the test red.
2. `test_unusable_credential_material_fails_closed_before_any_live_call` passed
   because empty key material also fails closed deeper in the signer. The test
   now pins the guard it names.

Both were corrected before the implementation was completed, not after a
verifier found them. All 13 guards — the stale-projection fence, projection
read-back confirmation, Project identity resolution, Project field identity,
raw-body signature, foreign-Project refusal, exact least privilege, repository
scope, token staleness, credential fail-closed, bearer-material redaction, the
resident-ingress marker and the RS256 signature — are demonstrated failing when
removed.

## Design notes a verifier should not have to rediscover

- **The App assertion is pure standard library.** The repository has no runtime
  third-party dependency, and this BIU adds none: RS256 is DER parsing plus
  EMSA-PKCS1-v1_5 and one modular exponentiation. Its correctness is not taken
  on trust — `test_signature_verifies_against_the_public_numbers_of_the_signing_key`
  recomputes the verification from the public numbers, and removing the
  signature step turns it red.
- **Test fixtures carry no real identity.** Every App id, installation id,
  Project identity and field identity in the offline suite is synthetic, so the
  offline portion is coupled to no environment.
- **A live `projects_v2_item` delivery names no repository.** The configured
  Project identity is therefore the only boundary such a delivery can be
  admitted against — which is exactly the control SWF-34 requires, arrived at
  from the payload shape rather than imposed on it.
- **The doctor transport probe asks the route for a marker only the shipped
  ingress serves**, so a tunnel answering from any other origin fails the probe
  rather than passing it. The probe identifies itself by user agent: an
  unidentified client is refused by the edge, which would otherwise look like an
  unreachable origin.

## Re-running the bounded live portion

A verifier runs the same two commands on the provisioned host, in its own
worktree, against the same sandbox identities:

```
python3 tools/live/py09b_live_checks.py        # 35 bounded live checks
python3 tools/live/py09b_proven_red.py         # 13 guards, each proven red
```

The live checks require the sandbox profile at
`~/.config/alienintent-sandbox/profile.json`, the sandbox tunnel active, and
the configured ingress port free. Each check is independently diagnosable: a
failure names the one capability that did not hold.
