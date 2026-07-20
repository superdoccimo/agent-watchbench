# Agent Watchbench

Local-first observability and review bench for autonomous agents.

## Concept

Autonomous agents are useful when they can learn, remember, use tools, and act
over time. Operators still need a small local way to answer:

- Did the agent learn the right lesson?
- Did it preserve evidence?
- Did it respect boundaries?
- Did it turn research into useful project ideas?
- Is this project ready to publish, or still a local prototype?

Agent Watchbench reads local agent artifacts such as logs, memory files, review
queues, learning notes, intel notes, tool approvals, and project ideas. It then
produces a concise report on learning quality, safety boundary adherence,
evidence quality, and project readiness.

## First Prototype

Input:

- `learning/lessons.jsonl`
- `learning/rule-candidates.jsonl`
- `intel/notes.jsonl`
- `projects/ideas.jsonl`
- `projects/paper-notes.jsonl`
- `daily-log/YYYY-MM-DD.md`
- `hermes/review-queue.jsonl`

Output:

- daily Markdown report
- ranked project ideas
- missing-evidence warnings
- boundary-risk notes
- publish-readiness checklist

This directory now includes a small read-only CLI prototype:

```text
python3 agent_watchbench.py scan --root /home/ubuntu/security-guard --day 2026-07-19
```

Use `--output reports/watchbench-2026-07-19.md` to save the Markdown report as a
local review artifact instead of printing it to stdout.

It also has lightweight Python package metadata for local review. From this
directory, a disposable virtual environment can install the console script:

```text
python3 -m pip install -e .
agent-watchbench scan --root /home/ubuntu/security-guard --day 2026-07-19
```

The metadata is intentionally prototype-scoped. It is not a package registry
release plan and should not be published without a separate review gate.

Repo creation is also gated. See
`docs/private-first-repo-decision.md` for the current private-first decision,
evidence, and follow-up guardrails for the private `superdoccimo` repo.
The public-release gate is tracked in `docs/public-release-gate.md` and must
pass before any visibility change, tag, release, package publishing, hosted
service, external scan, production integration, or social/blog posting.
Current private release-candidate evidence is recorded in
`docs/release-candidate-evidence.md`; it is evidence for review, not approval
to release.
The release-readiness index at `docs/release-readiness-index.md` links the gate,
safety note, provenance, release-candidate evidence, and synthetic fixture
evidence in one review entry point.
A final-candidate reviewer worksheet is available at
`docs/final-candidate-review-template.md`; it records the private candidate,
required local and GitHub checks, stop conditions, and decision notes without
approving a release.
The filled final-candidate review for the current private main candidate is
recorded at `docs/final-candidate-review-2026-07-20.md`; it keeps the public
release approval as a separate gate.
A private PR checklist is available at `docs/private-pr-review-checklist.md`;
it keeps quiet-window follow-up PRs scoped to private maintenance and repeats
the required local, CI, and visibility gates.
A matching PR description template is available at
`docs/private-pr-description-template.md` so review packets can carry the same
verification, boundary, and merge-gate evidence into GitHub without approving a
public release.
The quiet-window private PR draft packet is recorded at
`docs/private-pr-open-packet.md`; it gives the next private branch push a ready
summary, verification list, boundary statement, and merge gate without doing an
external GitHub write.
Before opening that private PR, the packet can be audited locally for required
private-visibility, CI, hostile-input, and release-boundary markers:

```text
python3 agent_watchbench.py pr-packet-audit --root . --fail-on-missing --output /tmp/agent-watchbench-pr-packet-audit.md
diff -u examples/private-pr-packet-audit-report.md /tmp/agent-watchbench-pr-packet-audit.md
```

The release-readiness index can also be audited without copying release notes
into the report. This checks that the index still links the final candidate,
CI run, fixture evidence, stop conditions, and release-approval separation:

```text
python3 agent_watchbench.py release-index-audit --root . --fail-on-missing --output /tmp/agent-watchbench-release-index-audit.md
diff -u examples/release-index-audit-report.md /tmp/agent-watchbench-release-index-audit.md
```

