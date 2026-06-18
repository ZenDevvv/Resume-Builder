import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


RESUME_REQUIRED_KEYS = [
    "basics",
    "headline",
    "summary",
    "experience",
    "projects",
    "skills",
    "education",
]

BASICS_REQUIRED_KEYS = ["name", "location", "phone", "email", "links"]


class ValidationError(ValueError):
    pass


def parse_frontmatter(markdown_text):
    text = markdown_text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, markdown_text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, markdown_text

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise ValidationError("Request frontmatter starts with '---' but never closes with '---'.")

    frontmatter = {}
    for line_number, raw_line in enumerate(lines[1:closing_index], start=2):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValidationError(
                f"Invalid frontmatter line {line_number}: expected 'key: value' format."
            )
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValidationError(f"Invalid frontmatter line {line_number}: empty key.")
        frontmatter[key] = strip_wrapping_quotes(value)

    body = "\n".join(lines[closing_index + 1 :]).strip()
    return frontmatter, body


def strip_wrapping_quotes(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def extract_section(markdown_body, heading_name):
    pattern = re.compile(
        rf"(?ims)^##\s+{re.escape(heading_name)}\s*$\n?(.*?)(?=^\s*##\s+|\Z)"
    )
    match = pattern.search(markdown_body)
    if not match:
        return ""
    return match.group(1).strip()


def clean_company_name(value):
    cleaned = re.sub(r"\s+", " ", value).strip()
    cleaned = re.sub(r"[\"'`]+", "", cleaned)
    cleaned = cleaned.rstrip(".,;:|")
    return cleaned


def is_generic_company_candidate(candidate):
    generic_tokens = {
        "the",
        "a",
        "an",
        "our",
        "your",
        "their",
        "company",
        "team",
        "role",
        "position",
        "organization",
        "business",
        "employer",
        "department",
        "we",
        "you",
    }
    lowered = candidate.lower()
    return lowered in generic_tokens


def looks_like_role_phrase(candidate):
    disallowed_tokens = {
        "engineer",
        "developer",
        "manager",
        "designer",
        "specialist",
        "intern",
        "lead",
        "architect",
        "analyst",
    }
    tokens = {token.strip(".,;:").lower() for token in candidate.split()}
    return bool(tokens & disallowed_tokens)


def infer_company_from_job_description(job_description):
    labeled_patterns = [
        re.compile(r"(?im)^\s*(?:company|employer|organization)\s*:\s*(.+?)\s*$"),
        re.compile(r"(?im)^\s*(?:hiring company|about company)\s*:\s*(.+?)\s*$"),
    ]
    for pattern in labeled_patterns:
        match = pattern.search(job_description)
        if match:
            candidate = clean_company_name(match.group(1))
            if candidate and not is_generic_company_candidate(candidate):
                return candidate

    phrase_pattern = re.compile(
        r"\b(?i:(?:at|for|with|join))\s+([A-Z][A-Za-z0-9&.,'\-]*(?:\s+[A-Z][A-Za-z0-9&.,'\-]*){0,4})"
    )
    for match in phrase_pattern.finditer(job_description):
        candidate = clean_company_name(match.group(1))
        if not candidate or is_generic_company_candidate(candidate):
            continue
        if looks_like_role_phrase(candidate):
            continue
        return candidate
    return ""


def ensure_non_empty(value, field_name, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f"'{field_name}' must be a non-empty string.")


def validate_resume_payload(payload):
    errors = []

    if not isinstance(payload, dict):
        return ["Resume root must be a JSON object."]

    for key in RESUME_REQUIRED_KEYS:
        if key not in payload:
            errors.append(f"Missing required resume key: '{key}'.")

    basics = payload.get("basics")
    if isinstance(basics, dict):
        for key in BASICS_REQUIRED_KEYS:
            if key not in basics:
                errors.append(f"Missing required basics key: '{key}'.")
        if "links" in basics and not isinstance(basics["links"], list):
            errors.append("'basics.links' must be an array.")
    elif basics is not None:
        errors.append("'basics' must be an object.")

    ensure_non_empty(payload.get("headline", ""), "headline", errors)

    for list_field in ["summary", "experience", "projects", "education"]:
        value = payload.get(list_field)
        if not isinstance(value, list) or not value:
            errors.append(f"'{list_field}' must be a non-empty array.")

    skills = payload.get("skills")
    if not isinstance(skills, dict) or not skills:
        errors.append("'skills' must be a non-empty object.")
    else:
        for label, values in skills.items():
            if not isinstance(values, list) or not values:
                errors.append(f"'skills.{label}' must be a non-empty array.")

    for idx, entry in enumerate(payload.get("experience", []), start=1):
        if not isinstance(entry, dict):
            errors.append(f"'experience[{idx}]' must be an object.")
            continue
        for key in ["company", "date_range", "bullets"]:
            if key not in entry:
                errors.append(f"Missing 'experience[{idx}].{key}'.")
        bullets = entry.get("bullets")
        if "bullets" in entry and (not isinstance(bullets, list) or not bullets):
            errors.append(f"'experience[{idx}].bullets' must be a non-empty array.")

    for idx, entry in enumerate(payload.get("projects", []), start=1):
        if not isinstance(entry, dict):
            errors.append(f"'projects[{idx}]' must be an object.")
            continue
        for key in ["name", "bullets"]:
            if key not in entry:
                errors.append(f"Missing 'projects[{idx}].{key}'.")
        bullets = entry.get("bullets")
        if "bullets" in entry and (not isinstance(bullets, list) or not bullets):
            errors.append(f"'projects[{idx}].bullets' must be a non-empty array.")

    for idx, entry in enumerate(payload.get("education", []), start=1):
        if not isinstance(entry, dict):
            errors.append(f"'education[{idx}]' must be an object.")
            continue
        if "school" not in entry:
            errors.append(f"Missing 'education[{idx}].school'.")

    return errors


def validate_request_file(request_path):
    markdown = request_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(markdown)
    role = (frontmatter.get("role") or "").strip()
    if not role:
        raise ValidationError("Request frontmatter must include a non-empty 'role'.")

    job_description = extract_section(body, "Job Description")
    if not job_description:
        raise ValidationError("Request body must include a non-empty '## Job Description' section.")

    return frontmatter, body, job_description


def validate_input_artifacts(resume_json_path, cover_letter_path):
    if not resume_json_path.exists():
        raise ValidationError(
            "Expected tailored resume JSON not found. "
            f"Create '{resume_json_path.name}' beside the request file."
        )
    if not cover_letter_path.exists():
        raise ValidationError(
            "Expected tailored cover-letter Markdown not found. "
            f"Create '{cover_letter_path.name}' beside the request file."
        )

    try:
        payload = json.loads(resume_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(f"Resume JSON is invalid: {error}") from error

    errors = validate_resume_payload(payload)
    if errors:
        joined = "\n- ".join(["Resume validation failed:"] + errors)
        raise ValidationError(joined)

    cover_letter_text = cover_letter_path.read_text(encoding="utf-8").strip()
    if not cover_letter_text:
        raise ValidationError("Cover-letter markdown is empty.")


def build_package_command(
    request_path,
    resume_json_path,
    cover_letter_path,
    role,
    company,
    output_root,
):
    scripts_dir = Path(__file__).resolve().parent
    package_script = scripts_dir / "package_application.py"

    command = [
        sys.executable,
        str(package_script),
        "--resume-input",
        str(resume_json_path),
        "--cover-letter-input",
        str(cover_letter_path),
        "--role",
        role,
        "--request-file",
        str(request_path),
        "--output-root",
        output_root,
    ]

    if company:
        command.extend(["--company", company])
    return command


def main():
    parser = argparse.ArgumentParser(
        description="Validate a request package and run the application packaging pipeline."
    )
    parser.add_argument("--request", required=True, help="Path to request markdown file under requests/.")
    parser.add_argument("--output-root", default="generated", help="Generated output root folder.")
    args = parser.parse_args()

    request_path = Path(args.request).resolve()
    if not request_path.exists():
        raise FileNotFoundError(f"Request file not found: {request_path}")

    frontmatter, _, job_description = validate_request_file(request_path)
    role = frontmatter["role"].strip()
    explicit_company = (frontmatter.get("company") or "").strip()
    inferred_company = infer_company_from_job_description(job_description)
    company = explicit_company or inferred_company

    resume_json_path = request_path.with_suffix(".resume.json")
    cover_letter_path = request_path.with_suffix(".cover-letter.md")
    validate_input_artifacts(resume_json_path, cover_letter_path)

    command = build_package_command(
        request_path=request_path,
        resume_json_path=resume_json_path,
        cover_letter_path=cover_letter_path,
        role=role,
        company=company,
        output_root=args.output_root,
    )

    print(f"Request file: {request_path}")
    print(f"Role: {role}")
    if explicit_company:
        print(f"Company: {explicit_company} (from frontmatter)")
    elif inferred_company:
        print(f"Company: {inferred_company} (inferred from job description)")
    else:
        print("Company: not provided and not inferred (using role-only package slug)")

    workspace = Path(__file__).resolve().parent.parent
    subprocess.run(command, check=True, cwd=workspace)


if __name__ == "__main__":
    main()

