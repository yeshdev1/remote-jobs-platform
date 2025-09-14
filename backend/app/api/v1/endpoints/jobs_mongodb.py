"""
MongoDB-based job endpoints for real-time operations.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging

from app.services.mongodb_service import mongodb_service
from app.schemas.job import JobListResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search", response_model=JobListResponse)
async def search_jobs_mongodb(
    q: str = Query("", description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    min_salary: Optional[float] = Query(None, ge=0, description="Minimum salary"),
    max_salary: Optional[float] = Query(None, ge=0, description="Maximum salary"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    job_type: Optional[str] = Query(None, description="Job type"),
    days_old: Optional[int] = Query(30, ge=1, le=365, description="Jobs posted within X days"),
    sort_by: str = Query("relevance", description="Sort by: relevance, created_at, salary_min"),
    sort_order: str = Query("desc", description="Sort order: asc, desc")
):
    """
    Search jobs using MongoDB with full-text search and advanced filtering.
    """
    try:
        # Prepare filters
        filters = {}
        if min_salary is not None:
            filters["min_salary"] = min_salary
        if max_salary is not None:
            filters["max_salary"] = max_salary
        if experience_level:
            filters["experience_level"] = experience_level
        if job_type:
            filters["job_type"] = job_type
        if days_old:
            filters["days_old"] = days_old
        
        # Convert sort parameters
        sort_order_int = -1 if sort_order == "desc" else 1
        
        # Search jobs
        result = await mongodb_service.search_jobs(
            query=q,
            filters=filters,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order_int
        )
        
        return JobListResponse(
            jobs=result["jobs"],
            total=result["total"],
            skip=result["skip"],
            limit=result["limit"]
        )
        
    except Exception as e:
        logger.error(f"MongoDB search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{job_id}")
async def get_job_mongodb(job_id: str):
    """
    Get a specific job by ID (source_url).
    """
    try:
        job = await mongodb_service.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")

@router.get("/company/{company_name}")
async def get_jobs_by_company(company_name: str, limit: int = Query(10, ge=1, le=50)):
    """
    Get jobs by company name.
    """
    try:
        jobs = await mongodb_service.get_jobs_by_company(company_name, limit)
        return {"jobs": jobs, "company": company_name, "count": len(jobs)}
        
    except Exception as e:
        logger.error(f"Failed to get jobs by company: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get jobs by company: {str(e)}")

@router.get("/{job_id}/similar")
async def get_similar_jobs(job_id: str, limit: int = Query(5, ge=1, le=20)):
    """
    Get similar jobs based on skills and experience level.
    """
    try:
        similar_jobs = await mongodb_service.get_similar_jobs(job_id, limit)
        return {"similar_jobs": similar_jobs, "reference_job_id": job_id, "count": len(similar_jobs)}
        
    except Exception as e:
        logger.error(f"Failed to get similar jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get similar jobs: {str(e)}")

@router.get("/stats/overview")
async def get_job_statistics():
    """
    Get job statistics for dashboard.
    """
    try:
        stats = await mongodb_service.get_job_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get job statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job statistics: {str(e)}")

@router.get("/search/suggestions")
async def get_search_suggestions(q: str = Query("", min_length=2), limit: int = Query(10, ge=1, le=20)):
    """
    Get search suggestions based on job titles and companies.
    """
    try:
        suggestions = await mongodb_service.get_search_suggestions(q, limit)
        return {"suggestions": suggestions, "query": q, "count": len(suggestions)}
        
    except Exception as e:
        logger.error(f"Failed to get search suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get search suggestions: {str(e)}")
