# AlienIntent

**Stop managing agents. Run a software factory.**

AlienIntent is an open-source autonomous software factory from **Alien Logic Lab**.

Most AI coding systems optimize for the next prompt, the next patch, or the next agent turn. AlienIntent is being built to optimize for something less glamorous and much more useful:

> **Finished software that still matches the intent that started the work.**

That means turning product intent into bounded engineering work, ordering that work intelligently, assigning it to capable workers, verifying the result independently, preserving evidence, recovering from failures, and learning which parts of the process should stop requiring model judgment at all.

AlienIntent is not trying to be another coding assistant.

It is trying to make the software-development loop itself autonomous.

---

## What AlienIntent is

AlienIntent treats software development as a production system.

A product requirement is not "done" because an agent wrote code. It is done when the required behavior exists, the evidence supports it, independent verification accepts it, and the result has been closed operationally.

The canonical lifecycle is:

```text
CAPTURE → SPECIFY → PLAN → TASKS → READY
        → IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE
```

The unit of product progress is the **requirement**.

The unit of autonomous execution is the **Bounded Implementation Unit (BIU)**: a deliberately constrained implementation contract carrying scope, dependencies, acceptance obligations, verification obligations, authority, budget, custody, and evidence requirements.

The factory's job is to keep those two things aligned.

### Humans govern intent. The factory executes it.

AlienIntent is autonomous at the execution layer, not at the authority layer.

Humans retain authority over product requirements, architecture, priorities, scope, boundaries, policy, and decisions that genuinely require human judgment. The factory turns those decisions into bounded executable work. Agents implement, gather evidence, independently verify, repair rejected candidates, and complete work within the authority they were given.

An agent does not acquire product authority merely because it can write code. When required authority is missing or genuinely ambiguous, the factory should stop at that boundary and ask for a decision instead of inventing one.

### Review is native to the factory

AlienIntent does **not** use pull requests as the review mechanism for its autonomous execution path. Pull requests are a human-oriented collaboration container; AlienIntent performs review as a factory operation against an exact candidate.

```text
bounded authority
    ↓
PRODUCER
    ↓
exact candidate SHA
    ↓
deterministic evidence and feature regressions
    ↓
independent VERIFIER
    ↓
repair if rejected
    ↓
ACCEPT
    ↓
direct landing of the accepted candidate
    ↓
DONE
```

**No PR does not mean no review. It means review is native to the factory.**

The accepted candidate is landed directly while preserving candidate identity and retained evidence. Human intervention is reserved for authority, intent, and decisions that cannot be resolved mechanically within the approved boundaries.

---

## The core idea

AlienIntent is built around a few opinions that are intentionally hard to dilute:

- **Activity is not progress.** A busy factory that never finishes the highest-priority requirement is failing.
- **Intent survives decomposition.** Priority, scope, dependencies, acceptance obligations, and verification obligations do not disappear because work was split into smaller tasks.
- **Agents are workers, not authority.** Product and architecture authority remain explicit.
- **Verification should be independent.** The worker that produced the change does not get to declare its own work correct.
- **Known failures should become machinery.** If the same reasoning keeps recurring, compile it into deterministic checks instead of paying a model to rediscover it.
- **Evidence beats vibes.** Candidate identity, test results, provenance, read-back, and closure receipts matter.
- **"Done" should be expensive to fake.**
- **Recovery is part of the product.** Crashes, missing outcomes, stale work, duplicate events, provider failures, and restarts are normal factory conditions, not exceptional stories.

---

## What the Python factory already contains

AlienIntent is under active pre-1.0 development, but the Python architecture is real and growing quickly.

The current codebase includes bounded contexts for:

- **Execution Coordination** — lifecycle orchestration, requirement-focused scheduling, bounded retries, reservations, release admission, and worker coordination.
- **Invocation Runtime** — real/test worker invocation, exact-candidate result correlation, process supervision, durable outcome read-back, and recovery semantics.
- **Context Assembly** — requirement inventory, ambiguity handling, decomposition inputs, compilation checks, and readiness preparation.
- **Evidence & Learning** — proof planning, immutable evidence, regression receipts, retained observations, and learning inputs.
- **Control Plane** — operator-facing commands and durable control operations.
- **Installation** — profile/identity/credential boundaries and installation validation surfaces.
- **Composition** — explicit assembly of production and test profiles without burying authority inside adapters.

The CLI currently exposes:

```text
alienintent version
alienintent status
alienintent health
alienintent doctor
alienintent explain
alienintent run
alienintent resume
alienintent stop
alienintent cancel
alienintent reconcile
alienintent decisions
```

Run:

```bash
alienintent --help
```

for the current command surface.

---

## What we are building next

The next several weeks are focused on turning the architecture into a continuously operating, self-hosted Python factory.

### Continuous autonomous execution

AlienIntent will continuously pull from READY work, honor requirement priority, order work by dependency topology, refill available capacity, and keep progressing without requiring a human to babysit each transition.

The scheduling objective is simple:

> **Finish the highest-priority unfinished requirement as quickly and safely as possible.**

