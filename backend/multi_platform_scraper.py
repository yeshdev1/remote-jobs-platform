#!/usr/bin/env python3
"""
Multi-platform job scraper with advanced AI salary extraction.
Scrapes from multiple job platforms and uses multi-prompting with varying temperatures
to extract salary information with high confidence.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from loguru import logger
import hashlib
import re

# Add the backend directory to the Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.core.database_sqlite import AsyncSessionLocal, engine, Base
from app.models.job import Job
from app.scraper.sources.linkedin_scraper import LinkedInScraper
from app.scraper.sources.remote_co_scraper import RemoteCoScraper
from app.scraper.sources.weworkremotely_scraper import WeWorkRemotelyScraper
from app.scraper.sources.angellist_scraper import AngelListScraper
from app.scraper.sources.stackoverflow_scraper import StackOverflowScraper
from app.ai_processor.salary_extractor import AdvancedSalaryExtractor
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

class MultiPlatformJobScraper:
    """Multi-platform job scraper with AI salary extraction."""
    
    def __init__(self):
        self.job_hashes = set()
        self.salary_extractor = AdvancedSalaryExtractor()
        
    async def scrape_all_platforms(self, jobs_per_platform: int = 50) -> List[Dict]:
        """Scrape jobs from all platforms."""
        all_jobs = []
        
        # Define scrapers
        scrapers = [
            ("LinkedIn", LinkedInScraper),
            ("Remote.co", RemoteCoScraper),
            ("WeWorkRemotely", WeWorkRemotelyScraper),
            ("AngelList", AngelListScraper),
            ("StackOverflow", StackOverflowScraper)
        ]
        
        for platform_name, scraper_class in scrapers:
            try:
                logger.info(f"Scraping {platform_name}...")
                
                async with scraper_class() as scraper:
                    jobs = await scraper.scrape_jobs(jobs_per_platform)
                    logger.info(f"Found {len(jobs)} jobs from {platform_name}")
                    all_jobs.extend(jobs)
                    
            except Exception as e:
                logger.error(f"Error scraping {platform_name}: {e}")
                continue
        
        # Remove duplicates
        unique_jobs = self._remove_duplicates(all_jobs)
        logger.info(f"Total unique jobs after deduplication: {len(unique_jobs)}")
        
        return unique_jobs
    
    def _remove_duplicates(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs using improved hashing."""
        unique_jobs = []
        
        for job in jobs:
            # Create a more robust hash
            title = job.get('title', '').lower().strip()
            company = job.get('company', '').lower().strip()
            
            # Normalize title and company
            title = re.sub(r'\([^)]*\)', '', title)  # Remove parentheses
            title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
            company = re.sub(r'\s+', ' ', company)
            
            # Create hash
            job_hash = hashlib.md5(f"{title}|{company}".encode()).hexdigest()
            
            if job_hash not in self.job_hashes:
                self.job_hashes.add(job_hash)
                unique_jobs.append(job)
        
        return unique_jobs
    
    async def extract_salaries_with_ai(self, jobs: List[Dict]) -> List[Dict]:
        """Extract salary information using AI for all jobs."""
        logger.info(f"Extracting salary information for {len(jobs)} jobs using AI...")
        
        processed_jobs = []
        for i, job in enumerate(jobs):
            try:
                logger.info(f"Processing job {i+1}/{len(jobs)}: {job.get('title', 'Unknown')}")
                processed_job = await self.salary_extractor.extract_salary_with_confidence(job)
                processed_jobs.append(processed_job)
                
                # Log salary extraction results
                salary = processed_job.get('ai_extracted_salary', 'No salary')
                confidence = processed_job.get('salary_confidence', 0)
                logger.info(f"  → Salary: {salary} (Confidence: {confidence:.2f})")
                
            except Exception as e:
                logger.error(f"Error processing job {i+1}: {e}")
                processed_jobs.append(job)
                continue
        
        return processed_jobs
    
    async def save_jobs_to_database(self, jobs: List[Dict]) -> int:
        """Save jobs to SQLite database."""
        saved_count = 0
        
        async with AsyncSessionLocal() as db:
            try:
                for job in jobs:
                    try:
                        # Convert posted_date to datetime if it's a string
                        if job.get('posted_date') and isinstance(job['posted_date'], str):
                            try:
                                from dateutil import parser
                                job['posted_date'] = parser.parse(job['posted_date'])
                            except:
                                job['posted_date'] = datetime.now()
                        
                        # Map salary information to correct fields
                        salary_info = self._extract_salary_info(job)
                        job['salary_min'] = salary_info.get('min')
                        job['salary_max'] = salary_info.get('max')
                        job['salary_currency'] = salary_info.get('currency', 'USD')
                        job['salary_period'] = salary_info.get('period', 'yearly')
                        
                        # Remove fields that don't exist in Job model
                        job.pop('salary', None)
                        job.pop('ai_extracted_salary', None)
                        job.pop('salary_confidence', None)
                        job.pop('salary_extraction_method', None)
                        job.pop('salary_extraction_details', None)
                        
                        # Set default values
                        job.setdefault('remote_type', 'remote')
                        job.setdefault('is_active', True)
                        job.setdefault('created_at', datetime.now())
                        job.setdefault('updated_at', datetime.now())
                        
                        # Create Job object
                        job_obj = Job(**job)
                        db.add(job_obj)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving job {job.get('title', 'Unknown')}: {e}")
                        continue
                
                await db.commit()
                logger.info(f"Successfully saved {saved_count} jobs to database")
                
            except Exception as e:
                logger.error(f"Error saving jobs to database: {e}")
                await db.rollback()
        
        return saved_count
    
    def _extract_salary_info(self, job: Dict) -> Dict:
        """Extract salary information and map to database fields."""
        salary_info = {'min': None, 'max': None, 'currency': 'USD', 'period': 'yearly'}
        
        # Check for AI extracted salary
        ai_salary = job.get('ai_extracted_salary', '')
        if ai_salary and 'no' not in ai_salary.lower():
            # Try to parse AI extracted salary
            parsed = self._parse_salary_text(ai_salary)
            if parsed:
                salary_info.update(parsed)
        
        # Check for original salary field
        original_salary = job.get('salary', '')
        if original_salary and not salary_info['min']:
            parsed = self._parse_salary_text(original_salary)
            if parsed:
                salary_info.update(parsed)
        
        return salary_info
    
    def _parse_salary_text(self, salary_text: str) -> Optional[Dict]:
        """Parse salary text to extract min, max, currency, and period."""
        if not salary_text:
            return None
        
        # Look for salary patterns
        import re
        
        # Range patterns like $50,000 - $80,000
        range_pattern = r'\$?([\d,]+)(?:k|K)?\s*-\s*\$?([\d,]+)(?:k|K)?'
        match = re.search(range_pattern, salary_text)
        if match:
            try:
                min_val = float(match.group(1).replace(',', ''))
                max_val = float(match.group(2).replace(',', ''))
                # Convert K to thousands
                if 'k' in match.group(1).lower():
                    min_val *= 1000
                if 'k' in match.group(2).lower():
                    max_val *= 1000
                return {'min': min_val, 'max': max_val, 'currency': 'USD', 'period': 'yearly'}
            except ValueError:
                pass
        
        # Single salary patterns
        single_pattern = r'\$?([\d,]+)(?:k|K)?'
        match = re.search(single_pattern, salary_text)
        if match:
            try:
                val = float(match.group(1).replace(',', ''))
                if 'k' in match.group(1).lower():
                    val *= 1000
                return {'min': val, 'max': val, 'currency': 'USD', 'period': 'yearly'}
            except ValueError:
                pass
        
        return None

