from pydantic import BaseModel, Field


class ExtractedResume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    education: list[str] = Field(default_factory=list)
    work_history: list[str] = Field(default_factory=list)


class MatchRequest(BaseModel):
    resume_id: int
    job_description: str


class MatchResult(BaseModel):
    resume_id: int
    score: int = Field(ge=1, le=10)
    justification: str
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
