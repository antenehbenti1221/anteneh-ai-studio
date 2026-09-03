from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone

app = FastAPI(title='Anteneh AI Studio API', version='0.1.0')
jobs = {}

class JobRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    duration: str = 'short'
    input_mode: str = 'text'
    aspect_ratio: str = '16:9'
    language: str = 'en'
    voice: str = 'natural-male'
    style: str = 'educational'

@app.get('/health')
def health():
    return {'ok': True, 'service': 'anteneh-ai-studio-api'}

@app.post('/api/jobs', status_code=202)
def create_job(request: JobRequest):
    job_id = str(uuid4())
    jobs[job_id] = {
        'id': job_id,
        'status': 'queued',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'request': request.model_dump(),
        'worker': None,
        'progress': 0,
        'result_url': None,
    }
    return jobs[job_id]

@app.get('/api/jobs/{job_id}')
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job
