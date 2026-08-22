from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import init_db, get_db, Resume, Match
from pdf_parser import extract_text_from_pdf
from llm_service import extract_resume_data, score_resume_against_jd
from models import MatchRequest

app = FastAPI(title="Smart Resume Screener")

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
import os
if os.path.isdir("frontend"):
    app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    raw_text = extract_text_from_pdf(file_bytes)

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")

    extracted = extract_resume_data(raw_text)

    resume = Resume(
        filename=file.filename,
        raw_text=raw_text,
        name=extracted.name,
        email=extracted.email,
        skills=extracted.skills,
        experience_years=extracted.experience_years,
        education=extracted.education,
        work_history=extracted.work_history,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {"resume_id": resume.id, "extracted": extracted}


@app.post("/match")
def match_resume(request: MatchRequest, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    from models import ExtractedResume

    extracted = ExtractedResume(
        name=resume.name,
        email=resume.email,
        skills=resume.skills or [],
        experience_years=resume.experience_years,
        education=resume.education or [],
        work_history=resume.work_history or [],
    )

    result = score_resume_against_jd(resume.id, extracted, request.job_description)

    match = Match(
        resume_id=resume.id,
        job_description=request.job_description,
        score=result.score,
        justification=result.justification,
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
    )
    db.add(match)
    db.commit()

    return result


@app.get("/candidates")
def list_candidates(db: Session = Depends(get_db)):
    """Return matches sorted by score, highest first (shortlist view)."""
    matches = db.query(Match).order_by(desc(Match.score)).all()
    results = []
    for m in matches:
        resume = db.query(Resume).filter(Resume.id == m.resume_id).first()
        results.append(
            {
                "resume_id": m.resume_id,
                "name": resume.name if resume else None,
                "score": m.score,
                "justification": m.justification,
                "matched_skills": m.matched_skills,
                "missing_skills": m.missing_skills,
            }
        )
    return results


@app.get("/")
def root():
    return {"status": "Smart Resume Screener API running"}
