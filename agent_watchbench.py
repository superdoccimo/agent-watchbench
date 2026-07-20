#!/usr/bin/env python3
"""Local-first agent operations review prototype."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


RISK_WORDS = (
    "secret",
    "token",
    "credential",
    "private key",
    "oauth",
    "external publish",
    "production change",
)
PRIVATE_FIXTURE_BLOCKERS = (
    "raw private log",
    "real user data",
    "private identifier",
    "private key",
    "oauth",
    "cookie",
    "credential",
)

ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*[:=]\s*(['\"]?)([^'\"\s#]{8,})\2")
SECRET_KINDS = (
    ("api-key", "apikey"),
    ("access-token", "accesstoken"),
    ("auth-token", "authtoken"),
    ("client-secret", "clientsecret"),
    ("private-key", "privatekey"),
    ("credential", "credential"),
    ("password", "password"),
    ("secret", "secret"),
    ("token", "token"),
)
SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "venv"}
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz", ".sqlite", ".db"}
SYNTHETIC_SECRET_FIXTURE_DIRS = (
    ("examples", "secret-scan-root"),
    ("tests", "fixtures", "secret-scan-root"),
)


@dataclass(frozen=True)
class WatchbenchReport:
    day: str
    learning_signals: list[str]
    project_ideas: list[dict]
    boundary_notes: list[str]

    def to_markdown(self) -> str:
        publish_status = "review required" if self.boundary_notes else "no obvious boundary blockers"
        lines = [
            f"# Agent Watchbench Report - {self.day}",
            "",
            "## Summary",
            f"- learning signals: {len(self.learning_signals)}",
            f"- ranked project ideas: {len(self.project_ideas)}",
            f"- boundary notes: {len(self.boundary_notes)}",
            f"- publish readiness: {publish_status}",
            "",
            "## Learning Signals",
        ]
        if self.learning_signals:
            lines.extend(f"- {signal}" for signal in self.learning_signals)
        else:
            lines.append("- none found")

        lines.extend(["", "## Project Ideas"])
        if self.project_ideas:
            for idea in self.project_ideas:
                title = idea.get("title") or idea.get("project_id") or "untitled"
                status = idea.get("status") or "unknown"
                first_step = idea.get("first_prototype") or idea.get("first_step") or "not recorded"
                lines.append(f"- {title} [{status}]: {first_step}")
        else:
            lines.append("- none found")

        lines.extend(["", "## Boundary Notes"])
        if self.boundary_notes:
            lines.extend(f"- {note}" for note in self.boundary_notes)
        else:
            lines.append("- no obvious boundary-risk terms in project idea metadata")

        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class SecretFinding:
    path: str
    line: int
    kind: str


@dataclass(frozen=True)
class SecretScanReport:
    root: Path
    files_checked: int
    findings: list[SecretFinding]

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Repository Secret Scan",
            "",
            "## Summary",
            f"- root: {self.root}",
            f"- files checked: {self.files_checked}",
            f"- findings: {len(self.findings)}",
            "- value policy: secret values are not printed",
            "",
            "## Findings",
        ]
        if self.findings:
            lines.extend(
                f"- {finding.path}:{finding.line} [{finding.kind}] value redacted"
                for finding in self.findings
            )
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class FixtureAuditItem:
    path: str
    synthetic_marker: bool
    boundary_terms: list[str]
    private_blockers: list[str]


@dataclass(frozen=True)
class FixtureAuditReport:
    root: Path
    files_checked: int
    items: list[FixtureAuditItem]

    def to_markdown(self) -> str:
        review_items = [item for item in self.items if not item.synthetic_marker or item.boundary_terms]
        lines = [
            "# Agent Watchbench Fixture Audit",
            "",
            "## Summary",
            f"- root: {self.root}",
            f"- files checked: {self.files_checked}",
            f"- files with synthetic marker: {sum(1 for item in self.items if item.synthetic_marker)}",
            f"- files needing boundary review: {len(review_items)}",
            f"- files with private-data blockers: {sum(1 for item in self.items if item.private_blockers)}",
            "- audit scope: examples/ and tests/fixtures/ only",
            "- value policy: fixture contents are not printed",
            "",
            "## Files",
        ]
        if self.items:
            for item in self.items:
                marker = "synthetic marker present" if item.synthetic_marker else "synthetic marker missing"
                boundary = ", ".join(item.boundary_terms) if item.boundary_terms else "no boundary terms"
                blockers = (
                    ", ".join(item.private_blockers) if item.private_blockers else "no private-data blockers"
                )
                lines.append(f"- {item.path}: {marker}; {boundary}; {blockers}")
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


PR_PACKET_MARKERS = (
    ("private visibility gate", "Repository visibility confirmed `PRIVATE`"),
    ("no public release action", "No public visibility change"),
    ("package registry boundary", "package registry"),
    ("hostile input boundary", "hostile input"),
    ("ci merge gate", "Merge only after CI passes"),
    ("release approval separation", "does not approve"),
    ("github actions check", "GitHub Actions passed"),
    ("real checkout secret scan", "--exclude-synthetic-fixtures --fail-on-findings"),
)

RELEASE_INDEX_MARKERS = (
    ("public release gate link", "docs/public-release-gate.md"),
    ("final candidate review link", "docs/final-candidate-review-2026-07-20.md"),
    ("current candidate commit", "9cf57ed974903fbe210f392f73c6b6f1ac7f7895"),
    ("current main ci run", "actions/runs/29710509162"),
    ("private visibility boundary", "Repository visibility stays private"),
    ("synthetic fixture evidence", "examples/fixture-report.md"),
    ("secret scan evidence", "examples/secret-scan-report.md"),
    ("fixture audit evidence", "examples/fixture-audit-report.md"),
    ("release approval separation", "not release approval"),
    ("stop conditions", "Stop and open a follow-up issue"),
)


def normalize_candidate_marker(candidate: str) -> str:
    marker = candidate.strip()
    if not marker:
        raise ValueError("candidate marker must not be empty")
    if any(character.isspace() for character in marker):
        raise ValueError("candidate marker must be a single token without whitespace")
    return marker


@dataclass(frozen=True)
class PrivatePrPacketAuditReport:
    packet_path: Path
    markers_checked: int
    missing_markers: list[str]

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Private PR Packet Audit",
            "",
            "## Summary",
            f"- packet: {self.packet_path}",
            f"- markers checked: {self.markers_checked}",
            f"- missing markers: {len(self.missing_markers)}",
            "- value policy: packet text is not copied into this report",
            "",
            "## Missing Markers",
        ]
        if self.missing_markers:
            lines.extend(f"- {marker}" for marker in self.missing_markers)
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ReleaseIndexAuditReport:
    index_path: Path
    markers_checked: int
    missing_markers: list[str]

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Release Index Audit",
            "",
            "## Summary",
            f"- index: {self.index_path}",
            f"- markers checked: {self.markers_checked}",
            f"- missing markers: {len(self.missing_markers)}",
            "- value policy: release index text is not copied into this report",
            "",
            "## Missing Markers",
        ]
        if self.missing_markers:
            lines.extend(f"- {marker}" for marker in self.missing_markers)
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ReleaseSyncAuditReport:
    root: Path
    candidate: str
    files_checked: list[str]
    stale_files: list[str]

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Release Sync Audit",
            "",
            "## Summary",
            f"- root: {self.root}",
            f"- candidate marker length: {len(self.candidate)}",
            f"- files checked: {len(self.files_checked)}",
            f"- files missing candidate marker: {len(self.stale_files)}",
            "- value policy: release document text is not copied into this report",
            "",
            "## Files Checked",
        ]
        if self.files_checked:
            lines.extend(f"- {path}" for path in self.files_checked)
        else:
            lines.append("- none found")

        lines.extend(["", "## Files Missing Candidate Marker"])
        if self.stale_files:
            lines.extend(f"- {path}" for path in self.stale_files)
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


def private_pr_packet_audit(root: Path, packet: Path | None = None) -> PrivatePrPacketAuditReport:
    packet_path = packet or root / "docs" / "private-pr-open-packet.md"
    if not packet_path.is_absolute():
        packet_path = root / packet_path
    try:
        text = packet_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    missing = [label for label, marker in PR_PACKET_MARKERS if marker not in text]
    return PrivatePrPacketAuditReport(
        packet_path=packet_path,
        markers_checked=len(PR_PACKET_MARKERS),
        missing_markers=missing,
    )


def release_index_audit(root: Path, index: Path | None = None) -> ReleaseIndexAuditReport:
    index_path = index or root / "docs" / "release-readiness-index.md"
    if not index_path.is_absolute():
        index_path = root / index_path
    try:
        text = index_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    missing = [label for label, marker in RELEASE_INDEX_MARKERS if marker not in text]
    return ReleaseIndexAuditReport(
        index_path=index_path,
        markers_checked=len(RELEASE_INDEX_MARKERS),
        missing_markers=missing,
    )


def release_sync_audit(root: Path, candidate: str, files: Sequence[Path] | None = None) -> ReleaseSyncAuditReport:
    candidate = normalize_candidate_marker(candidate)
    default_files = (
        Path("docs/release-readiness-index.md"),
        Path("docs/final-candidate-review-2026-07-20.md"),
    )
    target_files = files or default_files
    files_checked: list[str] = []
    stale_files: list[str] = []
    for target in target_files:
        path = target if target.is_absolute() else root / target
        rel_path = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()
        files_checked.append(rel_path)
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            stale_files.append(rel_path)
            continue
        if candidate not in text:
            stale_files.append(rel_path)
    return ReleaseSyncAuditReport(
        root=root,
        candidate=candidate,
        files_checked=files_checked,
        stale_files=stale_files,
    )


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError as exc:
            records.append(
                {
                    "project_id": f"invalid-jsonl-line-{line_no}",
                    "title": f"Invalid JSONL line {line_no}",
                    "status": "needs_review",
                    "first_prototype": f"{path}: {exc.msg}",
                }
            )
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def learning_signals(root: Path, day: str) -> list[str]:
    review = root / "learning" / "reviews" / f"{day}.md"
    if not review.exists():
        return []
    in_signals = False
    signals: list[str] = []
    for line in review.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_signals = line.strip() == "## Signals To Review"
            continue
        if in_signals and line.startswith("- "):
            signals.append(line[2:].strip())
    return signals


def rank_project_ideas(records: Iterable[dict]) -> list[dict]:
    def score(record: dict) -> tuple[int, str]:
        status = str(record.get("status") or "").lower()
        has_first_step = bool(record.get("first_prototype") or record.get("first_step"))
        has_boundary = bool(record.get("safety_boundary"))
        value = 0
        if status in {"prototype", "active", "idea"}:
            value += 2
        if has_first_step:
            value += 2
        if has_boundary:
            value += 1
        return (-value, str(record.get("project_id") or record.get("title") or ""))

    return sorted(records, key=score)


def boundary_notes(records: Iterable[dict]) -> list[str]:
    notes: list[str] = []
    for record in records:
        project_id = record.get("project_id") or record.get("title") or "unknown"
        text = json.dumps(record, ensure_ascii=False).lower()
        hits = [word for word in RISK_WORDS if word in text]
        if hits:
            notes.append(f"{project_id}: review boundary terms before publication ({', '.join(hits)})")
    return notes


def build_report(root: Path, day: str) -> WatchbenchReport:
    ideas = rank_project_ideas(read_jsonl(root / "projects" / "ideas.jsonl"))
    return WatchbenchReport(
        day=day,
        learning_signals=learning_signals(root, day),
        project_ideas=ideas[:5],
        boundary_notes=boundary_notes(ideas),
    )


def iter_text_files(root: Path) -> Iterable[Path]:
    pending = [root]
    while pending:
        current = pending.pop(0)
        for path in sorted(current.iterdir()):
            if path.is_dir():
                if path.name not in SKIP_DIRS:
                    pending.append(path)
                continue
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
                continue
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            yield path


def secret_kind(key: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    for kind, marker in SECRET_KINDS:
        if marker in normalized:
            return kind
    return None


def secret_scan(root: Path, exclude_synthetic_fixtures: bool = False) -> SecretScanReport:
    findings: list[SecretFinding] = []
    files_checked = 0
    for path in iter_text_files(root):
        rel_parts = path.relative_to(root).parts
        if exclude_synthetic_fixtures and any(
            rel_parts[: len(fixture_dir)] == fixture_dir for fixture_dir in SYNTHETIC_SECRET_FIXTURE_DIRS
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files_checked += 1
        rel_path = path.relative_to(root).as_posix()
        for line_no, line in enumerate(text.splitlines(), start=1):
            assignment = ASSIGNMENT_RE.match(line)
            if not assignment:
                continue
            kind = secret_kind(assignment.group(1))
            if not kind:
                continue
            findings.append(SecretFinding(rel_path, line_no, kind))
    return SecretScanReport(root=root, files_checked=files_checked, findings=findings)


def fixture_audit(root: Path) -> FixtureAuditReport:
    items: list[FixtureAuditItem] = []
    files_checked = 0
    fixture_roots = [root / "examples", root / "tests" / "fixtures"]
    for fixture_root in fixture_roots:
        if not fixture_root.exists():
            continue
        for path in iter_text_files(fixture_root):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            files_checked += 1
            lowered = text.lower()
            rel_path = path.relative_to(root).as_posix()
            if rel_path == "examples/fixture-audit-report.md":
                files_checked -= 1
                continue
            synthetic_marker = any(marker in lowered for marker in ("synthetic", "fixture", "placeholder"))
            boundary_terms_found = [term for term in RISK_WORDS if term in lowered]
            private_blockers = [term for term in PRIVATE_FIXTURE_BLOCKERS if term in lowered]
            items.append(
                FixtureAuditItem(
                    path=rel_path,
                    synthetic_marker=synthetic_marker,
                    boundary_terms=boundary_terms_found,
                    private_blockers=private_blockers,
                )
            )
    return FixtureAuditReport(root=root, files_checked=files_checked, items=sorted(items, key=lambda item: item.path))


def write_report(markdown: str, output: Path | None) -> None:
    if output is None:
        print(markdown, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a local Agent Watchbench report.")
    parser.add_argument(
        "command",
        choices=[
            "scan",
            "secret-scan",
            "fixture-audit",
            "pr-packet-audit",
            "release-index-audit",
            "release-sync-audit",
        ],
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--day")
    parser.add_argument("--output", type=Path, help="Write the Markdown report to a local file.")
    parser.add_argument(
        "--packet",
        type=Path,
        help="Private PR packet to audit. Defaults to docs/private-pr-open-packet.md under --root.",
    )
    parser.add_argument(
        "--index",
        type=Path,
        help="Release-readiness index to audit. Defaults to docs/release-readiness-index.md under --root.",
    )
    parser.add_argument(
        "--candidate",
        help="Candidate commit or marker expected in release review documents.",
    )
    parser.add_argument(
        "--release-doc",
        type=Path,
        action="append",
        help="Release document to check for --candidate. May be repeated.",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Return a non-zero exit code when secret-scan finds possible secrets.",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Return a non-zero exit code when pr-packet-audit finds missing markers.",
    )
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Return a non-zero exit code when release-sync-audit finds stale documents.",
    )
    parser.add_argument(
        "--exclude-synthetic-fixtures",
        action="store_true",
        help="Exclude Agent Watchbench synthetic secret-scan fixtures from secret-scan.",
    )
    args = parser.parse_args(argv)

    if args.command == "scan":
        if not args.day:
            parser.error("--day is required for scan")
        write_report(build_report(args.root, args.day).to_markdown(), args.output)
        return 0
    if args.command == "secret-scan":
        report = secret_scan(args.root, exclude_synthetic_fixtures=args.exclude_synthetic_fixtures)
        write_report(report.to_markdown(), args.output)
        return 1 if args.fail_on_findings and report.findings else 0
    if args.command == "fixture-audit":
        write_report(fixture_audit(args.root).to_markdown(), args.output)
        return 0
    if args.command == "pr-packet-audit":
        report = private_pr_packet_audit(args.root, args.packet)
        write_report(report.to_markdown(), args.output)
        return 1 if args.fail_on_missing and report.missing_markers else 0
    if args.command == "release-index-audit":
        report = release_index_audit(args.root, args.index)
        write_report(report.to_markdown(), args.output)
        return 1 if args.fail_on_missing and report.missing_markers else 0
    if args.command == "release-sync-audit":
        if not args.candidate:
            parser.error("--candidate is required for release-sync-audit")
        try:
            report = release_sync_audit(args.root, args.candidate, args.release_doc)
        except ValueError as exc:
            parser.error(str(exc))
        write_report(report.to_markdown(), args.output)
        return 1 if args.fail_on_stale and report.stale_files else 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
