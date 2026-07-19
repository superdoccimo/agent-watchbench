from pathlib import Path
import contextlib
import io
import shutil
import tomllib
import tempfile
import unittest

import agent_watchbench


FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]


class AgentWatchbenchTests(unittest.TestCase):
    def test_scan_report_includes_learning_project_and_boundary_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "learning" / "reviews").mkdir(parents=True)
            (root / "projects").mkdir()
            shutil.copy(FIXTURES / "learning-review.md", root / "learning" / "reviews" / "2099-01-02.md")
            shutil.copy(FIXTURES / "ideas.jsonl", root / "projects" / "ideas.jsonl")

            report = agent_watchbench.build_report(root, "2099-01-02").to_markdown()

        self.assertIn("- learning signals: 2", report)
        self.assertIn("- ranked project ideas: 2", report)
        self.assertIn("- boundary notes: 1", report)
        self.assertIn("- publish readiness: review required", report)
        self.assertIn("fixture passed", report)
        self.assertIn("Agent Watchbench [prototype]: read-only scan report", report)
        self.assertIn("agent-watchbench: review boundary terms", report)

    def test_missing_inputs_still_render_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = agent_watchbench.build_report(Path(tmp), "2099-01-02").to_markdown()

        self.assertIn("- publish readiness: no obvious boundary blockers", report)
        self.assertIn("- none found", report)
        self.assertIn("no obvious boundary-risk terms", report)

    def test_scan_can_write_report_to_local_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "reports" / "watchbench.md"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                status = agent_watchbench.main(
                    ["scan", "--root", str(root), "--day", "2099-01-02", "--output", str(output)]
                )

            self.assertEqual(status, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertTrue(output.exists())
            self.assertIn("# Agent Watchbench Report - 2099-01-02", output.read_text(encoding="utf-8"))

    def test_checked_in_fixture_root_regenerates_example_report(self):
        report = agent_watchbench.build_report(ROOT / "examples" / "fixture-root", "2099-01-02").to_markdown()

        expected = (ROOT / "examples" / "fixture-report.md").read_text(encoding="utf-8")
        self.assertEqual(report, expected)

    def test_pyproject_exposes_local_console_script(self):
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(metadata["project"]["name"], "agent-watchbench")
        self.assertEqual(metadata["project"]["scripts"]["agent-watchbench"], "agent_watchbench:main")
        self.assertEqual(metadata["tool"]["setuptools"]["py-modules"], ["agent_watchbench"])

    def test_private_first_decision_keeps_repo_creation_gated(self):
        decision = (ROOT / "docs" / "private-first-repo-decision.md").read_text(encoding="utf-8")

        self.assertIn("Create a private `superdoccimo/agent-watchbench` repository", decision)
        self.assertIn("private `superdoccimo/agent-watchbench` repository", decision)
        self.assertIn("Do not publish to\na package registry", decision)
        self.assertIn("synthetic fixtures only", decision)

    def test_safety_note_documents_green_zone_boundaries(self):
        safety = (ROOT / "SAFETY.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("local-only prototype", safety)
        self.assertIn("Use synthetic fixtures", safety)
        self.assertIn("hostile input", safety)
        self.assertIn("Do not publish to a\n  package registry", safety)
        self.assertIn("must not print secret\n  values", safety)
        self.assertIn("SAFETY.md", readme)

    def test_provenance_note_records_local_heartbeat_origin(self):
        provenance = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        decision = (ROOT / "docs" / "private-first-repo-decision.md").read_text(encoding="utf-8")

        self.assertIn("mamushi local heartbeat prototype", provenance)
        self.assertIn("projects/ideas.jsonl", provenance)
        self.assertIn("synthetic fixtures", provenance)
        self.assertIn("does not include raw private logs", provenance)
        self.assertIn("PROVENANCE.md", readme)
        self.assertIn("Safety and provenance notes are linked", decision)

    def test_public_release_gate_documents_issue_one_boundary(self):
        gate = (ROOT / "docs" / "public-release-gate.md").read_text(encoding="utf-8")
        safety = (ROOT / "SAFETY.md").read_text(encoding="utf-8")
        provenance = (ROOT / "PROVENANCE.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Agent Watchbench stays private", gate)
        self.assertIn("repository secret scan", gate)
        self.assertIn("no raw private logs", gate)
        self.assertIn("commands copied from external input", gate)
        self.assertIn("fixture-backed scan", gate)
        self.assertIn("separately approved", gate)
        self.assertIn("keep `superdoccimo/agent-watchbench` private", gate)
        self.assertIn("docs/public-release-gate.md", readme)
        self.assertIn("docs/public-release-gate.md", safety)
        self.assertIn("Issue #1 tracks", provenance)


if __name__ == "__main__":
    unittest.main()
