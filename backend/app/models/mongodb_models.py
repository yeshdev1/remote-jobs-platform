"""
MongoDB models for real-time operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator, _field_schema):
        return {"type": "string"}

class JobDocument(BaseModel):
    """MongoDB document model for jobs"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    company: str
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    salary_period: str = "yearly"
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    remote_type: str = "remote"  # Always remote for our platform
    source_url: str
    source_platform: str
    posted_date: Optional[datetime] = None
    application_url: Optional[str] = None
    company_logo: Optional[str] = None
    company_description: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    skills_required: Optional[List[str]] = None
    ai_generated_summary: Optional[str] = None
    ai_processed: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # MongoDB-specific fields
    search_score: Optional[float] = None  # For search relevance
    tags: Optional[List[str]] = None  # For categorization
    metadata: Optional[Dict[str, Any]] = None  # For additional data
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class JobSnapshot(BaseModel):
    """Daily snapshot of job data for analytics"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    job_id: str  # Reference to original job
    snapshot_date: datetime = Field(default_factory=datetime.utcnow)
    job_data: JobDocument
    metrics: Dict[str, Any] = Field(default_factory=dict)  # Additional metrics
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AnalyticsMetric(BaseModel):
    """Analytics metrics for dashboard"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    date: datetime = Field(default_factory=datetime.utcnow)
    metric_type: str  # 'daily_jobs', 'salary_trends', 'company_stats', etc.
    data: Dict[str, Any]
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class SearchQuery(BaseModel):
    """Search query tracking for analytics"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    query: str
    results_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
