from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging
from loguru import logger

from app.core.config import settings
from app.api.v1.api_simple import api_router

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app without lifespan
app = FastAPI(
    title="Remote Jobs Platform - US Salary Only (Simple)",
    description="A platform for remote technical and design jobs with US-level salaries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Allow all hosts for development
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Remote Jobs Platform - US Salary Only (Simple)",
        "version": "1.0.0",
        "status": "running",
        "database": "SQLite (manual setup)"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "SQLite (manual setup)"}

@app.get("/test-cors")
async def test_cors():
    """Test endpoint to verify CORS is working"""
    return {"message": "CORS test successful", "timestamp": "2025-09-01"}

@app.get("/setup-db")
async def setup_database():
    """Manual database setup endpoint"""
    try:
        from app.core.database_sqlite import engine, Base
        from sqlalchemy.ext.asyncio import AsyncSession
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        return {"message": "Database tables created successfully", "status": "success"}
    except Exception as e:
        logger.error(f"Database setup error: {e}")
        return {"message": f"Database setup failed: {str(e)}", "status": "error"}

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
