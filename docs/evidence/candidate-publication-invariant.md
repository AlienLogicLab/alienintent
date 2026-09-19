# Candidate publication invariant — bootstrap evidence

Date: 2026-09-19. Status: bootstrap evidence for the future Python Source Control port.
Origin: AlienIntent Issue #2 (PY-01), first canonical Python implementation BIU.
Authority: Founder decision of 2026-09-19.

## The invariant

```text
IMPLEMENT candidate
  -> durable candidate publication
  -> RESULT=VERIFY accepted
  -> VERIFY
  -> a fresh independent verifier can retrieve the exact candidate
```

A PRODUCER result may not advance to VERIFY unless the exact candidate is durably
identifiable and retrievable by a fresh VERIFIER invocation. For the GitHub-backed
Node bootstrap this means the producer branch must be pushed to the configured
remote before `RESULT=VERIFY` is accepted.

## What happened, and why it is evidence rather than a bug report

On Issue #2 the PRODUCER completed its work, committed
`5b1e3b32a39d20801c5ab007a1ef170e0706bff1` on branch
`b-disp/a3f6708a-6b31-4bf2-8459-95f1dd3763d0`, and signalled `RESULT=VERIFY`. The
dispatcher advanced the item to VERIFY and launched a VERIFIER.

The branch had never been pushed. A VERIFIER receives a fresh worktree created from
the configured baseline ref, so the candidate was unreachable from the verifying
invocation. The verification could not have succeeded even with correct worker
capabilities.

**The PRODUCER was not at fault.** `AGENTS.md` instructed every worker that "a local
commit does not authorize publication or live operation", and the durable assignment
did not authorize a push. The worker obeyed its instructions exactly. The defect was
that no artifact anywhere expressed the requirement that a candidate must be
retrievable before it can be verified.

This is the useful lesson: the missing rule was not in the worker, the provider, or
the dispatcher. It was an unstated invariant sitting between "commit" and "verify",
and it stayed invisible until an independent verifier had to reach for something that
was not there.

## Why the invariant is load-bearing

Verifier independence is an approved architectural property. A verifier that reviews
the producer's own working directory is not independent; it inherits uncommitted
state, local-only objects, and the producer's environment. Requiring a published
candidate is what makes independence mechanically achievable rather than aspirational:
the verifier names a remote ref, retrieves exactly that, and reviews it.

It also makes the candidate immutable in the relevant sense. A pushed ref with a named
SHA is a fixed object that the review, the result and any later audit can all cite. A
local commit can be amended, rebased or discarded with the worktree, and the Issue #2
worktree survived only because a stray `.pytest_cache/` tripped the cleanup check and
caused it to be retained.

## Requirements for the Python Source Control port

The Python implementation must enforce this in the execution path rather than rely on
worker instructions:

1. **Publication is a precondition of accepting `RESULT=VERIFY`**, checked by the
   control plane, not requested of the worker.
2. **The published ref and its SHA are recorded as part of the candidate identity** and
   carried with the invocation, so the verifier is told exactly what to retrieve.
3. **A result naming an unpublished candidate is rejected** and the lifecycle does not
   advance.
4. **Candidate publication is distinct from release publication.** Pushing a candidate
   branch must not imply authority to merge, deploy, operate live, or write to a
   protected branch.
5. **The source-control port abstracts "publish candidate" and "retrieve candidate"** so
   a non-Git backend can satisfy the same invariant.

## Repair applied to the Node bootstrap

Narrow and documentation-only. `AGENTS.md` now states the invariant and distinguishes
candidate publication from release publication. No Node runtime source, dispatcher
logic, or provider adapter was changed; Node remains frozen under Authority §42.

The Issue #2 candidate was published after the fact using the authorized PRODUCER
identity, preserving the exact existing commit rather than rerunning implementation.
