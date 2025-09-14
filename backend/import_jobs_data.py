# backend/import_jobs_data.py
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List

def transform_job_data(job: Dict[str, Any], source_platform: str) -> Dict[str, Any]:
    """Transform job data from JSON format to database format"""
    
    # Handle salary data
    salary_min = None
    salary_max = None
    salary_currency = 'USD'
    
    if isinstance(job.get('salary'), dict):
        salary_min = job['salary'].get('min')
        salary_max = job['salary'].get('max')
    elif isinstance(job.get('salary'), str):
        # Extract salary range from string like "$103,450 - $197,730"
        salary_str = job['salary']
        if ' - ' in salary_str:
            try:
                min_str, max_str = salary_str.split(' - ')
                salary_min = int(min_str.replace('$', '').replace(',', ''))
                salary_max = int(max_str.replace('$', '').replace(',', ''))
            except:
                pass
        elif salary_str.replace('$', '').replace(',', '').isdigit():
            try:
                salary_min = int(salary_str.replace('$', '').replace(',', ''))
            except:
                pass
    
    # Handle job_type (can be array or string)
    job_type = job.get('job_type', '')
    if isinstance(job_type, list):
        job_type = ', '.join(job_type)
    
    # Handle tags (convert array to comma-separated string)
    tags = job.get('tags', [])
    if isinstance(tags, list):
        tags = ', '.join(tags)
    
    # Handle skills_analysis
    skills_analysis = job.get('skills_analysis', {})
    core_skills = ', '.join(skills_analysis.get('core_skills', []))
    implied_skills = ', '.join(skills_analysis.get('implied_skills', []))
    complementary_skills = ', '.join(skills_analysis.get('complementary_skills', []))
    
    # Create transformed job data
    transformed_job = {
        'title': job.get('title', ''),
        'company': job.get('company', ''),
        'job_type': job_type,
        'location': job.get('location', ''),
        'url': job.get('url', ''),
        'description': job.get('description', ''),
        'salary_min': salary_min,
        'salary_max': salary_max,
        'salary_currency': salary_currency,
        'tags': tags,
        'core_skills': core_skills,
        'implied_skills': implied_skills,
        'complementary_skills': complementary_skills,
        'job_id': job.get('job_id', ''),
        'element_id': job.get('element_id', ''),
        'source_platform': source_platform,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    return transformed_job

def insert_job(cursor: sqlite3.Cursor, job: Dict[str, Any]) -> int:
    """Insert a single job into the database"""
    
    insert_sql = """
    INSERT INTO jobs (
        title, company, job_type, location, url, description,
        salary_min, salary_max, salary_currency, tags,
        core_skills, implied_skills, complementary_skills,
        job_id, element_id, source_platform, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(insert_sql, (
        job['title'],
        job['company'],
        job['job_type'],
        job['location'],
        job['url'],
        job['description'],
        job['salary_min'],
        job['salary_max'],
        job['salary_currency'],
        job['tags'],
        job['core_skills'],
        job['implied_skills'],
        job['complementary_skills'],
        job['job_id'],
        job['element_id'],
        job['source_platform'],
        job['created_at'],
        job['updated_at']
    ))
    
    return cursor.lastrowid

def import_jobs_from_json(json_file_path: str, source_platform: str) -> int:
    """Import jobs from a JSON file"""
    
    if not os.path.exists(json_file_path):
        print(f"❌ File not found: {json_file_path}")
        return 0
    
    print(f"📁 Processing {source_platform} jobs from {json_file_path}")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        jobs_data = json.load(f)
    
    if not isinstance(jobs_data, list):
        print(f"❌ Invalid JSON format in {json_file_path}")
        return 0
    
    # Connect to database
    db_path = 'backend/remote_jobs.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    imported_count = 0
    
    for job in jobs_data:
        try:
            # Transform the job data
            transformed_job = transform_job_data(job, source_platform)
            
            # Insert the job
            job_id = insert_job(cursor, transformed_job)
            imported_count += 1
            
            print(f"  ✅ Imported: {transformed_job['title']} at {transformed_job['company']}")
            
        except Exception as e:
            print(f"  ❌ Error importing job: {e}")
            continue
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print(f"📊 Successfully imported {imported_count} jobs from {source_platform}")
    return imported_count

def main():
    """Main function to import all job data"""
    
    print("🚀 Starting job data import process...")
    
    # Define the JSON files and their source platforms
    json_files = [
        {
            'path': 'scraper/ai-agent-scripts/job_results/remoteok_jobs.json',
            'platform': 'RemoteOK'
        },
        {
            'path': 'scraper/ai-agent-scripts/job_results/remotive_jobs.json',
            'platform': 'Remotive'
        },
        {
            'path': 'scraper/ai-agent-scripts/job_results/weworkremotely_jobs.json',
            'platform': 'WeWorkRemotely'
        }
    ]
    
    total_imported = 0
    
    for json_file in json_files:
        try:
            count = import_jobs_from_json(json_file['path'], json_file['platform'])
            total_imported += count
        except Exception as e:
            print(f"❌ Error processing {json_file['path']}: {e}")
            continue
    
    print(f"\n🎉 Import completed! Total jobs imported: {total_imported}")
    
    # Show final database stats
    db_path = 'backend/remote_jobs.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT source_platform, COUNT(*) FROM jobs GROUP BY source_platform")
    platform_counts = cursor.fetchall()
    
    print(f"\n�� Database Statistics:")
    print(f"Total jobs in database: {total_jobs}")
    for platform, count in platform_counts:
        print(f"  {platform}: {count} jobs")
    
    conn.close()

if __name__ == "__main__":
    main()