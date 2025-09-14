"""
Test script for the AI Job Board Search Agent.

This script initializes and runs the agent to fetch remote jobs from various sources.
"""

import asyncio
import argparse
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Import the agent
from app.ai_agents.ai_job_board_search_agent import AIJobBoardSearchAgent

async def main():
    """Run the job board search agent and print results"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the AI Job Board Search Agent')
    parser.add_argument('--jobs', type=int, default=10, help='Number of jobs to fetch per source')
    parser.add_argument('--purge', action='store_true', help='Purge existing jobs from database')
    parser.add_argument('--no-purge', dest='purge', action='store_false', help='Keep existing jobs in database')
    parser.set_defaults(purge=True)
    
    args = parser.parse_args()
    
    print("Starting AI Job Board Search Agent...")
    print(f"Settings: {args.jobs} jobs per source, purge={args.purge}")
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        return
    
    # Initialize and run the agent
    try:
        agent = AIJobBoardSearchAgent()
        result = await agent.run(max_jobs_per_source=args.jobs, purge_existing=args.purge)
        
        # Print results
        print("\n" + "="*50)
        print("AI Job Board Search Agent Results:")
        print("="*50)
        print(f"Status: {result['status']}")
        print(f"Jobs Fetched: {result['jobs_fetched']}")
        print(f"Jobs Stored: {result['jobs_stored']}")
        print(f"Sources: {', '.join(result['sources'])}")
        print("="*50)
        
        # Print timestamp
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error running agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
