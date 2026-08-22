import os
import json
from groq import Groq
from dotenv import load_dotenv
from models import ExtractedResume, MatchResult

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Llama 3.3 70B is a strong free-tier default on Groq; swap if you want faster/cheaper.
MODEL = "openai/gpt-oss-120b"


EXTRACTION_PROMPT = """You are a resume parser. Extract structured information from the resume text below.

Return ONLY valid JSON (no markdown, no commentary) matching this exact schema:
{{
  "name": string or null,
  "email": string or null,
  "phone": string or null,
  "skills": [list of strings],
  "experience_years": number or null,
  "education": [list of strings, e.g. "B.Tech CSE, VIT-AP, 2026"],
  "work_history": [list of strings, e.g. "Backend Intern at X (2024-2025)"]
}}

Resume text:
---
{resume_text}
---

JSON:"""


SCORING_PROMPT = """You are an expert technical recruiter. Compare the candidate's extracted resume data with the job description and rate the fit on a scale of 1-10.

Return ONLY valid JSON (no markdown, no commentary) matching this exact schema:
{{
  "score": integer from 1 to 10,
  "justification": "2-3 sentence explanation of the score",
  "matched_skills": [list of skills from the resume that match the JD],
  "missing_skills": [list of important skills the JD wants but resume lacks]
}}

Candidate resume data:
{resume_json}

Job description:
---
{job_description}
---

JSON:"""


def _call_groq(prompt: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    return json.loads(content)


def extract_resume_data(resume_text: str) -> ExtractedResume:
    prompt = EXTRACTION_PROMPT.format(
        resume_text=resume_text[:8000]
    )  # guard against huge inputs
    raw = _call_groq(prompt)
    return ExtractedResume(**raw)


def score_resume_against_jd(
    resume_id: int, resume_data: ExtractedResume, job_description: str
) -> MatchResult:
    prompt = SCORING_PROMPT.format(
        resume_json=resume_data.model_dump_json(indent=2),
        job_description=job_description,
    )
    raw = _call_groq(prompt)
    return MatchResult(resume_id=resume_id, **raw)
