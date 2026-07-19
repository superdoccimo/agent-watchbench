# Agent Watchbench Release-Candidate Evidence

Date: 2026-07-19
Scope: private release-preparation evidence for `superdoccimo/agent-watchbench`

Agent Watchbench remains private. This note records the current release-candidate
evidence without changing repository visibility, tagging, creating a GitHub
release, publishing a package, deploying a hosted service, running an external
scan, integrating production, changing credentials/OAuth, or posting socially.

## Candidate

- Candidate commit: `22d85dbe42d17f45abff65dab36d7ca9437cd477`
- Source PR: `https://github.com/superdoccimo/agent-watchbench/pull/6`
- Main CI run: `https://github.com/superdoccimo/agent-watchbench/actions/runs/29684624194`
- CI result observed: `completed` / `success`
- Repository visibility observed during the prior merge verification: `PRIVATE`

## Evidence Snapshot

- GitHub Actions ran the read-only synthetic fixture gate on `main`.
- The workflow kept `contents: read` permissions.
- The workflow compiled `agent_watchbench.py`.
- The workflow ran `python -m unittest discover -s tests -v`.
- The workflow regenerated the synthetic fixture report from
  `examples/fixture-root` and diffed it against `examples/fixture-report.md`.
- Local post-merge verification for the same candidate recorded 10 passing
  tests, the exact fixture diff, and a clean whitespace diff check.

## Remaining Release Gate

Before any public visibility change, tag, GitHub release, package registry
publishing, hosted service, external scan, production integration, or social/blog
posting:

- Run and record a repository secret scan.
- Reconfirm checked-in examples contain only synthetic fixture data.
- Reconfirm README, `SAFETY.md`, `PROVENANCE.md`, and
  `docs/public-release-gate.md` still describe the local-only hostile-input
  boundary.
- Re-run local tests and the fixture report diff on the final candidate commit.
- Re-check the GitHub Actions fixture gate on the final candidate commit.

## Decision

This is a reviewable release-candidate evidence packet, not a release approval.
If any gate item changes or fails, keep the repository private and open the
smallest follow-up issue with the failed evidence item and next verification
step.
