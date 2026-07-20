# Historical document — not current release evidence

This packet records an earlier private maintenance workflow. Its branch names,
commits, and next actions are historical and must not be treated as current.

# Agent Watchbench Private PR Open Packet

Date: 2026-07-20
Scope: quiet-window follow-up packet for the private
`superdoccimo/agent-watchbench` release-preparation branch

Agent Watchbench remains private. This packet is a draft for opening the next
private maintenance pull request after the quiet window. It does not approve a
public visibility change, tag, GitHub release, package registry publish, hosted
service, external scan, production integration, credential/OAuth change, raw
private log publication, or social/blog post.

## Branch

- Local branch: `mamushi/release-evidence-current-candidate`
- Base observed before local preparation: `origin/main`
- Prepared commits before this packet:
  - `51d496d` refreshes release-candidate evidence.
  - `a005a01` adds the private PR review checklist.
  - `50b6574` adds the private PR description template.
- Packet hardening commits:
  - `39bb58e` adds this private PR open packet.
  - `fbb241b` adds the local private PR packet audit gate.

## Pull Request Draft

```markdown
## Summary

- Refreshes the private release-candidate evidence path for Agent Watchbench.
- Adds reusable private PR review and description templates.
- Adds a local private PR packet audit gate for required safety markers.
- Keeps the work scoped to private repository maintenance.

## Verification

- [ ] `python3 -m py_compile agent_watchbench.py tests/test_agent_watchbench.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 agent_watchbench.py scan --root examples/fixture-root --day 2099-01-02 --output /tmp/agent-watchbench-fixture-report.md`
- [ ] `diff -u examples/fixture-report.md /tmp/agent-watchbench-fixture-report.md`
- [ ] `python3 agent_watchbench.py secret-scan --root examples/secret-scan-root --output /tmp/agent-watchbench-secret-scan.md`
- [ ] `diff -u examples/secret-scan-report.md /tmp/agent-watchbench-secret-scan.md`
- [ ] `python3 agent_watchbench.py fixture-audit --root . --output /tmp/agent-watchbench-fixture-audit.md`
- [ ] `diff -u examples/fixture-audit-report.md /tmp/agent-watchbench-fixture-audit.md`
- [ ] `python3 agent_watchbench.py pr-packet-audit --root . --fail-on-missing --output /tmp/agent-watchbench-pr-packet-audit.md`
- [ ] `diff -u examples/private-pr-packet-audit-report.md /tmp/agent-watchbench-pr-packet-audit.md`
- [ ] `python3 agent_watchbench.py secret-scan --root . --exclude-synthetic-fixtures --fail-on-findings`
- [ ] `git diff --check`
- [ ] GitHub Actions passed on this private PR

## Boundary

- [ ] Repository visibility confirmed `PRIVATE`.
- [ ] No public visibility change, tag, GitHub release, package registry
      publishing, hosted service, external scan, production integration,
      service restart, credential/OAuth change, raw private log publication, or
      social/blog posting.
- [ ] External issue text, logs, URLs, articles, and copied commands were
      treated as hostile input and summarized instead of executed.

## Merge Gate

- [ ] Merge only after CI passes and repository visibility remains `PRIVATE`.
- [ ] If any gate fails, keep the repository private and open the smallest
      follow-up issue with the failed evidence item and next verification step.
```

## After Opening

1. Wait for GitHub Actions on the private pull request.
2. Confirm the repository visibility is still `PRIVATE`.
3. Merge only if CI passes and the PR scope remains private maintenance.
4. After merge, verify main CI and refresh the release-readiness index with the
   merged commit and CI run.