async def main():
    """Main function to run the multi-platform scraper."""
    logger.info("Starting multi-platform job scraper with AI salary extraction...")
    
    # Purge existing jobs
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(Job))
            await db.commit()
            logger.info("Purged existing jobs from database")
        except Exception as e:
            logger.error(f"Error purging database: {e}")
    
    # Run scraper
    scraper = MultiPlatformJobScraper()
    
    # Scrape jobs from all platforms (50 jobs per platform = 250 total)
    jobs = await scraper.scrape_all_platforms(jobs_per_platform=50)
    
    logger.info(f"Found {len(jobs)} unique jobs across all platforms")
    
    # Extract salary information using AI
    jobs_with_salaries = await scraper.extract_salaries_with_ai(jobs)
    
    # Save to database
    saved_count = await scraper.save_jobs_to_database(jobs_with_salaries)
    
    logger.info(f"Successfully scraped and saved {saved_count} jobs with AI salary extraction!")
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*50)
    logger.info(f"Total jobs scraped: {len(jobs)}")
    logger.info(f"Jobs saved to database: {saved_count}")
    
    # Count jobs with salary information
    jobs_with_salary = [j for j in jobs_with_salaries if j.get('ai_extracted_salary') and 'no' not in j.get('ai_extracted_salary', '').lower()]
    logger.info(f"Jobs with salary information: {len(jobs_with_salary)}")
    
    # Show sample of jobs with salaries
    if jobs_with_salary:
        logger.info("\nSample jobs with salary information:")
        for i, job in enumerate(jobs_with_salary[:5]):
            salary = job.get('ai_extracted_salary', 'No salary')
            confidence = job.get('salary_confidence', 0)
            logger.info(f"  {i+1}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            logger.info(f"     Salary: {salary} (Confidence: {confidence:.2f})")

if __name__ == "__main__":
    asyncio.run(main())
