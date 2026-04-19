from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from ai_service.model import (
    load_assets,
    match_jobs_for_resume,
    match_uploaded_resume,
    match_resumes_for_job,
)

app = FastAPI(title="AI Job Matching Service")


class ResumeRequest(BaseModel):
    resume_id: str
    top_k: int = 10


class JobRequest(BaseModel):
    job_id: str
    top_k: int = 10


@app.on_event("startup")
def startup():
    load_assets()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/match/jobs-for-resume")
def match_jobs(req: ResumeRequest):
    try:
        return match_jobs_for_resume(req.resume_id, req.top_k)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/match/upload-resume")
async def match_uploaded_resume_endpoint(
        file: UploadFile = File(...),
        top_k: int = Form(10)
):
    """
    Upload a resume file (.txt, .pdf, .docx) and return job matches.
    """
    try:
        file_bytes = await file.read()
        return match_uploaded_resume(file_bytes=file_bytes, filename=file.filename, top_k=top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/match/resumes-for-job")
def match_resumes(req: JobRequest):
    try:
        return match_resumes_for_job(req.job_id, req.top_k)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
