from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./resume_screener.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    raw_text = Column(Text)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    skills = Column(JSON, default=list)
    experience_years = Column(Float, nullable=True)
    education = Column(JSON, default=list)
    work_history = Column(JSON, default=list)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer)
    job_description = Column(Text)
    score = Column(Integer)
    justification = Column(Text)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
