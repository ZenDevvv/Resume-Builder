import json
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


# --- New tests for analysis + validation support (lightweight smoke tests) ---

class AnalyzeJobDescriptionSmokeTests(unittest.TestCase):
    def test_analyze_extracts_keywords_and_phrases(self):
        # Import inside test to avoid side effects on other modules during collection
        from pathlib import Path
        import sys as _sys
        scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        if str(scripts_dir) not in _sys.path:
            _sys.path.insert(0, str(scripts_dir))
        import analyze_job_description as ajd

        jd = (
            "We are looking for a Web Developer. "
            "Build and iterate clickable prototypes using no-code and low-code platforms. "
            "Experience with Notion, research, and AI tools is required. "
            "Conduct market research and organize project documentation."
        )
        analysis = ajd.analyze_request_or_text(jd_text=jd)
        self.assertIn("high_priority_keywords", analysis)
        self.assertTrue(len(analysis["high_priority_keywords"]) > 3)
        # Should pick up key repeated/important terms
        joined = " ".join(analysis["high_priority_keywords"]).lower()
        self.assertTrue(any(k in joined for k in ["prototype", "research", "notion", "no-code"]))
        self.assertIn("analysis_text", analysis)

    def test_analyze_from_request_file(self):
        import tempfile
        from pathlib import Path
        import sys as _sys
        scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        if str(scripts_dir) not in _sys.path:
            _sys.path.insert(0, str(scripts_dir))
        import analyze_job_description as ajd
        import run_request_package as runner

        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp) / "req.md"
            req.write_text(
                "---\nrole: Test Role\ncompany: Acme\n---\n\n"
                "## Job Description\n"
                "Build prototypes. Use React and AI tools. Research and organize knowledge.\n",
                encoding="utf-8",
            )
            analysis = ajd.analyze_request_or_text(request_path=req)
            self.assertEqual(analysis.get("role"), "Test Role")
            self.assertIn("high_priority_keywords", analysis)


class ValidateTailoringSmokeTests(unittest.TestCase):
    def test_validate_runs_without_crashing_on_minimal_inputs(self):
        import tempfile
        from pathlib import Path
        import sys as _sys
        scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        if str(scripts_dir) not in _sys.path:
            _sys.path.insert(0, str(scripts_dir))
        import validate_tailoring as vt

        with tempfile.TemporaryDirectory() as tmp:
            # Minimal resume
            resume_p = Path(tmp) / "resume.json"
            resume_p.write_text(json.dumps({
                "headline": "Web Developer | React",
                "summary": ["Built prototypes using React and AI-assisted tools."],
                "experience": [{"company": "Uzaro Solutions Technology Inc.", "date_range": "Now", "bullets": ["Built things"]}],
                "projects": [{"name": "ALMA", "bullets": ["Multi-tenant"]}],
                "skills": {"Frontend": ["React"]},
                "education": [{"school": "Uni"}],
                "basics": {"name": "Test", "location": "", "phone": "", "email": "", "links": []}
            }), encoding="utf-8")

            cover_p = Path(tmp) / "cover.md"
            cover_p.write_text("I can build prototypes and conduct research using AI tools.", encoding="utf-8")

            jd = "Build prototypes. Conduct research. Use AI tools and React."

            # Should not raise
            result = vt.validate(resume_path=resume_p, cover_path=cover_p, request_path=None, jd_text=jd)
            self.assertIn("coverage_percent", result)
            self.assertIn("overall", result)
