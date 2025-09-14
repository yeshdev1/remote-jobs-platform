from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Use SQLite for local development
database_url = "sqlite+aiosqlite:///./remote_jobs.db"

# Create async engine for SQLite
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Import Base from models
from app.models.job import Base
