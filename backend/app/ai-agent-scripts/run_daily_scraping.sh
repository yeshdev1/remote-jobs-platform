#!/bin/bash

# Daily Job Scraping Script
# Runs all v2 scrapers with timestamp optimization

SCRIPT_DIR="/home/ubuntu/remote-jobs-platform/backend/app/ai-agent-scripts"
PROJECT_ROOT="/home/ubuntu/remote-jobs-platform"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$SCRIPT_DIR/logs"
DATE=$(date +%Y%m%d_%H%M%S)

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "🚀 Starting daily job scraping at $(date)"

# Check if virtual environment exists
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please create a virtual environment first: python3 -m venv $VENV_PATH"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Verify Python environment
echo "🐍 Using Python: $(which python)"
echo "🐍 Python version: $(python --version)"

# Function to run scraper with logging
run_scraper() {
    local scraper_name=$1
    local script_name=$2
    
    echo "📊 Starting $scraper_name scraper..."
    cd "$SCRIPT_DIR"
    
    # Run the scraper and capture output (using python from venv)
    python "$script_name" > "$LOG_DIR/${scraper_name}_${DATE}.log" 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ $scraper_name scraper completed successfully"
    else
        echo "❌ $scraper_name scraper failed with exit code $exit_code"
    fi
    
    return $exit_code
}

# Run all scrapers sequentially
run_scraper "remoteok" "remote_remoteok_scraper_v2.py"
sleep 30  # Brief pause between scrapers

run_scraper "remotive" "remote_remotive_scraper_v2.py"
sleep 30

run_scraper "weworkremotely" "remote_weworkremotely_scraper_v2.py"

echo "🎉 Daily scraping completed at $(date)"

# Deactivate virtual environment
deactivate

# Optional: Clean up old log files (keep last 7 days)
find "$LOG_DIR" -name "*.log" -mtime +7 -delete

# Optional: Send summary email (uncomment if you want email notifications)
# echo "Daily job scraping completed. Check logs in $LOG_DIR" | mail -s "Job Scraping Summary" your-email@example.com