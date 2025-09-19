from fastapi import APIRouter
from .endpoints import jobs, analytics_simple

api_router = APIRouter()

api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(analytics_simple.router, prefix="/analytics", tags=["analytics"])

# Add a simple health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "endpoint": "api"}
