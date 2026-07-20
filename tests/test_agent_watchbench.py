from pathlib import Path
import contextlib
import io
import shutil
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
        metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('name = "agent-watchbench"', metadata)
        self.assertIn('requires-python = ">=3.10"', metadata)
        self.assertIn('agent-watchbench = "agent_watchbench:main"', metadata)
        self.assertIn('py-modules = ["agent_watchbench"]', metadata)

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

    def test_ci_workflow_runs_readonly_fixture_gate(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gate = (ROOT / "docs" / "public-release-gate.md").read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("python -m py_compile agent_watchbench.py", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("--root examples/fixture-root", workflow)
        self.assertIn("diff -u examples/fixture-report.md", workflow)
        self.assertIn("GitHub Actions", readme)
        self.assertIn("GitHub Actions fixture gate passes", gate)

    def test_release_candidate_evidence_consumes_passing_ci_without_approval(self):
        evidence = (ROOT / "docs" / "release-candidate-evidence.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("a40470368d4569fd4da6a284de56357c82bd164c", evidence)
        self.assertIn("actions/runs/29708990144", evidence)
        self.assertIn("completed` / `success", evidence)
        self.assertIn("contents: read", evidence)
        self.assertIn("python -m unittest discover -s tests -v", evidence)
        self.assertIn("examples/fixture-root", evidence)
        self.assertIn("synthetic fixtures\n  excluded", evidence)
        self.assertIn("not a release approval", evidence)
        self.assertIn("repository secret scan", evidence)
        self.assertIn("docs/release-candidate-evidence.md", readme)

    def test_secret_scan_reports_locations_without_values(self):
        report = agent_watchbench.secret_scan(FIXTURES / "secret-scan-root").to_markdown()

        self.assertIn("- findings: 2", report)
        self.assertIn("- .env.sample:1 [token] value redacted", report)
        self.assertIn("- subdir/config.txt:1 [client-secret] value redacted", report)
        self.assertNotIn("synthetic_placeholder_value", report)

    def test_checked_in_secret_scan_fixture_report_regenerates(self):
        report = agent_watchbench.secret_scan(Path("examples/secret-scan-root")).to_markdown()

        expected = (ROOT / "examples" / "secret-scan-report.md").read_text(encoding="utf-8")
        self.assertEqual(report, expected)

    def test_secret_scan_can_fail_on_findings_without_printing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "secret-scan.md"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                status = agent_watchbench.main(
                    [
                        "secret-scan",
                        "--root",
                        str(FIXTURES / "secret-scan-root"),
                        "--output",
                        str(output),
                        "--fail-on-findings",
                    ]
                )

            report = output.read_text(encoding="utf-8")

        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("- findings: 2", report)
        self.assertNotIn("synthetic_placeholder_value", report)

    def test_secret_scan_fail_on_findings_passes_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "note.txt").write_text("synthetic clean fixture\n", encoding="utf-8")

            status = agent_watchbench.main(["secret-scan", "--root", str(root), "--fail-on-findings"])

        self.assertEqual(status, 0)

    def test_secret_scan_can_exclude_synthetic_secret_fixtures(self):
        report = agent_watchbench.secret_scan(ROOT, exclude_synthetic_fixtures=True).to_markdown()

        self.assertIn("- findings: 0", report)
        self.assertNotIn("examples/secret-scan-root/.env.sample", report)

    def test_readme_and_release_gate_document_secret_scan_fixture(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gate = (ROOT / "docs" / "public-release-gate.md").read_text(encoding="utf-8")

        self.assertIn("agent_watchbench.py secret-scan", readme)
        self.assertIn("examples/secret-scan-report.md", readme)
        self.assertIn("--fail-on-findings", readme)
        self.assertIn("--exclude-synthetic-fixtures", readme)
        self.assertIn("--fail-on-findings", gate)
        self.assertIn("--exclude-synthetic-fixtures", gate)
        self.assertIn("secret values are not printed", gate)
        self.assertIn("examples/secret-scan-root", gate)

    def test_fixture_audit_reports_inventory_without_contents(self):
        report = agent_watchbench.fixture_audit(ROOT).to_markdown()

        self.assertIn("- audit scope: examples/ and tests/fixtures/ only", report)
        self.assertIn("- files with private-data blockers: 0", report)
        self.assertIn("examples/secret-scan-root/.env.sample", report)
        self.assertIn("no private-data blockers", report)
        self.assertNotIn("synthetic_placeholder_value", report)

    def test_checked_in_fixture_audit_report_regenerates(self):
        report = agent_watchbench.fixture_audit(Path(".")).to_markdown()

        expected = (ROOT / "examples" / "fixture-audit-report.md").read_text(encoding="utf-8")
        self.assertEqual(report, expected)

    def test_readme_release_gate_and_ci_document_fixture_audit(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gate = (ROOT / "docs" / "public-release-gate.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("fixture-audit", readme)
        self.assertIn("examples/fixture-audit-report.md", readme)
        self.assertIn("examples/fixture-audit-report.md", gate)
        self.assertIn("fixture-audit", workflow)

    def test_release_readiness_index_links_review_evidence_without_approval(self):
        index = (ROOT / "docs" / "release-readiness-index.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("docs/public-release-gate.md", index)
        self.assertIn("SAFETY.md", index)
        self.assertIn("PROVENANCE.md", index)
        self.assertIn("docs/release-candidate-evidence.md", index)
        self.assertIn("docs/final-candidate-review-template.md", index)
        self.assertIn("examples/fixture-report.md", index)
        self.assertIn("examples/secret-scan-report.md", index)
        self.assertIn("examples/fixture-audit-report.md", index)
        self.assertIn("a40470368d4569fd4da6a284de56357c82bd164c", index)
        self.assertIn("actions/runs/29708990144", index)
        self.assertIn("not release approval", index)
        self.assertIn("Stop and open a follow-up issue", index)
        self.assertIn("docs/release-readiness-index.md", readme)
        self.assertIn("docs/final-candidate-review-template.md", readme)

    def test_final_candidate_review_template_keeps_release_decision_separate(self):
        template = (ROOT / "docs" / "final-candidate-review-template.md").read_text(encoding="utf-8")

        self.assertIn("a40470368d4569fd4da6a284de56357c82bd164c", template)
        self.assertIn("actions/runs/29708990144", template)
        self.assertIn("Expected repository visibility before review: `PRIVATE`", template)
        self.assertIn("python3 -m unittest discover -s tests -v", template)
        self.assertIn("--fail-on-findings", template)
        self.assertIn("Confirm the repository is still private", template)
        self.assertIn("Candidate is ready for a separate public-release decision", template)
        self.assertIn("does not approve", template)
        self.assertIn("Stop and keep the repository private", template)

    def test_private_pr_review_checklist_keeps_quiet_window_followup_gated(self):
        checklist = (ROOT / "docs" / "private-pr-review-checklist.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("private repository maintenance only", checklist)
        self.assertIn("Confirm the repository is still `PRIVATE`", checklist)
        self.assertIn("no existing open issues or pull requests", checklist)
        self.assertIn("hostile input", checklist)
        self.assertIn("python3 -m unittest discover -s tests -v", checklist)
        self.assertIn("--exclude-synthetic-fixtures --fail-on-findings", checklist)
        self.assertIn("git diff --check", checklist)
        self.assertIn("Merge only if CI passes", checklist)
        self.assertIn("repository visibility remains `PRIVATE`", checklist)
        self.assertIn("docs/private-pr-review-checklist.md", readme)

    def test_private_pr_description_template_carries_review_gates(self):
        template = (ROOT / "docs" / "private-pr-description-template.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("## Verification", template)
        self.assertIn("python3 -m unittest discover -s tests -v", template)
        self.assertIn("fixture-audit", template)
        self.assertIn("--exclude-synthetic-fixtures --fail-on-findings", template)
        self.assertIn("Repository visibility confirmed `PRIVATE`", template)
        self.assertIn("No public visibility change", template)
        self.assertIn("No package registry publishing", template)
        self.assertIn("hostile input", template)
        self.assertIn("Merge only after CI passes", template)
        self.assertIn("docs/private-pr-description-template.md", readme)

    def test_private_pr_open_packet_records_next_private_pr_without_release_approval(self):
        packet = (ROOT / "docs" / "private-pr-open-packet.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("mamushi/release-evidence-current-candidate", packet)
        self.assertIn("51d496d", packet)
        self.assertIn("a005a01", packet)
        self.assertIn("50b6574", packet)
        self.assertIn("39bb58e", packet)
        self.assertIn("fbb241b", packet)
        self.assertIn("private PR packet audit gate", packet)
        self.assertIn("examples/private-pr-packet-audit-report.md", packet)
        self.assertIn("Repository visibility confirmed `PRIVATE`", packet)
        self.assertIn("No public visibility change", packet)
        self.assertIn("package registry", packet)
        self.assertIn("hostile input", packet)
        self.assertIn("Merge only after CI passes", packet)
        self.assertIn("does not approve", packet)
        self.assertIn("docs/private-pr-open-packet.md", readme)

    def test_private_pr_packet_audit_reports_required_markers_without_copying_packet(self):
        report = agent_watchbench.private_pr_packet_audit(Path(".")).to_markdown()

        expected = (ROOT / "examples" / "private-pr-packet-audit-report.md").read_text(encoding="utf-8")
        self.assertEqual(report, expected)
        self.assertNotIn("Refreshes the private release-candidate evidence path", report)

    def test_private_pr_packet_audit_can_fail_on_missing_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "packet.md"
            packet.write_text("PRIVATE only\n", encoding="utf-8")

            status = agent_watchbench.main(
                ["pr-packet-audit", "--root", str(root), "--packet", str(packet), "--fail-on-missing"]
            )

        self.assertEqual(status, 1)

    def test_readme_documents_private_pr_packet_audit_gate(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("pr-packet-audit", readme)
        self.assertIn("--fail-on-missing", readme)
        self.assertIn("examples/private-pr-packet-audit-report.md", readme)


if __name__ == "__main__":
    unittest.main()
