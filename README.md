# Resume Editor Workflow

This workspace is a prompt-driven system where:

- You create **one request .md per job** (the job description + frontmatter) in the `requests/` folder.
- In a follow-up step you generate the tailored **resume** and **cover letter** based on that request; those outputs are placed inside `generated/<company-or-role-slug>/`.

**Core rule:** `requests/` holds **exactly one request markdown file per job/company** (plus the template). All tailored resume + cover letter outputs (JSON + MD sources + their rendered HTML/PDF) live under the matching folder in `generated/`.

## Core Files

- `data/master_resume.json`
  Canonical source of truth. Keep factual.
- `prompt_guide.md`
  Tailoring rules and guardrails (now includes the full Keyword-Driven Tailoring Algorithm).
- `instructions/auto_builder_prompt.md`
  Standard execution prompt for agent-style AI.
- `requests/request_template.md`
  Template you copy to create a new per-job request.
- `requests/<name>.md`
  The single request markdown for one job (frontmatter + full Job Description). One per job.
- `scripts/run_request_package.py`
  Validates a request and records a versioned snapshot (`request.vNNN.md`) into the corresponding generated/ folder.
- `scripts/package_application.py`
  Low-level helper that creates the job folder under generated/ and writes the request snapshot.
- `scripts/analyze_job_description.py` + `scripts/validate_tailoring.py`
  Tools that extract JD keywords/phrases and verify post-generation accuracy (coverage + fidelity).
- `scripts/analyze_job_description.py`
  Extracts high-priority keywords, exact phrases, responsibilities, and requirements from the JD. Produces analysis.json + readable summary used to drive accurate tailoring.
- `scripts/validate_tailoring.py`
  After generation, reports keyword coverage %, echoed phrases in cover letter, and fidelity warnings vs master. Use this to verify accuracy.

## Typical Usage (Two-Stage)

**Stage 1 – Create the request (one .md per job in requests/)**

1. Prompt the agent with the pasted job description.  
   The agent creates **one request markdown** under `requests/` (copy `request_template.md` first).

   Example result:
   - `requests/ovatech-web-developer.md`

2. (Recommended) Record/version the request:

```powershell
python scripts/run_request_package.py --request requests/<name>.md
```

   This creates `generated/<slug>/` and writes `request.vNNN.md` (history of the job request).

3. **Analyze the job description for accurate tailoring** (new best-practice step):

```powershell
python scripts/analyze_job_description.py --request requests/<name>.md --output generated/<slug>/
```

   This produces `analysis.json` and `analysis.txt` with high_priority_keywords and exact_phrases. The AI must use these for mirroring.

**Stage 2 – Generate resume + cover letter (outputs go into generated/)**

4. In a separate prompt, point the agent at the request + analysis and say "generate the resume and cover letter for this job using the Keyword-Driven Tailoring Algorithm in prompt_guide.md. Place the outputs inside the generated company folder."

   The agent produces (directly under the job folder):
   - `generated/<slug>/resume.json`
   - `generated/<slug>/cover-letter.md`

5. (Strongly recommended) Validate tailoring accuracy:

```powershell
python scripts/validate_tailoring.py --slug <slug>
```

   Review the coverage report and fix gaps if needed by regenerating with better evidence mapping.

6. Build the visual outputs (HTML + PDF) from the sources that now live in generated/:

```powershell
python scripts/build_resume.py --input generated/<slug>/resume.json --output-html generated/<slug>/resume.html
python scripts/build_cover_letter.py --input-md generated/<slug>/cover-letter.md --output-html generated/<slug>/cover-letter.html --role "..." --company "..."
python scripts/render_pdf.py --html generated/<slug>/resume.html --pdf generated/<slug>/resume.pdf
# repeat for cover-letter
```

Each request in `requests/` represents one job/company. All deliverables for that job live together in the matching `generated/<slug>/` folder.

## Accuracy & Best-Practice Tailoring (New Workflow)

To produce resumes and cover letters that are accurately fitted:

- Always run analysis before generation (gives objective keywords + exact phrases to mirror).
- The AI follows the detailed Keyword-Driven Tailoring Algorithm (see `prompt_guide.md`).
- After generation, always run the validator. Aim for:
  - Reasonable keyword coverage (exact terms from JD appear).
  - ≥3 exact phrase echoes in the cover letter.
  - Zero fidelity warnings (no invented tools/metrics).
- The validator + analysis make the tailoring auditable and repeatable.
- This process directly applies industry best practices for ATS + human review.

## Request File Contract

Each request markdown should use frontmatter:

- Required: `role`
- Optional: `company`, `focus`, `tone`

Body sections:

- Required: `## Job Description` (full JD text inline)
- Optional: `## Extra Instructions`

The request file (in `requests/`) is the source of truth for "what job is this for".

The runner (`run_request_package.py`) only cares about the request itself.  
Resume and cover letter sources are created in a later step and are placed directly inside the corresponding `generated/<slug>/` folder.

## Output Structure (per-job generated/ folder)

For every job you create a request for, a folder is created under `generated/` using a slug (`company-role` or just `role`):

`generated/<slug>/` contains the full package for that job:

- `request.vNNN.md` (versioned snapshots of the original request)
- `resume.json` (tailored structured resume – written by the generator in Stage 2)
- `cover-letter.md` (tailored cover letter – written by the generator in Stage 2)
- `resume.html`, `resume.pdf`
- `cover-letter.html`, `cover-letter.pdf`

`requests/` itself only ever contains the live request markdown files (one per job) + the template. No resume or cover letter files belong there.

Repeated runs increment the version for request snapshots (`v001`, `v002`, ...). The current `resume.json` and `cover-letter.md` are the latest sources (non-versioned).

## Validation Behavior

`scripts/run_request_package.py` fails fast with explicit errors when:

- request frontmatter is invalid or missing `role`
- `## Job Description` is missing/empty

Resume and cover letter sources are **not** validated or required when recording the request (they are generated in Stage 2 and placed in the generated/ job folder).

If `company` is not provided, it attempts conservative inference from the JD text.

## Manual Recording of a Request

To create/refresh the generated job folder + record a snapshot of the request:

```powershell
python scripts/package_application.py `
  --role "Web Developer" `
  --company "OVATech OPC" `
  --request-file requests/ovatech-web-developer.md
```

This creates the folder (e.g. `generated/ovatech-opc-web-developer/`) and writes `request.vNNN.md`.

After Stage 2 (when `resume.json` and `cover-letter.md` already exist inside the generated folder), you can run the build commands shown in the Typical Usage section.

## Re-extracting Source PDF

If the source resume PDF changes:

```powershell
python scripts/extract_pdf_resume.py --input "Zen Obrero RESUME.pdf" --output generated/source_extract.json
```

Then manually update `data/master_resume.json` to keep it factual and structured.

(Note: source_extract.json is an exception and lives in generated/ for inspection only.)
