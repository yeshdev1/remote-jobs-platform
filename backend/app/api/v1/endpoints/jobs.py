from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, insert
from typing import List, Optional
from app.core.database_sqlite import get_db
from app.models.job import Job
from app.schemas.job import JobResponse, JobListResponse, JobCreate
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=JobListResponse)
async def get_jobs(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    title: Optional[str] = Query(None, description="Filter by job title"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    source_platform: Optional[str] = Query(None, description="Filter by source platform (e.g., 'RemoteOK', 'Remotive', 'WeWorkRemotely')"),
    min_salary: Optional[float] = Query(None, ge=0, description="Minimum salary"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    job_type: Optional[str] = Query(None, description="Job type (e.g., 'software_dev', 'ux_ui_design', 'product')"),
    employment_type: Optional[str] = Query(None, description="Employment type (e.g., 'Full-Time', 'Contract', 'Part-Time')"),
    skills: Optional[str] = Query(None, description="Required skills (comma-separated)"),
    days_old: Optional[int] = Query(30, ge=1, le=365, description="Jobs posted within X days")
):
    """
    Get filtered list of remote jobs with US salaries.
    """
    
    # Build query - only return remote jobs
    query = select(Job).where(
        and_(
            Job.is_active == True,
            Job.remote_type == "remote"  # Only remote jobs
        )
    )
    
    # Filter by title
    if title:
        query = query.where(Job.title.ilike(f"%{title}%"))
    
    # Filter by company
    if company:
        query = query.where(Job.company.ilike(f"%{company}%"))
    
    # Filter by source platform
    if source_platform:
        query = query.where(Job.source_platform == source_platform)
    
    # Filter by minimum salary
    if min_salary:
        query = query.where(Job.salary_max >= min_salary)
    

    
    # Filter by experience level
    if experience_level:
        query = query.where(Job.experience_level == experience_level)
    
    # Filter by job type (job category: software_dev, ux_ui_design, product)
    if job_type:
        if job_type == "software_dev":
            # Software development jobs
            query = query.where(
                or_(
                    Job.job_type == "software_dev",
                    Job.title.ilike("%software%"),
                    Job.title.ilike("%engineer%"),
                    Job.title.ilike("%developer%"),
                    Job.title.ilike("%backend%"),
                    Job.title.ilike("%frontend%"),
                    Job.title.ilike("%full stack%"),
                    Job.title.ilike("%fullstack%"),
                    Job.title.ilike("%devops%"),
                    Job.title.ilike("%mobile%"),
                    Job.title.ilike("%ios%"),
                    Job.title.ilike("%android%"),
                    Job.title.ilike("%react%"),
                    Job.title.ilike("%node%"),
                    Job.title.ilike("%python%"),
                    Job.title.ilike("%java%"),
                    Job.title.ilike("%javascript%")
                )
            )
        elif job_type == "ux_ui_design":
            # Design jobs
            query = query.where(
                or_(
                    Job.job_type == "ux_ui_design",
                    Job.title.ilike("%design%"),
                    Job.title.ilike("%ux%"),
                    Job.title.ilike("%ui%"),
                    Job.title.ilike("%user experience%"),
                    Job.title.ilike("%user interface%"),
                    Job.title.ilike("%graphic%"),
                    Job.title.ilike("%visual%"),
                    Job.title.ilike("%creative%")
                )
            )
        elif job_type == "product":
            # Product management jobs
            query = query.where(
                or_(
                    Job.job_type == "product",
                    Job.title.ilike("%product%"),
                    Job.title.ilike("%pm%"),
                    Job.title.ilike("%product manager%"),
                    Job.title.ilike("%product owner%"),
                    Job.title.ilike("%business analyst%"),
                    Job.title.ilike("%strategy%")
                )
            )
        else:
            # Fallback to exact match
            query = query.where(Job.job_type == job_type)
    
    # Filter by employment type (Full-Time, Contract, etc.)
    if employment_type:
        query = query.where(Job.job_type == employment_type)
    
    # Filter by skills
    if skills:
        skill_list = [skill.strip().lower() for skill in skills.split(",")]
        # This is a simplified skill filter - in production you'd want more sophisticated matching
        for skill in skill_list:
            query = query.where(
                or_(
                    Job.description.ilike(f"%{skill}%"),
                    Job.requirements.ilike(f"%{skill}%")
                )
            )
    
    # Filter by recency
    if days_old:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        query = query.where(Job.created_at >= cutoff_date)
    
    # Order by most recent first
    query = query.order_by(Job.created_at.desc())
    
    # First, get total count without pagination
    count_query = select(Job).where(query.whereclause)
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    # Then apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    # Convert to response models
    job_responses = [JobResponse.model_validate(job) for job in jobs]
    
    return JobListResponse(
        jobs=job_responses,
        total=total_count,
        skip=skip,
        limit=limit
    )

@router.post("/ingest/o1-mini")
async def ingest_with_o1_mini(
    db: AsyncSession = Depends(get_db),
    max_jobs_per_source: int = Query(25, ge=1, le=200),
):
    """
    Run the o1-mini powered agent to ingest jobs that are:
    - remote
    - location-agnostic
    - US-based pay (USD)
    Persist into SQLite using the ORM schema.
    """
    try:
        from app.ai_agents.o1_remote_jobs_agent import O1RemoteJobsAgent

        agent = O1RemoteJobsAgent()
        result = await agent.run(db, max_jobs_per_source=max_jobs_per_source)
        return result
    except Exception as e:
        logger.error(f"o1-mini ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"o1-mini ingestion failed: {str(e)}")

@router.get("/ai-status")
async def get_ai_processor_status():
    """
    Get the current status of the AI processor including costs and configuration.
    """
    try:
        from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor
        
        # Initialize AI processor
        processor = CostEffectiveAIProcessor()
        
        # Get status information
        cost_summary = processor.get_daily_cost_summary()
        
        # Check which providers are available
        available_providers = []
        if processor.openai_client:
            available_providers.append("openai")
        if processor.anthropic_client:
            available_providers.append("anthropic")
        if processor.gemini_client:
            available_providers.append("google")
        
        return {
            "status": "operational",
            "available_providers": available_providers,
            "strategy": processor.strategy,
            "cost_summary": cost_summary,
            "configuration": {
                "daily_budget": processor.daily_budget,
                "max_jobs_per_day": processor.max_jobs_per_day,
                "model_mapping": {
                    complexity.value: config["provider"] 
                    for complexity, config in processor.model_mapping.items()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"AI status check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "available_providers": [],
            "cost_summary": {
                "total_cost": 0.0,
                "jobs_processed": 0,
                "cost_per_job": 0.0,
                "budget_remaining": 0.0,
                "jobs_remaining": 0,
                "strategy": "unknown"
            }
        }

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific job by ID.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.from_orm(job)

@router.post("/", response_model=JobResponse)
async def create_job(job_data: JobCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new job posting.
    """
    try:
        # Create new job instance
        new_job = Job(
            title=job_data.title,
            company=job_data.company,
            location=job_data.location,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            salary_currency=job_data.salary_currency or "USD",
            salary_period=job_data.salary_period or "yearly",
            description=job_data.description,
            requirements=job_data.requirements,
            benefits=job_data.benefits,
            job_type=job_data.job_type,
            experience_level=job_data.experience_level,
            remote_type="remote",  # Only remote jobs accepted
            source_url=job_data.source_url,
            source_platform=job_data.source_platform,
            posted_date=job_data.posted_date or datetime.now(),
            application_url=job_data.application_url,
            company_logo=job_data.company_logo,
            company_description=job_data.company_description,
            company_size=job_data.company_size,
            company_industry=job_data.company_industry,
            skills_required=job_data.skills_required,
            ai_generated_summary=job_data.ai_generated_summary,
            ai_processed=job_data.ai_processed or False,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add to database
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        return JobResponse.from_orm(new_job)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.get("/search/", response_model=JobListResponse)
async def search_jobs(
    q: str = Query(..., description="Search query"),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_platform: Optional[str] = Query(None, description="Filter by source platform (e.g., 'RemoteOK', 'Remotive', 'WeWorkRemotely')"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    job_type: Optional[str] = Query(None, description="Job type"),
    employment_type: Optional[str] = Query(None, description="Employment type")
):
    """
    Search jobs by text query with optional filters.
    """
    
    conditions = [
        Job.is_active == True,
        or_(
            Job.title.ilike(f"%{q}%"),
            Job.company.ilike(f"%{q}%"),
            Job.description.ilike(f"%{q}%"),
            Job.requirements.ilike(f"%{q}%")
        )
    ]
    
    # Add source platform filter if provided
    if source_platform:
        conditions.append(Job.source_platform == source_platform)
    
    # Add experience level filter if provided
    if experience_level:
        conditions.append(Job.experience_level == experience_level)
        
    # Add job type filter if provided
    if job_type:
        conditions.append(Job.job_type == job_type)
    
    # Add employment type filter if provided
    if employment_type:
        conditions.append(Job.job_type == employment_type)
    
    search_query = select(Job).where(and_(*conditions)).order_by(Job.created_at.desc())
    
    # First, get total count without pagination
    count_query = select(Job).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    # Apply pagination
    search_query = search_query.offset(skip).limit(limit)
    
    result = await db.execute(search_query)
    jobs = result.scalars().all()
    
    job_responses = [JobResponse.from_orm(job) for job in jobs]
    
    return JobListResponse(
        jobs=job_responses,
        total=total_count,
        skip=skip,
        limit=limit
    )

@router.get("/featured/", response_model=JobListResponse)
async def get_featured_jobs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get featured jobs (high-salary, recent, well-known companies).
    """
    
    # Conditions for featured jobs
    conditions = [
        Job.is_active == True,
        Job.salary_min >= 100000,  # $100k+ jobs
        Job.ai_processed == True,  # AI-verified jobs
        Job.created_at >= datetime.now() - timedelta(days=7)  # Recent jobs
    ]
    
    # First, get total count without pagination
    count_query = select(Job).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    # Featured jobs query with limit
    featured_query = select(Job).where(and_(*conditions)).order_by(
        Job.salary_max.desc(), Job.created_at.desc()
    ).limit(limit)
    
    result = await db.execute(featured_query)
    jobs = result.scalars().all()
    
    job_responses = [JobResponse.from_orm(job) for job in jobs]
    
    return JobListResponse(
        jobs=job_responses,
        total=total_count,
        skip=0,
        limit=limit
    )

@router.get("/stats/salary-ranges")
async def get_salary_ranges(db: AsyncSession = Depends(get_db)):
    """
    Get salary distribution statistics.
    """
    
    # This would be implemented with more sophisticated aggregation
    # For now, return basic stats
    return {
        "salary_ranges": [
            {"range": "50k-75k", "count": 0},
            {"range": "75k-100k", "count": 0},
            {"range": "100k-150k", "count": 0},
            {"range": "150k-200k", "count": 0},
            {"range": "200k+", "count": 0}
        ],
        "total_jobs": 0,
        "average_salary": 0
    }

@router.post("/", response_model=JobResponse)
async def create_job(job: JobCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new job listing.
    """
    try:
        # Create new job object
        db_job = Job(
            title=job.title,
            company=job.company,
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency or "USD",
            salary_period=job.salary_period or "yearly",
            description=job.description,
            requirements=job.requirements,
            benefits=job.benefits,
            job_type=job.job_type,
            experience_level=job.experience_level,
            remote_type=job.remote_type or "remote",
            source_url=job.source_url,
            source_platform=job.source_platform,
            posted_date=job.posted_date,
            application_url=job.application_url,
            company_logo=job.company_logo,
            company_description=job.company_description,
            company_size=job.company_size,
            company_industry=job.company_industry,
            skills_required=job.skills_required,
            ai_generated_summary=job.ai_generated_summary,
            ai_processed=job.ai_processed or False,
            is_active=True
        )
        
        db.add(db_job)
        await db.commit()
        await db.refresh(db_job)
        
        return db_job
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.post("/validate-ai")
async def validate_job_with_ai(
    job_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate a job posting using AI to determine if it's legitimate and extract structured data.
    """
    try:
        from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor
        
        # Initialize AI processor
        processor = CostEffectiveAIProcessor()
        
        # Validate the job
        result = await processor.validate_job(job_data)
        
        # Return the validation result
        return {
            "is_valid": result.is_valid,
            "confidence": result.confidence,
            "salary_range": result.salary_range,
            "remote_type": result.remote_type,
            "experience_level": result.experience_level,
            "skills": result.skills,
            "summary": result.summary,
            "reasoning": result.reasoning,
            "model_used": result.model_used,
            "cost": result.cost,
            "ai_processed": True
        }
        
    except Exception as e:
        logger.error(f"AI validation error: {e}")
        raise HTTPException(status_code=500, detail=f"AI validation failed: {str(e)}")

@router.post("/validate-batch")
async def validate_jobs_batch_with_ai(
    jobs_data: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """
    Validate multiple job postings using AI in batch for cost optimization.
    """
    try:
        from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor
        
        # Initialize AI processor
        processor = CostEffectiveAIProcessor()
        
        # Validate jobs in batch
        results = await processor.validate_jobs_batch(jobs_data)
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                "job_index": i,
                "is_valid": result.is_valid,
                "confidence": result.confidence,
                "salary_range": result.salary_range,
                "remote_type": result.remote_type,
                "experience_level": result.experience_level,
                "skills": result.skills,
                "summary": result.summary,
                "reasoning": result.reasoning,
                "model_used": result.model_used,
                "cost": result.cost
            })
        
        # Get cost summary
        cost_summary = processor.get_daily_cost_summary()
        
        return {
            "results": formatted_results,
            "total_jobs": len(results),
            "valid_jobs": len([r for r in results if r.is_valid]),
            "cost_summary": cost_summary
        }
        
    except Exception as e:
        logger.error(f"Batch AI validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch AI validation failed: {str(e)}")
