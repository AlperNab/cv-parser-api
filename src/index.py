#!/usr/bin/env python3
"""
cv-parser-api — any CV/resume format → normalized JSON
Handles PDF, DOCX, plain text in 50+ languages
Extracts: skills taxonomy, experience timeline, education, certifications, contact info
"""
import anthropic
import base64
import json
import re
import sys
from pathlib import Path


SYSTEM = """You are an expert recruiter and HR systems specialist.
Parse this CV/resume and extract all information into structured JSON.

Rules:
- Normalize skill names (e.g. "JS" → "JavaScript", "ML" → "Machine Learning")
- Calculate years of experience per skill where inferable
- Standardize job titles to common variants
- Parse dates to YYYY-MM format
- Detect language of the CV
- Never invent information — null if not present

Return ONLY valid JSON — no markdown, no explanation.

Format:
{
  "contact": {
    "name": "string",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "linkedin": "string or null",
    "github": "string or null",
    "portfolio": "string or null",
    "website": "string or null"
  },
  "summary": "professional summary or objective, verbatim if short",
  "total_years_experience": number,
  "experience": [
    {
      "company": "string",
      "title": "string",
      "title_normalized": "Software Engineer|Product Manager|...",
      "location": "string or null",
      "start_date": "YYYY-MM or null",
      "end_date": "YYYY-MM or null",
      "is_current": true or false,
      "duration_months": number or null,
      "description": "string or null",
      "achievements": ["list of bullet points"],
      "technologies": ["list of tech mentioned"]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string or null",
      "field": "string or null",
      "start_date": "YYYY-MM or null",
      "end_date": "YYYY-MM or null",
      "gpa": "string or null",
      "honors": "string or null"
    }
  ],
  "skills": {
    "programming_languages": [{"name":"Python","years":5}],
    "frameworks": [{"name":"React","years":3}],
    "databases": [{"name":"PostgreSQL","years":2}],
    "cloud": [{"name":"AWS","years":2}],
    "tools": [{"name":"Git","years":5}],
    "soft_skills": ["Leadership","Communication"],
    "languages": [{"language":"English","level":"native"},{"language":"Arabic","level":"fluent"}],
    "other": []
  },
  "certifications": [
    {
      "name": "string",
      "issuer": "string or null",
      "date": "YYYY-MM or null",
      "expires": "YYYY-MM or null",
      "credential_id": "string or null"
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "technologies": ["list"],
      "url": "string or null",
      "date": "YYYY-MM or null"
    }
  ],
  "publications": [],
  "awards": [],
  "volunteer": [],
  "cv_language": "en|ar|fr|...",
  "cv_quality_score": number_0_to_100,
  "cv_quality_notes": ["suggestions for improvement"],
  "seniority_level": "junior|mid|senior|lead|executive",
  "primary_domain": "software-engineering|product|design|marketing|finance|legal|...",
  "confidence": 0.0
}"""


def read_file(path: Path) -> list:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        return [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}},
            {"type": "text", "text": "Parse this CV/resume completely."}
        ]

    if suffix in (".docx", ".doc"):
        try:
            import docx
            doc = docx.Document(str(path))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            text = path.read_text(encoding="utf-8", errors="replace")
        return [{"type": "text", "text": f"Parse this CV/resume:\n\n{text[:30000]}"}]

    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > 30000:
        text = text[:30000]
    return [{"type": "text", "text": f"Parse this CV/resume:\n\n{text}"}]


def parse(file_path: str) -> dict:
    client = anthropic.Anthropic()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Not found: {file_path}")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": read_file(path)}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
    return json.loads(raw)


def parse_text(text: str) -> dict:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Parse this CV:\n\n{text[:30000]}"}]
    )
    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
    return json.loads(raw)


def print_summary(result: dict):
    contact = result.get("contact", {})
    skills = result.get("skills", {})
    exp = result.get("experience", [])
    edu = result.get("education", [])

    print(f"\n{'═'*60}")
    print(f"  CV PARSED — {contact.get('name','Unknown')}")
    print(f"  {result.get('seniority_level','?').upper()} | {result.get('primary_domain','?')} | {result.get('total_years_experience',0)} yrs exp")
    print(f"{'═'*60}")

    if contact.get("email"):  print(f"  Email:    {contact['email']}")
    if contact.get("location"): print(f"  Location: {contact['location']}")
    if contact.get("linkedin"): print(f"  LinkedIn: {contact['linkedin']}")

    print(f"\n  Experience ({len(exp)} roles):")
    for role in exp[:4]:
        curr = " (current)" if role.get("is_current") else ""
        dur = f" · {role.get('duration_months',0)//12}y {role.get('duration_months',0)%12}m" if role.get("duration_months") else ""
        print(f"    • {role.get('title','?')} @ {role.get('company','?')}{curr}{dur}")

    print(f"\n  Education:")
    for e in edu:
        print(f"    • {e.get('degree','?')} in {e.get('field','?')} — {e.get('institution','?')}")

    all_skills = (
        [s["name"] for s in skills.get("programming_languages",[])] +
        [s["name"] for s in skills.get("frameworks",[])] +
        [s["name"] for s in skills.get("cloud",[])]
    )
    if all_skills:
        print(f"\n  Skills: {', '.join(all_skills[:12])}")

    langs = skills.get("languages", [])
    if langs:
        print(f"  Languages: {', '.join(f\"{l.get('language','')} ({l.get('level','')})\" for l in langs)}")

    certs = result.get("certifications", [])
    if certs:
        print(f"\n  Certifications: {', '.join(c.get('name','') for c in certs[:4])}")

    print(f"\n  CV Quality: {result.get('cv_quality_score',0)}/100")
    notes = result.get("cv_quality_notes", [])
    for note in notes[:3]:
        print(f"    → {note}")
    print(f"  Confidence: {int(result.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m cv_parser_api <resume.pdf|.docx|.txt> [--json]")
        sys.exit(0)

    if args[0] == "-":
        result = parse_text(sys.stdin.read())
    else:
        result = parse(args[0])

    if "--json" in args:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_summary(result)