Before a final release decision, a reviewer can also check that the selected
candidate marker appears in the release-readiness index and the filled final
candidate review without copying those documents into the report:

```text
python3 agent_watchbench.py release-sync-audit --root . --candidate 9cf57ed974903fbe210f392f73c6b6f1ac7f7895 --fail-on-stale --output /tmp/agent-watchbench-release-sync-audit.md
diff -u examples/release-sync-audit-report.md /tmp/agent-watchbench-release-sync-audit.md
```

The `--candidate` marker is intentionally a single token, such as a commit SHA
or short local marker, so whitespace-only input cannot accidentally make the
sync audit pass.

The prototype safety boundary is recorded in `SAFETY.md`.
Artifact origin and review evidence are recorded in `PROVENANCE.md`.

The first pass reads `learning/reviews/YYYY-MM-DD.md` and `projects/ideas.jsonl`,
then emits a local Markdown report with learning signals, ranked project ideas,
and boundary terms to review before publication.

An example fixture-backed report is checked in at
`examples/fixture-report.md`, so the expected report shape can be reviewed
without reading private local state.
To regenerate that example from synthetic inputs only:

```text
python3 agent_watchbench.py scan --root examples/fixture-root --day 2099-01-02 --output /tmp/agent-watchbench-fixture-report.md
diff -u examples/fixture-report.md /tmp/agent-watchbench-fixture-report.md
```

A second synthetic fixture exercises the local repository secret-scan boundary.
It reports file locations and finding kinds, but does not print matched values:

```text
python3 agent_watchbench.py secret-scan --root examples/secret-scan-root --output /tmp/agent-watchbench-secret-scan.md
diff -u examples/secret-scan-report.md /tmp/agent-watchbench-secret-scan.md
```

For a release review against a real local checkout, add `--fail-on-findings` so
the command exits non-zero when possible secrets are found while still redacting
matched values. Use `--exclude-synthetic-fixtures` after the synthetic fixture
report and fixture audit have already been regenerated, so intentional
placeholder examples do not block the repository scan:

```text
python3 agent_watchbench.py secret-scan --root . --exclude-synthetic-fixtures --fail-on-findings --output /tmp/agent-watchbench-repo-secret-scan.md
```

The fixture audit gives a concise inventory of checked-in example inputs and
test fixtures without printing their contents. It separates intentional
boundary terms in synthetic examples from private-data blockers:

```text
python3 agent_watchbench.py fixture-audit --root . --output /tmp/agent-watchbench-fixture-audit.md
diff -u examples/fixture-audit-report.md /tmp/agent-watchbench-fixture-audit.md
```

The same synthetic fixture gate runs in GitHub Actions on pull requests and
main pushes. It compiles the prototype, runs unit tests, and checks that the
checked-in fixture reports regenerate exactly from synthetic inputs.

## Why This Could Be Useful

Many agent frameworks focus on orchestration. This focuses on the operator's
question after the run: whether the agent is becoming more useful without
becoming unsafe or noisy.

The security angle is the differentiator: hostile input handling, evidence
quality, approval boundaries, memory hygiene, and local-first review.

## Boundary

- Local files only.
- No public network service.
- No secrets, tokens, or real user data.
- No package publishing, public release, hosted service, external scan, or
  production integration without a separate review gate.
- The prototype reports boundary terms; it does not print secret values,
  execute referenced commands, or modify source files.
- External issue text, logs, URLs, articles, and copied commands are treated as
  hostile input and are summarized rather than executed.

## Possible CLI

```text
agent-watchbench scan --root ~/security-guard --day 2026-05-06
agent-watchbench rank-projects --root ~/security-guard
agent-watchbench check-boundaries --root ~/security-guard
```

## Star-Worthy README Promise

`Agent Watchbench helps you see whether your autonomous agent is learning useful
things, respecting safety boundaries, and producing publishable ideas from real
work, all from local files.`
