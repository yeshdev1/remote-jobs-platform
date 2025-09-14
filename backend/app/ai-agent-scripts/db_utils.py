import sqlite3
import os
import sys
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the parent directories to the path so we can import from there
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)
from import_jobs_data import transform_job_data, insert_job

def load_env_file(env_path: str) -> Dict[str, str]:
    """Load environment variables from a .env file"""
    env_vars = {}
    
    if not os.path.exists(env_path):
        print(f"⚠️ .env file not found at {env_path}")
        return env_vars
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Match KEY=VALUE pattern, handling quotes
                match = re.match(r'^([A-Za-z0-9_]+)=[\'\"]?(.*?)[\'\"]?$', line)
                if match:
                    key, value = match.groups()
                    env_vars[key] = value
    except Exception as e:
        print(f"⚠️ Error loading .env file: {e}")
    
    return env_vars

def get_openai_api_key() -> Optional[str]:
    """Get the OpenAI API key from the .env file in the same directory"""
    # Look for .env file in the same directory as this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, '.env')
    
    print(f"🔑 Looking for .env file at {env_path}")
    
    # Load environment variables from .env file
    env_vars = load_env_file(env_path)
    
    # Get the OpenAI API key
    api_key = env_vars.get('OPENAI_API_KEY')
    
    if api_key:
        print("✅ Found OpenAI API key in .env file")
        # Mask the API key for security
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        print(f"🔑 Using API key: {masked_key}")
    else:
        print("⚠️ OpenAI API key not found in .env file")
    
    return api_key

def get_db_connection():
    """Get a connection to the SQLite database"""
    # Get the backend directory path (3 levels up from this file)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Try to find the database in the backend directory
    db_path = os.path.join(backend_dir, 'remote_jobs.db')
    
    if os.path.exists(db_path):
        print(f"📂 Connecting to database at {db_path}")
        return sqlite3.connect(db_path)
    
    # Try some other possible paths as fallback
    possible_db_paths = [
        'remote_jobs.db',                   # Current directory
        '../remote_jobs.db',                # One level up
        '../../remote_jobs.db',             # Two levels up
        '../../../remote_jobs.db',          # Three levels up
    ]
    
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = os.path.abspath(path)
            print(f"📂 Connecting to database at {db_path}")
            return sqlite3.connect(db_path)
    
    # If we get here, we couldn't find the database
    raise FileNotFoundError("Could not find the remote_jobs.db database file")

def job_exists_by_url(cursor: sqlite3.Cursor, url: str) -> bool:
    """Check if a job already exists in the database by URL
    
    Args:
        cursor: Database cursor
        url: Job URL to check
    
    Returns:
        True if job exists, False otherwise
    """
    if not url:
        return False
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE url = ?", (url,))
    count = cursor.fetchone()[0]
    return count > 0

def insert_jobs_into_db(jobs: List[Dict[str, Any]], source_platform: str) -> int:
    """Insert jobs directly into the database
    
    Args:
        jobs: List of job dictionaries to insert
        source_platform: Source platform name (e.g., 'RemoteOK', 'Remotive', 'WeWorkRemotely')
    
    Returns:
        Number of jobs successfully inserted
    """
    if not jobs:
        print("❌ No jobs to insert")
        return 0
    
    print(f"🚀 Inserting {len(jobs)} jobs from {source_platform} into database...")
    
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
            
            # Transform the job data
            transformed_job = transform_job_data(job, source_platform)
            
            # Check if job already exists by URL
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
