# AlienIntent documentation

AlienIntent keeps autonomous software engineering aligned with intent, evidence,
and outcomes. It is developed by Alien Logic Lab.

- [Operations and installation contract](operations.md)
- [Repository-state admission](operations/forward-momentum.md)
- [Bounded work packet template](templates/work-packet.md)
- [Governing agent directive](migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md)
- [Name and organization decision](decisions/2026-09-18-alienintent-name-and-organization.md)

## Where a document belongs

| Directory | Holds |
|---|---|
| `decisions/` | canonical decision records only |
| `proposals/` | submitted proposals, immutable provenance |
| `research/` | research, prior-art and strategy analysis |
| `strategy/` | strategic direction that guides but does not authorize |
| `evidence/` | verification and proof records |
| `architecture/` | architecture authority and contracts |
| `work-units/` | BIUs, plans and planning notes |

## Document hygiene rules

1. `decisions/` holds canonical decision records — not drafts, working notes or filename-version variants.
2. Authority is stated inside the document, never by a `-v2`, `-updated`, `-final`, `-new` or `-copy` suffix.
3. Supersession is explicit and traceable: the superseding document says **Supersedes:** and the superseded one says **Superseded by:**, each linking the other.
4. A proposal stays provenance; it never becomes the canonical decision. Canonicalizing one produces a separate decision record and records the mapping.
5. Research and strategy material is distinct from binding decisions, even when a Founder wrote it.
6. Documentation directories are lowercase.
7. No two repository paths may differ only by case.
8. Each document has exactly one canonical path.
9. Relocating a document updates every inbound reference in the same change.
10. Cleanup never resolves a substantive authority conflict silently — it stops and reports the conflict.

The configuration example uses synthetic identities and paths. Installation secrets,
private profiles and runtime state belong outside the repository. Documentation
of a supported contract does not establish that a particular live installation has
passed its operational proof.
