# Work unit: registering hand-written packets, importing earlier work, and reading the record

**Label:** `WORK-REGISTRATION-AND-FAMILY-HISTORY` (the document label is kept for continuity with the split record; the permanent identifier is created by the identity service when this packet is registered).
**Status:** Draft for independent review, 2026-10-02 (revision 9 — checked against the landed sibling; Issue 153's commit is on `main`; release, not assessment, waits until the parent packet and this packet are on `main`; section 13). Revision 7 followed the sibling's revision 11: `work import` calls the sibling's `import_completed`, an explicitly authorized historical record; the kind stays `issue`; `git show` failures in `show` are the typed `GIT_READ_FAILED` (section 17). Not approved; assessed HOLD at `ddd6f22` for its dependencies; not released. Submitted after its sibling, [`IDENTITY-SERVICE-AND-COMPILER-CONNECTION`](identity-service-and-compiler-connection.md), on which it depends.
**Origin:** parent [`IDENTITY-SERVICE-AND-REGISTRATION`](identity-service-and-registration.md) at commit `269c87c`; the private evidence records under `/home/netmarine/.local/state/alienintent/manual/identity-registration-agent-ready-269c87c/` (retained by the Founder on the Founder's machine and supplied to the VERIFIER on request; outside the repository, never published): `native-result.json` (sha256 `c4286813c8bcdf968a96a9904d35b838558f953d84fb1a6c4ea603253811e730`), `independent-review.md` (sha256 `02cf1c48d6d3d02727bbf2eda93a11d246f7b24ce6606c102d3756c6268bf4ee`) and `simplified-children-review-f8ce1a0.md` (sha256 `d20c50506cd0d4b49b9d01b2e8e5dc033c1e40813d96a5af505a9a0f8a6d803f`); formal design 6.1A and 6.1C; canonical plan 2.3; the Founder's directions of 2026-10-01 (path document section 4).
**Position on the path:** unit 1b of [the shortest dependency path](python-execution-path-20260930.md).
**Authority:** formal design section 5, 6.1, **6.1A**, **6.1C**, 7.1–7.3; canonical plan section 2.3.
**Roles:** one PRODUCER (reviews its own complete change before handing it over); one fresh VERIFIER checks the exact published candidate; a REVIEWER performs the independent design review; a separate CLOSURE instance lands the accepted candidate.

## 0. The whole design (plain English)

The sibling gives every piece of work one row: identifier, request reference, label, optional parent, state, a pointer to the packet's repository, path and exact commit, and references to assessment, approval and verification evidence. This unit adds the three operations people need and nothing else:

- **`work register`** — registers a hand-written packet: one row pointing at the packet's exact commit, with an optional parent when the packet is a split child. The packet text and every later revision live in Git. Registration creates nothing but the row.
- **`work import`** — records earlier completed work (Issue 153) as a row at `DONE`, pointing at the packet commit it was done against, with its existing evidence references. Nothing is invented.
- **`work show`** — reads one row, its parent, its children and the packet at the pinned commit.

Editing a packet is a new commit and changes nothing in the table. Moving a row's pointer to a newer commit — making changed instructions executable — is a controlled operation with renewed assessment and approval, owned by the later assessment unit; this unit does not move pointers.

**Design basis (Founder, 2026-10-01):** Git for text and history; no version table; the fewest parts.

### Problem-to-safeguard table

| Rule | Failure it prevents | Required behavior | Check |
| --- | --- | --- | --- |
| Registration is a pointer, not a copy | packet text duplicated into the database and drifting from Git | the row holds repository, path, commit; `show` reads the text from Git at that commit | 1, 4 |
| The commit holds exactly the registered instructions | a pointer at the baseline, a branch head or an edited working copy | the operator supplies the packet file; the sibling's adapter requires `git show <commit>:<path>` to be byte-equal to it (`POINTER_MISMATCH`) and the commit retained (`COMMIT_NOT_RETAINED`) | 1, 3 |
| A new commit authorizes nothing | an edit becoming executable without assessment | no operation here moves a pointer | 4 |
| Optional parent by identifier | a forced parent; lineage in text | `parent_id` only when the document names a registered parent | 2 |
| Import without invented history | manufactured assessments or approvals | import records the pointer, `DONE`, and the evidence references the operator gives, as given; none are invented | 3 |
| Repeat changes nothing; all or nothing | duplicate rows; half-written registrations | the sibling's transaction and unique `request_ref` | 1, 3 |

## 1. What is wrong today (verified in code at `origin/main` `7901011…`)

No record exists for any real work item; the executor reads Issue text (`src/alienintent/composition/sandbox_run_profile.py` lines 80–98, 174–209) and fetches instructions from a branch head rather than an exact commit (line 205).

## 2. One observable result

After this unit: (a) `alienintent work register --file <packet.md> --repo <name> --path <path> --commit <40 hex> --label <label> [--parent <id>] [--kind BIU]` creates the row or returns the existing one, only if Git at that commit holds exactly the file's bytes; (b) `alienintent work import --repo <name> --path <packet.md> --commit <40 hex> --label PY-SELF-00 --issue 153 --assessment <ref> …` records Issue 153 at `DONE`; (c) `alienintent work show <id or label>` returns the row, parent, children and the packet text at the pinned commit; (d) repeating any command changes nothing; a crash leaves nothing.

## 3. Exact starting revision

The landed revision of the sibling on `main`; the PRODUCER pins the then-current `main` at release.

## 4. Existing components being reused

| Component | Reused for | Where |
| --- | --- | --- |
| `WorkIdentityService` and the `WorkItemRepository` port (`transaction`, `register`, `import_completed`, `find`, `children`), the `work_item` row, the `git` retrievability check | everything written | the sibling |
| `git show <commit>:<path>` (in the sibling's adapter) | reading the packet at the pinned commit | — |
| Evidence repository `Ref` | the three evidence references | `evidence_learning/domain/records.py` |
| Operator CLI and control plane | the three commands | `control_plane/adapters/cli.py`, `control_plane/application/operator.py` |

## 5. Rules (domain: `domain/work_registration.py`)

- The instructions being registered are the bytes of the packet file the operator names; the sibling's `register` retrieves `<commit>:<path>` and refuses unless byte-equal, so an uncommitted edit, a wrong commit or the implementation baseline can never be registered as the packet.
- `request_ref` for a hand-written packet is `packet:<repo>/<path>` — the stable location of the document, independent of its commit, label or parent. For an import it is `issue:<n>`.
- `label` is what `--label` says; no prose is parsed.
- `parent_id`, when given, must name a registered row (the sibling's foreign key); the relationship is the `--parent` argument, not text in the packet. The split's obligation accounting is the content of the packets, assessed by Agent Ready against the exact commits; it is not a database rule.
- Import records the evidence references the operator gives (`--assessment`, `--approval`, `--verification`), as given and possibly none; state is `DONE`; nothing else is written and nothing is invented.
- `show` never moves a pointer.

## 6. Sequences

**`work register --file <packet.md> --repo <name> --path <path> --commit <40 hex> …`**: read the file's bytes → `register("packet:<repo>/<path>", label, kind, parent_id, (repo, path, commit, bytes))` in the sibling's transaction (which performs the byte comparison and the retained-ref check) → return the row. A repeat returns the existing row unchanged, whatever the arguments.
**`work import`**: read the file's bytes → the sibling's `import_completed("issue:<n>", label, kind, (repo, path, commit, bytes), the given evidence references)` — one transaction: the same byte comparison and retained-ref check, the row created at `DONE` as an explicitly authorized historical record with exactly the given evidence references; no transition, no invented step or approval. A repeat returns the existing row unchanged, whatever the arguments.
**`work show`**: one read transaction: `find`, the parent row, `children`; then `git show <commit>:<path>` (an unexpected failure of that call is `GIT_READ_FAILED`, naming the path, as a read error — nothing to roll back). Three statements and one `git` call.

## 7. Behavior after each relevant completion

Same command → the same row, no change. A new commit of the packet → no change. A split: the child's packet is registered with `--parent`; the parent's row is untouched. Retired or `DONE` rows keep everything.

## 8. Restart and missed-signal recovery

A crash inside a transaction leaves nothing; a rerun completes. No pending state.

## 9. Failure behavior

`POINTER_MISMATCH`, `COMMIT_NOT_RETAINED`, `PARENT_NOT_REGISTERED`, `GIT_READ_FAILED`, the sibling's other refusals → rolled back, nothing written. `UNKNOWN_IDENTITY` is a read answer. `PUBLICATION_FAILED` from `work register` or `work import` means the row was saved but its tag and commit did not reach the remote; rerunning the same command returns the same row and completes publication. `work show`'s own `git show` failure is `GIT_READ_FAILED` as a read error, not a rollback (nothing was being written).

## 10. Permissions and prohibited actions

Permitted: sections 11–12. Prohibited: creating identifiers outside the sibling's service; moving a pointer; storing packet text in the database; GitHub reads or writes; assessment attempts or approvals; advancing state beyond `CAPTURE` except `DONE` on import; manufacturing evidence; `subprocess`, `uuid`, `datetime` or `time` in domain or application code.

## 11. Exact permitted production files

| File | Change |
| --- | --- |
| `src/alienintent/context_assembly/domain/work_registration.py` (new) | the rules of section 5 |
| `src/alienintent/context_assembly/application/work_registration.py` (new) | the three operations, in a class whose name differs from the compiler's existing `WorkRegistration` (`initial_compilation_service.py`) |
| `src/alienintent/context_assembly/adapters/work_item_repository.py` | `git show` for reading the packet (the sibling's adapter already runs `git`) |
| `src/alienintent/composition/work_registry.py` | the registration service, exposed on `WorkRegistry` under a new attribute (the existing `registration` attribute, the compiler's `WorkRegistration`, is left as it is); and one no-argument profile factory for the CLI's existing `--profile-factory`, which reads two required environment variables, `ALIENINTENT_PROJECT_CONFIGURATION` (the project configuration file path) and `ALIENINTENT_PROJECT` (the project name), passes them to the existing `load_project_configuration`, and exposes `work_registry`; either variable missing is `ConfigurationInvalid`. No new CLI flag, no new configuration format, no default path. Used by check 5; tests use their own factories |
| `src/alienintent/control_plane/adapters/cli.py`, `src/alienintent/control_plane/application/operator.py` | `work register`, `work import`, `work show` |

## 12. Exact permitted test files

`tests/context_assembly/test_work_registration.py` (new); `tests/context_assembly/test_work_identity_service.py`, `tests/composition/test_work_registry.py`, `tests/control_plane/test_cli.py`.

## 13. Dependencies

The landed sibling. For the real-repository check: this packet and its sibling at their landed commits on `main`; for the import check, Issue 153's packet at `2f5d3e4`, on `main` since `175d992`; a row being created has no `work/<id>` tag yet, so its commit must be on the default branch or the packets branch. For the same reason, before the PRODUCER is released, the release owner (the session that releases the PRODUCER) lands one docs-only commit on `main` containing only two files: the parent packet `identity-service-and-registration.md` byte-identical to `269c87c`, and this packet byte-identical to its READY-assessed revision — as `c99fb01` did for the sibling. Check 5 registers the parent packet and this packet at that landed `main` commit. The clone the VERIFIER uses for check 5 must contain it. Issue 153 has no assessment, approval or verification record in the evidence repository (its readiness assessments were bootstrap files under `docs/`, and none names `2f5d3e4`), so the import sets no evidence reference; that absence is the truthful record.

## 14. Acceptance checks (each names the wrong implementation it catches)

1. **Register a packet.** `work register` on this packet at its landed commit creates one row with `request_ref = packet:<repo>/<path>`, the label from the document, `CAPTURE`, no parent, the exact pointer; a repeat returns the same row unchanged; a file that differs by one byte from Git at the commit (an uncommitted edit), or the baseline commit given as the packet commit, is `POINTER_MISMATCH`; a commit on a deleted branch is `COMMIT_NOT_RETAINED`; a fault before `COMMIT` leaves no row; two processes registering it at once end with one row; the database holds no packet text and the evidence repository's record count is unchanged. Catches copies in the database and unverified or wrong-commit pointers.
2. **Optional parent.** Registering the sibling's packet with `--parent` = the parent packet's id sets `parent_id`; `children(parent)` returns it; a `--parent` naming no row is `PARENT_NOT_REGISTERED`; registering without `--parent` leaves it null; retiring the child keeps `parent_id`; nothing parses the packet text for a parent or a label. Catches a forced parent and lineage in text.
3. **Import of earlier work.** Importing Issue 153 at `2f5d3e4` creates a row at `DONE` through `import_completed` (no `set_state` call) with `request_ref = issue:153`, label `PY-SELF-00`, the pointer, and no evidence reference (none exists); importing a fixture item with `--assessment <ref>` stores exactly that reference; a repeat changes nothing; the evidence repository's record count is unchanged by either. Catches manufactured history.
4. **Show.** `show` returns the row, parent, children and the packet text byte-identical to `git show <commit>:<path>`; after a new commit to the path, the row and the text `show` returns are unchanged; a counting wrapper shows three statements and one `git` call regardless of how many commits the path has; a fault-injected failure of that `git show` call surfaces as `GIT_READ_FAILED` naming the path, not a swallowed exception. Catches moved pointers, hidden scans, and a silent infrastructure failure.
5. **Real repository (integration owner of the parent's combined check).** The VERIFIER migrates a verification copy through the sibling, registers the parent packet and both child packets (the children with `--parent`), shows each, reruns as a no-op, commits an edit to one packet on a scratch branch and shows the unchanged pointer and text, and imports Issue 153. No GitHub access.
6. **Existing suites green** plus architecture fitness.
7. **Publication through the commands.** Against a local bare remote configured for the project, `work register` and `work import` each leave the row's `work/<id>` on the remote at the row's commit (the sibling's check 10 tests the operation itself); with the push failing, each command exits non-zero naming `PUBLICATION_FAILED`, the row exists, and rerunning the same command returns the same row, publishes, and exits zero. Catches a command that hides a failed push or cannot complete it by rerunning.

## 15. Required negative checks (VERIFIER mutations)

Store the packet text in the row, or compare digests instead of bytes → check 1 fails. Move the pointer on a repeat with a newer commit → checks 1 and 4 fail. Invent an evidence reference on import → check 3 fails. Derive the parent or the label from the packet text → check 2 fails. Walk the path's history in `show` → check 4's counting case fails. Swallow a failed `git show` in `show` instead of raising `GIT_READ_FAILED` → check 4's fault case fails.

## 16. Claims this unit does not prove

Assessment, approval, verification and the controlled pointer move (the later units, which fill `assessment_ref`, `approval_ref`, `verification_ref` and advance `state`); dispatch; GitHub association; obligation accounting of a split (the content of the packets, assessed by Agent Ready).

## 17. Review record

**Revision 9 (2026-10-02).** Checked against the landed sibling (`main` `73341e3`): its `register`, `import_completed`, `find`, `children` and `Pointer` match this packet. Four facts updated, nothing else: Issue 153's commit `2f5d3e4` is now on `main`; check 5 needs a profile factory exposing `work_registry` (no production composition built one), placed in the already permitted `work_registry.py`; the new service's class name must not repeat the compiler's existing `WorkRegistration`. Fourth: the release owner lands the parent packet (`269c87c`) and this packet (its READY revision) on `main` before release, so check 5's commits are retained. After an independent review (FAIL: the factory's inputs were unstated), the factory's inputs are named, the existing `registration` attribute is kept, and the landing owner and revisions are stated. A second independent review (FAIL: a merge cannot land those exact bytes without unrelated documents) changed the landing to one docs-only commit of the two files, as for the sibling.

**Revision 8 (2026-10-02).** The operation `import_completed` and its own acceptance check are in the sibling, its check 9; this unit supplies the `work import` caller (`3a1f9f5`). Check 7, publication through the commands, was added later at `4889d65` under the same revision number.

**Revision 7 (2026-10-01).** Follows the sibling's revision 11, which restores the Founder's decisions that revision 10 had wrongly changed. `work import` calls the sibling's `import_completed`: an explicitly authorized historical record at `DONE`, with exactly the given evidence, no transition and nothing invented — replacing revision 6's `initial_state="DONE"`. The kind is `issue` again. Kept: `GIT_READ_FAILED` for `show`. Revision 6's `external` rename is superseded.

**Revision 6 (2026-10-01).** An independent adversarial review of the sibling's revision 9 found, among other things, that neither document stated how `work import` reaches `state = DONE` (the sibling's `register` took no state argument), and that the vendor noun "Issue" was a kind literal in the permanent schema. Both are fixed in the sibling's revision 10 and followed here: `work import` now names `register(..., initial_state="DONE")` explicitly; its `request_ref` kind is `external`, not `issue` (the CLI flag stays `--issue`, since it names a real outside number the operator supplies, not a domain concept). The review also named a read-path gap — `show`'s `git show` call had no stated failure behavior — closed here with `GIT_READ_FAILED`.

**Revision 5 (2026-10-01).** The Founder directed Git for packet text and history and the removal of the version table and custom history. This unit shrank to three operations over the sibling's row: register a pointer, import earlier work with its existing evidence, read. The obligation and dependency rules of revisions 2–4 are not database rules any more: they are the content of the packets, assessed against exact commits. **Revisions 2–4:** the single-table-plus-version-table design and its reviews (`f8ce1a0`, `3cca550`; private record `simplified-children-review-f8ce1a0.md`). **Revision 1:** the earlier design (`875bea8`).

Independent reviewer, please check explicitly: correctness (every operation is one transaction over the sibling's row plus `git` reads; nothing here can move a pointer or invent evidence), known antipatterns (copies of Git content in the database, lineage in text, manufactured history), and unnecessary complexity (anything not required by a demonstrated failure).