Not "keep every agent busy."

### Requirements → executable BIUs

The factory is being built to ingest structured product requirements and compile them into bounded implementation contracts with:

- preserved requirement identity;
- inherited priority;
- dependency structure;
- acceptance criteria;
- verification obligations;
- capability requirements;
- budgets;
- authority boundaries;
- evidence requirements.

The goal is to make "what should the agent do?" a compiled artifact, not an improvisation.

### Independent producer / verifier roles

AlienIntent separates implementation from verification.

A producer publishes an exact candidate. A fresh verifier retrieves that candidate independently, runs deterministic feature regressions, evaluates the acceptance obligations, and either accepts or sends findings back for bounded repair.

No self-certification.

### VERIFY that gets smarter over time

AlienIntent's VERIFY stage is designed to accumulate enforceable knowledge.

A failure discovered once by qualitative review should, where practical, become a feature-level regression check that runs automatically on future relevant changes.

That turns experience into machinery.

The long-term target:

```text
novel failure
    ↓
review finding
    ↓
proven regression
    ↓
deterministic VERIFY rule
    ↓
future model tokens not required
```

### Crash-safe execution and deterministic recovery

The factory is being hardened around real failure modes:

- worker exits without a durable result;
- background work outlives a provider session;
- duplicate or delayed outcomes;
- stale commands;
- unknown external effects;
- lost events;
- process restarts;
- provider/capacity failures;
- interrupted closure;
- partial work with uncertain ownership.

If ownership is unknown, replacement should not create duplicate effects. If ownership is conclusively dead and the result is missing, recovery should proceed deterministically within bounded authority.

### Candidate custody and evidence

AlienIntent tracks the exact implementation under review.

The factory is being built to retain:

- baseline revision;
- candidate branch and full SHA;
- producer identity;
- verifier identity;
- test/proof commands;
- expected and observed results;
- feature-regression receipts;
- evidence provenance;
- closure receipts;
- retained history across repair cycles.

"Looks like the same code" is not custody.

### Provider-neutral execution

AlienIntent is designed so the factory can route work across different model/provider combinations without making the core lifecycle provider-specific.

Planned routing features include:

- provider capability discovery;
- model/task compatibility;
- cheapest-capable routing;
- fallback/escalation providers;
- per-task cost and latency evidence;
- evidence-derived routing recommendations.

The core should care about worker contracts and durable outcomes, not vendor-specific folklore.

### Deterministic Test Worker

AlienIntent includes a deterministic worker implementation that exercises the same worker-facing contract as production workers without model inference or provider cost.

Planned scenarios cover:

- normal success;
- malformed output;
- missing output;
- delayed output;
- duplicate output;
- wrong identity/correlation;
- provider failure;
- crash before output;
- progress then crash;
- restart/resume;
- repair cycles;
- verifier rejection;
- human-decision conditions.

This is not a fake lifecycle. It is a way to torture the real lifecycle without burning tokens.

### Provider-free replay

Recorded events and evidence should be replayable for debugging, recovery, policy testing, and regression without recalling an LMM for outputs the factory already possesses.

### Operator control plane

The operator surface is growing toward:

- status;
- explain;
- run/resume;
- cancel/stop;
- reconcile;
- health/doctor;
- decision handling;
- event and evidence inspection;
- worker/provider visibility;
- cost visibility;
- capability visibility.

The objective is not to make humans micromanage the factory. It is to make intervention precise when intervention is actually required.

### Decision Inbox

Human decisions should arrive in one place with enough context to decide without reconstructing an agent's entire history.

A decision should be durable, attributable, and capable of automatically unblocking the waiting work.

### Factory yield and economics

AlienIntent is being instrumented around outcomes that matter:

- time per completed requirement;
- tokens per completed requirement;
- BIUs per completed requirement;
- repair cycles;
- verifier cycles;
- human interventions;
- provider/model cost;
- latency;
- first-pass acceptance;
- failure/recovery patterns.

The factory should get cheaper and more predictable as it gains evidence.

### Engineering Trajectory & Quality Evidence

AlienIntent will retain enough structured engineering history to answer questions such as:

- What changed?
- Why did it change?
- Which requirement caused it?
- What evidence supported the decision?
- Which worker/model produced it?
- What failed before it passed?
- Which regressions now protect it?
- What should future routing learn from this outcome?

### External creation-artifact intake

AlienIntent is also being designed to consume artifacts from frontier creation tools without treating those artifacts as authority.

Planned intake modes include:

1. **Intent / prototype input** — extract requirements and behavior.
2. **Candidate implementation input** — productionize externally generated code.
3. **Reference input** — mine ideas without granting execution authority.

This creates a path from prototypes, generated applications, design artifacts, and external agent output into the same governed factory.

### Installer, Doctor, and dashboard

The intended self-hosted experience is much simpler than the current developer setup:

```bash
alienintent init
alienintent doctor
alienintent run
```

`alienintent init` is planned to discover and configure as much as possible.

