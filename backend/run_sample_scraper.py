#!/usr/bin/env python3
"""
Sample scraper script to get ~50 job postings using the existing pipeline.
This script runs the full process: scrape -> AI validation -> save to SQLite DB
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger

# Add the backend directory to the Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.scraper.sources.linkedin_scraper import LinkedInScraper
from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor
from app.core.database_sqlite import AsyncSessionLocal, engine, Base
from app.models.job import Job
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

class SampleJobScraper:
    """Sample scraper to get ~50 job postings."""
    
    def __init__(self):
        self.scrapers = [
            LinkedInScraper(),
        ]
        self.ai_processor = CostEffectiveAIProcessor()
        
    async def run_sample_scrape(self, target_jobs: int = 50):
        """Run the full pipeline to get sample jobs."""
        logger.info(f"Starting sample scrape for {target_jobs} jobs...")
        start_time = datetime.now()
        
        try:
            # Step 1: Setup database
            await self._setup_database()
            
            # Step 2: Scrape new jobs
            new_jobs = await self._scrape_new_jobs(target_jobs)
            logger.info(f"Scraped {len(new_jobs)} new jobs")
            
            # Step 3: Process jobs with AI (optional - can skip if no API keys)
            processed_jobs = await self._process_jobs_with_ai(new_jobs)
            logger.info(f"Processed {len(processed_jobs)} jobs with AI")
            
            # Step 4: Save to database
            saved_count = await self._save_jobs_to_database(processed_jobs)
            logger.info(f"Saved {saved_count} jobs to database")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"Sample scrape completed in {duration}")
            logger.info(f"Total jobs in database: {await self._count_jobs_in_db()}")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"Error during sample scrape: {e}")
            raise
    
    async def _setup_database(self):
        """Setup SQLite database tables."""
        logger.info("Setting up SQLite database...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database setup complete")
    
    async def _scrape_new_jobs(self, target_jobs: int) -> List[Dict]:
        """Scrape new jobs from all sources."""
        all_jobs = []
        
        for scraper in self.scrapers:
            try:
                logger.info(f"Scraping jobs from {scraper.name}...")
                
                # Limit jobs per scraper to reach target
                max_jobs_per_scraper = min(target_jobs, 50)
                
                async with scraper:
                    jobs = await scraper.scrape_jobs(max_jobs=max_jobs_per_scraper)
                    
                    # Filter for remote jobs
                    filtered_jobs = [
                        job for job in jobs 
                        if job.get('is_remote') and self._is_valid_job(job)
                    ]
                    
                    all_jobs.extend(filtered_jobs)
                    logger.info(f"Found {len(filtered_jobs)} valid jobs from {scraper.name}")
                    
                    # Stop if we have enough jobs
                    if len(all_jobs) >= target_jobs:
                        break
                    
            except Exception as e:
                logger.error(f"Error scraping from {scraper.name}: {e}")
                continue
        
        # Remove duplicates based on source URL
        unique_jobs = {}
        for job in all_jobs:
            if job.get('source_url'):
                unique_jobs[job['source_url']] = job
        
        final_jobs = list(unique_jobs.values())[:target_jobs]
        logger.info(f"Final unique jobs: {len(final_jobs)}")
        return final_jobs
    
    def _is_valid_job(self, job: Dict) -> bool:
        """Check if job meets our criteria."""
        
        # Must be remote
        if not job.get('is_remote'):
            return False
        
        # Must have a title and company
        if not job.get('title') or not job.get('company'):
            return False
        
        # Must have a source URL
        if not job.get('source_url'):
            return False
        
        return True
    
    async def _process_jobs_with_ai(self, jobs: List[Dict]) -> List[Dict]:
        """Process jobs with AI for analysis and validation."""
        processed_jobs = []
        
        for job in jobs:
            try:
                logger.info(f"Processing job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                
                # Skip AI processing for now (no API keys configured)
                # Just clean up the job data for database insertion
                job['ai_processed'] = False
                job['ai_generated_summary'] = None
                
                # Set default values
                job.setdefault('remote_type', 'remote')
                job.setdefault('is_active', True)
                job.setdefault('created_at', datetime.now())
                job.setdefault('updated_at', datetime.now())
                
                # Convert posted_date string to datetime if it exists
                if job.get('posted_date') and isinstance(job['posted_date'], str):
                    try:
                        # Try to parse the date string
                        from dateutil import parser
                        job['posted_date'] = parser.parse(job['posted_date'])
                    except:
                        # If parsing fails, set to None
                        job['posted_date'] = None
                
                # Remove any fields that don't exist in the Job model
                # Keep only the fields that match the Job model
                cleaned_job = {}
                valid_fields = {
                    'title', 'company', 'location', 'salary_min', 'salary_max', 
                    'salary_currency', 'salary_period', 'description', 'requirements',
                    'benefits', 'job_type', 'experience_level', 'remote_type',
                    'source_url', 'source_platform', 'posted_date', 'application_url',
                    'company_logo', 'company_description', 'company_size', 'company_industry',
                    'skills_required', 'ai_generated_summary', 'ai_processed', 'is_active',
                    'created_at', 'updated_at'
                }
                
                for key, value in job.items():
                    if key in valid_fields:
                        cleaned_job[key] = value
                
                processed_jobs.append(cleaned_job)
                
            except Exception as e:
                logger.error(f"Error processing job: {e}")
                # Still add the job even if processing failed
                job.setdefault('remote_type', 'remote')
                job.setdefault('is_active', True)
                job.setdefault('created_at', datetime.now())
                job.setdefault('updated_at', datetime.now())
                
                # Convert posted_date string to datetime if it exists
                if job.get('posted_date') and isinstance(job['posted_date'], str):
                    try:
                        # Try to parse the date string
                        from dateutil import parser
                        job['posted_date'] = parser.parse(job['posted_date'])
                    except:
                        # If parsing fails, set to None
                        job['posted_date'] = None
                
                # Clean the job data
                cleaned_job = {}
                valid_fields = {
                    'title', 'company', 'location', 'salary_min', 'salary_max', 
                    'salary_currency', 'salary_period', 'description', 'requirements',
                    'benefits', 'job_type', 'experience_level', 'remote_type',
                    'source_url', 'source_platform', 'posted_date', 'application_url',
                    'company_logo', 'company_description', 'company_size', 'company_industry',
                    'skills_required', 'ai_generated_summary', 'ai_processed', 'is_active',
                    'created_at', 'updated_at'
                }
                
                for key, value in job.items():
                    if key in valid_fields:
                        cleaned_job[key] = value
                
                processed_jobs.append(cleaned_job)
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
                        logger.info(f"Updated existing job: {job_data.get('title')}")
                    else:
                        # Create new job
                        new_job = Job(**job_data)
                        session.add(new_job)
                        logger.info(f"Added new job: {job_data.get('title')} at {job_data.get('company')}")
                    
                    saved_count += 1
                
                await session.commit()
                logger.info(f"Successfully saved {saved_count} jobs to database")
                
            except Exception as e:
                logger.error(f"Error saving jobs to database: {e}")
                await session.rollback()
                saved_count = 0
        
        return saved_count
    
    async def _count_jobs_in_db(self) -> int:
        """Count total jobs in database."""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Job))
                jobs = result.scalars().all()
                return len(jobs)
            except Exception as e:
                logger.error(f"Error counting jobs: {e}")
                return 0

async def main():
    """Main function to run the sample scraper."""
    logger.info("🚀 Starting Sample Job Scraper")
    logger.info("=" * 50)
    
    try:
        scraper = SampleJobScraper()
        
        # Run the sample scrape for 50 jobs
        saved_count = await scraper.run_sample_scrape(target_jobs=50)
        
        logger.info("=" * 50)
        logger.info(f"✅ Sample scrape completed successfully!")
        logger.info(f"📊 Jobs saved to database: {saved_count}")
        logger.info("🌐 You can now view the jobs in the frontend at http://localhost:3000")
        
    except Exception as e:
        logger.error(f"❌ Sample scrape failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
