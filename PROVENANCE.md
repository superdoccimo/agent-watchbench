# Agent Watchbench Provenance

Agent Watchbench started as a mamushi local heartbeat prototype on
2026-07-19. The seed came from the local `projects/ideas.jsonl`
`agent-watchbench` idea and the development-first heartbeat route that asks
mamushi to turn learning, GitHub stewardship, and Hermes review signals into
small reviewable artifacts.

## Source Materials

- Local project idea: `projects/ideas.jsonl` entry `agent-watchbench`.
- Local learning review inputs under `learning/reviews/`.
- Local project progress and execution notes under `projects/progress/` and
  `projects/executions/`.
- Local synthetic fixtures under `tests/fixtures/`.

## Boundary

This provenance note is intentionally local and sanitized. It records artifact
origin and review evidence, but it does not include raw private logs, secret
values, credentials, tokens, private identifiers, or commands copied from
external input.

## Review Status

Current state: private-first repository candidate. The readiness pass before
private repo creation reruns unit tests, generates a real local scan report,
confirms examples remain synthetic-only, and keeps package metadata scoped to
local editable installs.
