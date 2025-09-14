"""
Scheduler for the AI Job Board Search Agent.

This script runs the agent on a schedule to keep the job database updated.
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/job_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the agent
from app.ai_agents.ai_job_board_search_agent import AIJobBoardSearchAgent

async def run_agent():
    """Run the job board search agent"""
    try:
        logger.info("Starting AI Job Board Search Agent...")
        
        # Check if OpenAI API key is set
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("OPENAI_API_KEY environment variable not set!")
            return
        
        # Initialize and run the agent
        agent = AIJobBoardSearchAgent()
        result = await agent.run(max_jobs_per_source=10, purge_existing=True)
        
        # Log results
        logger.info(f"Agent run completed: {result['status']}")
        logger.info(f"Jobs Fetched: {result['jobs_fetched']}")
        logger.info(f"Jobs Stored: {result['jobs_stored']}")
        logger.info(f"Sources: {', '.join(result['sources'])}")
        
    except Exception as e:
        logger.error(f"Error running agent: {e}")

async def main():
    """Run the agent on a schedule"""
    # Set schedule interval (in seconds)
    interval = int(os.getenv('JOB_AGENT_INTERVAL', 86400))  # Default: 24 hours
    
    logger.info(f"Starting Job Agent Scheduler (interval: {interval} seconds)")
    
    while True:
        start_time = time.time()
        
        # Run the agent
        await run_agent()
        
        # Calculate sleep time (to maintain consistent interval)
        elapsed = time.time() - start_time
        sleep_time = max(1, interval - elapsed)
        
        logger.info(f"Next run in {sleep_time:.1f} seconds at {datetime.fromtimestamp(time.time() + sleep_time)}")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Job Agent Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Job Agent Scheduler error: {e}")
