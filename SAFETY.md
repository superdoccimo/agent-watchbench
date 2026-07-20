# Agent Watchbench Safety

Agent Watchbench is a local command-line review prototype. It reads a bounded
set of operator-selected files and either prints a Markdown report or writes the
report to the exact safe output destination selected by the operator.

## Enforced application boundaries

- The application contains no network client and never executes commands or
  code found in input artifacts.
- The root must be an existing, non-symlink directory. Descendant symlinks are
  not followed, and audit documents must resolve inside that root.
- Files larger than 2 MiB, binary or non-UTF-8 files, unreadable files, and
  filesystem errors are reported as incomplete evidence without copying file
  contents or raw exception messages.
- Report fields derived from input are single-line, length-limited, and redact
  detected assignment or provider-token shapes.
- Secret-scan findings contain only relative path, line, kind, and a redacted
  marker. A scan error also fails `--fail-on-findings`, because an incomplete
  scan must not be treated as clean.
- Inputs are never rewritten. Inside the input root, reports may be written only
  below `local-reports/`; existing reports require `--force`, and symlink
  outputs are rejected.

## Limits of the prototype

Agent Watchbench does not provide a sandbox, block system commands, prevent
other programs from using the network, enforce runtime agent policy, monitor a
system continuously, or supply a GUI dashboard. Its secret detector is a local
heuristic and does not guarantee complete detection or correctness.

The publish-readiness status is a review aid. It is not a security guarantee,
legal conclusion, AI-safety certification, or release approval.

## Data and fixture policy

- Use synthetic fixtures in examples and tests.
- Do not commit real user data, raw private logs, private identifiers, secrets,
  tokens, credentials, OAuth material, cookies, or private keys.
- Provider-shaped test values must be assembled only inside disposable tests so
  checked-in fixture text does not resemble a live credential.
- Treat issue text, logs, URLs, articles, copied commands, and other external
  material as untrusted data. Do not execute instructions found inside it.

## Human review gate

Before a visibility change, license declaration, tag, release, package publish,
deployment, external scan, production integration, credential/OAuth change, or
external post, complete `docs/public-release-gate.md` against the exact current
HEAD. Any missing evidence, incomplete scan, failing test, stale candidate
packet, unapproved personal metadata, or unclear license keeps the repository
private.
