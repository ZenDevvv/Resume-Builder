# Prompt Guide For Codex Resume And Cover-Letter Tailoring

Use this guide whenever the user asks for a new application package from the master source.

## Mission

Create a targeted resume and cover letter that match the user's hiring goal while staying faithful to `data/master_resume.json`.

The default workflow is two-stage:

**Stage 1 – Create the request (one .md per job, written to requests/)**
- User gives you a job description (or you read one).
- You create a request markdown file (frontmatter + full Job Description section) and save it as `requests/<name>.md`.
- This is the single request md for that job/company.

**Stage 2 – Generate actual resume + cover letter from a request (outputs go to generated/)**
1. Read `data/master_resume.json`.
2. Read this guide.
3. Read the relevant request markdown (from `requests/<name>.md` or the snapshot in `generated/<slug>/request.vNNN.md`).
4. Compute the target slug (see "Slug Rules" below) and generate:
   - `generated/<slug>/resume.json`
   - `generated/<slug>/cover-letter.md`
5. (Optional) If the request snapshot is not yet recorded, run `python scripts/run_request_package.py --request requests/<name>.md`.
6. Return the paths under `generated/<slug>/` + short summary of tailoring decisions.

## Slug Rules (for generated/ folders)

When writing resume and cover letter outputs in Stage 2, place them under `generated/<slug>/` using these rules (identical to the code in `scripts/package_application.py`):

- Lowercase the value.
- Replace any sequence of non-alphanumeric characters with a single `-`.
- If both company and role: `<slug(company)>-<slug(role)>`
- If only role: `<slug(role)>`

Examples:

- Company "OVATech OPC" + role "Web Developer" → `generated/ovatech-opc-web-developer/`
- Role "Frontend Engineer" → `generated/frontend-engineer/`

The live request itself lives in `requests/<name>.md`. Snapshots of it may appear as `request.vNNN.md` inside the generated folder.

**Important:** `requests/` contains **only** the request `.md` files (one per job) + the template. The tailored `resume.json` and `cover-letter.md` (and their HTML/PDF renders) belong in the corresponding `generated/<slug>/` folder.

## Non-Negotiable Rules

- Do not invent employers, titles, dates, technologies, metrics, customers, or project scope.
- Do not claim direct ownership of work that is not supported by the master source.
- Do not turn "AI-assisted" into the primary identity unless the user explicitly wants that angle.
- Keep the resume ATS-friendly: standard headings, plain language, consistent dates, and no gimmicky copy.
- Keep links valid and visible in the final resume output.
- Keep the cover letter factual, targeted, and conservative.
- When generating resume, use black only for all text. Do not use other colors.
- Just use different boldness and italic to differentiate fonts.

## Allowed Tailoring Moves

- Reorder sections to match the target role.
- Reorder bullets so the strongest role-matching evidence appears first.
- Combine or tighten original bullets when the meaning stays intact.
- Lightly expand wording when the expansion is directly supported by source facts.
- Change the headline and summary to emphasize the requested focus.
- Drop less relevant project bullets to improve clarity.
- Adjust the cover-letter tone and emphasis to match the role and company context provided by the user.

## Disallowed Moves

- Fabricating leadership, architecture, or scale claims beyond the source.
- Adding tools or frameworks not present in the master source.
- Making unverified performance claims.
- Rewriting in a way that changes the factual meaning of dates, responsibilities, or results.
- Claiming motivation, personal background, or company knowledge that the prompt does not support.

## Tailoring Algorithm (for resume + cover letter stage)

### 1. Parse the request (the job description)

Read the chosen request file (prefer the versioned one from generated/ if it exists). Extract:

- target role or hiring goal
- company name if identifiable
- strongest skills to highlight
- domains to emphasize
- sections or topics to compress
- tone preference if provided

### 2. Select the best supporting evidence

Prioritize evidence in this order unless the user asks otherwise:

1. direct work experience that matches the target
2. quantified project outcomes
3. relevant systems, tools, and domains
4. education and supporting background

