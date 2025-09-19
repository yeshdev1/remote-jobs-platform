import os
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import time
# import boto3  # pyright: ignore[reportMissingImports]
from db_utils import insert_jobs_into_db, get_openai_api_key, validate_remote_job_with_o1, job_exists_by_url, get_db_connection, get_most_recent_scraped_time, should_process_job
from import_jobs_data import transform_job_data, insert_job

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36"
}

JOB_SOURCES = [
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]

def get_recent_jobs_dictionary():
    """Get all jobs scraped in the past 2 days and return as URL dictionary
    
    Returns:
        Dictionary with job URLs as keys and job data as values
    """
    from datetime import datetime, timedelta
    
    print("🔍 Fetching jobs from the past 2 days...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate cutoff time (2 days ago)
        cutoff_time = datetime.now() - timedelta(days=2)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Query jobs from the past 2 days
        cursor.execute("""
            SELECT url, title, company, scraped_at 
            FROM jobs 
            WHERE scraped_at >= ?
            ORDER BY scraped_at DESC
        """, (cutoff_str,))
        
        recent_jobs = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary with URL as key
        jobs_dict = {}
        for url, title, company, scraped_at in recent_jobs:
            if url:  # Only include jobs with valid URLs
                jobs_dict[url] = {
                    'title': title,
                    'company': company,
                    'scraped_at': scraped_at
                }
        
        print(f"📊 Found {len(jobs_dict)} jobs scraped in the past 2 days")
        return jobs_dict
        
    except Exception as e:
        print(f"❌ Error fetching recent jobs: {e}")
        return {}

def extract_url_from_job_data(job):
    """Extract URL from job data structure"""
    # WeWorkRemotely specific URL extraction
    if 'url' in job:
        return job['url']
    elif 'href' in job:
        # Construct full URL if it's a relative path
        href = job['href']
        if href.startswith('/'):
            return f"https://weworkremotely.com{href}"
        return href
    elif 'job_id' in job:
        return f"https://weworkremotely.com/remote-jobs/{job['job_id']}"
    return None

def filter_jobs_by_timestamp(job_listings, source_platform):
    """Filter jobs based on posted date vs most recent scraped time
    
    Args:
        job_listings: List of job data dictionaries
        source_platform: Platform name for database filtering
        
    Returns:
        tuple: (new_jobs, skipped_count) where new_jobs is list of jobs to process
               and skipped_count is number of jobs skipped
    """
    if not job_listings:
        return [], 0
    
    print(f"🔍 Filtering {len(job_listings)} jobs by timestamp for {source_platform}...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get most recent scraped time for this platform
        most_recent_scraped_time = get_most_recent_scraped_time(cursor, source_platform)
        
        new_jobs = []
        skipped_count = 0
        
        for job_data in job_listings:
            # Extract original job data
            original_job = job_data.get('original_job_data', {})
            
            if should_process_job(original_job, most_recent_scraped_time):
                new_jobs.append(job_data)
            else:
                skipped_count += 1
        
        conn.close()
        print(f"📊 Filtered results: {len(new_jobs)} new, {skipped_count} skipped")
        return new_jobs, skipped_count
        
    except Exception as e:
        print(f"❌ Error filtering jobs by timestamp: {e}")
        # Return all jobs if filtering fails
        return job_listings, 0

def extract_job_listings(xml_content):
    """Extract all job listings from the XML content"""
    if not xml_content:
        return []
    
    # Use XML parser for RSS feeds
    soup = BeautifulSoup(xml_content, 'xml')
    job_listings = []
    
    # Find all item elements (job listings) within the RSS feed
    items = soup.find_all('item')
    
    for i, item in enumerate(items):
        try:
            # Extract basic information from RSS item
            title_element = item.find('title')
            link_element = item.find('link')
            description_element = item.find('description')
            pub_date_element = item.find('pubDate')
            
            title = title_element.get_text(strip=True) if title_element else ''
            link = link_element.get_text(strip=True) if link_element else ''
            description = description_element.get_text(strip=True) if description_element else ''
            pub_date = pub_date_element.get_text(strip=True) if pub_date_element else ''
            
            # Skip if essential fields are missing
            if not title or not link:
                print(f"Skipping job {i}: missing essential fields")
                continue
            
            # Extract job ID from the URL
            job_id = link.split('/')[-1] if link else f"weworkremotely_{i}"
            
            # Create job data structure for timestamp filtering
            job_data = {
                'title': title,
                'url': link,
                'description': description,
                'publication_date': pub_date,
                'job_id': job_id,
                'source_xml': str(item)
            }
            
            # Package for AI analysis - pass the complete RSS item XML
            job_listing = {
                'html_content': str(item),  # Complete XML content of the RSS item
                'element_id': f"job_{i}",
                'job_id': job_id,
                'original_job_data': job_data
            }
            job_listings.append(job_listing)
            
        except Exception as e:
            print(f"Error extracting job {i}: {e}")
            continue
    
    return job_listings

def analyze_and_validate_with_o1_mini(job_listings, recent_jobs_dict):
    """Use o1-mini to analyze and validate each job listing in a single call"""
    from openai import OpenAI
    import re
    
    # Try to get API key from .env file in project root
    api_key = get_openai_api_key()
    if not api_key:
        print("⚠️ OpenAI API key not found")
        raise ValueError("OpenAI API key is required for job analysis")
        
    client = OpenAI(api_key=api_key)
    
    prompt = """
    Analyze this RSS feed job listing from WeWorkRemotely and extract all relevant information.
    
    Parse the RSS item content and extract:
    - title: Job title (from title element)
    - company: Company name (from title or description)
    - job_type: Employment type (Full-Time, Contract, Part-Time, etc.)
    - location: Location information (from title or description)
    - url: Job URL (from link element)
    - description: Job description/summary (from description element) and remove all special characters and markdown formatting
    - salary: Salary information (from title or description)
    - tags: Array of technologies/skills mentioned (from title or description)
    - skills_analysis: Object with core_skills, implied_skills, and complementary_skills arrays
    
    Additionally, validate if this job meets BOTH criteria:
    1. It's truly remote work (international or USA remote only)
    2. It's a software development/engineering OR product/UX/UI design role
    
    REMOTE VALIDATION Criteria:
    1. The job must be 100% remote (no office requirements, no specific city/state requirements)
    2. The job must be either:
       - International remote (can be done from anywhere in the world)
       - USA remote (can be done from anywhere in the United States)
    3. The job must NOT require:
       - Physical presence in a specific office
       - Specific time zone requirements that limit location
       - Local travel or in-person meetings
       - Work visa sponsorship for international candidates (unless explicitly stated)
    
    JOB TYPE VALIDATION Criteria:
    The job must be ONE of these types:
    - Software Development/Engineering (frontend, backend, full-stack, mobile, DevOps, QA, etc.)
    - Product Management/Product Owner roles
    - UX/UI Design (user experience, user interface, product design, etc.)
    - Data Science/Data Engineering (if technical/engineering focused)
    - Technical Writing (if for software/technical products)
    - Technical Product Marketing (if for software/tech products)
    
    REJECT these job types:
    - Sales, Marketing (non-technical), Customer Success, Support
    - HR, Finance, Operations, Business Development
    - Content Writing, Social Media, Copywriting (non-technical)
    - Administrative, Executive Assistant roles
    - Legal, Compliance, Accounting
    - Healthcare, Education, Consulting (non-tech)
    
    RSS item content:
    {job_html}
    
    Return ONLY a valid JSON object with this exact structure:
    {{
        "title": "Job title",
        "company": "Company name",
        "job_type": "Employment type",
        "location": "Location info",
        "url": "Job URL",
        "description": "Job description",
        "salary": "Salary info",
        "tags": ["technology", "skills", "array"],
        "skills_analysis": {{
            "core_skills": ["primary", "skills"],
            "implied_skills": ["implied", "skills"],
            "complementary_skills": ["additional", "skills"]
        }},
        "is_valid": true/false,
        "remote_type": "international" or "usa_only" or "not_remote",
        "job_type_category": "software_dev" or "product" or "ux_ui_design" or "not_tech",
        "confidence": 0.0-1.0,
        "reasoning": "Brief explanation covering both remote and job type validation",
        "red_flags": ["list", "of", "any", "concerning", "phrases", "found"]
    }}
    
    If the job is not technical/design OR not remote, set is_valid to false and return null for most fields.
    """
    
    analyzed_jobs = []
    
    for i, job in enumerate(job_listings):
        print(f"  Analyzing and validating job {i+1}/{len(job_listings)} (ID: {job['job_id']})...")
        
        try:
            response = client.chat.completions.create(
                model="o1-mini",
                messages=[
                    {"role": "user", "content": prompt.format(job_html=job['html_content'])}
                ]
            )
            
            ai_response = response.choices[0].message.content
            # Check if API response is null or empty
            if not ai_response or ai_response.strip() == "":
                print(f"  Skipping job {job['element_id']}: empty API response")
                continue
            
            # Extract JSON from the response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'(\{.*\})', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = ai_response
            
            # Try to parse the JSON response
            try:
                parsed_job = json.loads(json_str)
                
                # Add the original job_id to the parsed job
                parsed_job['job_id'] = job['job_id']
                
                # Check if job is valid (remote and tech)
                if not parsed_job.get('is_valid', False):
                    print(f"  ❌ Job {job['job_id']} rejected: {parsed_job.get('reasoning', 'Not remote or not tech')}")
                    print(f"     Red flags: {parsed_job.get('red_flags', [])}")
                    continue
                
                # Check if job URL exists in recent jobs dictionary
                job_url = parsed_job.get('url', '')
                if job_url and job_url in recent_jobs_dict:
                    existing_job = recent_jobs_dict[job_url]
                    print(f"  ⏭️  Skipping job {job['job_id']}: URL already exists in recent jobs ({existing_job['title']} at {existing_job['company']})")
                    continue
                
                # Job is valid and new - add all required metadata for DB
                remote_type = parsed_job.get('remote_type', 'unknown')
                job_type_category = parsed_job.get('job_type_category', 'unknown')
                confidence = parsed_job.get('confidence', 0.0)
                print(f"  ✅ Job {job['job_id']} validated as {remote_type} remote, {job_type_category} role (confidence: {confidence:.2f})")
                
                # Add validation metadata for DB insertion
                parsed_job['ai_processed'] = True
                parsed_job['ai_generated_summary'] = f"Validated as {remote_type} remote, {job_type_category} role. {parsed_job.get('reasoning', '')}"
                parsed_job['remote_type'] = remote_type
                parsed_job['job_type'] = job_type_category
                parsed_job['validation_confidence'] = confidence
                parsed_job['validation_red_flags'] = parsed_job.get('red_flags', [])
                
                analyzed_jobs.append(parsed_job)
                
            except json.JSONDecodeError as e:
                print(f"  Error parsing JSON for job {job['job_id']}: {e}")
                analyzed_jobs.append({
                    "job_id": job['job_id'],
                    "raw_analysis": ai_response,
                    "json_error": str(e)
                })
            
            # Add delay between requests to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error analyzing job {job['job_id']}: {e}")
            analyzed_jobs.append({
                "job_id": job['job_id'],
                "error": str(e)
            })
    
    return analyzed_jobs

def fetch_job_page(url):
    """Fetch the job listing page and return the XML content"""
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def clean_and_deduplicate_jobs(jobs):
    """Remove duplicate jobs based on URL and create cleaned array"""
    seen_urls = {}  # Dictionary for bookkeeping
    cleaned_jobs = []  # New array of cleaned jobs
    
    for job in jobs:
        # Get the URL from the job
        job_url = job.get('url', '')
        
        # If URL is not empty and not already seen
        if job_url and job_url not in seen_urls:
            # Add URL to dictionary for bookkeeping
            seen_urls[job_url] = True
            
            # Add the job to cleaned array
            cleaned_jobs.append(job)
        else:
            # URL is empty or already exists, skip this job
            print(f"Skipping duplicate or empty URL: {job_url}")
    
    return cleaned_jobs

def print_scraping_summary(existing_count, new_count, inserted_count, source_platform):
    """Print a comprehensive summary of the scraping process"""
    print(f"\n{'='*60}")
    print(f"📊 SCRAPING SUMMARY - {source_platform}")
    print(f"{'='*60}")
    print(f"🔍 Jobs already in database: {existing_count}")
    print(f"🆕 New jobs found: {new_count}")
    print(f"✅ Jobs successfully inserted: {inserted_count}")
    print(f"⏭️  Jobs skipped (duplicates/invalid): {new_count - inserted_count}")
    
    # Calculate processing efficiency, avoiding division by zero
    total_processed = existing_count + new_count
    if total_processed > 0:
        efficiency = ((existing_count + inserted_count) / total_processed * 100)
        print(f"📈 Total processing efficiency: {efficiency:.1f}%")
    else:
        print(f"📈 Total processing efficiency: N/A (no jobs processed)")
    
    print(f"{'='*60}")

def insert_jobs_into_db_streamlined(jobs, source_platform):
    """Insert jobs directly into the database without additional validation
    
    Args:
        jobs: List of job dictionaries to insert (already validated by AI)
        source_platform: Source platform name (e.g., 'RemoteOK', 'Remotive', 'WeWorkRemotely')
    
    Returns:
        Number of jobs successfully inserted
    """
    if not jobs:
        print("❌ No jobs to insert")
        return 0
    
    print(f"🚀 Inserting {len(jobs)} pre-validated jobs from {source_platform} into database...")
    
    # Connect to database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return 0
    
    imported_count = 0
    skipped_count = 0
    
    for job in jobs:
        try:
            # Skip None jobs
            if job is None:
                print(f"  ⏭️  Skipping None job")
                continue
            
            # Jobs are already validated by AI, so just transform and insert
            print(f"  🔄 Processing job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            
            # Transform the job data
            transformed_job = transform_job_data(job, source_platform)
            
            # Check if job already exists by URL (final safety check)
            if job_exists_by_url(cursor, transformed_job.get('url')):
                print(f"  ⏭️  Skipping existing job: {transformed_job['title']} at {transformed_job['company']}")
                skipped_count += 1
                continue
            
            # Insert the job
            job_id = insert_job(cursor, transformed_job)
            imported_count += 1
            
            print(f"  ✅ Imported: {transformed_job['title']} at {transformed_job['company']}")
            
        except Exception as e:
            print(f"  ❌ Error importing job: {e}")
            continue
    
    # Commit all changes
    conn.commit()
    
    # Show database stats for this platform
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE source_platform = ?", (source_platform,))
    platform_count = cursor.fetchone()[0]
    
    print(f"📊 Successfully imported {imported_count} new jobs from {source_platform}")
    print(f"📊 Skipped {skipped_count} existing jobs from {source_platform}")
    print(f"📊 Total {source_platform} jobs in database: {platform_count}")
    
    conn.close()
    return imported_count

def main():
    # First, get all jobs scraped in the past 2 days
    recent_jobs_dict = get_recent_jobs_dictionary()
    
    all_jobs = []
    total_skipped = 0
    
    for source in JOB_SOURCES:
        print(f"Scraping jobs from {source}...")
        html_content = fetch_job_page(source)
        
        if html_content:
            # Parse the XML to extract job listings
            job_listings = extract_job_listings(html_content)[:2]
            
            if job_listings:
                print(f"Found {len(job_listings)} job listings")
                
                # Filter jobs by timestamp instead of URL checking
                new_jobs, skipped_count = filter_jobs_by_timestamp(job_listings, "WeWorkRemotely")
                total_skipped += skipped_count
                
                if not new_jobs:
                    print(f"🎉 All {len(job_listings)} jobs from this source are older than last scrape!")
                    continue
                
                print(f"Processing {len(new_jobs)} new jobs (skipping {skipped_count} older jobs)...")
                
                # Analyze and validate jobs with AI in single call, checking against recent jobs
                analyzed_jobs = analyze_and_validate_with_o1_mini(new_jobs, recent_jobs_dict)
                
                if isinstance(analyzed_jobs, list):
                    all_jobs.extend(analyzed_jobs)
                else:
                    # If we got an error or raw response, add it to the results
                    all_jobs.append(analyzed_jobs)
                
                # Add a delay to avoid rate limiting
                time.sleep(3)
            else:
                print("No job listings found in this source")
    
    if not all_jobs and total_skipped > 0:
        print_scraping_summary(total_skipped, 0, 0, "WeWorkRemotely")
        print("🎉 No new jobs to process - all jobs are older than last scrape!")
        return []
    
    # Clean and deduplicate jobs
    print(f"\nCleaning and deduplicating {len(all_jobs)} jobs...")
    
    # Filter out None jobs before cleaning
    valid_jobs = [job for job in all_jobs if job is not None]
    print(f"Filtered out {len(all_jobs) - len(valid_jobs)} None jobs")
    
    cleaned_jobs = clean_and_deduplicate_jobs(valid_jobs)
    print(f"After deduplication: {len(cleaned_jobs)} unique jobs")
    
    # Save results to the specified file
    os.makedirs("job_results", exist_ok=True)
    out_path = "job_results/weworkremotely_jobs.json"
    
    with open(out_path, "w") as f:
        json.dump(cleaned_jobs, f, indent=2)
    
    print(f"✅ Saved {len(cleaned_jobs)} cleaned jobs to {out_path}")
    
    # Insert jobs directly into the database (no need for additional validation since it's done in AI call)
    inserted_count = insert_jobs_into_db_streamlined(cleaned_jobs, "WeWorkRemotely")
    
    # Print comprehensive summary
    print_scraping_summary(total_skipped, len(valid_jobs), inserted_count, "WeWorkRemotely")
    
    return cleaned_jobs

if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Scrape and analyze remote jobs from WeWorkRemotely')
    parser.add_argument('--api-key', type=str, help='OpenAI API key')
    parser.add_argument('--max-jobs', type=int, default=3, help='Maximum number of jobs to process per source')
    
    args = parser.parse_args()
    
    # If API key is provided as an argument, set it as an environment variable
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
        print(f"✅ Using API key from command line argument")
    
    # Process up to the specified number of jobs per source
    main()
