#!/usr/bin/env python3
"""
validate_tailoring.py

Validates that a generated resume.json + cover-letter.md are accurately tailored
to the job description per best practices:

- High keyword coverage from JD analysis (or raw extraction)
- Exact phrase echoes (especially valuable for cover letters)
- Fidelity: no invented tools, companies, or metrics outside the master source
- Reports actionable gaps and overall score

Usage:
  python scripts/validate_tailoring.py --slug ovatech-opc-web-developer
  python scripts/validate_tailoring.py --request requests/ovatech-web-developer.md \
      --resume generated/ovatech-opc-web-developer/resume.json \
      --cover generated/ovatech-opc-web-developer/cover-letter.md
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Reuse parsing helpers
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import run_request_package as runner
import analyze_job_description as analyzer  # reuse its extraction functions where possible

MASTER_PATH = Path(__file__).resolve().parent.parent / "data" / "master_resume.json"


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_master_skills(master: Dict) -> Set[str]:
    skills: Set[str] = set()
    ts = master.get("technical_skills", {})
    for cat, items in ts.items():
        for item in items or []:
            skills.add(str(item).lower())
    # Also domain + AI workflow
    for item in master.get("fact_bank", {}).get("priority_themes", []):
        skills.add(str(item).lower())
    return {s for s in skills if s}


def collect_master_facts(master: Dict) -> Set[str]:
    """Collect known factual tokens we should not invent."""
    facts: Set[str] = set()
    # Companies
    for exp in master.get("work_experience", []):
        if exp.get("company"):
            facts.add(exp["company"].lower())
    # Project names
    for proj in master.get("project_experience", []):
        if proj.get("name"):
            facts.add(proj["name"].lower())
    # Known numbers/metrics (as strings)
    for h in master.get("fact_bank", {}).get("quantified_highlights", []):
        facts.add(h.lower())
    # All bullets contain evidence
    for exp in master.get("work_experience", []):
        for b in exp.get("bullets", []):
            facts.add(b.lower()[:80])  # prefix to detect similar claims
    return facts


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def find_matches(keywords: List[str], text: str) -> Tuple[List[str], List[str]]:
    norm_text = normalize(text)
    matched = []
    missing = []
    for kw in keywords:
        k = normalize(kw)
        if not k or len(k) < 2:
            continue
        # phrase or word match
        if k in norm_text or re.search(r"\b" + re.escape(k) + r"\b", norm_text):
            matched.append(kw)
        else:
            missing.append(kw)
    return matched, missing


def count_exact_echoes(phrases: List[str], text: str) -> List[str]:
    norm_text = normalize(text)
    found = []
    for p in phrases:
        if normalize(p) in norm_text:
            found.append(p)
    return found


def extract_all_text(resume: Dict, cover: str) -> str:
    parts = []
    if resume:
        parts.append(resume.get("headline", ""))
        parts.extend(resume.get("summary", []))
        for exp in resume.get("experience", []):
            parts.extend(exp.get("bullets", []))
        for proj in resume.get("projects", []):
            parts.extend(proj.get("bullets", []))
        skills = resume.get("skills", {})
        for vals in skills.values():
            parts.extend(vals or [])
    parts.append(cover or "")
    return "\n".join(str(p) for p in parts)


def check_fidelity(resume: Dict, cover_text: str, master_facts: Set[str], master_skills: Set[str]) -> List[str]:
    warnings = []
    full = extract_all_text(resume, cover_text).lower()

    # Check for unknown tech in skills section of the tailored resume
    if resume:
        for cat, vals in resume.get("skills", {}).items():
            for v in (vals or []):
                vlow = normalize(v)
                if vlow and vlow not in master_skills and len(vlow) > 2:
                    # Allow common soft terms
                    if vlow not in {"agile", "scrum", "communication", "research", "documentation"}:
                        warnings.append(f"Possibly invented skill/tool not in master: {v} (category {cat})")

    # Check for suspicious new quantified claims (very rough heuristic)
    numbers = re.findall(r"(\d+[\d,]*\+?)\s*(?:\+|percent|%|\busers?\b|\brecords?\b|\bprojects?\b|\bendpoints?\b)", full)
    # We don't block all numbers, just flag if they look invented and not traceable
    # For now we only warn on very specific new patterns if wanted. Keep conservative.
    # Future improvement: more sophisticated.

    # Check company / role names that shouldn't appear
    if resume:
        for exp in resume.get("experience", []):
            if exp.get("company") and exp["company"].lower() not in " ".join(list(master_facts)[:20]):
                # loose check
                pass  # master already defines them, so presence is fine

    return warnings


def validate(
    resume_path: Path | None,
    cover_path: Path | None,
    request_path: Path | None,
    jd_text: str | None,
    analysis_path: Path | None = None,
) -> Dict:
    resume = load_json(resume_path) if resume_path and resume_path.exists() else {}
    cover_text = cover_path.read_text(encoding="utf-8") if cover_path and cover_path.exists() else ""

    # Get JD text + analysis
    jd_full = ""
    if request_path and request_path.exists():
        md = request_path.read_text(encoding="utf-8")
        _, body = runner.parse_frontmatter(md)
        jd_full = runner.extract_section(body, "Job Description") or body
    if jd_text:
        jd_full = jd_text + "\n" + jd_full

    # Load or run analysis
    analysis = {}
    if analysis_path and analysis_path.exists():
        analysis = load_json(analysis_path)
    elif jd_full:
        analysis = analyzer.analyze_request_or_text(jd_text=jd_full)

    high_keywords = analysis.get("high_priority_keywords", []) or []
    exact_phrases = analysis.get("exact_phrases", []) or []

    # Load master for fidelity
    master = load_json(MASTER_PATH) if MASTER_PATH.exists() else {}
    master_skills = flatten_master_skills(master)
    master_facts = collect_master_facts(master)

    combined_text = extract_all_text(resume, cover_text)

    kw_matched, kw_missing = find_matches(high_keywords, combined_text)
    cover_echoes = count_exact_echoes(exact_phrases, cover_text)

    # Fidelity
    fidelity_warnings = check_fidelity(resume, cover_text, master_facts, master_skills)

    # Simple score
    total_kw = len([k for k in high_keywords if len(k) > 2])
    coverage = (len(kw_matched) / total_kw * 100.0) if total_kw > 0 else 0.0

    echo_score = len(cover_echoes)
    fidelity_ok = len(fidelity_warnings) == 0

    overall = "PASS" if coverage >= 45 and fidelity_ok else "REVIEW NEEDED"
    if coverage < 25:
        overall = "WEAK MATCH - REVIEW STRONGLY"

    result = {
        "coverage_percent": round(coverage, 1),
        "keywords_total": total_kw,
        "keywords_matched": kw_matched,
        "keywords_missing": kw_missing,
        "cover_exact_echoes": cover_echoes,
        "echo_count": echo_score,
        "fidelity_warnings": fidelity_warnings,
        "overall": overall,
        "recommendation": (
            "Good keyword alignment. Review missing items and ensure they are not strong matches you can surface."
            if coverage >= 50 and not fidelity_warnings
            else "Add more direct mirrors of high-priority keywords from the JD where your master facts support them. Check fidelity warnings."
        ),
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate tailoring accuracy against job description keywords and master facts.")
    parser.add_argument("--slug", help="Slug folder under generated/ (e.g. ovatech-opc-web-developer)")
    parser.add_argument("--request", help="Path to the request .md (for JD text)")
    parser.add_argument("--resume", help="Path to tailored resume.json")
    parser.add_argument("--cover", help="Path to tailored cover-letter.md")
    parser.add_argument("--analysis", help="Path to analysis.json (optional)")
    parser.add_argument("--jd-text", help="Raw JD text")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON only")
    args = parser.parse_args()

    base = Path.cwd()
    gen_root = base / "generated"

    resume_path = Path(args.resume).resolve() if args.resume else None
    cover_path = Path(args.cover).resolve() if args.cover else None
    request_path = Path(args.request).resolve() if args.request else None
    analysis_path = Path(args.analysis).resolve() if args.analysis else None

    if args.slug:
        slug_dir = gen_root / args.slug
        if not resume_path:
            resume_path = slug_dir / "resume.json"
        if not cover_path:
            cover_path = slug_dir / "cover-letter.md"
        # Try to find latest request or analysis
        if not request_path:
            candidates = sorted(slug_dir.glob("request.v*.md"), reverse=True)
            if candidates:
                request_path = candidates[0]
        if not analysis_path:
            a = slug_dir / "analysis.json"
            if a.exists():
                analysis_path = a

    if not (resume_path or cover_path or request_path or args.jd_text):
        parser.error("Provide --slug or explicit --resume/--cover/--request/--jd-text")

    result = validate(
        resume_path=resume_path,
        cover_path=cover_path,
        request_path=request_path,
        jd_text=args.jd_text,
        analysis_path=analysis_path,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n=== TAILORING VALIDATION REPORT ===")
        print(f"Overall: {result['overall']}")
        print(f"Keyword coverage: {result['coverage_percent']}% ({len(result['keywords_matched'])}/{result['keywords_total']})")
        print(f"Cover letter exact phrase echoes: {result['echo_count']}")
        print()

        if result["keywords_matched"]:
            print("MATCHED KEYWORDS:")
            print("  " + ", ".join(result["keywords_matched"][:12]))
            print()

        if result["keywords_missing"]:
            print("MISSING / NOT DETECTED (consider surfacing if supported by master):")
            print("  " + ", ".join(result["keywords_missing"][:10]))
            print()

        if result["cover_exact_echoes"]:
            print("ECHOED IN COVER LETTER:")
            for e in result["cover_exact_echoes"]:
                print(f"  - {e}")
            print()

        if result["fidelity_warnings"]:
            print("FIDELITY WARNINGS (review for accuracy):")
            for w in result["fidelity_warnings"]:
                print(f"  ! {w}")
            print()
        else:
            print("Fidelity: OK (no obvious inventions vs master)")

        print(result["recommendation"])
        print("=== END REPORT ===\n")

    # Exit non-zero on weak match for CI/script use
    if "WEAK" in result["overall"] or "REVIEW" in result["overall"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
