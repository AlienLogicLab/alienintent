---
proposal_id: PROP-2026-0011
title: Factory Communications Fabric
submitted_by: founder
submitted_at: 2026-09-23
proposal_type: product_capability
authority_level: unresolved
status: submitted
---

# Factory Communications Fabric

## Intent

Provide durable, attributable communication across Founder and factory participants without
confusing ordinary communication with authority, lifecycle state or private reasoning.

## Proposed capability

A Founder ↔ Factory message board supports status/explanation requests, answers to
questions, decision responses, comments on work/proposals/plans and requests for governed
reprioritization or plan changes. `HumanDecisionRequired` remains a structured authority
event, not ordinary chat.

Agent ↔ Agent operational communication supports delegation, handoff, clarification,
findings, review comments, dependency questions, evidence references, progress/status and
capability discovery. Each durable message preserves sender, recipient/channel, project,
requirement/BIU/invocation correlation, message type, timestamp, thread identity, evidence
references, delivery state and authority. Founder observation may expose intentional
operational communications but never private chain-of-thought.

The core exposes a provider-neutral Agent Communication port. Agent2Agent (A2A) should be
evaluated as an initial standards-based adapter/protocol; A2A remains outside core domain
vocabulary.

## Semantic overlap reconciliation

SF-REQ-006 and SF-REQ-035 own structured authority escalation and the Decision Inbox.
SF-REQ-029 owns observable trajectory/evidence, including no private chain-of-thought.
This fabric may emit durable observations to trajectory and route authority events to the
Decision Inbox, but none of those requirements cleanly owns bidirectional operational
communication or its provider-neutral port. A new canonical capability is likely, pending
intake and Founder authority.

## Scheduling

Deferred until Factory core is sufficiently complete and hardened. Priority and Wave are
unassigned; no BIU, implementation/release authority or current Wave 2 change is created.
