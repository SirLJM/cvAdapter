# CV Adapter

ATS (Applicant Tracking System) optimization tool that adapts your CV to match job descriptions using Claude AI. It analyzes job postings, suggests targeted changes to your CV content, and generates optimized PDFs.

## Prerequisites

- Python 3.11+
- [CV App](https://github.com/your-org/CV) running locally (PDF generation backend)
- Anthropic API key

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # Add your ANTHROPIC_API_KEY
```

## Running

Start the CV App first (PDF generation backend), then start cvAdapter:

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

Open http://localhost:8080 in your browser.

## Ports

| Service | Port | Purpose |
|---------|------|---------|
| cvAdapter | 8080 | This app - web UI and API |
| CV App API | 8000 | PDF generation backend |
| CV Playwright | 8001 | Internal to CV App, no conflict |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/versions` | List available CV versions and languages |
| GET | `/api/cv/{version}/{language}` | Get CV data for a version/language |
| POST | `/api/analyze` | Analyze job description and suggest CV adaptations |
| POST | `/api/finalize` | Apply selected changes and generate PDF |
| GET | `/api/history` | List adaptation history |
| GET | `/api/history/{id}/pdf` | Download a previously generated PDF |

## Workflow

1. Select CV version and language
2. Paste a job description
3. Review suggested changes (accept/reject individually)
4. Optionally fill in application tracking info (company, position, date, link)
5. Generate optimized PDF
6. View past adaptations in History tab
