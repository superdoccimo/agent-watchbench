# Agent Watchbench Final-Candidate Review Template

Copy this template to a temporary directory after the candidate commit and its
GitHub Actions run exist. Do not commit a filled copy while claiming that its
own SHA is the candidate; a commit cannot contain its own final SHA.

This worksheet records evidence only. It does not approve a visibility change,
license, tag, release, package publish, deployment, integration, credential
change, external scan, or external post.

## Candidate under review

- Candidate commit: `<CANDIDATE_SHA>`
- Source pull request or direct-push record: `<SOURCE_REFERENCE>`
- Candidate CI run: `<CI_RUN_URL>`
- CI result: `<STATUS>` / `<CONCLUSION>`
- Repository visibility observed: `PRIVATE`
- Local working tree status: `<GIT_STATUS>`

## Required local checks

- [ ] `git status --short`
- [ ] `git diff --check`
- [ ] `python3 -m py_compile agent_watchbench.py tests/test_agent_watchbench.py`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] Disposable local editable install and `agent-watchbench --help`
- [ ] Regenerate and diff all checked-in synthetic reports
- [ ] Run the repository secret scan with
      `--exclude-synthetic-fixtures --fail-on-findings`
- [ ] Run candidate-specific `release-sync-audit` against this filled temporary
      worksheet
- [ ] Review Git history and commit metadata without copying detected values

## Required GitHub checks

- [ ] Candidate is still the current default-branch HEAD
- [ ] Candidate CI completed successfully
- [ ] Repository remains `PRIVATE`
- [ ] No open release-blocking issue or pull request supersedes the candidate

## Human Approval Required

- [ ] License and copyright holder selected
- [ ] Any non-noreply author email in public history explicitly approved or
      removed through a separately authorized history rewrite
- [ ] Public description and thumbnail match the CLI/Markdown implementation
- [ ] A named human selected exactly one outcome: PASS, CONDITIONAL PASS, or BLOCK

## Stop Conditions

Stop and keep the repository private for any secret or private-data finding,
incomplete scan, failing test, stale fixture, stale candidate packet, failed CI,
unsafe workflow, unclear provenance, unapproved personal metadata, license
conflict, or materially misleading public claim.

## Decision notes

- Reviewer: `<HUMAN_REVIEWER>`
- Reviewed at: `<TIMESTAMP_AND_TIMEZONE>`
- Decision: `<PASS_CONDITIONAL_PASS_OR_BLOCK>`
- Remaining blocker: `<BLOCKER_OR_NONE>`
- Next action: `<EXACT_NEXT_ACTION>`
