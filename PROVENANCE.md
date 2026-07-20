# Agent Watchbench Provenance

Agent Watchbench began on 2026-07-19 as a local prototype derived from an
internal project idea and learning-review workflow. The implementation and
public examples in this repository were developed for this project; the current
tree contains no vendored runtime dependency, image, logo, or binary asset.

## Source materials

- A local `agent-watchbench` project idea.
- Local learning-review and project-planning artifact shapes.
- Synthetic fixtures under `examples/` and `tests/fixtures/`.
- Python standard-library functionality for parsing and report generation.

The public tree does not include the original private logs or private agent
state that motivated the prototype.

## Authorship and license

The project author and copyright holder is described in English as "mamushi,
the beloved AI agent of minokamo mamu." The public project contact is
`summer@minokamo.xyz`. The project is licensed under the MIT License; the full
terms are in `LICENSE`.

## Third-party components

- Runtime dependencies: none.
- Local build backend: setuptools, declared in `pyproject.toml`.
- CI actions: `actions/checkout` and `actions/setup-python`.

The build backend and both CI actions declare the MIT license. Their code is not
copied into this repository; they are referenced as build or CI tooling.

## Review history

GitHub Issue #1 is closed; it recorded creation of the first explicit
public-release gate. Historical private-candidate worksheets and PR packets are
retained under `docs/archive/`. Their SHA, CI, branch, and decision statements
are historical facts and are not current release evidence.

## Boundary

This note records origin and verification context without including secret
values, credentials, private identifiers, raw private logs, or external commands
to execute. Public visibility and publication approval remain separate human
decisions; the MIT license does not grant release approval.
