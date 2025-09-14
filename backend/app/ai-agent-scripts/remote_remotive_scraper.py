import os
import requests
import json
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from openai import OpenAI
# import boto3
from db_utils import insert_jobs_into_db, get_openai_api_key, validate_remote_job_with_o1

# Get API key from .env file in project root
api_key = get_openai_api_key()

# Initialize OpenAI client if API key is available
client = None
if api_key:
    client = OpenAI(api_key=api_key)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36"
}

JOB_CATEGORIES = [
    "software-dev",
    "design",
    "data",
    "qa",
]

JOB_BASE_URL = "https://remotive.com/api/remote-jobs?category="


def fetch_job_page(url):
    """Fetch the job listing page and return the HTML content"""
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        # Parse JSON response
        json_data = response.json()
        return json_data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_job_listings(json_data):
    """Extract all job listings from the JSON data"""
    if not json_data:
        return []
    
    # Extract jobs from the JSON structure
    jobs = json_data.get('jobs', [])
    
    job_listings = []
    for i, job in enumerate(jobs):
        # Create HTML-like structure from the job data for AI processing
        job_html = f"""
        <div class="job-listing">
            <div class="job-id">{job.get('id', '')}</div>
            <div class="job-title">{job.get('title', '')}</div>
            <div class="company-name">{job.get('company_name', '')}</div>
            <div class="company-logo">{job.get('company_logo', '')}</div>
            <div class="category">{job.get('category', '')}</div>
            <div class="tags">{', '.join(job.get('tags', []))}</div>
            <div class="job-type">{job.get('job_type', '')}</div>
            <div class="publication-date">{job.get('publication_date', '')}</div>
            <div class="location">{job.get('candidate_required_location', '')}</div>
            <div class="salary">{job.get('salary', '')}</div>
            <div class="description">{job.get('description', '')}</div>
            <div class="job-url">{job.get('url', '')}</div>
        </div>
        """
        
        # Send the complete job data to AI
        job_data = {
            'html_content': job_html,  # Structured HTML with job data
            'element_id': f"job_{i}",  # Just an ID for reference
            'job_id': job.get('id', '')  # Store the job ID for reference
        }
        job_listings.append(job_data)
    
    return job_listings


def analyze_with_o1_mini(job_listings):
    """Use o1-mini to analyze each job listing individually"""
    # Check if client is initialized
    if client is None:
        print("⚠️ OpenAI client not initialized - API key not available")
        raise ValueError("OpenAI API key is required for job analysis")
        
    prompt = """
    Analyze this HTML job listing from Remotive and extract all relevant information.
    
    Parse the HTML content and extract:
    - title: Job title (from heading elements or title text)
    - company: Company name (from company elements or text)
    - job_type: Employment type (Full-Time, Contract, Part-Time, etc.)
    - location: Location information (from location elements or text)
    - url: Complete job URL (construct from href attributes or links)
    - description: Job description/summary (from description text or content)
    - salary: Salary information (from salary elements or text)
    - tags: Array of technologies/skills mentioned (from tag elements or text)
    - skills_analysis: Object with core_skills, implied_skills, and complementary_skills arrays
    - if it is not either an technical or design job, then return null
    
    HTML job listing:
    {job_html}
    
    Return ONLY a valid JSON object with the extracted information. No additional text or explanation.
    """
    
    analyzed_jobs = []
    
    for i, job in enumerate(job_listings):
        print(f"  Analyzing job {i+1}/{len(job_listings)} (ID: {job['element_id']})...")
        
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
                
                # Add the original element_id to the parsed job
                parsed_job['element_id'] = job['element_id']
                
                # Validate the job is truly remote using o1-mini
                print(f"  🔍 Validating remote status for job {job['element_id']}...")
                validation_result = validate_remote_job_with_o1(parsed_job)
                
                # Only include jobs that are validated as remote AND tech roles
                if validation_result.get('is_valid', False):
                    remote_type = validation_result.get('remote_type', 'unknown')
                    job_type = validation_result.get('job_type', 'unknown')
                    confidence = validation_result.get('confidence', 0.0)
                    print(f"  ✅ Job {job['element_id']} validated as {remote_type} remote, {job_type} role (confidence: {confidence:.2f})")
                    
                    # Add validation metadata
                    parsed_job['ai_processed'] = True
                    parsed_job['ai_generated_summary'] = f"Validated as {remote_type} remote, {job_type} role. {validation_result.get('reasoning', '')}"
                    parsed_job['remote_type'] = remote_type
                    parsed_job['job_type'] = job_type
                    parsed_job['validation_confidence'] = confidence
                    parsed_job['validation_red_flags'] = validation_result.get('red_flags', [])
                    
                    analyzed_jobs.append(parsed_job)
                else:
                    print(f"  ❌ Job {job['element_id']} rejected: {validation_result.get('reasoning', 'Not remote or not tech')}")
                    print(f"     Red flags: {validation_result.get('red_flags', [])}")
                
            except json.JSONDecodeError as e:
                print(f"  Error parsing JSON for job {job['element_id']}: {e}")
                analyzed_jobs.append({
                    "element_id": job['element_id'],
                    "raw_analysis": ai_response,
                    "json_error": str(e)
                })
            
            # Add delay between requests to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error analyzing job {job['element_id']}: {e}")
            analyzed_jobs.append({
                "element_id": job['element_id'],
                "error": str(e)
            })
    
    return analyzed_jobs

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

