# Agent Watchbench Release-Readiness Index

Date: 2026-07-20
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
- Final-candidate review template: `docs/final-candidate-review-template.md`
- Filled final-candidate review: `docs/final-candidate-review-2026-07-20.md`
- Synthetic fixture report: `examples/fixture-report.md`
- Synthetic secret-scan report: `examples/secret-scan-report.md`
- Content-redacted fixture audit: `examples/fixture-audit-report.md`

## Current Gate State

- Current candidate commit: `a40470368d4569fd4da6a284de56357c82bd164c`
- Current main CI run:
  `https://github.com/superdoccimo/agent-watchbench/actions/runs/29708990144`
- Final-candidate review template target commit:
  `a40470368d4569fd4da6a284de56357c82bd164c`
- Final-candidate review template CI run:
  `https://github.com/superdoccimo/agent-watchbench/actions/runs/29708990144`
- Filled final-candidate review target commit:
  `9cf57ed974903fbe210f392f73c6b6f1ac7f7895`
- Filled final-candidate review CI run:
  `https://github.com/superdoccimo/agent-watchbench/actions/runs/29710509162`
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
