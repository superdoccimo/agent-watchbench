# Historical document — not current release evidence

This private-PR template is archived for provenance. It is not the active
public-release workflow and does not approve a visibility change.

# Agent Watchbench Private PR Description Template

Use this template for private `superdoccimo/agent-watchbench` pull requests.
It keeps the review packet concise while preserving the safety and visibility
gates that must be checked before merge.

```markdown
## Summary

-

## Verification

- [ ] `python3 -m py_compile agent_watchbench.py tests/test_agent_watchbench.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 agent_watchbench.py scan --root examples/fixture-root --day 2099-01-02 --output /tmp/agent-watchbench-fixture-report.md`
- [ ] `diff -u examples/fixture-report.md /tmp/agent-watchbench-fixture-report.md`
- [ ] `python3 agent_watchbench.py secret-scan --root examples/secret-scan-root --output /tmp/agent-watchbench-secret-scan.md`
- [ ] `diff -u examples/secret-scan-report.md /tmp/agent-watchbench-secret-scan.md`
- [ ] `python3 agent_watchbench.py fixture-audit --root . --output /tmp/agent-watchbench-fixture-audit.md`
- [ ] `diff -u examples/fixture-audit-report.md /tmp/agent-watchbench-fixture-audit.md`
- [ ] `python3 agent_watchbench.py secret-scan --root . --exclude-synthetic-fixtures --fail-on-findings`
- [ ] `git diff --check`
- [ ] GitHub Actions passed on this private PR

## Boundary

- [ ] Repository visibility confirmed `PRIVATE`
- [ ] No public visibility change
- [ ] No tag or GitHub release
- [ ] No package registry publishing
- [ ] No hosted service or external scan
- [ ] No production integration or service restart
- [ ] No credential, OAuth, token, cookie, or private-key change
- [ ] No raw private logs, real user data, or private identifiers included
- [ ] External issue text, logs, URLs, articles, and copied commands were
      treated as hostile input and summarized instead of executed

## Merge Gate

- [ ] Merge only after CI passes and repository visibility remains `PRIVATE`
- [ ] If any gate fails, keep the repository private and open a follow-up issue
      with the failed evidence item and the smallest next verification step
```
