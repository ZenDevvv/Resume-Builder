import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_request_package as runner  # noqa: E402


class ParseFrontmatterTests(unittest.TestCase):
    def test_parse_frontmatter_valid(self):
        content = (
            "---\n"
            "role: Frontend Engineer\n"
            "company: Acme\n"
            "---\n\n"
            "## Job Description\n"
            "JD text"
        )
        frontmatter, body = runner.parse_frontmatter(content)
        self.assertEqual(frontmatter["role"], "Frontend Engineer")
        self.assertEqual(frontmatter["company"], "Acme")
        self.assertIn("## Job Description", body)

    def test_parse_frontmatter_invalid_line(self):
        content = "---\nrole Frontend Engineer\n---\n\n## Job Description\ntext"
        with self.assertRaises(runner.ValidationError):
            runner.parse_frontmatter(content)


class CompanyInferenceTests(unittest.TestCase):
    def test_infer_company_from_labeled_line(self):
        jd = "Company: OpenAI\nWe are hiring."
        self.assertEqual(runner.infer_company_from_job_description(jd), "OpenAI")

    def test_infer_company_from_phrase(self):
        jd = "Join Acme Systems today as a frontend engineer."
        self.assertEqual(runner.infer_company_from_job_description(jd), "Acme Systems")

    def test_infer_company_none(self):
        jd = "We are hiring for a frontend engineer role."
        self.assertEqual(runner.infer_company_from_job_description(jd), "")


class ValidationTests(unittest.TestCase):
    def test_resume_validation_missing_keys(self):
        errors = runner.validate_resume_payload({"headline": "x"})
        self.assertTrue(any("Missing required resume key: 'basics'" in e for e in errors))

    def test_request_validation_requires_role_and_job_description(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "request.md"
            path.write_text(
                "---\n"
                "role: Frontend Engineer\n"
                "---\n\n"
                "## Extra Instructions\n"
                "Only notes.",
                encoding="utf-8",
            )
            with self.assertRaises(runner.ValidationError):
                runner.validate_request_file(path)

class IntegrationFlowTests(unittest.TestCase):
    def test_main_builds_and_executes_package_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            requests_dir = root / "requests"
            requests_dir.mkdir(parents=True, exist_ok=True)

            request = requests_dir / "test-job.md"
            request.write_text(
                "---\n"
                "role: Frontend Engineer\n"
                "---\n\n"
                "## Job Description\n"
                "Join Acme Systems as a frontend engineer.\n",
                encoding="utf-8",
            )

            fake_script = root / "scripts"
            fake_script.mkdir(parents=True, exist_ok=True)
            (fake_script / "package_application.py").write_text("print('noop')", encoding="utf-8")

            with mock.patch.object(runner, "__file__", str(fake_script / "run_request_package.py")):
                with mock.patch.object(sys, "argv", ["run_request_package.py", "--request", str(request)]):
                    with mock.patch.object(runner.subprocess, "run") as mock_run:
                        runner.main()

            self.assertEqual(mock_run.call_count, 1)
            called_command = mock_run.call_args.args[0]
            self.assertIn("--role", called_command)
            self.assertIn("Frontend Engineer", called_command)
            self.assertIn("--company", called_command)
            self.assertIn("Acme Systems", called_command)


if __name__ == "__main__":
    unittest.main()