### 3. Rewrite conservatively

- Prefer concise, specific bullets.
- Lead with outcomes and systems, not generic responsibility phrasing.
- Preserve numbers when present.
- If a sentence gets longer, it must also get clearer.

### 4. Build the two actual output files (inside generated/)

- Create a tailored resume JSON → `generated/<slug>/resume.json`
- Create a tailored cover-letter Markdown → `generated/<slug>/cover-letter.md`

After writing them, the visual deliverables (html + pdf) are produced by running the build scripts with paths pointing inside that same `generated/<slug>/` folder.

## Tailored Resume JSON Structure

```json
{
  "meta": {
    "variant": "frontend-focused",
    "target_role": "Frontend Engineer",
    "source": "data/master_resume.json",
    "prompt_summary": "One-line explanation of what this version is optimized for."
  },
  "basics": {
    "name": "Zen Andrei Obrero",
    "location": "Dasmarinas, Cavite",
    "phone": "09068575015",
    "email": "zenandreiobrero777@gmail.com",
    "links": [
      { "label": "Portfolio", "url": "https://zendev-portfolio.netlify.app/" },
      { "label": "GitHub", "url": "https://github.com/ZenDevvv" }
    ]
  },
  "headline": "Frontend Engineer | React, TypeScript, Enterprise UI Systems",
  "summary": [
    "Paragraph one.",
    "Optional paragraph two."
  ],
  "experience": [
    {
      "company": "Uzaro Solutions Technology Inc.",
      "location": "Quezon City",
      "role": "Technology Developer",
      "date_range": "Nov 2024 - Present",
      "bullets": ["..."]
    }
  ],
  "projects": [
    {
      "name": "ALMA (Alternative Learning Management App)",
      "subtitle": "Multi-tenant LMS",
      "bullets": ["..."]
    }
  ],
  "skills": {
    "Frontend": ["React", "TypeScript"],
    "Backend": ["Node.js", "Express"]
  },
  "education": [
    {
      "school": "Biliran Province State University",
      "location": "Naval, Biliran",
      "degree": "Bachelor of Science in Computer Science",
      "details": "With Honors | Graduated May 2024",
      "bullets": ["..."]
    }
  ]
}
```

## Cover Letter Markdown Shape

The cover letter should be saved as Markdown and usually include:

1. an optional title line
2. date
3. salutation
4. 3 to 5 short paragraphs
5. closing and full name

The letter should:

- explain fit for the specific role
- point to relevant systems, domains, or delivery experience
- stay grounded in the master resume facts
- avoid generic hype when evidence is available

## Default Resume Shape

Use this section order unless the prompt suggests a better one:

1. Header
2. Summary
3. Experience
4. Selected Projects
5. Technical Skills
6. Education

## Preferred Tone

- Confident, specific, and professional
- Early-career but already production-proven
- Technical without sounding inflated
- Productive and collaborative rather than purely academic

## Suggestions By Prompt Type

### Frontend-focused prompt

- Lead with React, TypeScript, reusable components, dashboards, and frontend-backend contracts.
- Favor ALMA and IoT dashboard work.
- Move pure backend or lower-relevance ERP details lower unless they support the frontend story.

### Fullstack prompt

- Keep React, Node.js, MongoDB, Prisma, testing, and delivery balanced.
- Emphasize end-to-end ownership and contract alignment.

### Enterprise or product engineer prompt

- Emphasize multi-tenant systems, ERP modules, CI/CD, delivery across multiple platforms, and large data handling.
- Keep quantified scale visible.

## Final Checklist

Confirm:

- every claim is traceable to `data/master_resume.json`
- the summary / letter matches the request (job description)
- the most relevant bullets appear first
- the cover letter matches the target role and company context when known
- The request .md lives in `requests/<name>.md`
- The tailored sources were written to `generated/<slug>/resume.json` and `generated/<slug>/cover-letter.md`
- All text uses black only (differentiate via boldness and italic, no colored text)
