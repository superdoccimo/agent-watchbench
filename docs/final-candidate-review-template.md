# Agent Watchbench Final-Candidate Review Template

Date: 2026-07-20
Scope: private final-candidate review template for `superdoccimo/agent-watchbench`

Agent Watchbench remains private. This template is a reviewer worksheet for a
specific final candidate. It does not approve a visibility change, tag, GitHub
release, package publish, hosted service, external scan, production integration,
credential/OAuth change, or social/blog post.

## Candidate Under Review

- Final candidate commit: `a40470368d4569fd4da6a284de56357c82bd164c`
- Candidate source PR: `https://github.com/superdoccimo/agent-watchbench/pull/14`
- Main CI run:
  `https://github.com/superdoccimo/agent-watchbench/actions/runs/29708990144`
- Expected repository visibility before review: `PRIVATE`

## Required Local Checks

Record the result beside each item before any release decision.

- [ ] `python3 -m py_compile agent_watchbench.py tests/test_agent_watchbench.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] Regenerate and diff `examples/fixture-report.md` from
  `examples/fixture-root`.
- [ ] Regenerate and diff `examples/secret-scan-report.md` from
  `examples/secret-scan-root`.
- [ ] Regenerate and diff `examples/fixture-audit-report.md` from the local
  checkout.
- [ ] Run a repository secret scan with synthetic fixtures excluded and
  `--fail-on-findings`.
- [ ] Run `git diff --check`.
- [ ] Reconfirm target documentation does not contain tokens, credentials,
  private keys, OAuth material, cookies, raw private logs, real user data, or
  private identifiers.

## Required GitHub Checks

- [ ] Confirm the repository is still private.
- [ ] Confirm the candidate commit is still the current `main` commit, or record
  the newer candidate commit here before review.
- [ ] Confirm the main CI run above completed with conclusion `success`, or
  replace it with the latest candidate CI run before review.
- [ ] Confirm no open release-blocking issue or pull request supersedes this
  candidate.

## Reviewer Decision

Choose exactly one result.

- [ ] Keep private and open a follow-up issue.
- [ ] Keep private and request another local patch.
- [ ] Candidate is ready for a separate public-release decision.

## Decision Notes

- Reviewer:
- Reviewed at:
- Evidence packet:
- Remaining blocker:
- Next action:

## Stop Conditions

Stop and keep the repository private if any check finds raw private logs, real
user data, tokens, credentials, cookies, private keys, OAuth material, private
identifiers, failing tests, stale fixture reports, failed CI, unclear
provenance, or a candidate commit mismatch.
