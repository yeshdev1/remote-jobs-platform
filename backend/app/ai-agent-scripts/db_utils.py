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

def validate_remote_job_with_o1(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if a job is truly international remote or USA remote only using o1-mini
    
    Args:
        job_data: Job data dictionary containing title, company, description, etc.
    
    Returns:
        Dictionary with validation results including is_valid, remote_type, and reasoning
    """
    from openai import OpenAI
    import json
    import re
    
    # Get OpenAI API key
    api_key = get_openai_api_key()
    if not api_key:
        print("⚠️ OpenAI API key not found for validation")
        return {
            "is_valid": False,
            "remote_type": "unknown",
            "job_type": "unknown",
            "reasoning": "No API key available for validation",
            "confidence": 0.0,
            "red_flags": []
        }
    
    client = OpenAI(api_key=api_key)
    
    # Extract key information for validation
    title = job_data.get('title', '')
    company = job_data.get('company', '')
    description = job_data.get('description', '')
    location = job_data.get('location', '')
    
    validation_prompt = f"""
    You are a job validation expert. Analyze this job posting to determine if it meets BOTH criteria:
    1. It's truly remote work (international or USA remote only)
    2. It's a software development/engineering OR product/UX/UI design role

    Job Information:
    - Title: {title}
    - Company: {company}
    - Location: {location}
    - Description: {description}

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

    Red Flags to Watch For:
    REMOTE RED FLAGS:
    - "Hybrid" or "partially remote" positions
    - "Must be located in [specific city/state]"
    - "Occasional office visits required"
    - "Must work in [specific time zone]"
    - "Local candidates preferred"
    
    JOB TYPE RED FLAGS:
    - Sales, marketing, or business development focus
    - Customer support or success roles
    - Administrative or operational roles
    - Non-technical writing or content creation
    - HR, finance, or legal roles

    Return ONLY a JSON object with this exact structure:
    {{
        "is_valid": true/false,
        "remote_type": "international" or "usa_only" or "not_remote",
        "job_type": "software_dev" or "product" or "ux_ui_design" or "not_tech",
        "confidence": 0.0-1.0,
        "reasoning": "Brief explanation covering both remote and job type validation",
        "red_flags": ["list", "of", "any", "concerning", "phrases", "found"]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="o1-mini",
            messages=[
                {"role": "user", "content": validation_prompt}
            ]
        )
        
        ai_response = response.choices[0].message.content
        
        # Extract JSON from the response
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
        
        # Parse the JSON response
        validation_result = json.loads(json_str)
        
        # Ensure all required fields are present
        validation_result.setdefault("is_valid", False)
        validation_result.setdefault("remote_type", "not_remote")
        validation_result.setdefault("job_type", "not_tech")
        validation_result.setdefault("confidence", 0.0)
        validation_result.setdefault("reasoning", "Unable to determine")
        validation_result.setdefault("red_flags", [])
        
        return validation_result
        
    except Exception as e:
        print(f"❌ Error validating job with o1-mini: {e}")
        return {
            "is_valid": False,
            "remote_type": "unknown",
            "job_type": "unknown",
            "reasoning": f"Validation error: {str(e)}",
            "confidence": 0.0,
            "red_flags": []
        }

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
            
            # Validate job is truly remote using o1-mini
            print(f"  🔍 Validating job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            validation_result = validate_remote_job_with_o1(job)
            
            # Only proceed if job is validated as remote
            if not validation_result.get('is_valid', False):
                print(f"  ❌ Job rejected: {validation_result.get('reasoning', 'Not remote')}")
                print(f"     Red flags: {validation_result.get('red_flags', [])}")
                skipped_count += 1
                continue
            
            # Log validation success
            remote_type = validation_result.get('remote_type', 'unknown')
            job_type = validation_result.get('job_type', 'unknown')
            confidence = validation_result.get('confidence', 0.0)
            print(f"  ✅ Job validated as {remote_type} remote, {job_type} role (confidence: {confidence:.2f})")
            
            # Transform the job data
            transformed_job = transform_job_data(job, source_platform)
            
            # Add validation metadata to the job
            transformed_job['ai_processed'] = True
            transformed_job['ai_generated_summary'] = f"Validated as {remote_type} remote, {job_type} role. {validation_result.get('reasoning', '')}"
            transformed_job['remote_type'] = remote_type
            transformed_job['job_type'] = job_type
            
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
