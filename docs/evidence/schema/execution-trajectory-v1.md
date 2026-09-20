# Execution Trajectory v1

An Execution Trajectory is append-oriented factual event data for one BIU. It records observations and their provenance; it does not declare quality conclusions.

Each JSONL line is one event. Required in every event: `schema_version` (`"1.0"`), `event_id` (unique within the file), `project`, `biu_id`, `event_type`, `actor_role`, `evidence_refs` (nonempty), and `recorded_at` (UTC ISO-8601). All other fields are optional because they are not meaningful for every event.

`candidate_ref` is provider-neutral candidate identity; `candidate_type` may identify a source revision, local artifact, archive, or another durable form. `branch` and `commit_sha` are optional source-control detail, not candidate requirements. `invocation_id` identifies an execution attempt independently of candidate identity. `lifecycle_from` and `lifecycle_to` are used when the event observes a lifecycle change. `authority_ref` identifies the durable decision that authorized or resolved an action.

`observation_type` distinguishes worker claim, independent verification, Git observation, CI observation, state-record observation, and derived timestamp arithmetic. `verified` means this recorder independently located the cited durable evidence; it does not turn a worker claim into a reproduced result.

`token_usage` and `cost` accept an object with native provider fields, or the literal `"UNKNOWN"`. Missing is not zero. A known partial amount must state its scope; it must not be represented as end-to-end cost. `elapsed_seconds` is a nonnegative measured interval with a definition in `description` when its endpoints are not self-evident.

Recommended event types include `BIU_RELEASED`, `INVOCATION_STARTED`, `CANDIDATE_PUBLISHED`, `VERIFICATION_STARTED`, `VERIFICATION_REJECTED`, `FINDING_RECORDED`, `REWORK_STARTED`, `VERIFICATION_ACCEPTED`, `HUMAN_DECISION_REQUIRED`, `HUMAN_DECISION_RECORDED`, `CANDIDATE_LANDED`, `POST_MERGE_VERIFIED`, `INVOCATION_CAPACITY_FAILED`, and `BIU_DONE`. New factual event types are permitted; conclusions belong in Quality Evidence.
