#!/usr/bin/env python3
"""Local-first agent operations review prototype."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence


MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_INPUT_LINE_CHARS = 10_000
MAX_REPORT_FIELD_CHARS = 500
MAX_LEARNING_SIGNALS = 100
MAX_JSONL_RECORDS = 10_000

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
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "venv",
    ".eggs",
}
SKIP_DIR_SUFFIXES = (".egg-info", ".dist-info")
SYNTHETIC_SECRET_FIXTURE_DIRS = (
    ("examples", "secret-scan-root"),
    ("tests", "fixtures", "secret-scan-root"),
)
CANDIDATE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")

PROVIDER_SECRET_PATTERNS = (
    (
        "github-token",
        re.compile(r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9_]{20,})\b"),
    ),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    ),
)
ASSIGNMENT_RE = re.compile(
    r"""
    (?:^|\bexport\s+|[\"'])
    (?P<key>(?:[A-Z0-9_.-]*[_.-])?(?:API[_-]?KEY|ACCESS[_-]?TOKEN|AUTH[_-]?TOKEN|
        CLIENT[_-]?SECRET|PASSWORD|PRIVATE[_-]?KEY|CREDENTIAL|SECRET|TOKEN))
    [\"']?\s*[:=]\s*[\"']?
    (?P<value>[^\s\"'#,;]{8,})
    """,
    re.IGNORECASE | re.VERBOSE,
)

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
    ("safety boundary link", "SAFETY.md"),
    ("provenance link", "PROVENANCE.md"),
    ("final candidate template link", "docs/final-candidate-review-template.md"),
    ("synthetic fixture evidence", "examples/fixture-report.md"),
    ("secret scan evidence", "examples/secret-scan-report.md"),
    ("fixture audit evidence", "examples/fixture-audit-report.md"),
    ("human approval separation", "Human Approval Required"),
    ("stop conditions", "Stop Conditions"),
)


@dataclass(frozen=True)
class ScanError:
    path: str
    kind: str


@dataclass(frozen=True)
class WatchbenchReport:
    day: str
    learning_signals: list[str]
    project_ideas: list[dict]
    boundary_notes: list[str]
    missing_evidence: list[str]

    def to_markdown(self) -> str:
        review_required = bool(self.boundary_notes or self.missing_evidence)
        publish_status = "review required" if review_required else "no obvious review flags"
        lines = [
            f"# Agent Watchbench Report - {self.day}",
            "",
            "## Summary",
            f"- learning signals: {len(self.learning_signals)}",
            f"- ranked project ideas: {len(self.project_ideas)}",
            f"- boundary notes: {len(self.boundary_notes)}",
            f"- missing-evidence warnings: {len(self.missing_evidence)}",
            f"- publish-readiness heuristic: {publish_status}",
            "",
            "## Learning Signals",
        ]
        if self.learning_signals:
            lines.extend(f"- {sanitize_report_text(signal)}" for signal in self.learning_signals)
        else:
            lines.append("- none found")

        lines.extend(["", "## Project Ideas"])
        if self.project_ideas:
            for idea in self.project_ideas:
                title = sanitize_report_text(idea.get("title") or idea.get("project_id") or "untitled")
                status_value = sanitize_report_text(idea.get("status") or "unknown")
                first_step = sanitize_report_text(
                    idea.get("first_prototype") or idea.get("first_step") or "not recorded"
                )
                lines.append(f"- {title} [{status_value}]: {first_step}")
        else:
            lines.append("- none found")

        lines.extend(["", "## Boundary Notes"])
        if self.boundary_notes:
            lines.extend(f"- {sanitize_report_text(note)}" for note in self.boundary_notes)
        else:
            lines.append("- no obvious boundary-risk terms in project idea metadata")

        lines.extend(["", "## Missing Evidence Warnings"])
        if self.missing_evidence:
            lines.extend(f"- {sanitize_report_text(warning)}" for warning in self.missing_evidence)
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ProjectRankReport:
    project_ideas: list[dict]
    missing_evidence: list[str]

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Project Ranking",
            "",
            "## Summary",
            f"- ranked project ideas: {len(self.project_ideas)}",
            f"- missing-evidence warnings: {len(self.missing_evidence)}",
            "- ranking heuristic: status, recorded first step, and safety boundary metadata",
            "",
            "## Project Ideas",
        ]
        if self.project_ideas:
            for idea in self.project_ideas:
                title = sanitize_report_text(idea.get("title") or idea.get("project_id") or "untitled")
                status_value = sanitize_report_text(idea.get("status") or "unknown")
                first_step = sanitize_report_text(
                    idea.get("first_prototype") or idea.get("first_step") or "not recorded"
                )
                lines.append(f"- {title} [{status_value}]: {first_step}")
        else:
            lines.append("- none found")

        lines.extend(["", "## Missing Evidence Warnings"])
        if self.missing_evidence:
            lines.extend(f"- {sanitize_report_text(warning)}" for warning in self.missing_evidence)
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class SecretFinding:
    path: str
    line: int
    kind: str


@dataclass(frozen=True)
class SecretScanReport:
    files_checked: int
    findings: list[SecretFinding]
    scan_errors: list[ScanError]

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Repository Secret Scan",
            "",
            "## Summary",
            "- root: <ROOT>",
            f"- files checked: {self.files_checked}",
            f"- findings: {len(self.findings)}",
            f"- scan errors: {len(self.scan_errors)}",
            f"- scan complete: {'yes' if not self.scan_errors else 'no'}",
            "- value policy: secret values are not printed",
            "- detector scope: heuristic only; complete secret detection is not guaranteed",
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
        lines.extend(["", "## Scan Errors"])
        if self.scan_errors:
            lines.extend(f"- {error.path} [{error.kind}]" for error in self.scan_errors)
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
    files_checked: int
    items: list[FixtureAuditItem]
    scan_errors: list[ScanError]

    def to_markdown(self) -> str:
        review_items = [item for item in self.items if not item.synthetic_marker or item.boundary_terms]
        lines = [
            "# Agent Watchbench Fixture Audit",
            "",
            "## Summary",
            "- root: <ROOT>",
            f"- files checked: {self.files_checked}",
            f"- files with synthetic marker: {sum(1 for item in self.items if item.synthetic_marker)}",
            f"- files needing boundary review: {len(review_items)}",
            f"- files with private-data blockers: {sum(1 for item in self.items if item.private_blockers)}",
            f"- scan errors: {len(self.scan_errors)}",
            "- audit scope: examples/ and tests/fixtures/ only",
            "- value policy: fixture contents are not printed",
            "",
            "## Files",
        ]
        if self.items:
            for item in self.items:
                marker = "synthetic marker present" if item.synthetic_marker else "synthetic marker missing"
                boundary = ", ".join(item.boundary_terms) if item.boundary_terms else "no boundary terms"
                blockers = ", ".join(item.private_blockers) if item.private_blockers else "no private-data blockers"
                lines.append(f"- {item.path}: {marker}; {boundary}; {blockers}")
        else:
            lines.append("- none found")
        lines.extend(["", "## Scan Errors"])
        if self.scan_errors:
            lines.extend(f"- {error.path} [{error.kind}]" for error in self.scan_errors)
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class PrivatePrPacketAuditReport:
    packet_path: str
    markers_checked: int
    missing_markers: list[str]
    scan_error: str | None = None

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Private PR Packet Audit",
            "",
            "## Summary",
            f"- packet: {self.packet_path}",
            f"- markers checked: {self.markers_checked}",
            f"- missing markers: {len(self.missing_markers)}",
            f"- scan errors: {1 if self.scan_error else 0}",
            "- value policy: packet text is not copied into this report",
            "",
            "## Missing Markers",
        ]
        if self.missing_markers:
            lines.extend(f"- {marker}" for marker in self.missing_markers)
        else:
            lines.append("- none found")
        lines.extend(["", "## Scan Errors"])
        lines.append(f"- {self.scan_error}" if self.scan_error else "- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ReleaseIndexAuditReport:
    index_path: str
    markers_checked: int
    missing_markers: list[str]
    scan_error: str | None = None

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Release Index Audit",
            "",
            "## Summary",
            f"- index: {self.index_path}",
            f"- markers checked: {self.markers_checked}",
            f"- missing markers: {len(self.missing_markers)}",
            f"- scan errors: {1 if self.scan_error else 0}",
            "- value policy: release index text is not copied into this report",
            "",
            "## Missing Markers",
        ]
        if self.missing_markers:
            lines.extend(f"- {marker}" for marker in self.missing_markers)
        else:
            lines.append("- none found")
        lines.extend(["", "## Scan Errors"])
        lines.append(f"- {self.scan_error}" if self.scan_error else "- none found")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ReleaseSyncAuditReport:
    candidate: str
    files_checked: list[str]
    stale_files: list[str]
    scan_errors: list[ScanError]

    def to_markdown(self) -> str:
        lines = [
            "# Agent Watchbench Release Sync Audit",
            "",
            "## Summary",
            "- root: <ROOT>",
            f"- candidate marker length: {len(self.candidate)}",
            f"- files checked: {len(self.files_checked)}",
            f"- files missing candidate marker: {len(self.stale_files)}",
            f"- scan errors: {len(self.scan_errors)}",
            "- value policy: candidate and release document text are not copied into this report",
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
        lines.extend(["", "## Scan Errors"])
        if self.scan_errors:
            lines.extend(f"- {error.path} [{error.kind}]" for error in self.scan_errors)
        else:
            lines.append("- none found")
        return "\n".join(lines) + "\n"


def sanitize_report_text(value: object, max_chars: int = MAX_REPORT_FIELD_CHARS) -> str:
    text = str(value)
    normalized = []
    for character in text:
        category = unicodedata.category(character)
        normalized.append(" " if character.isspace() or category.startswith("C") else character)
    text = re.sub(r"\s+", " ", "".join(normalized)).strip()
    for _, pattern in PROVIDER_SECRET_PATTERNS:
        text = pattern.sub("<REDACTED>", text)
    text = ASSIGNMENT_RE.sub(lambda match: match.group(0)[: match.start("value") - match.start()] + "<REDACTED>", text)
    if len(text) > max_chars:
        text = text[: max_chars - 1] + "…"
    return text or "(empty)"


def normalize_day(day: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise ValueError("day must use YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(day)
    except ValueError as exc:
        raise ValueError("day must be a valid calendar date") from exc
    if parsed.isoformat() != day:
        raise ValueError("day must use canonical YYYY-MM-DD")
    return day


def normalize_candidate_marker(candidate: str) -> str:
    if not candidate:
        raise ValueError("candidate marker must not be empty")
    if candidate != candidate.strip() or not CANDIDATE_RE.fullmatch(candidate):
        raise ValueError("candidate marker must be an ASCII token of at most 128 safe characters")
    return candidate


def canonical_path(path: Path, strict: bool = False) -> Path:
    """Return an absolute filesystem identity suitable for containment checks."""
    absolute = Path(os.path.abspath(path))
    if os.name == "nt":
        # realpath expands Windows 8.3 aliases and resolves reparse-point targets.
        return Path(os.path.realpath(absolute, strict=strict))
    return absolute.resolve(strict=strict)


def path_is_link_like(path: Path) -> bool:
    """Treat symlinks and Windows reparse points, including junctions, as links."""
    try:
        if path.is_symlink():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & reparse_point)
    except FileNotFoundError:
        return False
    except OSError:
        return True


def validate_root(root: Path) -> Path:
    try:
        lexical = Path(os.path.abspath(root))
        if path_is_link_like(lexical):
            raise ValueError("root must not be a symlink or junction")
        resolved = canonical_path(lexical, strict=True)
    except FileNotFoundError as exc:
        raise ValueError("root must exist") from exc
    except OSError as exc:
        raise ValueError("root could not be inspected") from exc
    if not resolved.is_dir():
        raise ValueError("root must be a directory")
    return resolved


def is_within(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def path_label(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return "<OUTSIDE_ROOT>"


def has_symlink_component(path: Path, root: Path) -> bool:
    if not is_within(path, root):
        return True
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        try:
            if path_is_link_like(current):
                return True
        except OSError:
            return True
        if not current.exists():
            break
    return False


def path_uses_symlink(path: Path) -> bool:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            if path_is_link_like(current):
                return True
        except OSError:
            return True
        if not current.exists():
            break
    return False


def confined_path(root: Path, supplied: Path | None, default: Path) -> Path:
    candidate = supplied if supplied is not None else default
    if ".." in candidate.parts:
        raise ValueError("audit input must not contain parent traversal")
    if not candidate.is_absolute():
        candidate = root / candidate
    lexical = Path(os.path.abspath(candidate))
    if path_uses_symlink(lexical):
        raise ValueError("audit input must not use symlinks or junctions")
    canonical = canonical_path(lexical)
    if not is_within(canonical, root):
        raise ValueError("audit input must remain inside root")
    return canonical


def safe_read_text(path: Path, root: Path) -> tuple[str | None, ScanError | None]:
    label = path_label(path, root)
    if not is_within(path, root):
        return None, ScanError(label, "outside-root")
    if has_symlink_component(path, root):
        return None, ScanError(label, "symlink")
    try:
        file_stat = path.stat()
    except FileNotFoundError:
        return None, ScanError(label, "missing")
    except PermissionError:
        return None, ScanError(label, "permission-denied")
    except OSError:
        return None, ScanError(label, "io-error")
    if not stat.S_ISREG(file_stat.st_mode):
        return None, ScanError(label, "not-regular-file")
    if file_stat.st_size > MAX_FILE_BYTES:
        return None, ScanError(label, "file-too-large")
    try:
        data = path.read_bytes()
    except PermissionError:
        return None, ScanError(label, "permission-denied")
    except OSError:
        return None, ScanError(label, "io-error")
    if b"\x00" in data:
        return None, ScanError(label, "binary-file")
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, ScanError(label, "invalid-utf8-or-binary")


def iter_candidate_files(root: Path) -> tuple[list[Path], list[ScanError]]:
    pending = [root]
    files: list[Path] = []
    errors: list[ScanError] = []
    while pending:
        current = pending.pop(0)
        try:
            entries = sorted(current.iterdir(), key=lambda path: path.name)
        except PermissionError:
            errors.append(ScanError(path_label(current, root), "permission-denied"))
            continue
        except OSError:
            errors.append(ScanError(path_label(current, root), "io-error"))
            continue
        for path in entries:
            label = path_label(path, root)
            try:
                if path_is_link_like(path):
                    errors.append(ScanError(label, "symlink"))
                    continue
                if path.is_dir():
                    if path.name not in SKIP_DIRS and not path.name.endswith(SKIP_DIR_SUFFIXES):
                        pending.append(path)
                    continue
                if path.is_file():
                    files.append(path)
                    continue
                errors.append(ScanError(label, "not-regular-file"))
            except PermissionError:
                errors.append(ScanError(label, "permission-denied"))
            except OSError:
                errors.append(ScanError(label, "io-error"))
    return sorted(files, key=lambda path: path_label(path, root)), sorted(
        errors, key=lambda error: (error.path, error.kind)
    )


def read_jsonl(path: Path, root: Path) -> tuple[list[dict], list[str]]:
    text, error = safe_read_text(path, root)
    label = path_label(path, root)
    if error:
        return [], [f"{label}: {error.kind}"]
    records: list[dict] = []
    warnings: list[str] = []
    assert text is not None
    for line_no, line in enumerate(text.splitlines(), start=1):
        if len(line) > MAX_INPUT_LINE_CHARS:
            warnings.append(f"{label}:{line_no}: line-too-long")
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if len(records) >= MAX_JSONL_RECORDS:
            warnings.append(f"{label}: record-limit-reached")
            break
        try:
            value = json.loads(stripped)
        except json.JSONDecodeError:
            warnings.append(f"{label}:{line_no}: invalid-jsonl")
            continue
        if isinstance(value, dict):
            records.append(value)
        else:
            warnings.append(f"{label}:{line_no}: expected-object")
    return records, warnings


def learning_signals(root: Path, day: str) -> tuple[list[str], list[str]]:
    review = confined_path(root, None, Path("learning") / "reviews" / f"{day}.md")
    text, error = safe_read_text(review, root)
    label = path_label(review, root)
    if error:
        return [], [f"{label}: {error.kind}"]
    assert text is not None
    in_signals = False
    signals: list[str] = []
    warnings: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if len(line) > MAX_INPUT_LINE_CHARS:
            warnings.append(f"{label}:{line_no}: line-too-long")
            continue
        if line.startswith("## "):
            in_signals = line.strip() == "## Signals To Review"
            continue
        if in_signals and line.startswith("- "):
            if len(signals) >= MAX_LEARNING_SIGNALS:
                warnings.append(f"{label}: signal-limit-reached")
                break
            signals.append(sanitize_report_text(line[2:].strip()))
    return signals, warnings


def rank_project_ideas(records: Iterable[dict]) -> list[dict]:
    def score(record: dict) -> tuple[int, str]:
        status_value = str(record.get("status") or "").lower()
        has_first_step = bool(record.get("first_prototype") or record.get("first_step"))
        has_boundary = bool(record.get("safety_boundary"))
        value = 0
        if status_value in {"prototype", "active", "idea"}:
            value += 2
        if has_first_step:
            value += 2
        if has_boundary:
            value += 1
        tie_breaker = sanitize_report_text(record.get("project_id") or record.get("title") or "")
        return -value, tie_breaker

    return sorted(records, key=score)


def boundary_notes(records: Iterable[dict]) -> list[str]:
    notes: list[str] = []
    for record in records:
        project_id = sanitize_report_text(record.get("project_id") or record.get("title") or "unknown")
        text = json.dumps(record, ensure_ascii=False, sort_keys=True).lower()
        hits = [word for word in RISK_WORDS if word in text]
        if hits:
            notes.append(f"{project_id}: review boundary terms before publication ({', '.join(hits)})")
    return notes


def build_report(root: Path, day: str) -> WatchbenchReport:
    root = validate_root(root)
    day = normalize_day(day)
    ideas_path = confined_path(root, None, Path("projects") / "ideas.jsonl")
    ideas_raw, idea_warnings = read_jsonl(ideas_path, root)
    signals, learning_warnings = learning_signals(root, day)
    ideas = rank_project_ideas(ideas_raw)
    return WatchbenchReport(
        day=day,
        learning_signals=signals,
        project_ideas=ideas[:5],
        boundary_notes=boundary_notes(ideas),
        missing_evidence=learning_warnings + idea_warnings,
    )


def build_project_rank_report(root: Path) -> ProjectRankReport:
    root = validate_root(root)
    ideas_path = confined_path(root, None, Path("projects") / "ideas.jsonl")
    ideas_raw, idea_warnings = read_jsonl(ideas_path, root)
    return ProjectRankReport(
        project_ideas=rank_project_ideas(ideas_raw)[:5],
        missing_evidence=idea_warnings,
    )


def secret_findings_for_line(line: str) -> list[str]:
    kinds = {kind for kind, pattern in PROVIDER_SECRET_PATTERNS if pattern.search(line)}
    assignment = ASSIGNMENT_RE.search(line)
    if assignment:
        key = re.sub(r"[^a-z0-9]", "", assignment.group("key").lower())
        if "privatekey" in key:
            kinds.add("private-key")
        elif "clientsecret" in key:
            kinds.add("client-secret")
        elif "password" in key:
            kinds.add("password")
        elif "apikey" in key:
            kinds.add("api-key")
        elif "credential" in key:
            kinds.add("credential")
        elif "secret" in key:
            kinds.add("secret")
        else:
            kinds.add("token")
    return sorted(kinds)


def secret_scan(
    root: Path,
    exclude_synthetic_fixtures: bool = False,
    excluded_paths: Sequence[Path] = (),
) -> SecretScanReport:
    root = validate_root(root)
    excluded = {canonical_path(path) for path in excluded_paths}
    findings: list[SecretFinding] = []
    files_checked = 0
    files, scan_errors = iter_candidate_files(root)
    for path in files:
        if path in excluded:
            continue
        rel_parts = path.relative_to(root).parts
        if exclude_synthetic_fixtures and any(
            rel_parts[: len(fixture_dir)] == fixture_dir for fixture_dir in SYNTHETIC_SECRET_FIXTURE_DIRS
        ):
            continue
        text, error = safe_read_text(path, root)
        if error:
            scan_errors.append(error)
            continue
        files_checked += 1
        label = path_label(path, root)
        assert text is not None
        for line_no, line in enumerate(text.splitlines(), start=1):
            for kind in secret_findings_for_line(line):
                findings.append(SecretFinding(label, line_no, kind))
    return SecretScanReport(
        files_checked=files_checked,
        findings=sorted(findings, key=lambda finding: (finding.path, finding.line, finding.kind)),
        scan_errors=sorted(scan_errors, key=lambda error: (error.path, error.kind)),
    )


def fixture_audit(root: Path) -> FixtureAuditReport:
    root = validate_root(root)
    items: list[FixtureAuditItem] = []
    files_checked = 0
    scan_errors: list[ScanError] = []
    fixture_roots = [root / "examples", root / "tests" / "fixtures"]
    for fixture_root in fixture_roots:
        if not fixture_root.exists():
            scan_errors.append(ScanError(path_label(fixture_root, root), "missing"))
            continue
        files, traversal_errors = iter_candidate_files(fixture_root)
        for error in traversal_errors:
            prefixed = path_label(fixture_root / error.path, root)
            scan_errors.append(ScanError(prefixed, error.kind))
        for path in files:
            rel_path = path_label(path, root)
            if rel_path == "examples/fixture-audit-report.md":
                continue
            text, error = safe_read_text(path, root)
            if error:
                scan_errors.append(error)
                continue
            files_checked += 1
            assert text is not None
            lowered = text.lower()
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
    return FixtureAuditReport(
        files_checked=files_checked,
        items=sorted(items, key=lambda item: item.path),
        scan_errors=sorted(scan_errors, key=lambda error: (error.path, error.kind)),
    )


def private_pr_packet_audit(root: Path, packet: Path | None = None) -> PrivatePrPacketAuditReport:
    root = validate_root(root)
    packet_path = confined_path(root, packet, Path("docs/archive/private-pr-open-packet.md"))
    text, error = safe_read_text(packet_path, root)
    content = text or ""
    missing = [label for label, marker in PR_PACKET_MARKERS if marker not in content]
    return PrivatePrPacketAuditReport(
        packet_path=path_label(packet_path, root),
        markers_checked=len(PR_PACKET_MARKERS),
        missing_markers=missing,
        scan_error=f"{path_label(packet_path, root)} [{error.kind}]" if error else None,
    )


def release_index_audit(root: Path, index: Path | None = None) -> ReleaseIndexAuditReport:
    root = validate_root(root)
    index_path = confined_path(root, index, Path("docs/release-readiness-index.md"))
    text, error = safe_read_text(index_path, root)
    content = text or ""
    missing = [label for label, marker in RELEASE_INDEX_MARKERS if marker not in content]
    return ReleaseIndexAuditReport(
        index_path=path_label(index_path, root),
        markers_checked=len(RELEASE_INDEX_MARKERS),
        missing_markers=missing,
        scan_error=f"{path_label(index_path, root)} [{error.kind}]" if error else None,
    )


def release_sync_audit(root: Path, candidate: str, files: Sequence[Path]) -> ReleaseSyncAuditReport:
    root = validate_root(root)
    candidate = normalize_candidate_marker(candidate)
    if not files:
        raise ValueError("release-sync-audit requires at least one --release-doc")
    files_checked: list[str] = []
    stale_files: list[str] = []
    scan_errors: list[ScanError] = []
    for target in files:
        path = confined_path(root, target, target)
        label = path_label(path, root)
        files_checked.append(label)
        text, error = safe_read_text(path, root)
        if error:
            stale_files.append(label)
            scan_errors.append(error)
            continue
        assert text is not None
        candidate_pattern = re.compile(
            rf"(?<![A-Za-z0-9._-]){re.escape(candidate)}(?![A-Za-z0-9._-])"
        )
        if not candidate_pattern.search(text):
            stale_files.append(label)
    return ReleaseSyncAuditReport(
        candidate=candidate,
        files_checked=files_checked,
        stale_files=stale_files,
        scan_errors=scan_errors,
    )


def validate_output(root: Path, output: Path | None, force: bool) -> Path | None:
    if output is None:
        return None
    if output.suffix.lower() != ".md":
        raise ValueError("output must be a Markdown file ending in .md")
    if not output.is_absolute():
        output = Path.cwd() / output
    lexical = Path(os.path.abspath(output))
    if path_uses_symlink(lexical):
        raise ValueError("output must not use symlinks or junctions")
    canonical = canonical_path(lexical)
    if is_within(canonical, root):
        allowed = root / "local-reports"
        if not is_within(canonical, allowed):
            raise ValueError("outputs inside root must stay under local-reports")
    if canonical.exists():
        if path_is_link_like(canonical) or not canonical.is_file():
            raise ValueError("output must be a regular file")
        if not force:
            raise ValueError("output already exists; use --force to replace a report")
    return canonical


def reject_output_input_collision(output: Path | None, inputs: Iterable[Path]) -> None:
    if output is None:
        return
    if any(canonical_path(path) == output for path in inputs):
        raise ValueError("output must not replace an audit input")


def write_report(markdown: str, output: Path | None, force: bool = False) -> None:
    if output is None:
        print(markdown, end="")
        return
    temporary_path: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if path_uses_symlink(output.parent):
            raise ValueError("output must not use symlinks")
        if not force:
            with output.open("x", encoding="utf-8", newline="\n") as report_file:
                report_file.write(markdown)
            return
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            delete=False,
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
        ) as report_file:
            report_file.write(markdown)
            temporary_path = Path(report_file.name)
        os.replace(temporary_path, output)
        temporary_path = None
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError("output could not be written") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a local Agent Watchbench report.")
    parser.add_argument(
        "command",
        choices=[
            "scan",
            "rank-projects",
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
    parser.add_argument("--force", action="store_true", help="Replace an existing safe Markdown report.")
    parser.add_argument(
        "--packet",
        type=Path,
        help="Private PR packet under --root. Defaults to docs/archive/private-pr-open-packet.md.",
    )
    parser.add_argument(
        "--index",
        type=Path,
        help="Release-readiness index under --root. Defaults to docs/release-readiness-index.md.",
    )
    parser.add_argument("--candidate", help="Candidate commit or marker expected in release review documents.")
    parser.add_argument(
        "--release-doc",
        type=Path,
        action="append",
        help="Release document under --root to check for --candidate. May be repeated and is required.",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Return non-zero when secret-scan finds possible secrets or cannot scan completely.",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Return non-zero when a marker audit finds missing markers or cannot read its document.",
    )
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Return non-zero when release-sync-audit finds stale or unreadable documents.",
    )
    parser.add_argument(
        "--exclude-synthetic-fixtures",
        action="store_true",
        help="Exclude Agent Watchbench synthetic secret-scan fixtures from secret-scan.",
    )
    args = parser.parse_args(argv)

    try:
        root = validate_root(args.root)
        output = validate_output(root, args.output, args.force)
        if args.command == "scan":
            if not args.day:
                parser.error("--day is required for scan")
            report_text = build_report(root, args.day).to_markdown()
            write_report(report_text, output, args.force)
            return 0
        if args.command == "rank-projects":
            report = build_project_rank_report(root)
            write_report(report.to_markdown(), output, args.force)
            return 0
        if args.command == "secret-scan":
            report = secret_scan(
                root,
                exclude_synthetic_fixtures=args.exclude_synthetic_fixtures,
                excluded_paths=[output] if output is not None else (),
            )
            write_report(report.to_markdown(), output, args.force)
            incomplete = bool(report.scan_errors)
            return 1 if args.fail_on_findings and (report.findings or incomplete) else 0
        if args.command == "fixture-audit":
            report = fixture_audit(root)
            write_report(report.to_markdown(), output, args.force)
            has_blockers = any(item.private_blockers for item in report.items)
            return 1 if report.scan_errors or has_blockers else 0
        if args.command == "pr-packet-audit":
            packet_path = confined_path(root, args.packet, Path("docs/archive/private-pr-open-packet.md"))
            reject_output_input_collision(output, [packet_path])
            report = private_pr_packet_audit(root, args.packet)
            write_report(report.to_markdown(), output, args.force)
            return 1 if args.fail_on_missing and (report.missing_markers or report.scan_error) else 0
        if args.command == "release-index-audit":
            index_path = confined_path(root, args.index, Path("docs/release-readiness-index.md"))
            reject_output_input_collision(output, [index_path])
            report = release_index_audit(root, args.index)
            write_report(report.to_markdown(), output, args.force)
            return 1 if args.fail_on_missing and (report.missing_markers or report.scan_error) else 0
        if args.command == "release-sync-audit":
            if not args.candidate:
                parser.error("--candidate is required for release-sync-audit")
            if not args.release_doc:
                parser.error("at least one --release-doc is required for release-sync-audit")
            release_paths = [confined_path(root, path, path) for path in args.release_doc]
            reject_output_input_collision(output, release_paths)
            report = release_sync_audit(root, args.candidate, args.release_doc)
            write_report(report.to_markdown(), output, args.force)
            return 1 if args.fail_on_stale and (report.stale_files or report.scan_errors) else 0
    except ValueError as exc:
        parser.error(str(exc))
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
