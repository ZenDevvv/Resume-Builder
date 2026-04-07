# Resume Editor Workflow

This workspace is a Codex-assisted application package generator built around a factual source resume, prompt-guided tailoring rules, and a repeatable HTML-to-PDF pipeline.

## Core Files

- `data/master_resume.json`
  Canonical source of truth extracted from the original resume PDF. Keep this factual.
- `prompt_guide.md`
  Rules Codex should follow when tailoring both resumes and cover letters.
- `templates/resume_template.html`
  HTML shell used for generated resumes.
- `templates/resume.css`
  ATS-friendly styling for resume HTML and PDF.
- `templates/cover_letter_template.html`
  HTML shell used for generated cover letters.
- `templates/cover_letter.css`
  ATS-friendly styling for cover-letter HTML and PDF.

## Output Structure

Each job-description prompt should create its own package folder under `generated/`.

Folder naming:

- `generated/<company-role-slug>/` when the company can be identified
- `generated/<role-slug>/` when the company is missing

Versioned files inside the folder:

- `resume.vNNN.json`
- `resume.vNNN.html`
- `resume.vNNN.pdf`
- `cover-letter.vNNN.md`
- `cover-letter.vNNN.html`
- `cover-letter.vNNN.pdf`
- `request.vNNN.md`

Repeated runs for the same slug stay in the same folder and create `v002`, `v003`, and so on.

## Sample Inputs

The `samples/` folder now uses the same package naming pattern as generated application folders, but stores source inputs instead of rendered outputs.

Examples:

- `samples/acme-frontend-engineer/`
- `samples/fullstack-developer/`

Each sample folder contains:

- `resume.json`
- `cover-letter.md`
- `request.md`

## Workflow

1. Start from `data/master_resume.json`.
2. Read `prompt_guide.md`.
3. Tailor the resume JSON and cover-letter Markdown for the target job.
4. Package the application into a versioned folder.
5. Build HTML outputs.
6. Render PDFs.

## Packaging Command

Once the tailored resume JSON and cover-letter Markdown exist, package them with:

```powershell
python scripts/package_application.py `
  --resume-input samples/acme-frontend-engineer/resume.json `
  --cover-letter-input samples/acme-frontend-engineer/cover-letter.md `
  --role "Frontend Engineer" `
  --company "Acme" `
  --request-file samples/acme-frontend-engineer/request.md
```

This command creates the folder if needed, selects the next version number, copies the source artifacts, builds the HTML files, renders the PDFs, and writes a request snapshot.

## Re-extracting the Source PDF

If the source PDF changes, extract its text and link metadata first:

```powershell
python scripts/extract_pdf_resume.py --input "Zen Obrero RESUME.pdf" --output generated/source_extract.json
```

Then update `data/master_resume.json` manually so it stays structured and factual.

## How To Use Codex

Tell Codex what kind of application package you want, for example:

- "Create an application package for a frontend engineer role at Acme focused on React dashboards."
- "Tailor the resume and write a cover letter for a fullstack Node.js role with Prisma and multi-tenant systems."
- "Make an enterprise product engineer package for an ERP SaaS company."

Codex should:

1. Read `data/master_resume.json`.
2. Read `prompt_guide.md`.
3. Infer the role and company when possible.
4. Create a new application folder in `generated/`.
5. Save the request snapshot, tailored resume JSON, and cover-letter Markdown.
6. Build the HTML files and render the PDFs.
7. Return the package folder path plus a short summary of what changed.

## Notes

- The master source should remain factual.
- Tailored outputs may reorder, compress, and lightly expand wording, but must not invent employers, dates, metrics, tools, or project scope.
- Cover letters should be conservative and factual, using the same source resume and prompt.
- The HTML outputs are intentionally clean and ATS-friendly rather than visually identical to the original resume PDF.
