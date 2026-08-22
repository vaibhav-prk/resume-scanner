# Smart Resume Screener

Parses PDF resumes, extracts structured candidate data, and scores fit against a job description using an LLM — with justification, not just a number.

## Objective

Given a resume (PDF) and a job description (text), the system:

1. Extracts structured data from the resume (skills, experience, education)
2. Computes a 1–10 match score against the job description
3. Returns a shortlist of candidates ranked by fit, with reasoning for each score

## Architecture

```
Client
  │
  ▼
FastAPI (main.py)
  │
  ├── POST /upload-resume ──► pdf_parser.py (pdfplumber: PDF → raw text)
  │                                │
  │                                ▼
  │                         llm_service.py (Groq: raw text → structured JSON)
  │                                │
  │                                ▼
  │                         database.py (SQLite: store resume)
  │
  ├── POST /match ──► llm_service.py (Groq: resume + JD → score + justification)
  │                        │
  │                        ▼
  │                  database.py (SQLite: store match)
  │
  └── GET /candidates ──► database.py (query matches, sorted by score desc)
```

**Backend**: FastAPI + Pydantic for request/response validation
**PDF extraction**: pdfplumber
**LLM**: Groq API (`openai/gpt-oss-120b`) for both structured extraction and scoring
**Database**: SQLite via SQLAlchemy — two tables, `resumes` and `matches` (one-to-many)

## Database schema

**`resumes`**: `id`, `filename`, `raw_text`, `name`, `email`, `skills` (JSON), `experience_years`, `education` (JSON), `work_history` (JSON)

**`matches`**: `id`, `resume_id`, `job_description`, `score`, `justification`, `matched_skills` (JSON), `missing_skills` (JSON)

`resume_id` in `matches` is a soft reference to `resumes.id` (not an enforced foreign key) — acceptable for this scope, noted here rather than left implicit.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
GROQ_API_KEY=your_key_here
```

Run the server:

```bash
uvicorn main:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`.

## Endpoints

| Method | Path             | Purpose                                                   |
| ------ | ---------------- | --------------------------------------------------------- |
| POST   | `/upload-resume` | Upload a PDF, extract structured data, store it           |
| POST   | `/match`         | Score a stored resume against a job description           |
| GET    | `/candidates`    | List all scored candidates, sorted by fit (highest first) |

## LLM usage

Both extraction and scoring use Groq's `openai/gpt-oss-120b` with `response_format={"type": "json_object"}` to force valid JSON output, avoiding markdown-fence stripping or regex-based parsing.

**Extraction prompt** — takes raw resume text, returns structured JSON (name, email, skills, experience, education, work history). Output is validated against a Pydantic schema (`ExtractedResume`) so malformed LLM output fails loudly instead of silently corrupting the database.

**Scoring prompt** — takes the structured resume JSON plus a job description, returns a 1–10 score, a 2–3 sentence justification, and lists of matched vs. missing skills. Temperature is set low (0.2) to keep scores reasonably consistent across repeated runs on the same input.

Exact prompt templates are in `llm_service.py` (`EXTRACTION_PROMPT`, `SCORING_PROMPT`).

## Known limitations

- Scanned/image-only PDFs won't extract text (pdfplumber has no OCR fallback)
- LLM scoring isn't fully deterministic — repeated runs on the same resume/JD pair may vary by a point or two
- No authentication/authorization on endpoints — out of scope for this project
- Frontend dashboard is optional per the brief and not included in this build

## Testing

`test_pipeline.py` runs an end-to-end smoke test (health check → upload → match → candidate list) against a running local server:

```bash
python test_pipeline.py path/to/resume.pdf
```
