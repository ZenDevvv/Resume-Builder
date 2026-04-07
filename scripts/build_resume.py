import argparse
import html
import json
from pathlib import Path


def require_keys(data, keys, context):
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"Missing required keys in {context}: {', '.join(missing)}")


def escape(text):
    return html.escape(str(text), quote=True)


def render_links(links):
    items = []
    for link in links:
        label = escape(link["label"])
        url = escape(link["url"])
        items.append(f'<a class="hero-link" href="{url}">{label}<span>{url}</span></a>')
    return "".join(items)


def render_summary(summary):
    return "".join(
        f'<p class="summary-paragraph">{escape(paragraph)}</p>' for paragraph in summary
    )


def render_entry(entry):
    bullets = "".join(f"<li>{escape(bullet)}</li>" for bullet in entry["bullets"])
    subtitle_parts = [entry.get("role"), entry.get("location")]
    subtitle = " | ".join(part for part in subtitle_parts if part)
    return f"""
    <article class="entry">
      <div class="entry-header">
        <div>
          <div class="entry-title">{escape(entry["company"])}</div>
          <div class="entry-subtitle">{escape(subtitle)}</div>
        </div>
        <div class="entry-date">{escape(entry["date_range"])}</div>
      </div>
      <ul class="entry-list">{bullets}</ul>
    </article>
    """


def render_project(project):
    bullets = "".join(f"<li>{escape(bullet)}</li>" for bullet in project["bullets"])
    subtitle = (
        f'<div class="project-subtitle">{escape(project["subtitle"])}</div>'
        if project.get("subtitle")
        else ""
    )
    return f"""
    <article class="entry">
      <div class="project-name">{escape(project["name"])}</div>
      {subtitle}
      <ul class="entry-list">{bullets}</ul>
    </article>
    """


def render_skills(skills):
    rows = []
    for label, values in skills.items():
        rows.append(
            f"""
            <div class="skill-row">
              <div class="skill-label">{escape(label)}</div>
              <div class="skill-value">{escape(", ".join(values))}</div>
            </div>
            """
        )
    return f'<div class="skills-grid">{"".join(rows)}</div>'


def render_education(items):
    rendered = []
    for item in items:
        bullets = "".join(f"<li>{escape(bullet)}</li>" for bullet in item.get("bullets", []))
        details = item.get("details")
        if not details:
            detail_parts = [item.get("degree"), item.get("honors"), item.get("graduation")]
            details = " | ".join(part for part in detail_parts if part)
        rendered.append(
            f"""
            <article class="entry">
              <div class="entry-header">
                <div>
                  <div class="entry-title">{escape(item["school"])}</div>
                  <div class="education-meta">{escape(item.get("location", ""))}</div>
                </div>
              </div>
              <div class="entry-subtitle">{escape(details)}</div>
              <ul class="entry-list">{bullets}</ul>
            </article>
            """
        )
    return "".join(rendered)


def build_html(payload, template_path, css_path):
    require_keys(
        payload,
        ["basics", "headline", "summary", "experience", "projects", "skills", "education"],
        "resume payload",
    )
    basics = payload["basics"]
    require_keys(basics, ["name", "location", "phone", "email", "links"], "basics")

    template = template_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")

    header = f"""
    <h1 class="hero-name">{escape(basics["name"])}</h1>
    <div class="hero-headline">{escape(payload["headline"])}</div>
    <div class="hero-meta">{escape(basics["location"])} | {escape(basics["phone"])} | {escape(basics["email"])}</div>
    <div class="hero-links">{render_links(basics["links"])}</div>
    """

    replacements = {
        "__TITLE__": escape(f'{basics["name"]} Resume'),
        "__INLINE_CSS__": css,
        "__HEADER__": header,
        "__SUMMARY__": render_summary(payload["summary"]),
        "__EXPERIENCE__": "".join(render_entry(entry) for entry in payload["experience"]),
        "__PROJECTS__": "".join(render_project(project) for project in payload["projects"]),
        "__SKILLS__": render_skills(payload["skills"]),
        "__EDUCATION__": render_education(payload["education"]),
    }

    html_output = template
    for key, value in replacements.items():
        html_output = html_output.replace(key, value)
    return html_output


def main():
    parser = argparse.ArgumentParser(description="Build resume HTML from structured JSON.")
    parser.add_argument("--input", required=True, help="Path to tailored resume JSON.")
    parser.add_argument("--output-html", required=True, help="Destination HTML path.")
    parser.add_argument(
        "--template",
        default="templates/resume_template.html",
        help="Path to the HTML template.",
    )
    parser.add_argument(
        "--css",
        default="templates/resume.css",
        help="Path to the resume stylesheet.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output_html).resolve()
    template_path = Path(args.template).resolve()
    css_path = Path(args.css).resolve()

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    html_output = build_html(payload, template_path, css_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_output, encoding="utf-8")
    print(f"Wrote HTML resume to {output_path}")


if __name__ == "__main__":
    main()
