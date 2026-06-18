# Auto Builder Prompt (Agent Execution)

Use this file as the instruction source when generating tailored resume and cover letter for a job request.

## Usage Flow

There are two distinct stages:

1. **Request generation** (first interaction):
   - User provides a job description (paste the JD).
   - You create **one** well-formed request markdown file and write it to `requests/<name>.md` (using frontmatter + ## Job Description).
   - This is the single request .md for that job/company.

2. **Resume + Cover Letter generation** (separate later prompt):
   - User asks you to generate the actual files **based on the request**.
   - You read the request (from `requests/<name>.md` or the snapshot `generated/<slug>/request.vNNN.md`).
   - **Run (or ensure existence of) analysis**: `python scripts/analyze_job_description.py --request requests/<name>.md --output generated/<slug>/` if `analysis.json` is missing.
   - You compute (or are told) the target slug folder and write the outputs **directly into `generated/<slug>/`**:
     - `generated/<slug>/resume.json`
     - `generated/<slug>/cover-letter.md`

## Inputs You Must Read (for resume/cover stage)

1. `data/master_resume.json`
2. `prompt_guide.md` (the full Keyword-Driven Tailoring Algorithm)
3. The specific request markdown for the target job (the generated request .md or snapshot)
4. **Analysis artifact if available**: `generated/<slug>/analysis.json` or `analysis.txt` (run `python scripts/analyze_job_description.py --request ...` if missing). This provides the high_priority_keywords, exact_phrases, and responsibilities extracted from the JD.

## Required Output Files

After reading the request, determine the target folder using the slug rules (company-role or just role, lowercased, non-alphanumerics turned into single dashes). Write:

- `generated/<slug>/resume.json`
- `generated/<slug>/cover-letter.md`

The resume JSON must satisfy the structure expected by the project (see prompt_guide.md for full shape). Do **not** write these two files into `requests/`.

## Content Rules

- Follow the full "Keyword-Driven Tailoring Algorithm" in prompt_guide.md exactly (analysis first, evidence mapping, reorder + mirror, cover letter echo rule, final self-check).
- Stay factual and traceable to `data/master_resume.json`.
- Do not invent employers, titles, dates, metrics, tools, customers, or ownership. Never add tools absent from the master (e.g. Notion, Webflow, Zapier).
- Use exact JD language for keywords and phrases where your facts support it.
- Keep links valid.
- Follow visual design rules from prompt_guide.md (black text only; differentiate with boldness/italic).
- After writing files, run the validator: `python scripts/validate_tailoring.py --slug <slug>` and note the results.

## Recording the Request (recommended)

After the user creates a request in `requests/`, run (or tell the user to run):

```powershell
python scripts/run_request_package.py --request requests/<name>.md
```

This ensures `generated/<slug>/request.vNNN.md` exists. The folder is now ready for you to write the resume and cover letter sources into it.

## Final Response Format (resume/cover stage)

Respond with:

1. The request you used (`requests/<name>.md` or the snapshot)
2. The generated slug / folder: `generated/<slug>/`
3. Paths of the created `generated/<slug>/resume.json` and `generated/<slug>/cover-letter.md`
4. Short summary of tailoring decisions (include the list of high-priority keywords addressed and order changes made)
5. Analysis used (reference analysis.json or note that you manually extracted)
6. Validation result (paste key lines from `python scripts/validate_tailoring.py --slug <slug>`)
7. Any fidelity notes or remaining gaps

After you write the two source files, remind the user (or run yourself) the build commands to produce HTML + PDF next to them.
