"""
Test script for the O1 Remote Jobs Agent.
"""

import os
import json
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the agent
from app.ai_agents.o1_remote_jobs_agent import O1RemoteJobsAgent

async def main():
    """Run the O1 Remote Jobs Agent and print results"""
    print("Starting O1 Remote Jobs Agent...")
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("OPENAI_API_KEY environment variable not set.")
        print("Using a placeholder API key for testing. In production, set your actual API key.")
        # Set a placeholder API key for testing
        os.environ['OPENAI_API_KEY'] = 'sk-placeholder-api-key-for-testing'
    
    # Initialize agent
    agent = O1RemoteJobsAgent()
    
    # Fetch jobs (use a small number for testing)
    print("Fetching jobs...")
    jobs = await agent.fetch_jobs(max_jobs_per_source=1)
    
    # Print results
    print(f"\nGenerated {len(jobs)} jobs:")
    for i, job in enumerate(jobs[:5], 1):  # Print first 5 jobs
        print(f"\nJob {i}:")
        print(f"Title: {job.get('title')}")
        print(f"Company: {job.get('company')}")
        print(f"Source: {job.get('source_platform')}")
        print(f"Salary: ${job.get('salary_min')} - ${job.get('salary_max')}")
        print(f"Skills: {', '.join(job.get('skills_required', []))}")
    
    # Save jobs to file for inspection
    output_file = "generated_jobs.json"
    with open(output_file, "w") as f:
        json.dump(jobs, f, indent=2, default=str)
    
    print(f"\nAll jobs saved to {output_file}")
    print(f"Completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main())
