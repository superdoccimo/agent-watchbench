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


def secret_scan(root: Path) -> SecretScanReport:
    findings: list[SecretFinding] = []
    files_checked = 0
    for path in iter_text_files(root):
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


def write_report(markdown: str, output: Path | None) -> None:
    if output is None:
        print(markdown, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a local Agent Watchbench report.")
    parser.add_argument("command", choices=["scan", "secret-scan"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--day")
    parser.add_argument("--output", type=Path, help="Write the Markdown report to a local file.")
    args = parser.parse_args(argv)

    if args.command == "scan":
        if not args.day:
            parser.error("--day is required for scan")
        write_report(build_report(args.root, args.day).to_markdown(), args.output)
        return 0
    if args.command == "secret-scan":
        write_report(secret_scan(args.root).to_markdown(), args.output)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
