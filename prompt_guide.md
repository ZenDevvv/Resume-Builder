# Prompt Guide For Codex Resume And Cover-Letter Tailoring

Use this guide whenever the user asks for a new application package from the master source.

## Mission

Create a targeted resume and cover letter that match the user's hiring goal while staying faithful to `data/master_resume.json`.

The default workflow is:

1. Read `data/master_resume.json`.
2. Read this guide.
3. Read the request file under `requests/*.md` and extract role/company context plus full job description.
4. Generate and save:
   - `requests/<name>.resume.json`
   - `requests/<name>.cover-letter.md`
5. Run `python scripts/run_request_package.py --request requests/<name>.md`.
6. Return the generated package folder path, version, and short summary of tailoring decisions.

## Package Naming Rules

- Use a filesystem-safe lowercase slug.
- If both company and role are known, use `company-role`.
- If the company is missing, use the role only.
- Repeated runs for the same slug should stay in the same folder and increment the version number.

Examples:

- `generated/acme-frontend-engineer/`
- `generated/fullstack-developer/`

## Non-Negotiable Rules

- Do not invent employers, titles, dates, technologies, metrics, customers, or project scope.
- Do not claim direct ownership of work that is not supported by the master source.
- Do not turn "AI-assisted" into the primary identity unless the user explicitly wants that angle.
- Keep the resume ATS-friendly: standard headings, plain language, consistent dates, and no gimmicky copy.
- Keep links valid and visible in the final resume output.
- Keep the cover letter factual, targeted, and conservative.

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

## Tailoring Algorithm

### 1. Parse the user request

Extract:

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

### 4. Build both outputs

- Create a tailored resume JSON.
- Create a tailored cover-letter Markdown file.
- Write the original prompt or job-targeting instruction to `request.vNNN.md`.

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

Before building the PDFs, confirm:

- every claim is traceable to `data/master_resume.json`
- the summary matches the prompt
- the most relevant bullets appear first
- the cover letter matches the target role and company context when known
- the final JSON and Markdown are complete
- the outputs are stored in the correct package folder and version
