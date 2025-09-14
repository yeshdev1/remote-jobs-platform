import os
import requests
import json
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from openai import OpenAI
# import boto3
from db_utils import insert_jobs_into_db, get_openai_api_key

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

# Sources to scrape from WeWorkRemotely
JOB_SOURCES = [
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]

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

def extract_job_listings(xml_content):
    """Extract all job listings from the XML content"""
    if not xml_content:
        return []
    
    # Use XML parser instead of HTML parser
    soup = BeautifulSoup(xml_content, 'html.parser')
    job_listings = []
    
    # Find all item elements (job listings) within the channel
    items = soup.find_all('item')
    
    for i, item in enumerate(items):
        # Extract all content from the item element
        item_html = str(item)
        
        # Create job data object following the same format as other scrapers
        job_data = {
            'html_content': item_html,  # Complete XML content of the item
            'element_id': f"job_{i}",  # Just an ID for reference
            'job_id': f"weworkremotely_{i}"  # Store a job ID for reference
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
    Analyze this RSS feed job listing from WeWorkRemotely and extract all relevant information.
    
    Parse the RSS item content and extract:
    - title: Job title (from title element)
    - company: Company name (from title or description)
    - job_type: Employment type (Full-Time, Contract, Part-Time, etc.)
    - location: Location information (from title or description)
    - url: Job URL (from link element)
    - description: Job description/summary (from description element)
    - salary: Salary information (from title or description)
    - tags: Array of technologies/skills mentioned (from title or description)
    - skills_analysis: Object with core_skills, implied_skills, and complementary_skills arrays
    
    RSS item content:
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
                parsed_job['job_id'] = job['job_id']
                
                analyzed_jobs.append(parsed_job)
            except json.JSONDecodeError as e:
                print(f"  Error parsing JSON for job {job['element_id']}: {e}")
                analyzed_jobs.append({
                    "element_id": job['element_id'],
                    "job_id": job['job_id'],
                    "raw_analysis": ai_response,
                    "json_error": str(e)
                })
            
            # Add delay between requests to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error analyzing job {job['element_id']}: {e}")
            analyzed_jobs.append({
                "element_id": job['element_id'],
                "job_id": job['job_id'],
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

def main(max_jobs_per_source=10):
    """Main function to scrape jobs and analyze them with AI"""
    all_jobs = []
    
    for source in JOB_SOURCES:
        print(f"\nScraping jobs from {source}...")
        xml_content = fetch_job_page(source)
        
        if xml_content:
            # Extract job listings from XML content
            job_listings = extract_job_listings(xml_content)
            
            # Limit the number of jobs to process per source
            jobs_to_analyze = job_listings[:max_jobs_per_source]
            
            if jobs_to_analyze:
                print(f"Found {len(job_listings)} job listings, analyzing {len(jobs_to_analyze)} with AI...")
                
                # Analyze with AI
                analyzed_jobs = analyze_with_o1_mini(jobs_to_analyze)
                
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
    out_path = "job_results/weworkremotely_jobs.json"
    
    with open(out_path, "w") as f:
        json.dump(cleaned_jobs, f, indent=2)
    
    print(f"✅ Saved {len(cleaned_jobs)} cleaned jobs to {out_path}")
    
    # Insert jobs directly into the database
    inserted_count = insert_jobs_into_db(cleaned_jobs, "WeWorkRemotely")
    print(f"📊 Database insertion complete: {inserted_count} jobs inserted")
    
    # Upload to S3 if needed
    # upload_to_s3(cleaned_jobs, f"weworkremotely_jobs_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json")
    
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
        # Reinitialize the OpenAI client with the new API key
        client = OpenAI(api_key=args.api_key)
    
    # Process up to the specified number of jobs per source
    main()