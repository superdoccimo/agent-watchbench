# Agent Watchbench Fixture Audit

## Summary
- root: .
- files checked: 13
- files with synthetic marker: 9
- files needing boundary review: 11
- files with private-data blockers: 0
- audit scope: examples/ and tests/fixtures/ only
- value policy: fixture contents are not printed

## Files
- examples/fixture-report.md: synthetic marker present; secret, token; no private-data blockers
- examples/fixture-root/learning/reviews/2099-01-02.md: synthetic marker present; no boundary terms; no private-data blockers
- examples/fixture-root/projects/ideas.jsonl: synthetic marker missing; secret, token; no private-data blockers
- examples/private-pr-packet-audit-report.md: synthetic marker missing; no boundary terms; no private-data blockers
- examples/secret-scan-report.md: synthetic marker missing; secret, token; no private-data blockers
- examples/secret-scan-root/.env.sample: synthetic marker present; token; no private-data blockers
- examples/secret-scan-root/README.md: synthetic marker present; secret; no private-data blockers
- examples/secret-scan-root/subdir/config.txt: synthetic marker present; secret; no private-data blockers
- tests/fixtures/ideas.jsonl: synthetic marker missing; secret, token; no private-data blockers
- tests/fixtures/learning-review.md: synthetic marker present; no boundary terms; no private-data blockers
- tests/fixtures/secret-scan-root/.env.sample: synthetic marker present; token; no private-data blockers
- tests/fixtures/secret-scan-root/README.md: synthetic marker present; secret; no private-data blockers
- tests/fixtures/secret-scan-root/subdir/config.txt: synthetic marker present; secret; no private-data blockers
