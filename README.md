# Agent Watchbench

Agent Watchbench is a local-first command-line review bench for organizing a
small set of AI-agent artifacts into Markdown evidence for a human reviewer.

It detects and reports review signals. It does not guarantee that an agent is
safe, enforce a sandbox, block network or command execution, or approve a
release.

## Current prototype

The implemented `scan` command reads exactly these files below the operator's
chosen root:

- `learning/reviews/YYYY-MM-DD.md`
- `projects/ideas.jsonl`

It produces a Markdown report containing:

- learning signals from the `Signals To Review` section;
- up to five project ideas ranked by simple, documented metadata heuristics;
- boundary-risk keyword notes;
- missing-evidence warnings; and
- a publish-readiness heuristic that tells a human whether review flags exist.

The publish-readiness line is not a formal checklist, security certification,
or release approval. Missing inputs, malformed JSONL, and unsafe or unreadable
files remain visible as review warnings without copying their contents.

## Input and output boundary

Agent Watchbench does not change input agent artifacts. It writes only the
Markdown report requested by the operator:

- without `--output`, the report is printed to stdout;
- an output outside the input root may be any new `.md` file;
- an output inside the input root must be below `local-reports/`; and
- an existing report is replaced only with `--force`.

This is the precise meaning of input read-only behavior: input artifacts remain
unchanged, while the explicitly selected report destination is writable.
Symlinks are not followed. A root symlink, a root-external audit document,
or a parent-traversal audit path is rejected before report generation. Binary
or non-UTF-8 data, an unreadable file, or a file larger than 2 MiB makes the
affected audit incomplete rather than silently expanding its boundary.

## Local installation

Python 3.10 or newer is required. From a local checkout on POSIX systems:

```text
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
agent-watchbench --help
```

On Windows PowerShell, activation is not required when the venv executables are
called explicitly:

```text
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\agent-watchbench.exe --help
```

The package metadata exists for local installation and testing. This repository
does not authorize a package-registry publish.

## Scan example

```text
python3 agent_watchbench.py scan \
  --root <AGENT_ROOT> \
  --day 2099-01-02 \
  --output <AGENT_ROOT>/local-reports/watchbench-2099-01-02.md
```

The checked-in synthetic example can be regenerated without reading private
agent state:

```text
python3 agent_watchbench.py scan --root ./examples/fixture-root --day 2099-01-02 --output <TEMP_DIR>/fixture-report.md
diff -u examples/fixture-report.md <TEMP_DIR>/fixture-report.md
```

For a project-only review, `rank-projects` reads `projects/ideas.jsonl` and
emits the ranked idea section without requiring a daily learning review:

```text
python3 agent_watchbench.py rank-projects --root ./examples/fixture-root --output <TEMP_DIR>/project-ranking-report.md
diff -u examples/project-ranking-report.md <TEMP_DIR>/project-ranking-report.md
```

## Audit commands

The implemented CLI commands are:

- `scan`
- `rank-projects`
- `secret-scan`
- `fixture-audit`
- `pr-packet-audit`
- `release-index-audit`
- `release-sync-audit`

`secret-scan` is a local heuristic. It reports only relative path, line number,
finding kind, and a redacted marker. It never prints the matched value, but it
is not a replacement for a mature secret-scanning product and does not
guarantee complete detection.

```text
python3 agent_watchbench.py secret-scan --root ./examples/secret-scan-root --output <TEMP_DIR>/secret-scan-report.md
python3 agent_watchbench.py secret-scan --root . --exclude-synthetic-fixtures --fail-on-findings --output <TEMP_DIR>/repository-secret-scan.md
python3 agent_watchbench.py fixture-audit --root . --output <TEMP_DIR>/fixture-audit-report.md
```

`fixture-audit` inventories `examples/` and `tests/fixtures/` without copying
fixture contents into its report. The archived private-PR packet can still be
checked as historical process evidence:

```text
python3 agent_watchbench.py pr-packet-audit --root . --fail-on-missing --output <TEMP_DIR>/private-pr-packet-audit.md
python3 agent_watchbench.py release-index-audit --root . --fail-on-missing --output <TEMP_DIR>/release-index-audit.md
```

Candidate-specific values are intentionally not stored in active release docs:
a commit cannot contain its own final SHA. `release-sync-audit` therefore
requires one or more explicit `--release-doc` files created after the candidate
exists. CI exercises this behavior with a synthetic document:

```text
python3 agent_watchbench.py release-sync-audit \
  --root ./examples/release-sync-root \
  --candidate synthetic-candidate-commit \
  --release-doc candidate-review.md \
  --fail-on-stale \
  --output <TEMP_DIR>/release-sync-audit.md
```

For a real decision, a reviewer creates a temporary Markdown evidence packet
containing the exact current HEAD and its observed CI run, then points
`release-sync-audit` at that packet. The generated audit is evidence, not
approval.

## Deferred branch freshness

Before pushing or opening a PR from a branch that was held locally during a
quiet window, run the checklist in
`docs/deferred-branch-freshness.md`. It compares the branch against current
`origin/main`, flags empty or already-equivalent patches, and catches branches
that need a local rebase before review.

## Safety and limitations

- Local files are the only application inputs; the program contains no network
  client and does not execute text found in artifacts.
- Command-looking text, issue text, logs, URLs, and copied instructions are
  treated as untrusted data and may appear only as length-limited, redacted
  report fields.
- The tool does not provide a sandbox, network firewall, SOC monitor, GUI
  dashboard, runtime policy enforcement, or boundary-violation blocking.
- The tool does not guarantee AI safety, evidence correctness, publishability,
  or complete secret detection.
- Human review remains mandatory before any visibility, license, release, tag,
  package, deployment, integration, credential, or external-posting action.

See `SAFETY.md`, `PROVENANCE.md`, and
`docs/release-readiness-index.md` for the active review boundary. Historical
private-repository packets are retained under `docs/archive/` and must not be
treated as current release evidence.

## GitHub Actions

CI uses read-only repository permissions, runs on `pull_request` and pushes to
`main`, tests Python 3.10 through 3.14 on Ubuntu and Windows, regenerates the
synthetic reports, performs the repository secret scan with synthetic secret
fixtures excluded, and verifies a local editable install.

Passing CI is necessary evidence but is not public-release approval.

## License

Agent Watchbench is released under the MIT License. Copyright (c) 2026
mamushi, the beloved AI agent of minokamo mamu. See `LICENSE` for the full
terms. Project contact: `summer@minokamo.xyz`.

The MIT license selection does not itself approve a repository visibility
change, package publish, release, deployment, or external post.

## Future work

Possible future inputs include lessons, rule candidates, intel notes, paper
notes, daily logs, and review queues. `check-boundaries` is a possible future
standalone command; it is not implemented as a standalone command in the
current prototype.
