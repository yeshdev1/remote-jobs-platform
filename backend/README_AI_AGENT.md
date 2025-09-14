# AI Job Board Search Agent

This project implements an AI-powered agent that fetches remote job listings from various job boards, processes them with OpenAI, and stores them in a database.

## Features

- Scrapes job listings from multiple remote job boards:
  - Remote.co
  - WeWorkRemotely
  - WorkingNomads
- Uses OpenAI's GPT-4o Mini model to:
  - Generate concise job summaries
  - Extract key skills from job descriptions
  - Determine experience levels
  - Estimate salary ranges
- Stores processed job data in SQLite database
- Provides tools for viewing and querying the job data

## Setup

1. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install python-dotenv openai aiohttp beautifulsoup4 loguru tabulate
   ```

3. Create a `.env` file with your OpenAI API key:
   ```
   # Database Configuration
   DATABASE_URL=sqlite+aiosqlite:///./remote_jobs.db

   # AI API Keys
   OPENAI_API_KEY=your_openai_api_key_here

   # Application Configuration
   DEBUG=True
   LOG_LEVEL=INFO
   ```

## Usage

### Running the Job Agent

Run the simple job agent to fetch and process jobs:

```bash
python simple_job_agent.py
```

This will:
1. Generate dummy job data (or scrape real job boards if web scraping is enabled)
2. Process the jobs with OpenAI (if a valid API key is provided)
3. Store the jobs in the SQLite database
4. Display a summary of the results

### Viewing Jobs

View jobs stored in the database:

```bash
# View all jobs (limited to 10 by default)
python view_jobs.py

# View a specific job by ID
python view_jobs.py --id 1

# Filter jobs by source
python view_jobs.py --source remote.co

# Limit the number of jobs displayed
python view_jobs.py --limit 5
```

## Project Structure

- `simple_job_agent.py`: Main agent implementation
- `view_jobs.py`: Script for viewing jobs in the database
- `remote_jobs.db`: SQLite database storing job data

## Implementation Details

### Job Scraping

The agent includes scrapers for multiple job boards:
- SimpleRemoteCoScraper: Scrapes Remote.co
- SimpleWeWorkRemotelyScraper: Scrapes WeWorkRemotely
- SimpleWorkingNomadsScraper: Scrapes WorkingNomads

Each scraper implements methods for making HTTP requests, parsing HTML, and extracting job data.

### AI Processing

Jobs are processed with OpenAI's GPT-4o Mini model to extract additional information:
- Concise job summaries
- Key skills required
- Estimated salary ranges

### Database Schema

Jobs are stored in a SQLite database with the following schema:

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary_min REAL,
    salary_max REAL,
    salary_currency TEXT DEFAULT 'USD',
    description TEXT,
    source_url TEXT UNIQUE,
    source_platform TEXT NOT NULL,
    posted_date TEXT,
    skills_required TEXT,
    ai_generated_summary TEXT,
    ai_processed INTEGER DEFAULT 0,
    created_at TEXT
)
```

## Future Improvements

- Add more job sources
- Improve web scraping reliability
- Enhance AI processing to extract more information
- Add a web interface for browsing jobs
- Implement job alerts and notifications
