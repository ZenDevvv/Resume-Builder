import argparse
import html
import json
import re
from datetime import date
from pathlib import Path


def escape(text):
    return html.escape(str(text), quote=True)


def render_links(links):
    items = []
    for link in links:
        label = escape(link["label"])
        url = escape(link["url"])
        items.append(f'<a class="letter-link" href="{url}">{label}<span>{url}</span></a>')
    return "".join(items)


def format_inline(text):
    escaped = escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped


def markdown_to_html(markdown_text):
    blocks = []
    paragraph_lines = []
    list_items = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            blocks.append(f"<p>{format_inline(' '.join(paragraph_lines))}</p>")
            paragraph_lines = []

    def flush_list():
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{format_inline(item)}</li>" for item in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items = []

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue

        if line.startswith("# "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h1>{format_inline(line[2:].strip())}</h1>")
            continue

        if line.startswith("## "):
            flush_paragraph()
            flush_list()
            blocks.append(f"<h2>{format_inline(line[3:].strip())}</h2>")
            continue

        if line.startswith("- "):
            flush_paragraph()
            list_items.append(line[2:].strip())
            continue

        flush_list()
        paragraph_lines.append(line)

    flush_paragraph()
    flush_list()
    return "".join(blocks)


def build_html(markdown_path, output_path, template_path, css_path, basics_path, role, company):
    markdown_text = markdown_path.read_text(encoding="utf-8")
    template = template_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    basics_payload = json.loads(basics_path.read_text(encoding="utf-8"))
    basics = basics_payload["basics"]

    target_parts = [part for part in [role, company] if part]
    target_line = " | ".join(target_parts) if target_parts else "General Application"

    header = f"""
    <h1 class="letter-name">{escape(basics["name"])}</h1>
    <div class="letter-role">{escape(role or 'Targeted Application')}</div>
    <div class="letter-meta">{escape(basics["location"])} | {escape(basics["phone"])} | {escape(basics["email"])}</div>
    <div class="letter-target">{escape(str(date.today()))} | {escape(target_line)}</div>
    <div class="letter-links">{render_links(basics["links"])}</div>
    """

    html_output = template
    replacements = {
        "__TITLE__": escape(f'{basics["name"]} Cover Letter'),
        "__INLINE_CSS__": css,
        "__HEADER__": header,
        "__BODY__": markdown_to_html(markdown_text),
    }
    for key, value in replacements.items():
        html_output = html_output.replace(key, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_output, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build cover-letter HTML from Markdown.")
    parser.add_argument("--input-md", required=True, help="Path to the source Markdown.")
    parser.add_argument("--output-html", required=True, help="Destination HTML path.")
    parser.add_argument("--role", default="", help="Target role for the letter header.")
    parser.add_argument("--company", default="", help="Target company for the letter header.")
    parser.add_argument(
        "--resume-data",
        default="data/master_resume.json",
        help="Path to the master resume data file for contact information.",
    )
    parser.add_argument(
        "--template",
        default="templates/cover_letter_template.html",
        help="Path to the cover-letter HTML template.",
    )
    parser.add_argument(
        "--css",
        default="templates/cover_letter.css",
        help="Path to the cover-letter stylesheet.",
    )
    args = parser.parse_args()

    build_html(
        markdown_path=Path(args.input_md).resolve(),
        output_path=Path(args.output_html).resolve(),
        template_path=Path(args.template).resolve(),
        css_path=Path(args.css).resolve(),
        basics_path=Path(args.resume_data).resolve(),
        role=args.role.strip(),
        company=args.company.strip(),
    )
    print(f"Wrote cover-letter HTML to {Path(args.output_html).resolve()}")


if __name__ == "__main__":
    main()
