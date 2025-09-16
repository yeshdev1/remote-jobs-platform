#!/usr/bin/env python3
"""
Script to clear job data that is older than a month from the SQLite database.
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

def get_db_connection():
    """Get a connection to the SQLite database"""
    # Get the backend directory path (2 levels up from this file)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
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

def get_old_jobs_count(cursor: sqlite3.Cursor, days_old: int = 30) -> Dict[str, Any]:
    """Count jobs older than specified days"""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    cutoff_timestamp = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
    
    # Count total old jobs
    cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE created_at < ?
    """, (cutoff_timestamp,))
    total_old_count = cursor.fetchone()[0]
    
    # Count old jobs by platform
    cursor.execute("""
        SELECT source_platform, COUNT(*) FROM jobs 
        WHERE created_at < ?
        GROUP BY source_platform
    """, (cutoff_timestamp,))
    platform_counts = dict(cursor.fetchall())
    
    # Count total jobs in database
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_count = cursor.fetchone()[0]
    
    return {
        'total_old': total_old_count,
        'total_all': total_count,
        'by_platform': platform_counts,
        'cutoff_date': cutoff_date,
        'cutoff_timestamp': cutoff_timestamp
    }

def clear_old_jobs(days_old: int = 30, dry_run: bool = False) -> bool:
    """Clear jobs older than specified days"""
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts before deletion
        print(f"📊 Analyzing jobs older than {days_old} days...")
        counts = get_old_jobs_count(cursor, days_old)
        
        print(f"   Cutoff date: {counts['cutoff_date'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Total jobs in database: {counts['total_all']}")
        print(f"   Jobs older than {days_old} days: {counts['total_old']}")
        
        if counts['by_platform']:
            print("   Old jobs by platform:")
            for platform, count in counts['by_platform'].items():
                print(f"     {platform}: {count} jobs")
        
        if counts['total_old'] == 0:
            print("✅ No old jobs found to delete!")
            conn.close()
            return True
        
        if dry_run:
            print(f"\n🔍 DRY RUN: Would delete {counts['total_old']} jobs older than {days_old} days")
            print("   (No actual deletion performed)")
            conn.close()
            return True
        
        # Ask for confirmation
        print(f"\n⚠️  WARNING: This will delete {counts['total_old']} jobs older than {days_old} days!")
        print(f"   Cutoff date: {counts['cutoff_date'].strftime('%Y-%m-%d %H:%M:%S')}")
        response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        
        if response not in ['yes', 'y']:
            print("❌ Operation cancelled by user")
            conn.close()
            return False
        
        # Delete old jobs
        cursor.execute("""
            DELETE FROM jobs 
            WHERE created_at < ?
        """, (counts['cutoff_timestamp'],))
        deleted_count = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM jobs")
        remaining_count = cursor.fetchone()[0]
        
        print(f"✅ Successfully deleted {deleted_count} old jobs from database")
        print(f"✅ Remaining jobs: {remaining_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing old jobs: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def show_old_jobs_analysis(days_old: int = 30):
    """Show analysis of old jobs without deleting them"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        counts = get_old_jobs_count(cursor, days_old)
        
        print(f"📊 Analysis of jobs older than {days_old} days:")
        print(f"   Cutoff date: {counts['cutoff_date'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Total jobs in database: {counts['total_all']}")
        print(f"   Jobs older than {days_old} days: {counts['total_old']}")
        
        if counts['by_platform']:
            print("   Old jobs by platform:")
            for platform, count in counts['by_platform'].items():
                print(f"     {platform}: {count} jobs")
        else:
            print("   No old jobs found")
        
        # Show some examples of old jobs
        if counts['total_old'] > 0:
            print(f"\n📋 Sample of old jobs (showing up to 5):")
            cursor.execute("""
                SELECT title, company, source_platform, created_at 
                FROM jobs 
                WHERE created_at < ?
                ORDER BY created_at ASC
                LIMIT 5
            """, (counts['cutoff_timestamp'],))
            
            old_jobs = cursor.fetchall()
            for i, (title, company, platform, created_at) in enumerate(old_jobs, 1):
                print(f"   {i}. {title} at {company} ({platform}) - {created_at}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing old jobs: {e}")

def main():
    """Main function"""
    print("🗑️  Old Data Cleanup Utility")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "analyze":
            days = 30
            if len(sys.argv) > 2:
                try:
                    days = int(sys.argv[2])
                except ValueError:
                    print("❌ Invalid number of days. Using default 30 days.")
            show_old_jobs_analysis(days)
            return
        
        elif command == "clear":
            days = 30
            dry_run = False
            
            # Parse arguments
            for i, arg in enumerate(sys.argv[2:], 2):
                if arg.isdigit():
                    days = int(arg)
                elif arg == "--dry-run":
                    dry_run = True
            
            clear_old_jobs(days, dry_run)
            return
        
        elif command == "help":
            print("Usage:")
            print("  python3.11 clear_old_data.py analyze [days]     - Analyze old jobs (default: 30 days)")
            print("  python3.11 clear_old_data.py clear [days] [--dry-run] - Clear old jobs (default: 30 days)")
            print("  python3.11 clear_old_data.py help               - Show this help")
            print("")
            print("Examples:")
            print("  python3.11 clear_old_data.py analyze 30         - Analyze jobs older than 30 days")
            print("  python3.11 clear_old_data.py clear 30 --dry-run - Preview deletion of 30+ day old jobs")
            print("  python3.11 clear_old_data.py clear 7            - Delete jobs older than 7 days")
            return
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python3.11 clear_old_data.py help' for usage information")
            return
    
    # Interactive mode
    while True:
        print("\nOptions:")
        print("1. Analyze old jobs")
        print("2. Clear old jobs")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            days_input = input("Enter number of days (default 30): ").strip()
            try:
                days = int(days_input) if days_input else 30
                show_old_jobs_analysis(days)
            except ValueError:
                print("❌ Invalid number. Using default 30 days.")
                show_old_jobs_analysis(30)
        
        elif choice == "2":
            days_input = input("Enter number of days (default 30): ").strip()
            try:
                days = int(days_input) if days_input else 30
            except ValueError:
                print("❌ Invalid number. Using default 30 days.")
                days = 30
            
            dry_run_input = input("Dry run first? (y/n, default n): ").strip().lower()
            dry_run = dry_run_input in ['y', 'yes']
            
            if dry_run:
                print(f"\n🔍 Running dry run for jobs older than {days} days...")
                clear_old_jobs(days, dry_run=True)
            else:
                clear_old_jobs(days, dry_run=False)
        
        elif choice == "3":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-3.")

if __name__ == "__main__":
    main()
