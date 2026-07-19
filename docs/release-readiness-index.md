# Agent Watchbench Release-Readiness Index

Date: 2026-07-19
Scope: private release-preparation index for `superdoccimo/agent-watchbench`

Agent Watchbench remains private. This page is a reviewer entry point that links
the current safety, provenance, fixture, and release-candidate evidence without
approving a public release, package publish, hosted service, external scan,
production integration, credential change, or social/blog post.

## Review Map

- Public-release gate: `docs/public-release-gate.md`
- Safety boundary: `SAFETY.md`
- Provenance: `PROVENANCE.md`
- Release-candidate evidence: `docs/release-candidate-evidence.md`
- Synthetic fixture report: `examples/fixture-report.md`
- Synthetic secret-scan report: `examples/secret-scan-report.md`
- Content-redacted fixture audit: `examples/fixture-audit-report.md`

## Current Gate State

- Current candidate commit: `307e4f6fd84324bf567869209a84b7d3a34f7211`
- Current main CI run:
  `https://github.com/superdoccimo/agent-watchbench/actions/runs/29692314708`
- Current CI result observed: `completed` / `success`
- Repository visibility stays private until the public-release gate is reviewed
  on a final candidate commit.
- Checked-in examples are synthetic fixtures only and are reviewed through a
  content-redacted fixture audit.
- Secret-scan fixture evidence reports locations and finding kinds, not matched
  values.
- CI evidence is useful review input, but it is not release approval.
- A release decision still needs a final local test run, regenerated fixture
  diffs, repository visibility check, and GitHub Actions check on the candidate
  commit.

## Stop Conditions

Stop and open a follow-up issue instead of releasing if any final candidate
check finds raw private logs, real user data, tokens, credentials, cookies,
private keys, OAuth material, private identifiers, failing tests, stale fixture
reports, failed CI, or unclear provenance.

## Next Review Step

Before any visibility change, tag, GitHub release, package registry publishing,
hosted service, external scan, production integration, credential/OAuth change,
or social/blog posting, update this index with the final candidate commit,
latest CI run, local verification commands, and the reviewer decision.
