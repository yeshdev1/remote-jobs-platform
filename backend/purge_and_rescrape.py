#!/usr/bin/env python3
"""
Purge database and run fresh scrape with improved deduplication and AI validation.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set
from loguru import logger
import hashlib

# Add the backend directory to the Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.scraper.sources.linkedin_scraper import LinkedInScraper
from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor
from app.core.database_sqlite import AsyncSessionLocal, engine, Base
from app.models.job import Job
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

class ImprovedJobScraper:
    """Improved scraper with better deduplication and AI validation."""
    
    def __init__(self):
        self.scrapers = [
            LinkedInScraper(),
        ]
        self.ai_processor = CostEffectiveAIProcessor()
        self.seen_jobs: Set[str] = set()  # Track seen jobs for deduplication
        
    async def purge_database(self):
        """Purge all existing job data."""
        logger.info("🗑️ Purging existing job data...")
        
        async with AsyncSessionLocal() as session:
            try:
                # Delete all jobs
                result = await session.execute(delete(Job))
                await session.commit()
                logger.info(f"✅ Deleted {result.rowcount} existing jobs")
            except Exception as e:
                logger.error(f"❌ Error purging database: {e}")
                await session.rollback()
                raise
    
    def generate_job_hash(self, job: Dict) -> str:
        """Generate a unique hash for a job based on title, company, and location."""
        # Create a normalized string for hashing
        title = job.get('title', '').lower().strip()
        company = job.get('company', '').lower().strip()
        location = job.get('location', '').lower().strip()
        
        # Remove common variations that don't make jobs unique
        title = title.replace('(freelance, remote)', '').replace('(remote)', '').strip()
        title = title.replace('software engineer, ', '').replace(' - ai training', '').strip()
        
        # Create hash
        job_string = f"{title}|{company}|{location}"
        return hashlib.md5(job_string.encode()).hexdigest()
    
    def is_duplicate_job(self, job: Dict) -> bool:
        """Check if this job is a duplicate based on improved logic."""
        job_hash = self.generate_job_hash(job)
        
        if job_hash in self.seen_jobs:
            logger.info(f"🔄 Duplicate job detected: {job.get('title')} at {job.get('company')}")
            return True
        
        self.seen_jobs.add(job_hash)
        return False
    
    async def run_fresh_scrape(self, target_jobs: int = 50):
        """Run a fresh scrape with improved deduplication."""
        logger.info(f"🚀 Starting fresh scrape for {target_jobs} unique jobs...")
        start_time = datetime.now()
        
        try:
            # Step 1: Purge existing data
            await self.purge_database()
            
            # Step 2: Setup database
            await self._setup_database()
            
            # Step 3: Scrape new jobs with better deduplication
            new_jobs = await self._scrape_new_jobs(target_jobs)
            logger.info(f"📊 Scraped {len(new_jobs)} unique jobs")
            
            # Step 4: AI validation and processing
            processed_jobs = await self._process_jobs_with_ai(new_jobs)
            logger.info(f"🤖 AI processed {len(processed_jobs)} jobs")
            
            # Step 5: Save to database
            saved_count = await self._save_jobs_to_database(processed_jobs)
            logger.info(f"💾 Saved {saved_count} jobs to database")
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"✅ Fresh scrape completed in {duration}")
            logger.info(f"📈 Total unique jobs in database: {await self._count_jobs_in_db()}")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error during fresh scrape: {e}")
            raise
    
    async def _setup_database(self):
        """Setup SQLite database tables."""
        logger.info("🔧 Setting up SQLite database...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database setup complete")
    
    async def _scrape_new_jobs(self, target_jobs: int) -> List[Dict]:
        """Scrape new jobs with improved deduplication."""
        all_jobs = []
        
        for scraper in self.scrapers:
            try:
                logger.info(f"🔍 Scraping jobs from {scraper.name}...")
                
                # Scrape more jobs than needed to account for duplicates
                max_jobs_per_scraper = min(target_jobs * 2, 100)
                
                async with scraper:
                    jobs = await scraper.scrape_jobs(max_jobs=max_jobs_per_scraper)
                    
                    # Filter for remote jobs and remove duplicates
                    for job in jobs:
                        if (job.get('is_remote') and 
                            self._is_valid_job(job) and 
                            not self.is_duplicate_job(job)):
                            
                            all_jobs.append(job)
                            logger.info(f"✅ Added unique job: {job.get('title')} at {job.get('company')}")
                            
                            # Stop if we have enough unique jobs
                            if len(all_jobs) >= target_jobs:
                                break
                    
                    logger.info(f"📊 Found {len(all_jobs)} unique jobs from {scraper.name}")
                    
                    # Stop if we have enough jobs
                    if len(all_jobs) >= target_jobs:
                        break
                    
            except Exception as e:
                logger.error(f"❌ Error scraping from {scraper.name}: {e}")
                continue
        
        # Limit to target number
        final_jobs = all_jobs[:target_jobs]
        logger.info(f"🎯 Final unique jobs: {len(final_jobs)}")
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
        
        # Filter out very generic or low-quality job titles
        title = job.get('title', '').lower()
        if any(generic in title for generic in ['intern', 'trainee', 'volunteer']):
            return False
        
        return True
    
    async def _process_jobs_with_ai(self, jobs: List[Dict]) -> List[Dict]:
        """Process jobs with AI for validation and enhancement."""
        processed_jobs = []
        
        for i, job in enumerate(jobs, 1):
            try:
                logger.info(f"🤖 Processing job {i}/{len(jobs)}: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                
                # Try AI processing if available
                try:
                    # Use the cost-effective AI processor
                    ai_analysis = await self.ai_processor.validate_job(job)
                    
                    if ai_analysis and ai_analysis.is_valid:
                        job['ai_processed'] = True
                        job['ai_generated_summary'] = getattr(ai_analysis, 'summary', '')
                        job['remote_type'] = getattr(ai_analysis, 'remote_type', 'remote')
                        job['experience_level'] = getattr(ai_analysis, 'experience_level', 'mid')
                        job['skills_required'] = getattr(ai_analysis, 'skills', [])
                        
                        # Update salary if AI found better info
                        if hasattr(ai_analysis, 'salary_min') and ai_analysis.salary_min:
                            job['salary_min'] = ai_analysis.salary_min
                        if hasattr(ai_analysis, 'salary_max') and ai_analysis.salary_max:
                            job['salary_max'] = ai_analysis.salary_max
                        if hasattr(ai_analysis, 'salary_currency') and ai_analysis.salary_currency:
                            job['salary_currency'] = ai_analysis.salary_currency
                        
                        logger.info(f"✅ AI validated job: {job.get('title')}")
                    else:
                        logger.warning(f"⚠️ AI validation failed for: {job.get('title')}")
                        job['ai_processed'] = False
                    
                except Exception as ai_error:
                    logger.warning(f"⚠️ AI processing failed for job {job.get('title')}: {ai_error}")
                    # Continue without AI processing
                    job['ai_processed'] = False
                
                # Set default values
                job.setdefault('remote_type', 'remote')
                job.setdefault('is_active', True)
                job.setdefault('created_at', datetime.now())
                job.setdefault('updated_at', datetime.now())
                
                # Convert posted_date string to datetime if it exists
                if job.get('posted_date') and isinstance(job['posted_date'], str):
                    try:
                        from dateutil import parser
                        job['posted_date'] = parser.parse(job['posted_date'])
                    except:
                        job['posted_date'] = None
                
                # Clean the job data for database insertion
                cleaned_job = self._clean_job_data(job)
                processed_jobs.append(cleaned_job)
                
                # Rate limiting for AI API calls
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error processing job: {e}")
                # Still add the job even if processing failed
                job.setdefault('remote_type', 'remote')
                job.setdefault('is_active', True)
                job.setdefault('created_at', datetime.now())
                job.setdefault('updated_at', datetime.now())
                
                cleaned_job = self._clean_job_data(job)
                processed_jobs.append(cleaned_job)
                continue
        
        return processed_jobs
    
    def _clean_job_data(self, job: Dict) -> Dict:
        """Clean job data for database insertion."""
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
        
        return cleaned_job
    
    async def _save_jobs_to_database(self, jobs: List[Dict]) -> int:
        """Save processed jobs to database."""
        saved_count = 0
        
        async with AsyncSessionLocal() as session:
            try:
                for job_data in jobs:
                    # Create new job (no duplicates should exist after purging)
                    new_job = Job(**job_data)
                    session.add(new_job)
                    logger.info(f"💾 Adding job: {job_data.get('title')} at {job_data.get('company')}")
                    saved_count += 1
                
                await session.commit()
                logger.info(f"✅ Successfully saved {saved_count} jobs to database")
                
            except Exception as e:
                logger.error(f"❌ Error saving jobs to database: {e}")
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
                logger.error(f"❌ Error counting jobs: {e}")
                return 0

async def main():
    """Main function to run the improved scraper."""
    logger.info("🚀 Starting Improved Job Scraper with Deduplication")
    logger.info("=" * 60)
    
    try:
        scraper = ImprovedJobScraper()
        
        # Run the fresh scrape for 50 unique jobs
        saved_count = await scraper.run_fresh_scrape(target_jobs=50)
        
        logger.info("=" * 60)
        logger.info(f"✅ Fresh scrape completed successfully!")
        logger.info(f"📊 Unique jobs saved to database: {saved_count}")
        logger.info(f"🔄 Duplicates prevented: {len(scraper.seen_jobs) - saved_count}")
        logger.info("🌐 You can now view the unique jobs in the frontend")
        
    except Exception as e:
        logger.error(f"❌ Fresh scrape failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
