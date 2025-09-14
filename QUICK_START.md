# 🚀 Quick Start Guide - Remote Jobs Platform

## Prerequisites
- Docker and Docker Compose installed
- Claude API key from Anthropic (https://console.anthropic.com/)

## 🏃‍♂️ Get Started in 5 Minutes

### 1. Clone and Setup
```bash
# Navigate to project directory
cd remote-jobs-platform

# Run the setup script
./setup.sh
```

### 2. Configure API Keys
Edit the `.env` file and add your API keys:
```bash
# Required: Claude API key for AI processing
ANTHROPIC_API_KEY=your_claude_api_key_here

# Optional: OpenAI API key as backup
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start the Platform
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Platform
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

## 🔧 Manual Setup (Alternative)

### 1. Install Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Start Services
```bash
# Backend (Terminal 1)
cd backend
uvicorn main:app --reload

# Frontend (Terminal 2)
cd frontend
npm run dev

# Scheduler (Terminal 3)
cd backend
python -m app.scheduler.job_scheduler
```

## 📊 What Happens Next

### First Run
1. **Database Setup**: Tables are created automatically
2. **Initial Scraping**: First job data is collected
3. **AI Processing**: Claude analyzes and validates jobs
4. **Data Population**: Jobs appear in the frontend

### Daily Operations
- **2:00 AM**: Automated job updates run
- **AI Processing**: New jobs are analyzed
- **Data Refresh**: Fresh opportunities appear
- **Health Checks**: System monitoring runs hourly

## 🐛 Troubleshooting

### Common Issues
```bash
# Check service status
docker-compose ps

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart

# Reset everything
docker-compose down -v
docker-compose up --build
```

### Database Issues
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U remote_user -d remote_jobs

# Check tables
\dt

# View jobs
SELECT COUNT(*) FROM jobs;
```

## 📈 Monitoring

### Check System Health
- **API Health**: http://localhost:8000/health
- **Database**: Check logs for connection status
- **AI Processing**: Monitor Claude API usage
- **Scraping**: View job collection statistics

### Key Metrics
- **Jobs Collected**: Total jobs in database
- **AI Processed**: Jobs validated by Claude
- **USD Jobs**: Jobs with confirmed US salaries
- **Remote Jobs**: Confirmed remote positions

## 🔒 Security Notes

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique passwords for databases
- Rotate API keys regularly
- Monitor API usage and costs

### Production Deployment
- Use HTTPS for all communications
- Implement proper authentication
- Set up monitoring and alerting
- Regular security updates

## 🎯 Next Steps

### Customization
1. **Add Job Sources**: Implement new scrapers
2. **Modify Filters**: Adjust salary ranges and criteria
3. **Custom AI Prompts**: Optimize Claude analysis
4. **UI Changes**: Modify frontend design

### Scaling
1. **Database Optimization**: Add indexes and caching
2. **Load Balancing**: Multiple backend instances
3. **CDN**: Static asset delivery
4. **Monitoring**: Advanced metrics and alerting

## 📚 Additional Resources

- **Project Overview**: PROJECT_OVERVIEW.md
- **API Documentation**: http://localhost:8000/docs
- **Docker Documentation**: https://docs.docker.com/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Next.js Documentation**: https://nextjs.org/docs

---

🎉 **You're all set!** The platform will start collecting and processing remote jobs with US salaries automatically.
