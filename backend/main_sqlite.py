from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from loguru import logger

from app.core.config import settings
from app.core.database_sqlite import engine, Base  # Using SQLite version
from app.api.v1.api_simple import api_router
from app.core.logging import setup_logging

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Remote Jobs Platform with SQLite...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("SQLite database tables created successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Remote Jobs Platform...")

# Create FastAPI app
app = FastAPI(
    title="Remote Jobs Platform - US Salary Only (SQLite)",
    description="A platform for remote technical and design jobs with US-level salaries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Remote Jobs Platform - US Salary Only (SQLite)",
        "version": "1.0.0",
        "status": "running",
        "database": "SQLite"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "SQLite"}

if __name__ == "__main__":
    uvicorn.run(
        "main_sqlite:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
