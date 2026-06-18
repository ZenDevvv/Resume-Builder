# Resume Editor Workflow

This workspace is a prompt-driven resume and cover-letter package builder.  
You provide one request markdown file plus one instruction prompt tag, and an agent (Codex or similar) generates tailored source files and final PDFs in a versioned output folder.

## Core Files

- `data/master_resume.json`
  Canonical source of truth. Keep factual.
- `prompt_guide.md`
  Tailoring rules and guardrails.
- `instructions/auto_builder_prompt.md`
  Standard execution prompt for agent-style AI.
- `requests/request_template.md`
  Template for per-job request files.
- `scripts/run_request_package.py`
  Validation + orchestration entrypoint.
- `scripts/package_application.py`
  Packaging/build/render pipeline.

## One-Prompt Agent Flow

1. Create a request file under `requests/` (copy `requests/request_template.md`).
2. Ask the agent in one message using tagged files:

   `Use @instructions/auto_builder_prompt.md and @requests/<name>.md`

3. Agent generates:
   - `requests/<name>.resume.json`
   - `requests/<name>.cover-letter.md`
4. Agent runs:

```powershell
python scripts/run_request_package.py --request requests/<name>.md
```

5. Pipeline validates, versions, builds HTML, and renders PDFs in `generated/`.

## Request File Contract

Each request markdown should use frontmatter:

- Required: `role`
- Optional: `company`, `focus`, `tone`

Body sections:

- Required: `## Job Description` (full JD text inline)
- Optional: `## Extra Instructions`

The packaging runner expects generated source files beside the request:

- `requests/<name>.resume.json`
- `requests/<name>.cover-letter.md`

## Output Structure

Each run writes to:

- `generated/<company-role-slug>/` when company exists (frontmatter or inferred)
- `generated/<role-slug>/` when company is missing

Versioned artifacts:

- `resume.vNNN.json`
- `resume.vNNN.html`
- `resume.vNNN.pdf`
- `cover-letter.vNNN.md`
- `cover-letter.vNNN.html`
- `cover-letter.vNNN.pdf`
- `request.vNNN.md`

Repeated runs increment version (`v001`, `v002`, ...).

## Validation Behavior

`scripts/run_request_package.py` fails fast with explicit errors when:

- request frontmatter is invalid or missing `role`
- `## Job Description` is missing/empty
- `requests/<name>.resume.json` is missing or structurally invalid
- `requests/<name>.cover-letter.md` is missing or empty

If `company` is not provided, it attempts conservative inference from the JD text.

## Manual Packaging (Legacy)

You can still run the original packaging command directly:

```powershell
python scripts/package_application.py `
  --resume-input samples/acme-frontend-engineer/resume.json `
  --cover-letter-input samples/acme-frontend-engineer/cover-letter.md `
  --role "Frontend Engineer" `
  --company "Acme" `
  --request-file samples/acme-frontend-engineer/request.md
```

## Re-extracting Source PDF

If the source resume PDF changes:

```powershell
python scripts/extract_pdf_resume.py --input "Zen Obrero RESUME.pdf" --output generated/source_extract.json
```

Then manually update `data/master_resume.json` to keep it factual and structured.
