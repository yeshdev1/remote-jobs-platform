#!/usr/bin/env python3
"""
Cron job script to run the job scheduler daily.
This script should be run via cron to update job data every 24 hours.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.scheduler.job_scheduler import JobScheduler
from loguru import logger

async def main():
    """Main function to run the scheduler once."""
    logger.info("Starting scheduled job update...")
    
    try:
        scheduler = JobScheduler()
        
        # Run the daily update once
        await scheduler.run_daily_update()
        
        logger.info("Scheduled job update completed successfully")
        
    except Exception as e:
        logger.error(f"Error during scheduled job update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
