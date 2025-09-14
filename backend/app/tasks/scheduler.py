"""
Scheduled tasks for automated ETL operations.
"""
import asyncio
from datetime import datetime, date, time
from typing import Dict, Any
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.etl_pipeline import etl_pipeline

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self._setup_jobs()
            self.scheduler.start()
            self.is_running = True
            logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler stopped")
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        
        # Daily sync from SQLite to MongoDB at 2 AM
        self.scheduler.add_job(
            self._daily_sync_job,
            CronTrigger(hour=2, minute=0),
            id='daily_sync',
            name='Daily SQLite to MongoDB Sync',
            replace_existing=True
        )
        
        # Daily snapshot creation at 3 AM
        self.scheduler.add_job(
            self._daily_snapshot_job,
            CronTrigger(hour=3, minute=0),
            id='daily_snapshot',
            name='Daily Job Snapshot',
            replace_existing=True
        )
        
        # Daily analytics generation at 4 AM
        self.scheduler.add_job(
            self._daily_analytics_job,
            CronTrigger(hour=4, minute=0),
            id='daily_analytics',
            name='Daily Analytics Generation',
            replace_existing=True
        )
        
        # Weekly cleanup at Sunday 1 AM
        self.scheduler.add_job(
            self._weekly_cleanup_job,
            CronTrigger(day_of_week=6, hour=1, minute=0),  # Sunday
            id='weekly_cleanup',
            name='Weekly Data Cleanup',
            replace_existing=True
        )
        
        # Hourly sync during business hours (9 AM - 6 PM, Monday-Friday)
        self.scheduler.add_job(
            self._hourly_sync_job,
            CronTrigger(hour='9-18', minute=0, day_of_week='0-4'),  # Mon-Fri
            id='hourly_sync',
            name='Hourly Sync During Business Hours',
            replace_existing=True
        )
        
        logger.info("Scheduled jobs configured")
    
    async def _daily_sync_job(self):
        """Daily sync job"""
        try:
            logger.info("Starting daily sync job")
            result = await etl_pipeline.sync_sqlite_to_mongodb()
            logger.info(f"Daily sync completed: {result}")
        except Exception as e:
            logger.error(f"Daily sync job failed: {e}")
    
    async def _daily_snapshot_job(self):
        """Daily snapshot job"""
        try:
            logger.info("Starting daily snapshot job")
            snapshot_path = await etl_pipeline.create_daily_snapshot()
            logger.info(f"Daily snapshot completed: {snapshot_path}")
        except Exception as e:
            logger.error(f"Daily snapshot job failed: {e}")
    
    async def _daily_analytics_job(self):
        """Daily analytics job"""
        try:
            logger.info("Starting daily analytics job")
            metrics = await etl_pipeline.generate_analytics_metrics()
            logger.info(f"Daily analytics completed: {len(metrics)} metrics generated")
        except Exception as e:
            logger.error(f"Daily analytics job failed: {e}")
    
    async def _weekly_cleanup_job(self):
        """Weekly cleanup job"""
        try:
            logger.info("Starting weekly cleanup job")
            await etl_pipeline.cleanup_old_data(days_to_keep=90)
            logger.info("Weekly cleanup completed")
        except Exception as e:
            logger.error(f"Weekly cleanup job failed: {e}")
    
    async def _hourly_sync_job(self):
        """Hourly sync job during business hours"""
        try:
            logger.info("Starting hourly sync job")
            result = await etl_pipeline.sync_sqlite_to_mongodb(batch_size=50)
            logger.info(f"Hourly sync completed: {result}")
        except Exception as e:
            logger.error(f"Hourly sync job failed: {e}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "scheduler_running": self.is_running,
            "jobs": jobs,
            "job_count": len(jobs)
        }
    
    def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Manually triggered job: {job_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}")
            return False

# Global scheduler instance
task_scheduler = TaskScheduler()
