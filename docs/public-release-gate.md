# Agent Watchbench Public-Release Gate

Date: 2026-07-19

Agent Watchbench stays private until every gate item below is complete and
recorded. This gate applies before any repository visibility change, tag,
GitHub release, package registry publishing, hosted service, external scan,
production integration, or social/blog posting.

## Checklist

- Run a repository secret scan and record the command and result. The local
  prototype includes a synthetic `examples/secret-scan-root` fixture and
  checked-in `examples/secret-scan-report.md` proving that finding locations are
  reported while secret values are not printed. For a real release-candidate
  checkout, regenerate the synthetic fixture report first, then run
  `secret-scan --root . --exclude-synthetic-fixtures --fail-on-findings` so
  possible non-fixture secrets stop the gate with a non-zero exit code while
  keeping matched values redacted.
- Confirm checked-in examples and fixtures contain no raw private logs, real
  user data, tokens, credentials, cookies, private keys, OAuth material, or
  private identifiers. The local `fixture-audit` command records a
  content-redacted inventory at `examples/fixture-audit-report.md` so this gate
  can be reviewed without exposing fixture values.
- Confirm the README covers local-only scope, hostile-input handling, and the
  rule that commands copied from external input are summarized rather than
  executed.
- Run unit tests or a fixture-backed scan locally and record the passing
  evidence.
- Confirm the GitHub Actions fixture gate passes on the release-candidate
  commit, including the synthetic fixture report diff.
- Keep package registry publishing, hosted service deployment, external
  scanning, production integration, and social/blog posting out of scope unless
  each action is separately approved.
- Record provenance for the reviewed prototype source and the verification
  evidence used for the release decision.

## Rollback

If any gate item fails, keep `superdoccimo/agent-watchbench` private, do not tag
or release the repository, and open a follow-up issue with the failed item,
evidence path, and smallest next review step. If `--fail-on-findings` exits
non-zero after `--exclude-synthetic-fixtures`, preserve only the redacted report
path and finding count in review notes; do not copy matched values.
