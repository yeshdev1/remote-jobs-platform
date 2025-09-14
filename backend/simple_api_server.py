"""
Simple FastAPI server to serve job data from SQLite database
"""

import sqlite3
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Simple Remote Jobs API",
    description="A simple API for remote jobs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "remote_jobs.db")

# Models
class Job(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    description: Optional[str] = None
    source_url: Optional[str] = None
    source_platform: str
    posted_date: Optional[str] = None
    skills_required: Optional[str] = None
    ai_generated_summary: Optional[str] = None
    ai_processed: bool = False
    created_at: Optional[str] = None

class JobsResponse(BaseModel):
    jobs: List[Job]
    total: int
    skip: int
    limit: int
    query: str = ""
    filters: Dict[str, Any] = {}

# Database connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return {
        "message": "Simple Remote Jobs API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        conn.close()
        return {
            "status": "healthy",
            "database": "SQLite",
            "job_count": job_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/v1/jobs/", response_model=JobsResponse)
async def get_jobs(
    skip: int = 0,
    limit: int = 50,
    title: Optional[str] = None,
    company: Optional[str] = None,
    min_salary: Optional[float] = None,
    max_salary: Optional[float] = None,
    source: Optional[str] = None,
    experience_level: Optional[str] = None,
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if title:
            query += " AND title LIKE ?"
            params.append(f"%{title}%")
        
        if company:
            query += " AND company LIKE ?"
            params.append(f"%{company}%")
        
        if min_salary:
            query += " AND salary_max >= ?"
            params.append(min_salary)
        
        if max_salary:
            query += " AND salary_min <= ?"
            params.append(max_salary)
        
        if source:
            query += " AND source_platform = ?"
            params.append(source)
        
        if experience_level:
            query += " AND experience_level = ?"
            params.append(experience_level)
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Process skills_required field
        for job in jobs:
            if job.get('skills_required'):
                try:
                    # Try to parse as JSON
                    skills = json.loads(job['skills_required'])
                    job['skills_required'] = skills
                except json.JSONDecodeError:
                    # If not JSON, split by comma
                    job['skills_required'] = job['skills_required'].split(',') if job['skills_required'] else []
            else:
                job['skills_required'] = []
        
        conn.close()
        
        # Build filters dict for response
        filters = {}
        if title:
            filters["title"] = title
        if company:
            filters["company"] = company
        if min_salary:
            filters["min_salary"] = min_salary
        if max_salary:
            filters["max_salary"] = max_salary
        if source:
            filters["source"] = source
        if experience_level:
            filters["experience_level"] = experience_level
        
        return {
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit,
            "query": "",
            "filters": filters
        }
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting jobs: {str(e)}")

@app.get("/api/v1/jobs/search/", response_model=JobsResponse)
async def search_jobs(
    q: str = Query(..., description="Search query"),
    skip: int = 0,
    limit: int = 50,
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build search query
        search_terms = q.split()
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        for term in search_terms:
            query += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Process skills_required field
        for job in jobs:
            if job.get('skills_required'):
                try:
                    # Try to parse as JSON
                    skills = json.loads(job['skills_required'])
                    job['skills_required'] = skills
                except json.JSONDecodeError:
                    # If not JSON, split by comma
                    job['skills_required'] = job['skills_required'].split(',') if job['skills_required'] else []
            else:
                job['skills_required'] = []
        
        conn.close()
        
        return {
            "jobs": jobs,
            "total": total,
            "skip": skip,
            "limit": limit,
            "query": q,
            "filters": {}
        }
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        
        job_dict = dict(job)
        
        # Process skills_required field
        if job_dict.get('skills_required'):
            try:
                # Try to parse as JSON
                skills = json.loads(job_dict['skills_required'])
                job_dict['skills_required'] = skills
            except json.JSONDecodeError:
                # If not JSON, split by comma
                job_dict['skills_required'] = job_dict['skills_required'].split(',') if job_dict['skills_required'] else []
        else:
            job_dict['skills_required'] = []
        
        conn.close()
        
        return job_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting job: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Simple Remote Jobs API with SQLite database at {DB_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
