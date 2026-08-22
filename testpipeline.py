"""
Quick end-to-end test for the Smart Resume Screener API.
Usage: python test_pipeline.py path/to/resume.pdf
"""

import sys
import requests

BASE_URL = "http://127.0.0.1:8000"

SAMPLE_JD = """
We are looking for a Backend Developer with strong Python skills.
Requirements: FastAPI or Flask experience, REST API design, SQL databases,
Git version control. Bonus: experience with LLMs or cloud platforms (AWS/GCP).
2+ years experience preferred but fresh graduates with strong projects considered.
"""


def test_root():
    r = requests.get(f"{BASE_URL}/")
    print("GET / ->", r.status_code, r.json())
    assert r.status_code == 200


def test_upload(pdf_path: str) -> int:
    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path, f, "application/pdf")}
        r = requests.post(f"{BASE_URL}/upload-resume", files=files)
    print("POST /upload-resume ->", r.status_code)
    print(r.json())
    assert r.status_code == 200
    return r.json()["resume_id"]


def test_match(resume_id: int):
    payload = {"resume_id": resume_id, "job_description": SAMPLE_JD}
    r = requests.post(f"{BASE_URL}/match", json=payload)
    print("POST /match ->", r.status_code)
    print(r.json())
    assert r.status_code == 200


def test_candidates():
    r = requests.get(f"{BASE_URL}/candidates")
    print("GET /candidates ->", r.status_code)
    print(r.json())
    assert r.status_code == 200


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py path/to/resume.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    print("=== 1. Health check ===")
    test_root()

    print("\n=== 2. Upload + extract resume ===")
    resume_id = test_upload(pdf_path)

    print("\n=== 3. Score against sample JD ===")
    test_match(resume_id)

    print("\n=== 4. List candidates ===")
    test_candidates()

    print("\nAll tests passed.")
