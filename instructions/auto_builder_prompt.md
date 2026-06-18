# Auto Builder Prompt (Agent Execution)

Use this file as the instruction source when generating one tailored application package from a request file.

## Inputs You Must Read

1. `data/master_resume.json`
2. `prompt_guide.md`
3. Tagged request file in `requests/*.md`

## Required Output Files (same basename as request)

Given a request file `requests/<name>.md`, create:

- `requests/<name>.resume.json`
- `requests/<name>.cover-letter.md`

The resume JSON must satisfy the renderer contract used by `scripts/build_resume.py`:

- top-level keys: `basics`, `headline`, `summary`, `experience`, `projects`, `skills`, `education`
- `basics` keys: `name`, `location`, `phone`, `email`, `links`

## Content Rules

- Stay factual and traceable to `data/master_resume.json`.
- Do not invent employers, titles, dates, metrics, tools, customers, or ownership.
- Tailor order and wording conservatively based on request and job description.
- Keep links valid.

## Packaging Command

After writing the two output files, run:

```powershell
python scripts/run_request_package.py --request requests/<name>.md
```

This command validates inputs, infers company from job description when missing, versions outputs, builds HTML, and renders PDFs.

## Final Response Format

Respond with:

1. Generated package folder path
2. Version token
3. Short summary of tailoring decisions
4. Any validation or inference notes
