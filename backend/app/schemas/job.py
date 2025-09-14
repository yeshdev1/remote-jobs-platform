from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class JobBase(BaseModel):
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    salary_currency: Optional[str] = Field(None, description="Salary currency")
    salary_period: Optional[str] = Field(None, description="Salary period (yearly/monthly/hourly)")
    description: Optional[str] = Field(None, description="Job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    benefits: Optional[str] = Field(None, description="Job benefits")
    job_type: Optional[str] = Field(None, description="Job type (full-time/part-time/contract)")
    experience_level: Optional[str] = Field(None, description="Experience level")
    remote_type: Optional[str] = Field(None, description="Remote work type")
    source_url: Optional[str] = Field(None, description="Source URL")
    url: Optional[str] = Field(None, description="Direct job URL")
    source_platform: str = Field(..., description="Source platform")
    posted_date: Optional[datetime] = Field(None, description="Posted date")
    application_url: Optional[str] = Field(None, description="Application URL")
    company_logo: Optional[str] = Field(None, description="Company logo URL")
    company_description: Optional[str] = Field(None, description="Company description")
    company_size: Optional[str] = Field(None, description="Company size")
    company_industry: Optional[str] = Field(None, description="Company industry")
    skills_required: Optional[List[str]] = Field(None, description="Required skills")
    ai_generated_summary: Optional[str] = Field(None, description="AI-generated summary")
    ai_processed: Optional[bool] = Field(False, description="Whether job was processed by AI")

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    remote_type: Optional[str] = None
    application_url: Optional[str] = None
    company_logo: Optional[str] = None
    company_description: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    skills_required: Optional[List[str]] = None
    ai_generated_summary: Optional[str] = None
    ai_processed: Optional[bool] = None
    is_active: Optional[bool] = None

class JobResponse(JobBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    skip: int
    limit: int

class JobSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    min_salary: Optional[float] = Field(None, description="Minimum salary")
    max_salary: Optional[float] = Field(None, description="Maximum salary")
    remote_type: Optional[str] = Field(None, description="Remote work type")
    experience_level: Optional[str] = Field(None, description="Experience level")
    skills: Optional[List[str]] = Field(None, description="Required skills")
    days_old: Optional[int] = Field(30, description="Jobs posted within X days")
    skip: int = Field(0, description="Number of records to skip")
    limit: int = Field(100, description="Number of records to return")
