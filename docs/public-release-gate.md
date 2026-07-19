# Agent Watchbench Public-Release Gate

Date: 2026-07-19

Agent Watchbench stays private until every gate item below is complete and
recorded. This gate applies before any repository visibility change, tag,
GitHub release, package registry publishing, hosted service, external scan,
production integration, or social/blog posting.

## Checklist

- Run a repository secret scan and record the command and result.
- Confirm checked-in examples and fixtures contain no raw private logs, real
  user data, tokens, credentials, cookies, private keys, OAuth material, or
  private identifiers.
- Confirm the README covers local-only scope, hostile-input handling, and the
  rule that commands copied from external input are summarized rather than
  executed.
- Run unit tests or a fixture-backed scan locally and record the passing
  evidence.
- Keep package registry publishing, hosted service deployment, external
  scanning, production integration, and social/blog posting out of scope unless
  each action is separately approved.
- Record provenance for the reviewed prototype source and the verification
  evidence used for the release decision.

## Rollback

If any gate item fails, keep `superdoccimo/agent-watchbench` private, do not tag
or release the repository, and open a follow-up issue with the failed item,
evidence path, and smallest next review step.
