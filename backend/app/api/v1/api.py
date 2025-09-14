from fastapi import APIRouter
from .endpoints import jobs, jobs_mongodb, analytics

api_router = APIRouter()

# Original SQLite-based endpoints
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs-sqlite"])

# New MongoDB-based endpoints for real-time operations
api_router.include_router(jobs_mongodb.router, prefix="/jobs-mongodb", tags=["jobs-mongodb"])

# Analytics and data lake endpoints
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