# def upload_to_s3(data, filename):
#     """Upload data to S3 bucket"""
#     s3 = boto3.client('s3')
#     bucket_name = 'job-scraper-data'
#     date_prefix = datetime.now().strftime("%Y/%m/%d")
#     s3_key = f"{date_prefix}/{filename}"
#     
#     try:
#         s3.put_object(
#             Body=json.dumps(data),
#             Bucket=bucket_name,
#             Key=s3_key,
#             ContentType='application/json'
#         )
#         print(f"✅ Uploaded data to s3://{bucket_name}/{s3_key}")
#     except Exception as e:
#         print(f"Error uploading to S3: {e}")

def main():
    """Main function to scrape jobs and analyze them with AI"""
    all_jobs = []
    
    for source in JOB_CATEGORIES:
        source = JOB_BASE_URL + source
        print(f"\nScraping jobs from {source}...")
        json_data = fetch_job_page(source)
        
        if json_data:
            # Parse the HTML to extract job listings
            job_listings = extract_job_listings(json_data)
            
            # Limit the number of jobs to process per source
            
            if job_listings:
                print(f"Found {len(job_listings)} job listings, analyzing {len(job_listings)} with AI...")
                
                # Analyze with AI
                analyzed_jobs = analyze_with_o1_mini(job_listings)
                
                if isinstance(analyzed_jobs, list):
                    all_jobs.extend(analyzed_jobs)
                else:
                    # If we got an error or raw response, add it to the results
                    all_jobs.append(analyzed_jobs)
                
                # Add a delay to avoid rate limiting
                time.sleep(3)
            else:
                print("No job listings found in this source")
    
    # Clean and deduplicate jobs
    print(f"\nCleaning and deduplicating {len(all_jobs)} jobs...")
    
    # Filter out None jobs before cleaning
    valid_jobs = [job for job in all_jobs if job is not None]
    print(f"Filtered out {len(all_jobs) - len(valid_jobs)} None jobs")
    
    cleaned_jobs = clean_and_deduplicate_jobs(valid_jobs)
    print(f"After deduplication: {len(cleaned_jobs)} unique jobs")
    
    # Save results to the specified file
    os.makedirs("job_results", exist_ok=True)
    out_path = "job_results/remotive_jobs.json"
    
    with open(out_path, "w") as f:
        json.dump(cleaned_jobs, f, indent=2)
    
    print(f"✅ Saved {len(cleaned_jobs)} cleaned jobs to {out_path}")
    
    # Insert jobs directly into the database
    inserted_count = insert_jobs_into_db(cleaned_jobs, "Remotive")
    print(f"📊 Database insertion complete: {inserted_count} jobs inserted")
    
    # Upload to S3 if needed
    # upload_to_s3(cleaned_jobs, f"remotive_jobs_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json")
    
    return cleaned_jobs

if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Scrape and analyze remote jobs from Remotive')
    parser.add_argument('--api-key', type=str, help='OpenAI API key')
    parser.add_argument('--max-jobs', type=int, default=3, help='Maximum number of jobs to process per source')
    
    args = parser.parse_args()
    
    # If API key is provided as an argument, set it as an environment variable
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
        print(f"✅ Using API key from command line argument")
        # Reinitialize the OpenAI client with the new API key
        client = OpenAI(api_key=args.api_key)
    
    # Process up to the specified number of jobs per source
    main()