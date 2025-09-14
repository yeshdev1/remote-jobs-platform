from fastapi import APIRouter
from .endpoints import jobs

api_router = APIRouter()

api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

# Add a simple health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "endpoint": "api"}
