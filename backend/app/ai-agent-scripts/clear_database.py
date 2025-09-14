#!/usr/bin/env python3
"""
Simple script to clear all job data from the SQLite database.
"""

import sqlite3
import os
import sys
from typing import Optional

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

def count_jobs(cursor: sqlite3.Cursor) -> dict:
    """Count jobs by platform"""
    cursor.execute("SELECT source_platform, COUNT(*) FROM jobs GROUP BY source_platform")
    platform_counts = dict(cursor.fetchall())
    
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_count = cursor.fetchone()[0]
    
    return {
        'total': total_count,
        'by_platform': platform_counts
    }

def clear_all_jobs() -> bool:
    """Clear all jobs from the database"""
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count jobs before deletion
        print("📊 Current database status:")
        counts = count_jobs(cursor)
        print(f"   Total jobs: {counts['total']}")
        for platform, count in counts['by_platform'].items():
            print(f"   {platform}: {count} jobs")
        
        if counts['total'] == 0:
            print("✅ Database is already empty!")
            conn.close()
            return True
        
        # Ask for confirmation
        print("\n⚠️  WARNING: This will delete ALL job data from the database!")
        response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        
        if response not in ['yes', 'y']:
            print("❌ Operation cancelled by user")
            conn.close()
            return False
        
        # Delete all jobs
        cursor.execute("DELETE FROM jobs")
        deleted_count = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM jobs")
        remaining_count = cursor.fetchone()[0]
        
        print(f"✅ Successfully deleted {deleted_count} jobs from database")
        print(f"✅ Remaining jobs: {remaining_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def clear_jobs_by_platform(platform: str) -> bool:
    """Clear jobs from a specific platform"""
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count jobs for this platform
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE source_platform = ?", (platform,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"✅ No {platform} jobs found in database!")
            conn.close()
            return True
        
        print(f"📊 Found {count} {platform} jobs in database")
        
        # Ask for confirmation
        print(f"\n⚠️  WARNING: This will delete ALL {platform} jobs from the database!")
        response = input(f"Are you sure you want to delete {count} {platform} jobs? (yes/no): ").lower().strip()
        
        if response not in ['yes', 'y']:
            print("❌ Operation cancelled by user")
            conn.close()
            return False
        
        # Delete jobs for this platform
        cursor.execute("DELETE FROM jobs WHERE source_platform = ?", (platform,))
        deleted_count = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        print(f"✅ Successfully deleted {deleted_count} {platform} jobs from database")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing {platform} jobs: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def show_database_status():
    """Show current database status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        counts = count_jobs(cursor)
        
        print("📊 Current Database Status:")
        print(f"   Total jobs: {counts['total']}")
        
        if counts['by_platform']:
            print("   Jobs by platform:")
            for platform, count in counts['by_platform'].items():
                print(f"     {platform}: {count} jobs")
        else:
            print("   Database is empty")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database status: {e}")

def main():
    """Main function"""
    print("🗑️  Database Clear Utility")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            show_database_status()
            return
        
        elif command == "clear":
            if len(sys.argv) > 2:
                platform = sys.argv[2]
                clear_jobs_by_platform(platform)
            else:
                clear_all_jobs()
            return
        
        elif command == "help":
            print("Usage:")
            print("  python3.11 clear_database.py status           - Show database status")
            print("  python3.11 clear_database.py clear            - Clear all jobs")
            print("  python3.11 clear_database.py clear RemoteOK   - Clear RemoteOK jobs only")
            print("  python3.11 clear_database.py clear Remotive   - Clear Remotive jobs only")
            print("  python3.11 clear_database.py clear WeWorkRemotely - Clear WeWorkRemotely jobs only")
            return
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python3.11 clear_database.py help' for usage information")
            return
    
    # Interactive mode
    while True:
        print("\nOptions:")
        print("1. Show database status")
        print("2. Clear all jobs")
        print("3. Clear jobs by platform")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            show_database_status()
        
        elif choice == "2":
            clear_all_jobs()
        
        elif choice == "3":
            print("\nAvailable platforms:")
            print("- RemoteOK")
            print("- Remotive") 
            print("- WeWorkRemotely")
            platform = input("Enter platform name: ").strip()
            if platform:
                clear_jobs_by_platform(platform)
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main()
