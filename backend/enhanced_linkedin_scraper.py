#!/usr/bin/env python3
"""
Enhanced LinkedIn scraper with AI salary extraction.
This version focuses on LinkedIn (which is working) and includes mock data
for other platforms to demonstrate the full system.
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
import random

# Add the backend directory to the Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from app.core.database_sqlite import AsyncSessionLocal, engine, Base
from app.models.job import Job
from app.scraper.sources.linkedin_scraper import LinkedInScraper
from app.ai_processor.salary_extractor import AdvancedSalaryExtractor
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

class EnhancedLinkedInScraper:
    """Enhanced LinkedIn scraper with AI salary extraction and mock data for other platforms."""
    
    def __init__(self):
        self.job_hashes = set()
        self.salary_extractor = AdvancedSalaryExtractor()
        
    async def scrape_all_platforms(self, jobs_per_platform: int = 50) -> List[Dict]:
        """Scrape jobs from LinkedIn and generate mock data for other platforms."""
        all_jobs = []
        
        # Scrape LinkedIn (working platform)
        try:
            logger.info("Scraping LinkedIn...")
            async with LinkedInScraper() as scraper:
                linkedin_jobs = await scraper.scrape_jobs(jobs_per_platform)
                logger.info(f"Found {len(linkedin_jobs)} jobs from LinkedIn")
                all_jobs.extend(linkedin_jobs)
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        
        # Generate mock data for other platforms to demonstrate the system
        mock_platforms = [
            ("Remote.co", self._generate_mock_remote_co_jobs),
            ("WeWorkRemotely", self._generate_mock_weworkremotely_jobs),
            ("AngelList", self._generate_mock_angellist_jobs),
            ("StackOverflow", self._generate_mock_stackoverflow_jobs)
        ]
        
        for platform_name, mock_func in mock_platforms:
            try:
                logger.info(f"Generating mock data for {platform_name}...")
                mock_jobs = mock_func(jobs_per_platform)
                logger.info(f"Generated {len(mock_jobs)} mock jobs for {platform_name}")
                all_jobs.extend(mock_jobs)
            except Exception as e:
                logger.error(f"Error generating mock data for {platform_name}: {e}")
        
        # Remove duplicates
        unique_jobs = self._remove_duplicates(all_jobs)
        logger.info(f"Total unique jobs after deduplication: {len(unique_jobs)}")
        
        return unique_jobs
    
    def _generate_mock_remote_co_jobs(self, count: int) -> List[Dict]:
        """Generate mock Remote.co jobs."""
        companies = ["TechCorp", "RemoteFirst", "DigitalNomad Co", "CloudTech", "VirtualWorks"]
        titles = ["Senior Software Engineer", "Full Stack Developer", "DevOps Engineer", "Product Manager", "UX Designer"]
        salaries = ["$80,000 - $120,000", "$90,000 - $130,000", "$70,000 - $110,000", "$100,000 - $150,000", "$60,000 - $90,000"]
        
        jobs = []
        for i in range(count):
            job = {
                'title': random.choice(titles),
                'company': random.choice(companies),
                'location': 'Remote',
                'source_url': f"https://remote.co/jobs/{i+1}",
                'posted_date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'description': f"Join our remote team as a {random.choice(titles).lower()}. We offer competitive salary and benefits.",
                'salary': random.choice(salaries),
                'source_platform': 'remote.co',
                'is_remote': True,
                'remote_type': 'remote'
            }
            jobs.append(job)
        
        return jobs
    
    def _generate_mock_weworkremotely_jobs(self, count: int) -> List[Dict]:
        """Generate mock WeWorkRemotely jobs."""
        companies = ["StartupXYZ", "RemoteHub", "TechStart", "DigitalAgency", "CloudStartup"]
        titles = ["Frontend Developer", "Backend Engineer", "Data Scientist", "Marketing Manager", "Sales Representative"]
        salaries = ["$75,000 - $105,000", "$85,000 - $115,000", "$95,000 - $125,000", "$65,000 - $95,000", "$55,000 - $85,000"]
        
        jobs = []
        for i in range(count):
            job = {
                'title': random.choice(titles),
                'company': random.choice(companies),
                'location': 'Remote',
                'source_url': f"https://weworkremotely.com/jobs/{i+1}",
                'posted_date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'description': f"Remote position for {random.choice(titles).lower()}. Work from anywhere in the world.",
                'salary': random.choice(salaries),
                'source_platform': 'weworkremotely',
                'is_remote': True,
                'remote_type': 'remote'
            }
            jobs.append(job)
        
        return jobs
    
    def _generate_mock_angellist_jobs(self, count: int) -> List[Dict]:
        """Generate mock AngelList jobs."""
        companies = ["AI Startup", "FinTech Co", "HealthTech", "EdTech Solutions", "GreenTech"]
        titles = ["Machine Learning Engineer", "Blockchain Developer", "Mobile App Developer", "Growth Hacker", "Technical Writer"]
        salaries = ["$110,000 - $160,000", "$120,000 - $170,000", "$100,000 - $140,000", "$80,000 - $120,000", "$70,000 - $100,000"]
        
        jobs = []
        for i in range(count):
            job = {
                'title': random.choice(titles),
                'company': random.choice(companies),
                'location': 'Remote',
                'source_url': f"https://wellfound.com/jobs/{i+1}",
                'posted_date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'description': f"Join our innovative startup as a {random.choice(titles).lower()}. Equity and competitive salary included.",
                'salary': random.choice(salaries),
                'source_platform': 'angellist',
                'is_remote': True,
                'remote_type': 'remote'
            }
            jobs.append(job)
        
        return jobs
    
    def _generate_mock_stackoverflow_jobs(self, count: int) -> List[Dict]:
        """Generate mock StackOverflow jobs."""
        companies = ["CodeCorp", "DevStudio", "TechGiant", "SoftwareHouse", "CodeCraft"]
        titles = ["Senior Python Developer", "React Specialist", "Database Administrator", "System Architect", "QA Engineer"]
        salaries = ["$95,000 - $135,000", "$105,000 - $145,000", "$85,000 - $125,000", "$115,000 - $155,000", "$75,000 - $105,000"]
        
        jobs = []
        for i in range(count):
            job = {
                'title': random.choice(titles),
                'company': random.choice(companies),
                'location': 'Remote',
                'source_url': f"https://stackoverflow.com/jobs/{i+1}",
                'posted_date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'description': f"Looking for an experienced {random.choice(titles).lower()} to join our remote team.",
                'salary': random.choice(salaries),
                'source_platform': 'stackoverflow',
                'is_remote': True,
                'remote_type': 'remote'
            }
            jobs.append(job)
        
        return jobs
    
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
                        job.pop('is_remote', None)
                        
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
    """Main function to run the enhanced LinkedIn scraper."""
    logger.info("Starting enhanced LinkedIn scraper with AI salary extraction...")
    
    # Purge existing jobs
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(delete(Job))
            await db.commit()
            logger.info("Purged existing jobs from database")
        except Exception as e:
            logger.error(f"Error purging database: {e}")
    
    # Run scraper
    scraper = EnhancedLinkedInScraper()
    
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
