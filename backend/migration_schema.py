# Create a fixed migration script
import sqlite3
import os
import sys
from datetime import datetime

def create_jobs_table():
    """Create the jobs table with all necessary columns"""
    
    # Connect to the database - use absolute path for reliability
    db_path = 'remote_jobs.db'  # Create in current directory
    print(f"Creating database at: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Creating jobs table with all columns...")
    
    # Drop the table if it exists (to start fresh)
    cursor.execute("DROP TABLE IF EXISTS jobs")
    
    # Create the jobs table with all columns at once
    create_table_sql = """
    CREATE TABLE jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        source_url TEXT,
        url TEXT,
        description TEXT,
        requirements TEXT,
        benefits TEXT,
        salary_min INTEGER,
        salary_max INTEGER,
        salary_currency TEXT DEFAULT 'USD',
        salary_period TEXT DEFAULT 'yearly',
        salary_text TEXT,
        skills_required TEXT,
        ai_generated_summary TEXT,
        job_type TEXT,
        experience_level TEXT,
        remote_type TEXT DEFAULT 'remote',
        source_platform TEXT,
        application_url TEXT,
        company_logo TEXT,
        company_description TEXT,
        company_size TEXT,
        company_industry TEXT,
        tags TEXT,
        core_skills TEXT,
        implied_skills TEXT,
        complementary_skills TEXT,
        job_id TEXT,
        element_id TEXT,
        posted_date TEXT,
        ai_processed BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ Jobs table created successfully!")
        return True
    except sqlite3.Error as e:
        print(f"❌ Error creating table: {e}")
        return False
    finally:
        conn.close()

def verify_schema():
    """Verify the table schema"""
    
    db_path = 'remote_jobs.db'
    print(f"Verifying schema at: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 Table schema:")
    cursor.execute("PRAGMA table_info(jobs)")
    columns = cursor.fetchall()
    
    for col in columns:
        col_id, name, data_type, not_null, default_val, pk = col
        print(f"  {name}: {data_type}")
    
    # Show current record count
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    print(f"\n📈 Current jobs in database: {count}")
    
    conn.close()

if __name__ == "__main__":
    print("�� Starting database schema migration...")
    
    if create_jobs_table():
        verify_schema()
        print("\n✅ Schema migration completed successfully!")
    else:
        print("\n❌ Schema migration failed!")
        sys.exit(1)