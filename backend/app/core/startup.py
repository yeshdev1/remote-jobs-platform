"""
Application startup and initialization.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from app.core.mongodb import mongodb_manager
from app.core.data_lake import data_lake_manager
from app.tasks.scheduler import task_scheduler
from app.services.etl_pipeline import etl_pipeline

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up application...")
    
    try:
        # Initialize MongoDB
        await mongodb_manager.connect()
        logger.info("MongoDB connected successfully")
        
        # Initialize Data Lake
        logger.info("Data Lake initialized successfully")
        
        # Start task scheduler if enabled
        import os
        if os.getenv('ENABLE_SCHEDULER', 'True').lower() == 'true':
            task_scheduler.start()
            logger.info("Task scheduler started")
        
        # Perform initial sync if needed
        try:
            await etl_pipeline.sync_sqlite_to_mongodb(batch_size=50)
            logger.info("Initial data sync completed")
        except Exception as e:
            logger.warning(f"Initial sync failed (this is normal on first run): {e}")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Stop task scheduler
        if task_scheduler.is_running:
            task_scheduler.stop()
            logger.info("Task scheduler stopped")
        
        # Disconnect from MongoDB
        await mongodb_manager.disconnect()
        logger.info("MongoDB disconnected")
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Application shutdown failed: {e}")

async def initialize_services():
    """Initialize all services"""
    try:
        # Initialize MongoDB
        await mongodb_manager.connect()
        
        # Initialize Data Lake
        # (Data lake initialization is done in constructor)
        
        # Start scheduler if enabled
        import os
        if os.getenv('ENABLE_SCHEDULER', 'True').lower() == 'true':
            task_scheduler.start()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise

async def cleanup_services():
    """Cleanup all services"""
    try:
        # Stop scheduler
        if task_scheduler.is_running:
            task_scheduler.stop()
        
        # Disconnect MongoDB
        await mongodb_manager.disconnect()
        
        logger.info("All services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Service cleanup failed: {e}")
