#!/usr/bin/env python3
"""
analyze_job_description.py

Extracts structured keywords, requirements, and phrases from a job request (or raw JD text)
to support accurate, best-practice tailoring of resumes and cover letters.

Follows researched methods:
- Highlight repeated/emphasized terms
- Separate required vs preferred
- Pull action verbs + responsibilities
- Identify high-value exact phrases to echo (esp. for cover letters)
- Provide human-readable summary for prompts

Usage examples:
  python scripts/analyze_job_description.py --request requests/ovatech-web-developer.md --output generated/ovatech-opc-web-developer/
  python scripts/analyze_job_description.py --jd-file some-jd.txt --format text
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

# Reuse robust parsing from the package runner (no duplication)
import sys
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import run_request_package as runner  # provides parse_frontmatter, extract_section, etc.


STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "with", "as", "by",
    "is", "are", "be", "will", "should", "must", "can", "may", "from", "that", "this",
    "we", "you", "your", "our", "their", "company", "role", "position", "team", "work",
    "experience", "job", "candidate", "applicant", "requirements", "responsibilities",
    "including", "etc", "etc.", "plus", "preferred", "required", "qualification",
    "qualifications", "skills", "ability", "abilities", "strong", "excellent", "highly",
    "minimum", "years", "year", "degree", "bachelor", "bachelor's", "remote", "full-time",
}

COMMON_ACTION_VERBS = {
    "build", "develop", "design", "implement", "create", "manage", "lead", "analyze",
    "research", "synthesize", "organize", "maintain", "track", "collaborate", "support",
    "iterate", "prototype", "automate", "optimize", "deliver", "coordinate", "improve",
    "integrate", "test", "deploy", "review", "architect", "drive", "ensure", "identify",
}

TECH_PATTERN = re.compile(
    r"\b(React|TypeScript|Node\.?js|MongoDB|Prisma|Next\.?js|Tailwind|Jest|Playwright|"
    r"GitHub|Docker|Firebase|Notion|Webflow|Zapier|Make|Airtable|Salesforce|HubSpot|"
    r"Python|JavaScript|REST|API|JWT|Zod|Express|Agile|Scrum|CI/CD|No-code|Low-code)\b",
    re.IGNORECASE,
)


def clean_phrase(phrase: str) -> str:
    phrase = phrase.strip()
    phrase = re.sub(r"\s+", " ", phrase)
    phrase = phrase.strip(" ,.;:()[]\"'")
    return phrase


def extract_keywords_from_text(text: str, top_n: int = 25) -> List[str]:
    """Simple frequency-based n-gram extraction for high-impact keywords/phrases."""
    lowered = text.lower()
    # Capture 1-5 word phrases around interesting contexts
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\.\-\+#/]*", lowered)
    ngrams: List[str] = []

    # unigrams (non-stop)
    for w in words:
        if w not in STOP_WORDS and len(w) > 2:
            ngrams.append(w)

    # bigrams + trigrams
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        if words[i] not in STOP_WORDS and words[i+1] not in STOP_WORDS:
            ngrams.append(bigram)
    for i in range(len(words) - 2):
        trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
        if all(w not in STOP_WORDS for w in [words[i], words[i+1], words[i+2]]):
            ngrams.append(trigram)

    # also capture some 4-grams around "using", "with", "and"
    for i in range(len(words) - 3):
        four = " ".join(words[i : i + 4])
        if "using" in four or "with " in four or " and " in four:
            ngrams.append(four)

    counts = Counter(ngrams)
    # Boost tech terms and known verbs
    scored = []
    for phrase, count in counts.items():
        score = count
        if any(v in phrase for v in COMMON_ACTION_VERBS):
            score += 1.5
        if TECH_PATTERN.search(phrase):
            score += 2
        if count >= 2:  # repeated = high priority per best practices
            score += 1
        scored.append((score, phrase))

    scored.sort(reverse=True)
    seen = set()
    results = []
    for _, p in scored:
        cp = clean_phrase(p)
        if cp and cp not in seen and len(cp) > 2:
            seen.add(cp)
            results.append(cp)
            if len(results) >= top_n:
                break
    return results


def extract_exact_phrases(text: str, min_words: int = 5, max_words: int = 14) -> List[str]:
    """Pull longer candidate phrases that are likely to be valuable to echo (esp. in cover letters)."""
    # Look for full responsibility sentences or "build X using Y" style phrases
    sentences = re.split(r"[.!?]\s+", text)
    candidates = []
    for s in sentences:
        s = clean_phrase(s)
        wc = len(s.split())
        if min_words <= wc <= max_words:
            # prefer those with action verbs or tech
            if any(v in s.lower() for v in COMMON_ACTION_VERBS) or TECH_PATTERN.search(s):
                candidates.append(s)
    # Also explicit "build and iterate..." style from the example JD
    explicit = re.findall(r'([A-Z][^.!?]{' + str(min_words*4) + r',50}?(?:tools|systems|workflows|research|prototypes)[^.!?]{0,30}?)', text)
    for e in explicit:
        c = clean_phrase(e)
        if c and len(c.split()) >= min_words:
            candidates.append(c)
    # Dedup preserving order
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:8]


def categorize(text: str) -> Dict[str, List[str]]:
    """Identify required vs preferred and responsibilities using common JD structures."""
    lowered = text.lower()

    required = []
    preferred = []

    # Labeled sections
    req_match = re.search(r"(?:specific requirements|requirements|we are looking for the following|must have|required).*?(?=\n\n|\n[A-Z]|\Z)", text, re.IGNORECASE | re.DOTALL)
    if req_match:
        for line in re.findall(r"[-•*]\s*(.+)", req_match.group(0)):
            t = clean_phrase(line)
            if t:
                required.append(t)

    pref_match = re.search(r"(?:preferred|nice to have|bonus|experience with).*?(?=\n\n|\n[A-Z]|\Z)", text, re.IGNORECASE | re.DOTALL)
    if pref_match:
        for line in re.findall(r"[-•*]\s*(.+)", pref_match.group(0)):
            t = clean_phrase(line)
            if t:
                preferred.append(t)

    # Fallback: split by "experience:" labels often seen
    exp_labels = re.findall(r"(?:Experience:)\s*(.+?)(?:\n\n|\n[A-Z]|\Z)", text, re.IGNORECASE | re.DOTALL)
    for block in exp_labels:
        for item in re.findall(r"[-•*]\s*(.+)", block):
            t = clean_phrase(item)
            if t and "(preferred)" in t.lower():
                preferred.append(t.replace("(preferred)", "").strip())
            elif t:
                required.append(t)

    # Responsibilities section
    resp_section = re.search(
        r"(?:responsibilities will include|your responsibilities|responsibilities).*?(?=\n\n|\n[A-Z]{3,}|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    responsibilities: List[str] = []
    if resp_section:
        for line in re.findall(r"[-•*]\s*(.+)", resp_section.group(0)):
            t = clean_phrase(line)
            if t:
                responsibilities.append(t)

    # Fallback plain bullets after "responsibilities" heading if present in body
    if not responsibilities:
        for m in re.finditer(r"^[-*]\s+(.+)$", text, re.MULTILINE):
            responsibilities.append(clean_phrase(m.group(1)))

    return {
        "required": [r for r in required if r][:10],
        "preferred": [p for p in preferred if p][:8],
        "responsibilities": responsibilities[:12],
    }


def extract_verbs(text: str) -> List[str]:
    verbs = set()
    for match in re.finditer(r"\b([A-Za-z]{3,})\b", text):
        w = match.group(1).lower()
        if w in COMMON_ACTION_VERBS:
            verbs.add(w)
    return sorted(verbs)


def build_analysis_text(analysis: Dict, jd_snippet: str) -> str:
    lines = []
    lines.append("=== JOB DESCRIPTION ANALYSIS (use for precise tailoring) ===")
    if analysis.get("role"):
        lines.append(f"Target Role: {analysis['role']}")
    if analysis.get("company"):
        lines.append(f"Company: {analysis['company']}")
    lines.append("")

    hp = analysis.get("high_priority_keywords", [])
    if hp:
        lines.append("HIGH-PRIORITY KEYWORDS (mirror these exactly where truthful):")
        lines.append(", ".join(hp[:15]))
        lines.append("")

    ex = analysis.get("exact_phrases", [])
    if ex:
        lines.append("EXACT PHRASES TO ECHO (include 3+ naturally in cover letter + resume):")
        for p in ex[:5]:
            lines.append(f"- {p}")
        lines.append("")

    cat = analysis.get("categorized", {})
    if cat.get("required"):
        lines.append("REQUIRED / CORE QUALIFICATIONS:")
        for r in cat["required"][:6]:
            lines.append(f"- {r}")
        lines.append("")

    if cat.get("responsibilities"):
        lines.append("KEY RESPONSIBILITIES (lead with matching evidence):")
        for r in cat["responsibilities"][:6]:
            lines.append(f"- {r}")
        lines.append("")

    verbs = analysis.get("key_verbs", [])
    if verbs:
        lines.append(f"ACTION VERBS TO MIRROR: {', '.join(verbs)}")
        lines.append("")

    lines.append("GUIDANCE: Prioritize direct matches from master_resume.json. Reorder bullets so strongest evidence appears first. Use the exact words above in summary, bullets, and cover letter.")
    lines.append("=== END ANALYSIS ===")
    return "\n".join(lines)


def analyze_request_or_text(request_path: Path | None = None, jd_text: str | None = None) -> Dict:
    if request_path:
        md = request_path.read_text(encoding="utf-8")
        frontmatter, body = runner.parse_frontmatter(md)
        job_description = runner.extract_section(body, "Job Description") or body
        role = (frontmatter.get("role") or "").strip()
        company = (frontmatter.get("company") or "").strip()
        extra = runner.extract_section(body, "Extra Instructions") or ""
        full_text = job_description + "\n" + extra
    else:
        frontmatter = {}
        job_description = jd_text or ""
        full_text = job_description
        role = ""
        company = ""

    # Extract
    high_priority = extract_keywords_from_text(full_text, top_n=22)
    exact = extract_exact_phrases(full_text)
    cat = categorize(full_text)
    verbs = extract_verbs(full_text)

    # Boost from explicit tech matches in original case
    tech_found = []
    for m in TECH_PATTERN.finditer(job_description or full_text):
        t = m.group(1)
        if t not in tech_found:
            tech_found.append(t)

    # Merge and dedup preserving some priority
    final_keywords = []
    seen = set()
    for k in (tech_found + high_priority):
        ck = clean_phrase(k)
        if ck and ck.lower() not in seen:
            seen.add(ck.lower())
            final_keywords.append(ck)
    final_keywords = final_keywords[:20]

    analysis = {
        "role": role,
        "company": company,
        "high_priority_keywords": final_keywords,
        "exact_phrases": exact,
        "key_verbs": verbs,
        "categorized": cat,
        "source_length": len(full_text),
    }
    analysis["analysis_text"] = build_analysis_text(analysis, job_description[:600])
    return analysis


def main():
    parser = argparse.ArgumentParser(description="Analyze job description for accurate resume/cover tailoring.")
    parser.add_argument("--request", help="Path to requests/*.md containing frontmatter + ## Job Description")
    parser.add_argument("--jd-file", help="Raw job description text file")
    parser.add_argument("--jd-text", help="Inline job description text (for scripting)")
    parser.add_argument("--output", default="", help="Directory or file path to write analysis.json (and text summary)")
    parser.add_argument("--format", choices=["json", "text", "both"], default="both", help="Output format")
    args = parser.parse_args()

    request_path = Path(args.request).resolve() if args.request else None
    jd_text = None
    if args.jd_file:
        jd_text = Path(args.jd_file).resolve().read_text(encoding="utf-8")
    elif args.jd_text:
        jd_text = args.jd_text

    if not request_path and not jd_text:
        parser.error("Provide one of --request, --jd-file, or --jd-text")

    analysis = analyze_request_or_text(request_path=request_path, jd_text=jd_text)

    out_dir = None
    out_file = None
    if args.output:
        p = Path(args.output)
        if p.suffix.lower() == ".json":
            out_file = p
            out_dir = p.parent
        else:
            out_dir = p
            out_dir.mkdir(parents=True, exist_ok=True)

    # Always print the analysis_text to stdout (useful in prompts / logs)
    if args.format in ("text", "both"):
        print(analysis["analysis_text"])

    # Write files
    if out_dir or out_file:
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
        if out_file:
            json_path = out_file
        else:
            # conventional name
            json_path = out_dir / "analysis.json"

        json_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
        print(f"\nWrote structured analysis to {json_path}")

        if args.format in ("text", "both"):
            txt_path = json_path.with_suffix(".txt")
            txt_path.write_text(analysis["analysis_text"], encoding="utf-8")
            print(f"Wrote readable analysis to {txt_path}")

    return analysis


if __name__ == "__main__":
    main()
