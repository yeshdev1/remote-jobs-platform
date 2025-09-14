import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.scraper.sources.linkedin_scraper import LinkedInScraper
from app.ai_processor.claude_processor import ClaudeProcessor
from app.core.database import AsyncSessionLocal
from app.models.job import Job
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

class JobScheduler:
    """Scheduler for daily job updates."""
    
    def __init__(self):
        self.scrapers = [
            LinkedInScraper(),
            # Add more scrapers here
        ]
        self.ai_processor = ClaudeProcessor()
        self.is_running = False
        
    async def start(self):
        """Start the scheduler."""
        logger.info("Starting Job Scheduler...")
        self.is_running = True
        
        # Schedule daily job update at 2 AM
        schedule.every().day.at("02:00").do(self.run_daily_update)
        
        # Schedule hourly health check
        schedule.every().hour.do(self.health_check)
        
        logger.info("Job Scheduler started successfully")
        
        # Run the scheduler loop
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    async def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping Job Scheduler...")
        self.is_running = False
    
    async def run_daily_update(self):
        """Run the daily job update process."""
        logger.info("Starting daily job update...")
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape new jobs
            new_jobs = await self._scrape_new_jobs()
            logger.info(f"Scraped {len(new_jobs)} new jobs")
            
            # Step 2: Process jobs with AI
            processed_jobs = await self._process_jobs_with_ai(new_jobs)
            logger.info(f"Processed {len(processed_jobs)} jobs with AI")
            
            # Step 3: Save to database
            saved_count = await self._save_jobs_to_database(processed_jobs)
            logger.info(f"Saved {saved_count} jobs to database")
            
            # Step 4: Clean up old jobs
            cleaned_count = await self._cleanup_old_jobs()
            logger.info(f"Cleaned up {cleaned_count} old jobs")
            
            # Step 5: Update existing jobs
            updated_count = await self._update_existing_jobs()
            logger.info(f"Updated {updated_count} jobs")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"Daily job update completed in {duration}")
            
        except Exception as e:
            logger.error(f"Error during daily job update: {e}")
            # Send notification or alert here
    
    async def _scrape_new_jobs(self) -> List[Dict]:
        """Scrape new jobs from all sources."""
        all_jobs = []
        
        for scraper in self.scrapers:
            try:
                logger.info(f"Scraping jobs from {scraper.name}...")
                
                async with scraper:
                    jobs = await scraper.scrape_jobs(max_jobs=settings.MAX_JOBS_PER_UPDATE // len(self.scrapers))
                    
                    # Filter for remote jobs with potential US salaries
                    filtered_jobs = [
                        job for job in jobs 
                        if job.get('is_remote') and self._has_potential_us_salary(job)
                    ]
                    
                    all_jobs.extend(filtered_jobs)
                    logger.info(f"Found {len(filtered_jobs)} valid jobs from {scraper.name}")
                    
            except Exception as e:
                logger.error(f"Error scraping from {scraper.name}: {e}")
                continue
        
        # Remove duplicates based on source URL
        unique_jobs = {}
        for job in jobs:
            if job.get('source_url'):
                unique_jobs[job['source_url']] = job
        
        return list(unique_jobs.values())
    
    async def _process_jobs_with_ai(self, jobs: List[Dict]) -> List[Dict]:
        """Process jobs with Claude AI for analysis and validation."""
        processed_jobs = []
        
        for job in jobs:
            try:
                logger.info(f"Processing job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                
                # Analyze job with Claude
                ai_analysis = await self.ai_processor.analyze_job_posting(job)
                
                # Validate salary with AI
                if job.get('salary'):
                    is_usd, min_sal, max_sal = await self.ai_processor.validate_us_salary(job['salary'])
                    
                    if is_usd:
                        job['salary_min'] = min_sal
                        job['salary_max'] = max_sal
                        job['salary_currency'] = 'USD'
                        job['ai_processed'] = True
                        job['ai_generated_summary'] = ai_analysis.get('summary', '')
                        
                        # Extract skills
                        if job.get('description'):
                            skills = await self.ai_processor.extract_skills(job['description'])
                            job['skills_required'] = skills
                        
                        processed_jobs.append(job)
                    else:
                        logger.info(f"Job {job.get('title')} does not have US salary, skipping")
                else:
                    # Job without salary, still process but mark for review
                    job['ai_processed'] = True
                    job['ai_generated_summary'] = ai_analysis.get('summary', '')
                    processed_jobs.append(job)
                
                # Rate limiting for AI API calls
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing job with AI: {e}")
                continue
        
        return processed_jobs
    
    async def _save_jobs_to_database(self, jobs: List[Dict]) -> int:
        """Save processed jobs to database."""
        saved_count = 0
        
        async with AsyncSessionLocal() as session:
            try:
                for job_data in jobs:
                    # Check if job already exists
                    existing_job = await session.execute(
                        select(Job).where(Job.source_url == job_data['source_url'])
                    )
                    existing_job = existing_job.scalar_one_or_none()
                    
                    if existing_job:
                        # Update existing job
                        for key, value in job_data.items():
                            if hasattr(existing_job, key):
                                setattr(existing_job, key, value)
                        existing_job.updated_at = datetime.now()
                    else:
                        # Create new job
                        new_job = Job(**job_data)
                        session.add(new_job)
                    
                    saved_count += 1
                
                await session.commit()
                logger.info(f"Successfully saved {saved_count} jobs to database")
                
            except Exception as e:
                logger.error(f"Error saving jobs to database: {e}")
                await session.rollback()
                saved_count = 0
        
        return saved_count
    
    async def _cleanup_old_jobs(self) -> int:
        """Remove jobs older than 30 days."""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Job).where(Job.created_at < cutoff_date)
            )
            old_jobs = result.scalars().all()
            
            for job in old_jobs:
                await session.delete(job)
            
            await session.commit()
            logger.info(f"Cleaned up {len(old_jobs)} old jobs")
            return len(old_jobs)
            
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            await session.rollback()
            return 0
    
    async def _update_existing_jobs(self) -> int:
        """Update existing jobs (e.g., mark expired ones as inactive)."""
        updated_count = 0
        
        async with AsyncSessionLocal() as session:
            try:
                # Mark jobs older than 14 days as potentially expired
                cutoff_date = datetime.now() - timedelta(days=14)
                
                result = await session.execute(
                    update(Job)
                    .where(Job.created_at < cutoff_date)
                    .values(is_active=False)
                )
                
                await session.commit()
                updated_count = result.rowcount
                logger.info(f"Updated {updated_count} jobs")
                
            except Exception as e:
                logger.error(f"Error updating existing jobs: {e}")
                await session.rollback()
                updated_count = 0
        
        return updated_count
    
    def _has_potential_us_salary(self, job: Dict) -> bool:
        """Check if job has potential for US salary."""
        
        # If we already have salary info, check if it's USD
        if job.get('salary_currency') == 'USD':
            return True
        
        # Check salary text for USD indicators
        salary_text = job.get('salary', '')
        if salary_text:
            usd_indicators = ['$', 'USD', 'US$', 'dollars', 'dollar']
            return any(indicator in salary_text.upper() for indicator in usd_indicators)
        
        # Check if it's a US company or location
        company = job.get('company', '').lower()
        location = job.get('location', '').lower()
        
        us_indicators = ['inc', 'llc', 'corp', 'united states', 'us', 'usa', 'california', 'new york', 'texas']
        return any(indicator in company or indicator in location for indicator in us_indicators)
    
    async def health_check(self):
        """Perform health check."""
        logger.info("Performing health check...")
        
        try:
            # Check database connection
            async with AsyncSessionLocal() as session:
                await session.execute(select(1))
            
            # Check AI API
            test_analysis = await self.ai_processor.analyze_job_posting({
                'title': 'Test Job',
                'company': 'Test Company',
                'description': 'Test description'
            })
            
            logger.info("Health check passed")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # Send alert here

async def main():
    """Main function to run the scheduler."""
    scheduler = JobScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        await scheduler.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())
