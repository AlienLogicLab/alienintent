# Node bootstrap webhook contract

This note describes the existing Node implementation at baseline
`b251979a8edd18e031840b0f08639938a6c141bb`. It is source evidence, not a
claim that the full live self-hosting proof has passed.

- **HTTP endpoint:** The [entrypoint](../../bin/alienintent.mjs) uses
  `node:http.createServer` without checking the request URL, so there is no
  restricted webhook path. Requests must use `POST`. The handler buffers the
  raw body, rejects bodies larger than 1 MiB with HTTP 413, and returns HTTP 401
  for a non-POST request or failed signature check after buffering.
- **Authentication:** The entrypoint reads `x-hub-signature-256` and passes the
  raw body buffer to `verifyWebhookSignature` in the
  [dispatcher](../../src/runtime/dispatcher.mjs). The expected value is
  `sha256=` followed by the hexadecimal HMAC-SHA256 of those exact bytes using
  the configured secret. Missing secrets, missing signatures and other prefixes
  fail verification. Equal buffer lengths are required before
  `crypto.timingSafeEqual` compares the complete expected and received values;
  JSON parsing occurs only after authentication.
- **Secret and bind configuration:** The
  [profile loader](../../src/config/profile.mjs) reads `webhook.secretFile`
  from an absolute path as UTF-8 and trims its contents; an unreadable or empty
  secret fails configuration loading. `webhook.listenAddress` and
  `webhook.listenPort` supply the host and port to the entrypoint's `listen`;
  the port must be an integer from 1 through 65535. The Node listener provides
  plain HTTP, so public ingress routing and TLS termination are external
  deployment responsibilities.
- **Subscriptions and actions:** The
  [GitHub App client](../../src/github/app-client.mjs) preflight requires both
  `issue_comment` and `projects_v2_item` subscriptions on the App registration
  and installation. The dispatcher's `acceptEvent` requires
  `x-github-delivery` and selects the event using `x-github-event`.
  `issue_comment` processing accepts only action `created`; result routing
  checks repository, Issue, invocation signal and the configured worker author.
  `projects_v2_item` processing selects action `edited` with a `Status` field
  change to `IMPLEMENT`, `VERIFY` or `ACCEPT` (normalized to uppercase), and
  requires item/content identifiers before authority enrichment and routing.
- **Acknowledgment versus execution:** The entrypoint parses authenticated
  JSON, awaits `relay.acceptEvent`, then returns an empty HTTP 202 response
  without inspecting its return value. Unsupported or irrelevant events can
  therefore receive 202 too. JSON parsing or relay exceptions produce HTTP 500.
  A 202 is not evidence of a worker launch, accepted workflow result, completed
  assignment or successful live proof; those require the dispatcher's separate
  authority, execution and durable-result evidence.
