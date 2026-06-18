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
- Never add tools, platforms, or frameworks (Notion, Webflow, Salesforce, etc.) unless they are already present in data/master_resume.json.
- Keep the resume ATS-friendly: standard headings, plain language, consistent dates, and no gimmicky copy.
- Keep links valid and visible in the final resume output.
- Keep the cover letter factual, targeted, and conservative. Echo phrases only where evidence exists.
- When generating resume, use black only for all text. Do not use other colors.
- Just use different boldness and italic to differentiate fonts.
- Always prefer the analysis output (or manual JD extraction) and run validation afterward.

## Allowed Tailoring Moves

- Reorder sections, bullets, and projects to surface strongest JD matches first.
- Reorder skills categories/items to put mirrored keywords early.
- Lightly rephrase using the *exact verbs and nouns* from the JD when the underlying fact from master supports it (e.g., change "Developed ... interfaces" → "Built production-grade React interfaces..." when "build" is in JD).
- Combine or tighten bullets while preserving all numbers and meaning.
- Update headline/summary to directly name the target role + top 2-4 JD keywords.
- Drop low-relevance bullets/projects when it improves signal (never drop to hide gaps).
- Adjust cover letter to specifically reference the role/company and echo JD language.

## Disallowed Moves

- Adding any tool, platform, or technology absent from master (Notion, Webflow, Zapier, etc.).
- Inventing new metrics, "X% improvement", or scale claims.
- Changing dates, titles, companies, or ownership.
- Using JD keywords in a way that implies unsupported experience.
- Over-claiming "expert" or leadership if not supported.
- Generic hype that cannot be backed by specific master facts.

## Keyword-Driven Tailoring Algorithm (Best-Practice Version)

This is the REQUIRED process. It directly implements proven methods:
- Deep JD analysis (highlight repeated keywords, requirements, verbs)
- Exact language mirroring (ATS + recruiter signal)
- Evidence mapping + reorder for relevance
- Strict fidelity to master source
- Cover letter phrase echoing

### 0. Analyze the JD (use analysis artifact when available)

1. Read the full request (`requests/<name>.md` or `generated/<slug>/request.vNNN.md`).
2. **If present**, load `analysis.json` or `analysis.txt` produced by `scripts/analyze_job_description.py`.
   - This gives: high_priority_keywords, exact_phrases, required items, key_verbs, responsibilities.
3. Otherwise manually extract:
   - Repeated or emphasized terms (skills, tools, domains, adjectives).
   - Required vs preferred qualifications.
   - Top action verbs and responsibility phrases.
   - 3–8 exact phrases worth echoing verbatim (gold for cover letters).
4. Write a short explicit list: "Must-mirror: X, Y, Z. Echo in cover: phraseA, phraseB."

**Rule**: Prefer the exact wording from the JD when your master facts support it.

### 1. Evidence mapping (two-column discipline)

Create a quick mental or scratch map:

JD Requirement / Keyword                  | Best supporting fact from data/master_resume.json (only)
------------------------------------------|------------------------------------------------------------
"Build and iterate clickable prototypes"  | ALMA + HMS multi-tenant builds + reusable React components
"No-code / low-code" + AI tools           | "AI-assisted workflow with Claude Opus, Codex, Gemini..." + prototyping speed
"Organize projects / Notion / documentation" | GitHub Projects + custom PMS + sprint delivery across 6+ platforms
"Research + synthesize"                   | Assessment/analytics modules + quantified outcomes

Prioritize in this strict order:
1. Direct work experience bullets that match target.
2. Quantified project outcomes (preserve numbers).
3. Relevant tools/systems/domains exactly as named in master.
4. Education + professional development (only if strong fit).

Drop or deprioritize anything with weak/no match.

### 2. Restructure + mirror language

- **Headline**: Start with target role | 2-4 strongest mirrored keywords.
- **Summary**: 1-2 short paragraphs. Include role title + 3+ high-priority keywords naturally in first paragraph.
- **Experience**: Reorder bullets so the single strongest JD-aligned bullet is first for the current role. Use exact JD verbs ("build", "iterate", "organize", "research") where the meaning is supported.
- **Projects**: Reorder + tighten so most relevant projects appear first. Update subtitle if it helps relevance.
- **Skills**: Reorder categories and items so JD-matched skills appear early (Frontend first if web role, etc.). Never add tools absent from master.
- Bullets must:
  - Lead with outcome or system (not "Responsible for...").
  - Use the JD's phrasing when truthful ("build and iterate clickable prototypes", "type-safe contracts", etc.).
  - Keep all original metrics.

### 3. Cover letter (exact phrase rule)

The cover letter MUST:
- Address the specific role and company (when known).
- Naturally echo **at least three** exact phrases or keyword clusters from the JD (research shows this strongly improves response rates).
- Point to 2–3 concrete, quantified proofs from your map.
- Stay 3–5 short paragraphs, professional, conservative.

Example good echo (when supported): "Build and iterate clickable prototypes using AI-powered platforms while maintaining structured project visibility."

### 4. Write the files + self-verify

Write:
- `generated/<slug>/resume.json` (update meta.variant and meta.prompt_summary to reference the JD focus + keywords used)
- `generated/<slug>/cover-letter.md`

Before finishing, run this mental checklist:

- [ ] All claims traceable to data/master_resume.json (no new employers, tools, dates, metrics, ownership).
- [ ] High-priority JD keywords appear in headline, summary, and at least one early bullet.
- [ ] At least 3 exact phrases or strong clusters echoed in the cover letter.
- [ ] Strongest evidence ordered first (no burying matches).
- [ ] No keyword stuffing — language stays natural and professional.
- [ ] Run `python scripts/validate_tailoring.py --slug <slug>` and address any "MISSING" or "FIDELITY WARNINGS".

After writing the two source files, the HTML/PDF are produced with the existing build commands.

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

Use the keyword analysis to decide emphasis. Examples below assume common dev roles:

### Frontend-focused prompt

- Lead with React, TypeScript, reusable components, dashboards, and frontend-backend contracts.
- Favor ALMA and IoT dashboard work.
- Move pure backend or lower-relevance ERP details lower unless they support the frontend story.
- Mirror exact frontend-related verbs from JD (build, iterate, integrate).

### Fullstack prompt

- Keep React, Node.js, MongoDB, Prisma, testing, and delivery balanced.
- Emphasize end-to-end ownership and contract alignment.

### Enterprise or product engineer prompt

- Emphasize multi-tenant systems, ERP modules, CI/CD, delivery across multiple platforms, and large data handling.
- Keep quantified scale visible.

## Final Checklist (Run After Generation)

Confirm (and preferably run `python scripts/validate_tailoring.py --slug <slug>`):

- Every claim is traceable to `data/master_resume.json` (no new tools, numbers, employers, ownership).
- High-priority keywords from the JD (or analysis.json) appear naturally in headline + summary + early bullets.
- At least 3 exact JD phrases or strong clusters are echoed in the cover letter.
- Strongest matching evidence is ordered first (bullets + projects).
- The summary / letter matches the request focus and tone.
- The request .md lives in `requests/<name>.md` and analysis (if generated) is next to the snapshot.
- The tailored sources were written to `generated/<slug>/resume.json` and `generated/<slug>/cover-letter.md`.
- All text uses black only (differentiate via boldness and italic, no colored text).
- Validation report shows reasonable coverage with zero fidelity warnings.
