# Agent Watchbench Public-Release Gate

Agent Watchbench stays private until every applicable item below is complete
against the exact current default-branch HEAD and a named human separately
authorizes the visibility change.

## Repository and GitHub state

- Record branch, HEAD SHA, `git status`, remote URL, untracked and ignored files.
- Confirm GitHub visibility is `PRIVATE`.
- Confirm the current HEAD's GitHub Actions run completed successfully.
- Confirm there is no open pull request or release-blocking issue that
  supersedes the candidate.

## Local implementation evidence

- Compile source and tests and run the complete unit suite.
- Perform a disposable local editable install and CLI help check.
- Regenerate and diff every checked-in synthetic report.
- Run normal and abnormal smoke tests for every command.
- Confirm input artifacts are unchanged and only the selected Markdown report
  destination is writable.

## Security and privacy evidence

- Run `secret-scan --root . --exclude-synthetic-fixtures --fail-on-findings`.
- Treat any scan error as incomplete evidence, not a clean result.
- Review tracked, untracked, ignored, and historical Git content locally for
  secrets, personal data, private paths, email addresses, internal hosts, IPs,
  OAuth data, cookies, keys, logs, images, and binary files.
- Report possible secrets only as path, line, kind, likelihood, and whether
  deletion or rotation is required. Never copy the value.
- Confirm examples and fixtures are synthetic and do not resemble live provider
  credentials closely enough to trigger avoidable push protection.

## Documentation and public claims

- README, SAFETY, PROVENANCE, implementation, tests, fixtures, and CI describe
  the same current behavior.
- Future work is clearly separated from implemented commands.
- Public text does not claim network blocking, sandboxing, SOC monitoring, GUI
  functionality, runtime boundary blocking, AI-safety guarantees, or complete
  secret detection.
- Public thumbnails and videos avoid fabricated scores, completion counts,
  evidence counts, GUI screens, or blocked-violation claims.

## License and rights

- A human selects OSS, source-visible proprietary, or another explicit form.
- LICENSE, package metadata, README, author, and copyright-holder statements
  agree with that selection.
- Build/CI dependency licenses and rights to fixtures, text, images, and logos
  are reviewed.

## Candidate evidence and decision

- Fill a temporary final-candidate worksheet after the candidate and CI exist.
- Run `release-sync-audit` against that explicit worksheet.
- Record exactly one decision: PASS, CONDITIONAL PASS, or BLOCK.
- Treat updated documentation as evidence, never as implicit approval.

## Stop and rollback

If any gate fails, keep the repository private and do not tag, release, publish,
deploy, integrate, change credentials, send content to an external scanner, or
post publicly. Preserve only redacted evidence and the smallest safe next step.
