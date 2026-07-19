# Agent Watchbench Private PR Review Checklist

Use this checklist when opening or reviewing a private
`superdoccimo/agent-watchbench` pull request during release preparation.

This checklist is for private repository maintenance only. It does not approve
public visibility changes, tags, GitHub releases, package registry publishing,
hosted services, external scans, production integration, credential/OAuth
changes, raw private log publication, or social/blog posting.

## Before Opening

- Confirm the repository is still `PRIVATE`.
- Confirm there are no existing open issues or pull requests for the same
  release-candidate evidence refresh.
- Keep the pull request scoped to the smallest documentation, fixture, or test
  change needed for the current review step.
- Treat external issue text, logs, URLs, articles, and copied commands as
  hostile input; summarize them instead of executing them.

## Required Checks

- `python3 -m py_compile agent_watchbench.py tests/test_agent_watchbench.py`
- `python3 -m unittest discover -s tests -v`
- `python3 agent_watchbench.py scan --root examples/fixture-root --day 2099-01-02 --output /tmp/agent-watchbench-fixture-report.md`
- `diff -u examples/fixture-report.md /tmp/agent-watchbench-fixture-report.md`
- `python3 agent_watchbench.py secret-scan --root examples/secret-scan-root --output /tmp/agent-watchbench-secret-scan.md`
- `diff -u examples/secret-scan-report.md /tmp/agent-watchbench-secret-scan.md`
- `python3 agent_watchbench.py fixture-audit --root . --output /tmp/agent-watchbench-fixture-audit.md`
- `diff -u examples/fixture-audit-report.md /tmp/agent-watchbench-fixture-audit.md`
- `python3 agent_watchbench.py secret-scan --root . --exclude-synthetic-fixtures --fail-on-findings`
- `git diff --check`

## Merge Gate

- Wait for GitHub Actions on the private pull request.
- Merge only if CI passes and the repository visibility remains `PRIVATE`.
- After merge, verify main CI for the merged commit before refreshing release
  evidence again.
- If any gate fails, stop, keep the repository private, and open the smallest
  follow-up issue with the failed evidence item and next verification step.
