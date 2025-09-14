"""
Simple AI Job Board Search Agent

This script fetches remote job listings from various sources and processes them with OpenAI.
"""

import os
import asyncio
import aiohttp
import sqlite3
import logging
import json
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SimpleJobScraper:
    """Simple job scraper for remote job boards"""
    
    def __init__(self, name, base_url):
        self.name = name
        self.base_url = base_url
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, url):
        """Make HTTP request with error handling and timeout"""
        try:
            # Set a timeout to avoid hanging
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout when requesting {url}")
            return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return None
    
    def parse_html(self, html):
        """Parse HTML content"""
        return BeautifulSoup(html, 'html.parser')
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.split()).strip()

class SimpleRemoteCoScraper(SimpleJobScraper):
    """Simple scraper for Remote.co"""
    
    def __init__(self):
        super().__init__("Remote.co", "https://remote.co")
    
    async def scrape_jobs(self, max_jobs=10):
        """Scrape jobs from Remote.co"""
        jobs = []
        url = f"{self.base_url}/remote-jobs/"
        
        html = await self.make_request(url)
        if not html:
            return jobs
        
        soup = self.parse_html(html)
        job_listings = soup.find_all('div', class_='job_listing')
        
        for listing in job_listings[:max_jobs]:
            try:
                # Extract job title
                title_elem = listing.find('h3', class_='job_title')
                if not title_elem:
                    continue
                title = self.clean_text(title_elem.get_text())
                
                # Extract company
                company_elem = listing.find('span', class_='company')
                company = self.clean_text(company_elem.get_text()) if company_elem else "Unknown"
                
                # Extract job URL
                link_elem = listing.find('a', href=True)
                if not link_elem:
                    continue
                job_url = f"{self.base_url}{link_elem['href']}" if link_elem['href'].startswith('/') else link_elem['href']
                
                # Extract description
                desc_elem = listing.find('div', class_='job_description')
                description = self.clean_text(desc_elem.get_text()) if desc_elem else ""
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': 'Remote',
                    'source_url': job_url,
                    'description': description,
                    'source_platform': 'remote.co',
                    'posted_date': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error parsing Remote.co listing: {e}")
        
        logger.info(f"Scraped {len(jobs)} jobs from Remote.co")
        return jobs

