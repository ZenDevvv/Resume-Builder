import argparse
import re
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


def main():
    parser = argparse.ArgumentParser(
        description="Create the per-job folder under generated/ and write a versioned snapshot of the request. The actual resume.json and cover-letter.md for the job are written directly into this folder by the generator (Stage 2)."
    )
    parser.add_argument("--role", required=True, help="Target role.")
    parser.add_argument("--company", default="", help="Target company. Optional.")
    parser.add_argument("--request-text", default="", help="Inline request text (job description wrapper).")
    parser.add_argument("--request-file", default="", help="Path to the request markdown file to snapshot.")
    parser.add_argument("--output-root", default="generated", help="Root folder for per-job packages (request snapshot + resume/cover outputs).")
    args = parser.parse_args()

    workspace = Path.cwd()
    output_root = (workspace / args.output_root).resolve()
    package_slug = build_package_slug(args.role, args.company)
    package_dir = output_root / package_slug
    package_dir.mkdir(parents=True, exist_ok=True)

    version_number = get_next_version(package_dir)
    version = version_token(version_number)

    if args.request_file:
        request_text = Path(args.request_file).resolve().read_text(encoding="utf-8")
    else:
        request_text = args.request_text.strip() or f"Application request for {args.role}"

    request_md = package_dir / f"request.{version}.md"
    write_request_snapshot(
        request_md,
        request_text,
        args.company.strip(),
        args.role.strip(),
        package_slug,
        version,
    )

    print(f"Request recorded: {request_md}")
    print(f"Version: {version}")


if __name__ == "__main__":
    main()
