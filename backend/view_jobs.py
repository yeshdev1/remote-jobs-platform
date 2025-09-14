"""
Script to view jobs stored in the SQLite database
"""

import sqlite3
import argparse
from tabulate import tabulate

def connect_to_db(db_path='remote_jobs.db'):
    """Connect to SQLite database"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def get_all_jobs(conn, limit=None, source=None):
    """Get all jobs from database"""
    cursor = conn.cursor()
    
    query = "SELECT * FROM jobs"
    params = []
    
    if source:
        query += " WHERE source_platform = ?"
        params.append(source)
    
    query += " ORDER BY id DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor.execute(query, params)
    return cursor.fetchall()

def display_job_summary(jobs):
    """Display a summary of jobs"""
    job_data = []
    for job in jobs:
        job_data.append([
            job['id'],
            job['title'],
            job['company'],
            job['source_platform'],
            job['salary_min'],
            job['salary_max'],
            job['ai_generated_summary'][:50] + '...' if job['ai_generated_summary'] and len(job['ai_generated_summary']) > 50 else job['ai_generated_summary']
        ])
    
    headers = ['ID', 'Title', 'Company', 'Source', 'Min Salary', 'Max Salary', 'Summary']
    print(tabulate(job_data, headers=headers, tablefmt='grid'))

def display_job_detail(job):
    """Display detailed information about a job"""
    print("\n" + "="*50)
    print(f"Job ID: {job['id']}")
    print(f"Title: {job['title']}")
    print(f"Company: {job['company']}")
    print("="*50)
    print(f"Source: {job['source_platform']}")
    print(f"URL: {job['source_url']}")
    print(f"Posted: {job['posted_date']}")
    print("="*50)
    print(f"Salary: ${job['salary_min']} - ${job['salary_max']} {job['salary_currency']}")
    print(f"Location: {job['location']}")
    print("="*50)
    print("Description:")
    print(job['description'])
    print("="*50)
    print("AI Summary:")
    print(job['ai_generated_summary'])
    print("="*50)
    
    if job['skills_required']:
        print("Skills:")
        skills = job['skills_required'].split(',')
        for skill in skills:
            print(f"- {skill}")
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description='View jobs in the database')
    parser.add_argument('--db', default='remote_jobs.db', help='Path to SQLite database')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of jobs to display')
    parser.add_argument('--source', help='Filter by source platform')
    parser.add_argument('--id', type=int, help='Display details for a specific job ID')
    
    args = parser.parse_args()
    
    conn = connect_to_db(args.db)
    
    if args.id:
        # Display details for a specific job
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (args.id,))
        job = cursor.fetchone()
        
        if job:
            display_job_detail(job)
        else:
            print(f"No job found with ID {args.id}")
    else:
        # Display summary of jobs
        jobs = get_all_jobs(conn, args.limit, args.source)
        if jobs:
            print(f"Found {len(jobs)} jobs")
            display_job_summary(jobs)
        else:
            print("No jobs found")
    
    conn.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("If you're missing the tabulate package, install it with: pip install tabulate")