class SimpleWeWorkRemotelyScraper(SimpleJobScraper):
    """Simple scraper for WeWorkRemotely"""
    
    def __init__(self):
        super().__init__("WeWorkRemotely", "https://weworkremotely.com")
    
    async def scrape_jobs(self, max_jobs=10):
        """Scrape jobs from WeWorkRemotely"""
        jobs = []
        url = f"{self.base_url}/categories/remote-programming-jobs"
        
        html = await self.make_request(url)
        if not html:
            return jobs
        
        soup = self.parse_html(html)
        job_listings = soup.find_all('li', class_='feature')
        
        for listing in job_listings[:max_jobs]:
            try:
                # Extract job title and company
                title_elem = listing.find('span', class_='title')
                if not title_elem:
                    continue
                
                title_text = self.clean_text(title_elem.get_text())
                # Split title and company (usually separated by " at ")
                if " at " in title_text:
                    title, company = title_text.split(" at ", 1)
                else:
                    title = title_text
                    company = "Unknown"
                
                # Extract job URL
                link_elem = listing.find('a', href=True)
                if not link_elem:
                    continue
                job_url = f"{self.base_url}{link_elem['href']}" if link_elem['href'].startswith('/') else link_elem['href']
                
                # Extract description
                desc_elem = listing.find('span', class_='company')
                description = self.clean_text(desc_elem.get_text()) if desc_elem else ""
                
                jobs.append({
                    'title': title.strip(),
                    'company': company.strip(),
                    'location': 'Remote',
                    'source_url': job_url,
                    'description': description,
                    'source_platform': 'weworkremotely',
                    'posted_date': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error parsing WeWorkRemotely listing: {e}")
        
        logger.info(f"Scraped {len(jobs)} jobs from WeWorkRemotely")
        return jobs

class SimpleWorkingNomadsScraper(SimpleJobScraper):
    """Simple scraper for WorkingNomads"""
    
    def __init__(self):
        super().__init__("WorkingNomads", "https://www.workingnomads.com")
    
    async def scrape_jobs(self, max_jobs=10):
        """Scrape jobs from WorkingNomads"""
        jobs = []
        url = f"{self.base_url}/jobs"
        
        html = await self.make_request(url)
        if not html:
            return jobs
        
        soup = self.parse_html(html)
        job_listings = soup.find_all('div', class_='job-list-item')
        
        for listing in job_listings[:max_jobs]:
            try:
                # Extract job title
                title_elem = listing.find('h2', class_='job-title')
                if not title_elem:
                    continue
                title = self.clean_text(title_elem.get_text())
                
                # Extract company
                company_elem = listing.find('span', class_='company')
                company = self.clean_text(company_elem.get_text()) if company_elem else "Unknown"
                
                # Extract job URL
                link_elem = listing.find('a', href=True)
                if not link_elem:
                    continue
                job_url = f"{self.base_url}{link_elem['href']}" if link_elem['href'].startswith('/') else link_elem['href']
                
                # Extract description
                desc_elem = listing.find('div', class_='job-description')
                description = self.clean_text(desc_elem.get_text()) if desc_elem else ""
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': 'Remote',
                    'source_url': job_url,
                    'description': description,
                    'source_platform': 'workingnomads',
                    'posted_date': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error parsing WorkingNomads listing: {e}")
        
        logger.info(f"Scraped {len(jobs)} jobs from WorkingNomads")
        return jobs

class SimpleJobAgent:
    """Simple agent that fetches and processes remote job listings"""
    
    def __init__(self):
        # Get OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # SQLite connection
        self.db_path = 'remote_jobs.db'
        self.conn = None
        
        # Initialize scrapers
        self.scrapers = [
            SimpleRemoteCoScraper(),
            SimpleWeWorkRemotelyScraper(),
            SimpleWorkingNomadsScraper()
        ]
    
    def setup_database(self):
        """Set up SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create jobs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary_min REAL,
            salary_max REAL,
            salary_currency TEXT DEFAULT 'USD',
            description TEXT,
            source_url TEXT UNIQUE,
            source_platform TEXT NOT NULL,
            posted_date TEXT,
            skills_required TEXT,
            ai_generated_summary TEXT,
            ai_processed INTEGER DEFAULT 0,
            created_at TEXT
        )
        ''')
        
        self.conn.commit()
        logger.info(f"Database setup complete: {self.db_path}")
    
    async def fetch_jobs(self, max_jobs_per_source=10):
        """Fetch jobs from all sources"""
        all_jobs = []
        
        for scraper in self.scrapers:
            try:
                async with scraper:
                    try:
                        jobs = await scraper.scrape_jobs(max_jobs=max_jobs_per_source)
                        all_jobs.extend(jobs)
                    except Exception as e:
                        logger.error(f"Error with {scraper.name} scraper: {e}")
            except Exception as e:
                logger.error(f"Failed to initialize {scraper.name} scraper: {e}")
                
                # Generate dummy jobs if scraper fails
                logger.info(f"Generating dummy jobs for {scraper.name}")
                dummy_jobs = self.generate_dummy_jobs(scraper.name, max_jobs_per_source)
                all_jobs.extend(dummy_jobs)
        
        logger.info(f"Fetched a total of {len(all_jobs)} jobs from all sources")
        return all_jobs
        
    def generate_dummy_jobs(self, source, count=5):
        """Generate dummy jobs for testing"""
        dummy_jobs = []
        
        job_titles = [
            "Remote Python Developer", 
            "Frontend React Engineer",
            "DevOps Specialist",
            "UI/UX Designer",
            "Product Manager"
        ]
        
        companies = [
            "TechCorp", 
            "RemoteFirst Inc",
            "Digital Nomads Ltd",
            "CloudScale",
            "DataDriven"
        ]
        
        for i in range(count):
            job_idx = i % len(job_titles)
            company_idx = i % len(companies)
            
            dummy_jobs.append({
                'title': job_titles[job_idx],
                'company': companies[company_idx],
                'location': 'Remote',
                'source_url': f"https://example.com/{source.lower()}/jobs/{i+1}",
                'description': f"This is a remote position for a {job_titles[job_idx]} at {companies[company_idx]}. The ideal candidate will have strong technical skills and the ability to work independently.",
                'source_platform': source.lower(),
                'posted_date': datetime.now().isoformat()
            })
        
        logger.info(f"Generated {count} dummy jobs for {source}")
        return dummy_jobs
    
    async def process_with_ai(self, jobs):
        """Process jobs with OpenAI"""
        processed_jobs = []
        
        for job in jobs:
            try:
                # Create a prompt for OpenAI
                prompt = f"""
                Analyze this remote job posting:
                
                Title: {job.get('title', '')}
                Company: {job.get('company', '')}
                Description: {job.get('description', '')[:500]}
                
                Please provide:
                1. A concise 1-2 sentence summary of this remote job
                2. A list of 3-5 key skills required (as a comma-separated list)
                3. Estimated salary range in USD (min and max)
                
                Format your response as JSON:
                {{
                    "summary": "...",
                    "skills": ["skill1", "skill2", "skill3"],
                    "salary_min": 70000,
                    "salary_max": 120000
                }}
                """
                
                # Call OpenAI API with gpt-4o-mini model
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                # Parse the response
                result = json.loads(response.choices[0].message.content)
                
                # Update job with AI-generated data
                job['ai_processed'] = True
                job['ai_generated_summary'] = result.get('summary', f"Remote position for {job['title']} at {job['company']}.")
                job['skills_required'] = result.get('skills', [])
                job['salary_min'] = result.get('salary_min', 70000)
                job['salary_max'] = result.get('salary_max', 120000)
                
                logger.info(f"Processed job: {job['title']} with AI")
                
            except Exception as e:
                logger.error(f"Error processing job with AI: {e}")
                job['ai_processed'] = False
                job['ai_generated_summary'] = f"Remote position for {job['title']} at {job['company']}."
                job['skills_required'] = []
                job['salary_min'] = 70000
                job['salary_max'] = 120000
            
            processed_jobs.append(job)
        
        return processed_jobs
    
    def store_jobs(self, jobs, purge_existing=True):
        """Store jobs in SQLite database"""
        if not self.conn:
            self.setup_database()
        
        cursor = self.conn.cursor()
        
        # Clear existing jobs if needed
        if purge_existing:
            cursor.execute("DELETE FROM jobs")
            logger.info("Purged existing jobs from database")
        
        # Insert jobs
        inserted_count = 0
        for job in jobs:
            # Convert skills list to string if needed
            skills = job.get('skills_required', [])
            if isinstance(skills, list):
                skills = ','.join(skills)
            
            try:
                cursor.execute('''
                INSERT INTO jobs (
                    title, company, location, salary_min, salary_max, salary_currency,
                    description, source_url, source_platform, posted_date,
                    skills_required, ai_generated_summary, ai_processed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.get('title', ''),
                    job.get('company', ''),
                    job.get('location', 'Remote'),
                    job.get('salary_min', 0),
                    job.get('salary_max', 0),
                    'USD',
                    job.get('description', ''),
                    job.get('source_url', ''),
                    job.get('source_platform', ''),
                    job.get('posted_date', datetime.now().isoformat()),
                    skills,
                    job.get('ai_generated_summary', ''),
                    1 if job.get('ai_processed', False) else 0,
                    datetime.now().isoformat()
                ))
                inserted_count += 1
            except sqlite3.IntegrityError:
                logger.warning(f"Duplicate job URL: {job.get('source_url')}")
            except Exception as e:
                logger.error(f"Error inserting job {job.get('title')}: {e}")
        
        self.conn.commit()
        logger.info(f"Inserted {inserted_count} jobs into database")
        return inserted_count
    
    def get_stored_jobs(self, limit=10):
        """Get jobs from database"""
        if not self.conn:
            self.setup_database()
        
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, title, company, ai_generated_summary, source_platform
        FROM jobs
        ORDER BY id DESC
        LIMIT ?
        ''', (limit,))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                'id': row[0],
                'title': row[1],
                'company': row[2],
                'summary': row[3],
                'source': row[4]
            })
        
        return jobs
    
    async def run(self, max_jobs_per_source=10, purge_existing=True, use_dummy_data=True):
        """Run the agent to fetch, process, and store jobs"""
        try:
            # Setup database
            self.setup_database()
            
            # Fetch jobs (or use dummy data)
            if use_dummy_data:
                logger.info("Using dummy data instead of scraping")
                jobs = []
                for source in ["remote.co", "weworkremotely", "workingnomads"]:
                    dummy_jobs = self.generate_dummy_jobs(source, max_jobs_per_source)
                    jobs.extend(dummy_jobs)
                logger.info(f"Generated {len(jobs)} dummy jobs")
            else:
                jobs = await self.fetch_jobs(max_jobs_per_source)
            
            # Process with AI
            processed_jobs = await self.process_with_ai(jobs)
            
            # Store jobs
            stored_count = self.store_jobs(processed_jobs, purge_existing)
            
            # Get sample of stored jobs
            sample_jobs = self.get_stored_jobs(5)
            
            return {
                "status": "success",
                "jobs_fetched": len(jobs),
                "jobs_stored": stored_count,
                "sample_jobs": sample_jobs
            }
            
        except Exception as e:
            logger.error(f"Error running job agent: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            if self.conn:
                self.conn.close()

async def main():
    """Run the simple job agent"""
    print("Starting Simple Job Agent...")
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        return
    
    # Run the agent
    agent = SimpleJobAgent()
    result = await agent.run(max_jobs_per_source=3)
    
    # Print results
    print("\n" + "="*50)
    print("Simple Job Agent Results:")
    print("="*50)
    print(f"Status: {result['status']}")
    print(f"Jobs Fetched: {result['jobs_fetched']}")
    print(f"Jobs Stored: {result['jobs_stored']}")
    print("="*50)
    
    # Print sample jobs
    if result.get('sample_jobs'):
        print("\nSample Jobs:")
        for job in result['sample_jobs']:
            print(f"\n{job['title']} at {job['company']} (from {job['source']})")
            print(f"Summary: {job['summary']}")
    
    print("\n" + "="*50)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
