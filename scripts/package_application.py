import argparse
import re
import shutil
import subprocess
from pathlib import Path


VERSION_PATTERN = re.compile(r"\.v(\d{3})\.")


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "application"


def build_package_slug(role, company):
    if company:
        return f"{slugify(company)}-{slugify(role)}"
    return slugify(role)


def get_next_version(folder):
    max_version = 0
    for path in folder.glob("*"):
        match = VERSION_PATTERN.search(path.name)
        if match:
            max_version = max(max_version, int(match.group(1)))
    return max_version + 1


def version_token(number):
    return f"v{number:03d}"


def write_request_snapshot(path, request_text, company, role, slug, version):
    lines = [
        "# Application Request",
        "",
        f"- Role: {role}",
        f"- Company: {company or 'Not provided'}",
        f"- Package: {slug}",
        f"- Version: {version}",
        "",
        request_text.strip(),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_command(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description="Package a tailored resume and cover letter into a versioned application folder.")
    parser.add_argument("--resume-input", required=True, help="Path to the tailored resume JSON source.")
    parser.add_argument("--cover-letter-input", required=True, help="Path to the tailored cover-letter Markdown source.")
    parser.add_argument("--role", required=True, help="Target role.")
    parser.add_argument("--company", default="", help="Target company. Optional.")
    parser.add_argument("--request-text", default="", help="Original prompt or job-targeting request.")
    parser.add_argument("--request-file", default="", help="Optional file containing the original request.")
    parser.add_argument("--output-root", default="generated", help="Root folder for generated application packages.")
    args = parser.parse_args()

    workspace = Path.cwd()
    output_root = (workspace / args.output_root).resolve()
    package_slug = build_package_slug(args.role, args.company)
    package_dir = output_root / package_slug
    package_dir.mkdir(parents=True, exist_ok=True)

    version_number = get_next_version(package_dir)
    version = version_token(version_number)

    resume_input = Path(args.resume_input).resolve()
    cover_letter_input = Path(args.cover_letter_input).resolve()
    if not resume_input.exists():
        raise FileNotFoundError(f"Resume input not found: {resume_input}")
    if not cover_letter_input.exists():
        raise FileNotFoundError(f"Cover-letter input not found: {cover_letter_input}")

    if args.request_file:
        request_text = Path(args.request_file).resolve().read_text(encoding="utf-8")
    else:
        request_text = args.request_text.strip() or f"Application package for {args.role}"

    resume_json = package_dir / f"resume.{version}.json"
    resume_html = package_dir / f"resume.{version}.html"
    resume_pdf = package_dir / f"resume.{version}.pdf"
    cover_md = package_dir / f"cover-letter.{version}.md"
    cover_html = package_dir / f"cover-letter.{version}.html"
    cover_pdf = package_dir / f"cover-letter.{version}.pdf"
    request_md = package_dir / f"request.{version}.md"

    shutil.copy2(resume_input, resume_json)
    shutil.copy2(cover_letter_input, cover_md)
    write_request_snapshot(request_md, request_text, args.company.strip(), args.role.strip(), package_slug, version)

    run_command(
        [
            "python",
            "scripts/build_resume.py",
            "--input",
            str(resume_json),
            "--output-html",
            str(resume_html),
        ],
        cwd=workspace,
    )
    run_command(
        [
            "python",
            "scripts/build_cover_letter.py",
            "--input-md",
            str(cover_md),
            "--output-html",
            str(cover_html),
            "--role",
            args.role.strip(),
            "--company",
            args.company.strip(),
        ],
        cwd=workspace,
    )
    run_command(
        [
            "python",
            "scripts/render_pdf.py",
            "--html",
            str(resume_html),
            "--pdf",
            str(resume_pdf),
        ],
        cwd=workspace,
    )
    run_command(
        [
            "python",
            "scripts/render_pdf.py",
            "--html",
            str(cover_html),
            "--pdf",
            str(cover_pdf),
        ],
        cwd=workspace,
    )

    print(f"Package folder: {package_dir}")
    print(f"Version: {version}")


if __name__ == "__main__":
    main()
