import contextlib
import hashlib
import io
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import agent_watchbench


FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_CANDIDATE = "synthetic-candidate-commit"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def windows_short_path(path: Path) -> Path:
    if os.name != "nt":
        raise OSError("Windows short paths are unavailable")
    import ctypes

    get_short_path = ctypes.windll.kernel32.GetShortPathNameW
    get_short_path.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    get_short_path.restype = ctypes.c_uint
    buffer = ctypes.create_unicode_buffer(32_768)
    result = get_short_path(str(path), buffer, len(buffer))
    if result == 0 or result >= len(buffer):
        raise OSError("Windows short path could not be resolved")
    return Path(buffer.value)


class AgentWatchbenchTests(unittest.TestCase):
    def populate_scan_root(self, root: Path) -> None:
        (root / "learning" / "reviews").mkdir(parents=True)
        (root / "projects").mkdir()
        shutil.copy(FIXTURES / "learning-review.md", root / "learning" / "reviews" / "2099-01-02.md")
        shutil.copy(FIXTURES / "ideas.jsonl", root / "projects" / "ideas.jsonl")

    def test_scan_report_includes_learning_projects_boundary_and_evidence_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.populate_scan_root(root)
            report = agent_watchbench.build_report(root, "2099-01-02").to_markdown()

        self.assertIn("- learning signals: 2", report)
        self.assertIn("- ranked project ideas: 2", report)
        self.assertIn("- boundary notes: 1", report)
        self.assertIn("- missing-evidence warnings: 0", report)
        self.assertIn("- publish-readiness heuristic: review required", report)
        self.assertIn("## Missing Evidence Warnings\n- none found", report)

    def test_missing_inputs_render_explicit_missing_evidence_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = agent_watchbench.build_report(Path(tmp), "2099-01-02").to_markdown()

        self.assertIn("- missing-evidence warnings: 2", report)
        self.assertIn("learning/reviews/2099-01-02.md: missing", report)
        self.assertIn("projects/ideas.jsonl: missing", report)

    def test_invalid_dates_and_day_traversal_are_rejected(self):
        for invalid in ("2099-02-30", "2099-1-2", "../../outside"):
            with self.subTest(invalid=invalid):
                with tempfile.TemporaryDirectory() as tmp:
                    with self.assertRaises(ValueError):
                        agent_watchbench.build_report(Path(tmp), invalid)

    def test_malformed_jsonl_is_reported_without_copying_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "projects").mkdir()
            private_value = "not-for-report-" + "x" * 20
            (root / "projects" / "ideas.jsonl").write_text(
                "{broken " + private_value + "\n", encoding="utf-8"
            )
            report = agent_watchbench.build_report(root, "2099-01-02").to_markdown()

        self.assertIn("projects/ideas.jsonl:1: invalid-jsonl", report)
        self.assertNotIn(private_value, report)

    def test_scan_redacts_sensitive_assignments_and_collapses_control_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.populate_scan_root(root)
            private_value = "sensitive" + "value" * 4
            review = root / "learning" / "reviews" / "2099-01-02.md"
            review.write_text(
                "# Synthetic\n\n## Signals To Review\n\n- SERVICE_" + "TOKEN=" + private_value + "\n",
                encoding="utf-8",
            )
            report = agent_watchbench.build_report(root, "2099-01-02").to_markdown()

        self.assertIn("<REDACTED>", report)
        self.assertNotIn(private_value, report)

    def test_command_shaped_input_is_data_and_is_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.populate_scan_root(root)
            sentinel = root / "command-ran"
            ideas = root / "projects" / "ideas.jsonl"
            ideas.write_text(
                '{"project_id":"command-fixture","title":"Synthetic","status":"idea",'
                '"first_step":"python -c create-command-ran"}\n',
                encoding="utf-8",
            )
            report = agent_watchbench.build_report(root, "2099-01-02").to_markdown()

        self.assertIn("python -c create-command-ran", report)
        self.assertFalse(sentinel.exists())

    def test_scan_changes_only_new_local_report_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.populate_scan_root(root)
            inputs = [
                root / "learning" / "reviews" / "2099-01-02.md",
                root / "projects" / "ideas.jsonl",
            ]
            before = {path: digest(path) for path in inputs}
            output = root / "local-reports" / "watchbench.md"
            status = agent_watchbench.main(
                ["scan", "--root", str(root), "--day", "2099-01-02", "--output", str(output)]
            )

            self.assertEqual(status, 0)
            self.assertTrue(output.exists())
            self.assertEqual(before, {path: digest(path) for path in inputs})

    def test_output_overwrite_requires_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "local-reports" / "watchbench.md"
            output.parent.mkdir()
            output.write_text("existing\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    agent_watchbench.main(
                        ["scan", "--root", str(root), "--day", "2099-01-02", "--output", str(output)]
                    )
            self.assertEqual(raised.exception.code, 2)
            status = agent_watchbench.main(
                [
                    "scan",
                    "--root",
                    str(root),
                    "--day",
                    "2099-01-02",
                    "--output",
                    str(output),
                    "--force",
                ]
            )
            self.assertEqual(status, 0)
            self.assertNotEqual(output.read_text(encoding="utf-8"), "existing\n")

    def test_output_never_replaces_an_explicit_audit_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_dir = root / "local-reports"
            report_dir.mkdir()
            release_doc = report_dir / "candidate.md"
            original = "Candidate: " + SYNTHETIC_CANDIDATE + "\n"
            release_doc.write_text(original, encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    agent_watchbench.main(
                        [
                            "release-sync-audit",
                            "--root",
                            str(root),
                            "--candidate",
                            SYNTHETIC_CANDIDATE,
                            "--release-doc",
                            str(release_doc),
                            "--output",
                            str(release_doc),
                            "--force",
                        ]
                    )
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(release_doc.read_text(encoding="utf-8"), original)

    def test_output_inside_root_must_use_local_reports_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for output in (root / "README.md", root / "local-reports" / "report.txt"):
                with self.subTest(output=output):
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            agent_watchbench.main(
                                ["scan", "--root", str(root), "--day", "2099-01-02", "--output", str(output)]
                            )

    @unittest.skipUnless(os.name == "nt", "Windows path aliases are Windows-specific")
    def test_windows_case_variants_are_canonicalized_before_containment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = agent_watchbench.validate_root(Path(tmp))
            target = root / "candidate.md"
            target.write_text("synthetic\n", encoding="utf-8")
            case_variant = Path(str(target).swapcase())

            confined = agent_watchbench.confined_path(root, case_variant, case_variant)

        self.assertEqual(confined, agent_watchbench.canonical_path(target))

    @unittest.skipUnless(os.name == "nt", "Windows 8.3 paths are Windows-specific")
    def test_windows_short_and_long_paths_share_one_canonical_identity(self):
        with tempfile.TemporaryDirectory(prefix="watchbench long path ") as tmp:
            long_root = agent_watchbench.validate_root(Path(tmp))
            short_root = windows_short_path(long_root)
            if str(short_root).casefold() == str(long_root).casefold():
                self.skipTest("8.3 aliases are disabled on this volume")
            target = long_root / "candidate.md"
            target.write_text("synthetic\n", encoding="utf-8")
            short_target = short_root / target.name

            self.assertEqual(agent_watchbench.validate_root(short_root), long_root)
            self.assertEqual(
                agent_watchbench.confined_path(long_root, short_target, short_target),
                target,
            )
            with self.assertRaisesRegex(ValueError, "local-reports"):
                agent_watchbench.validate_output(long_root, short_root / "README.md", False)
            self.assertEqual(
                agent_watchbench.validate_output(
                    long_root,
                    short_root / "local-reports" / "report.md",
                    False,
                ),
                long_root / "local-reports" / "report.md",
            )
            with tempfile.TemporaryDirectory() as outside_tmp:
                outside = Path(outside_tmp) / "outside.md"
                outside.write_text("synthetic\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "inside root"):
                    agent_watchbench.confined_path(long_root, outside, outside)

    def test_windows_reparse_points_are_treated_as_link_like(self):
        class ReparsePoint:
            def is_symlink(self) -> bool:
                return False

            def lstat(self):
                return type("Stat", (), {"st_file_attributes": 0x400})()

        self.assertTrue(agent_watchbench.path_is_link_like(ReparsePoint()))

    def test_output_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "local-reports"
            output_dir.mkdir()
            target = output_dir / "target.md"
            target.write_text("safe\n", encoding="utf-8")
            link = output_dir / "report.md"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    agent_watchbench.main(
                        [
                            "scan",
                            "--root",
                            str(root),
                            "--day",
                            "2099-01-02",
                            "--output",
                            str(link),
                            "--force",
                        ]
                    )

    def test_output_symlink_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            report_dir = root / "local-reports"
            try:
                report_dir.symlink_to(Path(outside_tmp), target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    agent_watchbench.main(
                        [
                            "scan",
                            "--root",
                            str(root),
                            "--day",
                            "2099-01-02",
                            "--output",
                            str(report_dir / "report.md"),
                        ]
                    )

    def test_nonexistent_file_root_and_symlink_root_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            file_root = base / "file"
            file_root.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                agent_watchbench.validate_root(base / "missing")
            with self.assertRaises(ValueError):
                agent_watchbench.validate_root(file_root)
            link = base / "root-link"
            try:
                link.symlink_to(base, target_is_directory=True)
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(ValueError):
                agent_watchbench.validate_root(link)

    def test_secret_scan_reports_locations_and_kinds_without_values(self):
        report = agent_watchbench.secret_scan(FIXTURES / "secret-scan-root").to_markdown()

        self.assertIn("- findings: 2", report)
        self.assertIn("- .env.sample:1 [token] value redacted", report)
        self.assertIn("- subdir/config.txt:1 [client-secret] value redacted", report)
        self.assertNotIn("synthetic_placeholder_value", report)

    def test_secret_scan_detects_provider_shapes_constructed_at_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            values = [
                "gh" + "p_" + "A" * 30,
                "s" + "k-" + "B" * 30,
                "AK" + "IA" + "C" * 16,
                "eyJ" + "D" * 12 + "." + "E" * 12 + "." + "F" * 12,
                "-----BEGIN " + "PRIVATE KEY-----",
            ]
            (root / ".env").write_text("\n".join(values) + "\n", encoding="utf-8")
            report = agent_watchbench.secret_scan(root)
            markdown = report.to_markdown()

        kinds = {finding.kind for finding in report.findings}
        self.assertTrue({"github-token", "openai-key", "aws-access-key", "jwt", "private-key"} <= kinds)
        for value in values:
            self.assertNotIn(value, markdown)

    def test_hidden_files_are_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_value = "placeholder" + "x" * 20
            (root / ".env").write_text("SERVICE_" + "TOKEN=" + private_value + "\n", encoding="utf-8")
            report = agent_watchbench.secret_scan(root)

        self.assertEqual(report.files_checked, 1)
        self.assertEqual(report.findings[0].path, ".env")

    def test_secret_scan_skips_generated_dependency_and_build_directories(self):
        skipped_dirs = ("node_modules", "dist", "build", ".tox")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "clean.txt").write_text("synthetic clean fixture\n", encoding="utf-8")
            for dirname in skipped_dirs:
                generated = root / dirname
                generated.mkdir()
                (generated / ".env").write_text("SERVICE_" + "TOKEN=" + "x" * 20 + "\n", encoding="utf-8")

            report = agent_watchbench.secret_scan(root)

        self.assertEqual(report.files_checked, 1)
        self.assertEqual(report.findings, [])
        self.assertEqual(report.scan_errors, [])

    def test_secret_scan_fail_on_findings_and_clean_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.txt").write_text("synthetic clean fixture\n", encoding="utf-8")
            self.assertEqual(
                agent_watchbench.main(["secret-scan", "--root", str(root), "--fail-on-findings"]), 0
            )
            (root / ".env").write_text("SERVICE_" + "TOKEN=" + "x" * 20 + "\n", encoding="utf-8")
            self.assertEqual(
                agent_watchbench.main(["secret-scan", "--root", str(root), "--fail-on-findings"]), 1
            )

    def test_binary_and_large_files_make_scan_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.txt").write_text("synthetic clean fixture\n", encoding="utf-8")
            (root / "binary.bin").write_bytes(b"\x00binary")
            with (root / "large.txt").open("wb") as stream:
                stream.truncate(agent_watchbench.MAX_FILE_BYTES + 1)
            report = agent_watchbench.secret_scan(root)

        kinds = {error.kind for error in report.scan_errors}
        self.assertIn("binary-file", kinds)
        self.assertIn("file-too-large", kinds)
        self.assertIn("- scan complete: no", report.to_markdown())

    def test_outward_and_circular_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            outside = Path(outside_tmp)
            outside_value = "outside" + "x" * 20
            (outside / "secret.txt").write_text("SERVICE_" + "TOKEN=" + outside_value, encoding="utf-8")
            outward = root / "outward"
            circular = root / "circular"
            try:
                outward.symlink_to(outside, target_is_directory=True)
                circular.symlink_to(root, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable")
            report = agent_watchbench.secret_scan(root)
            markdown = report.to_markdown()

        self.assertEqual(report.files_checked, 0)
        self.assertEqual([error.kind for error in report.scan_errors], ["symlink", "symlink"])
        self.assertNotIn(outside_value, markdown)

    @unittest.skipIf(os.name == "nt", "permission semantics are not reliable on Windows")
    def test_permission_denied_file_is_reported_without_exception_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked = root / "blocked.txt"
            blocked.write_text("synthetic\n", encoding="utf-8")
            blocked.chmod(0)
            try:
                report = agent_watchbench.secret_scan(root)
            finally:
                blocked.chmod(0o600)
        self.assertIn("permission-denied", {error.kind for error in report.scan_errors})

    def test_fixture_audit_reports_inventory_without_contents(self):
        report = agent_watchbench.fixture_audit(ROOT).to_markdown()

        self.assertIn("- audit scope: examples/ and tests/fixtures/ only", report)
        self.assertIn("- files with private-data blockers: 0", report)
        self.assertIn("examples/secret-scan-root/.env.sample", report)
        self.assertNotIn("synthetic_placeholder_value", report)

    def test_audit_inputs_reject_traversal_and_absolute_outside_paths(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            outside = Path(outside_tmp) / "outside.md"
            outside.write_text("synthetic\n", encoding="utf-8")
            for supplied in (Path("../outside.md"), Path("docs/../outside.md"), outside):
                with self.subTest(supplied=supplied):
                    with self.assertRaises(ValueError):
                        agent_watchbench.private_pr_packet_audit(root, supplied)
                    with self.assertRaises(ValueError):
                        agent_watchbench.release_index_audit(root, supplied)
                    with self.assertRaises(ValueError):
                        agent_watchbench.release_sync_audit(root, SYNTHETIC_CANDIDATE, [supplied])

    def test_private_pr_packet_audit_is_content_redacted(self):
        report = agent_watchbench.private_pr_packet_audit(ROOT).to_markdown()
        expected = (ROOT / "examples" / "private-pr-packet-audit-report.md").read_text(encoding="utf-8")

        self.assertEqual(report, expected)
        self.assertNotIn("Refreshes the private release-candidate evidence path", report)

    def test_release_index_audit_is_structural_and_content_redacted(self):
        report = agent_watchbench.release_index_audit(ROOT).to_markdown()
        expected = (ROOT / "examples" / "release-index-audit-report.md").read_text(encoding="utf-8")

        self.assertEqual(report, expected)
        self.assertNotIn("Stop and open a follow-up issue", report)

    def test_release_sync_requires_explicit_docs_and_detects_stale_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "current.md"
            stale = root / "stale.md"
            substring = root / "substring.md"
            current.write_text("Candidate: " + SYNTHETIC_CANDIDATE + "\n", encoding="utf-8")
            stale.write_text("Candidate: another-marker\n", encoding="utf-8")
            substring.write_text("Candidate: prefix-" + SYNTHETIC_CANDIDATE + "-suffix\n", encoding="utf-8")
            report = agent_watchbench.release_sync_audit(
                root, SYNTHETIC_CANDIDATE, [current, stale, substring]
            )

        self.assertEqual(report.files_checked, ["current.md", "stale.md", "substring.md"])
        self.assertEqual(report.stale_files, ["stale.md", "substring.md"])
        self.assertNotIn(SYNTHETIC_CANDIDATE, report.to_markdown())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "at least one"):
                agent_watchbench.release_sync_audit(Path(tmp), SYNTHETIC_CANDIDATE, [])

    def test_candidate_validation_rejects_blank_whitespace_control_and_length(self):
        invalid = ("", "   ", " leading", "trailing ", "two tokens", "control\x07", "x" * 129)
        for marker in invalid:
            with self.subTest(marker_length=len(marker)):
                with self.assertRaises(ValueError):
                    agent_watchbench.normalize_candidate_marker(marker)
        self.assertEqual(agent_watchbench.normalize_candidate_marker("abc-123._"), "abc-123._")

    def test_checked_in_reports_regenerate_exactly_and_use_portable_paths(self):
        checks = {
            ROOT / "examples" / "fixture-report.md": agent_watchbench.build_report(
                ROOT / "examples" / "fixture-root", "2099-01-02"
            ).to_markdown(),
            ROOT / "examples" / "secret-scan-report.md": agent_watchbench.secret_scan(
                ROOT / "examples" / "secret-scan-root"
            ).to_markdown(),
            ROOT / "examples" / "fixture-audit-report.md": agent_watchbench.fixture_audit(ROOT).to_markdown(),
            ROOT / "examples" / "private-pr-packet-audit-report.md": agent_watchbench.private_pr_packet_audit(
                ROOT
            ).to_markdown(),
            ROOT / "examples" / "release-index-audit-report.md": agent_watchbench.release_index_audit(
                ROOT
            ).to_markdown(),
            ROOT / "examples" / "release-sync-audit-report.md": agent_watchbench.release_sync_audit(
                ROOT / "examples" / "release-sync-root",
                SYNTHETIC_CANDIDATE,
                [Path("candidate-review.md")],
            ).to_markdown(),
        }
        for expected_path, actual in checks.items():
            with self.subTest(expected=expected_path.name):
                self.assertEqual(actual, expected_path.read_text(encoding="utf-8"))
                self.assertNotIn("\\", actual)

    def test_repeated_reports_are_byte_deterministic(self):
        first = agent_watchbench.build_report(ROOT / "examples" / "fixture-root", "2099-01-02").to_markdown()
        second = agent_watchbench.build_report(ROOT / "examples" / "fixture-root", "2099-01-02").to_markdown()
        self.assertEqual(first.encode(), second.encode())

    def test_secret_scan_can_exclude_synthetic_fixtures(self):
        report = agent_watchbench.secret_scan(ROOT, exclude_synthetic_fixtures=True)

        self.assertEqual(report.findings, [])
        self.assertNotIn("examples/secret-scan-root/.env.sample", report.to_markdown())

    def test_pyproject_exposes_local_console_script_and_tested_versions(self):
        metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('name = "agent-watchbench"', metadata)
        self.assertIn('requires-python = ">=3.10"', metadata)
        self.assertIn('agent-watchbench = "agent_watchbench:main"', metadata)
        self.assertIn('license = { text = "MIT" }', metadata)
        self.assertIn('License :: OSI Approved :: MIT License', metadata)
        self.assertIn('mamushi, the beloved AI agent of minokamo mamu', metadata)
        self.assertIn('email = "summer@minokamo.xyz"', metadata)
        for version in range(10, 15):
            self.assertIn(f'Programming Language :: Python :: 3.{version}', metadata)

    def test_mit_license_and_public_attribution_are_consistent(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        provenance = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
        attribution = "mamushi, the beloved AI agent of minokamo mamu"

        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 " + attribution, license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', license_text)
        self.assertIn(attribution, readme)
        self.assertIn(attribution, " ".join(provenance.split()))
        self.assertIn("summer@minokamo.xyz", readme)
        self.assertIn("summer@minokamo.xyz", provenance)

    def test_readme_and_safety_describe_actual_scope_and_limitations(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        safety = (ROOT / "SAFETY.md").read_text(encoding="utf-8")
        provenance = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")

        self.assertIn("learning/reviews/YYYY-MM-DD.md", readme)
        self.assertIn("projects/ideas.jsonl", readme)
        self.assertIn("Future work", readme)
        self.assertIn("not implemented as standalone", readme)
        self.assertIn("local-reports/", readme)
        self.assertNotIn("/home/ubuntu/security-guard", readme)
        self.assertIn("does not provide a sandbox", readme)
        self.assertIn("does not guarantee", safety)
        self.assertIn("Issue #1 is closed", provenance)

    def test_release_documents_have_no_active_hardcoded_candidate(self):
        active = [
            ROOT / "README.md",
            ROOT / "docs" / "release-readiness-index.md",
            ROOT / "docs" / "final-candidate-review-template.md",
            ROOT / ".github" / "workflows" / "ci.yml",
            ROOT / "tests" / "test_agent_watchbench.py",
            ROOT / "agent_watchbench.py",
        ]
        old_candidates = (
            "a4047036" + "8d4569fd4da6a284de56357c82bd164c",
            "9cf57ed9" + "74903fbe210f392f73c6b6f1ac7f7895",
            "29708" + "990144",
            "29710" + "509162",
        )
        for path in active:
            text = path.read_text(encoding="utf-8")
            for marker in old_candidates:
                self.assertNotIn(marker, text, path)

    def test_historical_private_documents_are_archived_and_labeled(self):
        archive = ROOT / "docs" / "archive"
        expected = (
            "private-first-repo-decision.md",
            "private-pr-description-template.md",
            "private-pr-open-packet.md",
            "private-pr-review-checklist.md",
            "release-candidate-evidence.md",
            "final-candidate-review-2026-07-20.md",
        )
        for name in expected:
            path = archive / name
            self.assertTrue(path.exists(), name)
            self.assertIn("Historical document", path.read_text(encoding="utf-8"))

    def test_ci_is_readonly_sha_pinned_cross_platform_and_complete(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0", workflow)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", workflow)
        self.assertIn("python -m pip install setuptools==80.9.0", workflow)
        self.assertIn("python -m pip install --no-deps --no-build-isolation -e .", workflow)
        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("windows-latest", workflow)
        for version in range(10, 15):
            self.assertIn(f'"3.{version}"', workflow)
        self.assertIn("tests/test_agent_watchbench.py", workflow)
        self.assertIn("private-pr-packet-audit", workflow)
        self.assertIn("release-index-audit", workflow)
        self.assertIn("release-sync-audit", workflow)
        self.assertIn("--exclude-synthetic-fixtures", workflow)
        self.assertNotIn("pull_request_target", workflow)


if __name__ == "__main__":
    unittest.main()