`alienintent doctor` is being expanded to validate work-management access, source control, credentials, providers, external capabilities, persistence, lifecycle mapping, transport, and execution readiness before autonomous work begins.

A dashboard is planned for:

- queued / active / completed work;
- WIP and capacity;
- current workers and models;
- lifecycle stage;
- elapsed time;
- cost;
- decisions;
- evidence;
- integration health;
- factory trajectory.

### Hosted AlienIntent

The architecture preserves a future hosted model in addition to self-hosting.

A hosted flow could eventually become:

```text
Install AlienIntent
→ choose organization
→ choose repositories
→ approve permissions
→ factory online
```

Self-hosting will remain a first-class path.

### Community learning

A later learning layer is planned for opt-in sharing of generalized/anonymized quality and provider evidence without requiring proprietary source code, secrets, or sensitive project content.

The goal is to let factories learn from factories without turning private engineering history into a public dataset.

---

## Architecture

AlienIntent's Python implementation follows:

- **Domain-Driven Design**
- **Hexagonal architecture**
- explicit bounded contexts
- explicit ports/adapters
- anti-corruption layers around external systems
- provider-neutral core contracts
- immutable evidence where possible
- versioned operational state
- deterministic checks before cognition

The architectural rule is straightforward:

> **External systems are adapters. Product intent belongs in the core.**

See:

- [`docs/decisions/alienintent-architectural-reset-and-separation.md`](docs/decisions/alienintent-architectural-reset-and-separation.md)
- [`docs/decisions/alienintent-software-factory-plan.md`](docs/decisions/alienintent-software-factory-plan.md)
- [`AGENTS.md`](AGENTS.md)

---

## Installation

AlienIntent is currently **pre-1.0** and evolving quickly. Python **3.12+** is required.

### Option 1 — editable development install

```bash
git clone https://github.com/AlienLogicLab/alienintent.git
cd alienintent

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

Then:

```bash
alienintent --help
alienintent version
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

### Option 2 — Install the local checkout as a CLI tool

If you use `pipx`:

```bash
git clone https://github.com/AlienLogicLab/alienintent.git
cd alienintent
pipx install .
```

If you use `uv`:

```bash
git clone https://github.com/AlienLogicLab/alienintent.git
cd alienintent
uv tool install .
```

These install the current source checkout. Packaged release distribution is still part of the productization work.

### Smoke-test the installation

```bash
alienintent --help
alienintent version
```

For development, prefer an isolated virtual environment and keep operational credentials/state outside the repository.

### Self-hosting

Full autonomous self-hosting currently requires developer-level configuration of work management, source control, identities/credentials, providers, persistence, and execution policy.

That setup is being collapsed behind the planned:

```bash
alienintent init
alienintent doctor
```

Until then, expect the self-hosted path to move quickly.

---

## Contribution policy

AlienIntent is public so people can inspect it, learn from it, test it, and fork it. **External code contributions are not open yet.**

For now:

- feel free to fork the repository and experiment independently;
- feedback, bug reports, edge cases, and deployment experience are welcome;
- do not open a pull request unless the Founder has explicitly invited or authorized that contribution;
- unsolicited pull requests will not be merged;
- changes to the canonical AlienIntent repository remain Founder-gated while the architecture and autonomous factory are still moving quickly.

This policy is separate from AlienIntent's internal execution architecture. The factory itself does not use pull requests for autonomous implementation or verification. If external contribution mechanics are opened later, that will be a repository-governance decision, not a change to the agent-native review model.

### Running the test suite

If you fork AlienIntent or are working on an authorized change, install the test runner with:

```bash
python -m pip install pytest
```

Run the tests relevant to your change. The full Python suite is:

```bash
python -m pytest -q
```

If you modify a protected feature surface, the applicable feature-regression pack matters as well.

---

## Feedback wanted

AlienIntent is being built in public because this problem is bigger than one codebase.

We want criticism. We want edge cases. We want people who have watched autonomous coding systems do impressive work and then quietly lose the plot three hours later.

But **positive feedback is useful too**.

If the direction makes sense to you:

- **Star the repository.**
- Open an Issue with the workflow you want AlienIntent to handle.
- Tell us which planned capability would make you actually deploy it.
- Tell us what already feels right.
- Tell us where the architecture is too heavy.
- Tell us where it is not strict enough.

A detailed "this would save my team real time because..." is more valuable than generic applause.

And if AlienIntent eventually runs one of your projects for days without you having to ask **"why did the agent stop?"**, we definitely want to hear about that.

---

## Project status

AlienIntent is **active, pre-1.0, and not yet a finished turnkey autonomous factory**.

The Python core and CLI are under rapid development. Interfaces may change. Some roadmap capabilities described above are implemented in part, some are actively being integrated, and some are planned for upcoming waves.

The project is intentionally public before it is polished.

That is the point.

---

## License

Apache License 2.0.

See [`LICENSE`](LICENSE).

---

**AlienIntent is built by [Alien Logic Lab](https://alienlogiclab.com).**

**Software agents are getting better. The process around them needs to get much better too.**
