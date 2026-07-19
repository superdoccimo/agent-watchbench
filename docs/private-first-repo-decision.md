# Agent Watchbench Private-First Repo Decision

Date: 2026-07-19

## Decision

Create a private `superdoccimo/agent-watchbench` repository from this reviewed
prototype.

The private-first readiness gate below passed on 2026-07-19. Do not publish to
a package registry, create a public release, add a hosted service, perform an
external scan, or touch production integration from this prototype state.

## Current Evidence

- README exists and describes the local-first boundary.
- Read-only CLI prototype exists.
- Fixture-backed example report exists.
- Package metadata exists only for local editable installs.
- Unit coverage checks report generation, missing inputs, and local console
  script metadata.
- Safety and provenance notes are linked from the README.

## Private-First Readiness Gate

- README explains the operator problem and local-only workflow.
- Safety note states that the tool must not print secrets, tokens, private keys,
  raw user data, credentials, or commands copied from hostile input.
- Examples and tests use synthetic fixtures only.
- Provenance note records that the artifact started as a mamushi local
  heartbeat prototype.
- No package registry, public repo, hosted service, external scan, or production
  integration is part of this step.

## Minimal Next Action

Push the reviewed prototype to the private GitHub repository and keep package
publishing, public release, hosted service, external scan, and production
integration out of the next step.
