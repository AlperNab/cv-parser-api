# cv-parser-api

> **Any CV/resume → normalized JSON.** Handles PDF, DOCX, plain text in 50+ languages. Extracts skills with years of experience, employment timeline, education, certifications, with seniority and domain detection.

[![PyPI](https://img.shields.io/pypi/v/cv-parser-api?style=flat)](https://pypi.org/project/cv-parser-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Quickstart

```bash
pip install cv-parser-api
python -m cv_parser_api resume.pdf
python -m cv_parser_api cv.pdf --json > parsed.json
```

## Output includes

- Contact info (email, LinkedIn, GitHub, portfolio)
- Full experience timeline with duration calculation
- Skills normalized and tagged by category (languages, frameworks, cloud, tools)
- Years of experience per skill where inferable
- Education with GPA and honors
- Certifications with expiry dates
- Projects with tech stack
- CV quality score (0–100) with improvement suggestions
- Seniority level detection (junior → executive)
- Primary domain classification

## Python API

```python
from cv_parser_api import parse, parse_text

result = parse("resume.pdf")
print(result["contact"]["name"])
print(result["total_years_experience"])
print(result["skills"]["programming_languages"])
# [{"name": "Python", "years": 5}, {"name": "TypeScript", "years": 3}]
```

## License
MIT © [Alper Nabil Gabra Zakher](https://github.com/AlperNab)
