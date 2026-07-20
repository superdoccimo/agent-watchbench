# Agent Watchbench Release-Readiness Index

This page is the active entry point for public-release review. It deliberately
contains no candidate SHA or CI run URL. Candidate-specific values belong in a
temporary filled copy of `docs/final-candidate-review-template.md`, created only
after the candidate exists and checked with `release-sync-audit`.

## Review map

- Public-release gate: `docs/public-release-gate.md`
- Safety boundary: `SAFETY.md`
- Provenance: `PROVENANCE.md`
- Final-candidate review template: `docs/final-candidate-review-template.md`
- Synthetic scan report: `examples/fixture-report.md`
- Synthetic secret-scan report: `examples/secret-scan-report.md`
- Content-redacted fixture audit: `examples/fixture-audit-report.md`
- Historical private evidence: `docs/archive/`

## Required evidence

- Current branch, HEAD, git status, remote URL, visibility, CI result, open pull
  requests, and open release-blocking issues are observed immediately before
  review.
- Source and tests compile and the full unit suite passes.
- All checked-in synthetic reports regenerate exactly.
- The repository secret scan completes with synthetic secret fixtures excluded
  and no findings.
- Git history and commit metadata are reviewed locally without copying detected
  values into the evidence packet.
- CI uses read-only permissions and safe fork-PR triggers.

## Human Approval Required

CI and local evidence do not approve publication. A human must verify that the
selected MIT License, copyright holder, and package metadata remain consistent,
approve or remediate personal commit metadata, confirm that public descriptions
and images are accurate, and authorize the visibility change separately.

## Stop Conditions

Stop and keep the repository private for any secret or personal-data finding,
incomplete scan, failed test, stale fixture, candidate mismatch, failed CI,
unsafe workflow, unclear provenance, license conflict, or misleading capability
claim. Record only redacted path, line, kind, and required remediation.

## Candidate synchronization

Create a temporary candidate worksheet, replace all placeholders with observed
values, and run `release-sync-audit` with the exact current HEAD and the
worksheet passed explicitly through `--release-doc`. Do not treat a checked-in
historical candidate worksheet as current evidence.
