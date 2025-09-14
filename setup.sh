#!/bin/bash

echo "�� Setting up Remote Jobs Platform - US Salary Only"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API keys before starting the platform"
    echo "   - ANTHROPIC_API_KEY: Your Claude API key from Anthropic"
    echo "   - OPENAI_API_KEY: Your OpenAI API key (optional)"
    echo ""
    echo "Press Enter when you've updated the .env file..."
    read
fi

# Create logs directory
mkdir -p logs

echo "🔧 Building and starting services..."
docker-compose up --build -d

echo ""
echo "🎉 Setup complete! The platform is starting up..."
echo ""
echo "�� Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo "🗄️  Database: localhost:5432"
echo ""
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart"
echo ""
echo "⏰ The scheduler will run daily at 2 AM to update job data"
echo "🔍 Check the logs to monitor scraping and AI processing"
