# 🏗️ Data Architecture Setup Guide

This guide will help you set up the complete data architecture for the Remote Jobs Platform, including MongoDB for real-time operations, Data Lake for daily snapshots, and automated ETL pipelines.

## 📋 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   NoSQL (Mongo) │    │  Data Lake (S3) │
│                 │◄──►│   Real-time     │    │  Daily Snapshots│
│  FastAPI + UI   │    │   Operations    │    │  Analytics      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Data Warehouse  │    │   ETL Pipeline  │
                       │ (PostgreSQL)    │◄───│  (Scheduled)    │
                       │ Analytics       │    │  Data Sync      │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Start Data Stack Services

```bash
# Start MongoDB, MinIO, Redis, and PostgreSQL
docker-compose -f docker-compose.data-stack.yml up -d

# Check services are running
docker-compose -f docker-compose.data-stack.yml ps
```

### 2. Configure Environment Variables

Copy the environment template and configure your settings:

```bash
cd backend
cp env.example .env
```

Edit `.env` with your configuration:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://admin:password123@localhost:27017
MONGODB_DATABASE=remote_jobs_platform

# Data Lake Configuration (MinIO)
DATA_LAKE_TYPE=minio
DATA_LAKE_BUCKET=remote-jobs-data
S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin123

# AI API Keys (configure your keys)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Initialize Services

```bash
# Start the application (this will initialize all services)
python main.py
```

## 🔧 Service Details

### MongoDB (Real-time Operations)
- **Port**: 27017
- **Admin UI**: http://localhost:8081 (MongoDB Express)
- **Credentials**: admin/password123
- **Purpose**: Fast job search, real-time operations, caching

### MinIO (Data Lake)
- **Port**: 9000 (API), 9001 (Console)
- **Console**: http://localhost:9001
- **Credentials**: minioadmin/minioadmin123
- **Purpose**: Daily snapshots, long-term storage, analytics

### Redis (Caching)
- **Port**: 6379
- **Purpose**: Session storage, API caching, rate limiting

### PostgreSQL (Data Warehouse)
- **Port**: 5432
- **Database**: remote_jobs_warehouse
- **Credentials**: postgres/postgres123
- **Purpose**: Structured analytics, reporting

## 📊 API Endpoints

### Real-time Operations (MongoDB)
```bash
# Search jobs with full-text search
GET /api/v1/jobs-mongodb/search?q=python&experience_level=senior

# Get job by ID
GET /api/v1/jobs-mongodb/{job_id}

# Get similar jobs
GET /api/v1/jobs-mongodb/{job_id}/similar

# Get job statistics
GET /api/v1/jobs-mongodb/stats/overview

# Get search suggestions
GET /api/v1/jobs-mongodb/search/suggestions?q=react
```

### Analytics & Data Lake
```bash
# Create daily snapshot
GET /api/v1/analytics/daily-snapshot

# Get daily metrics
GET /api/v1/analytics/metrics/daily?target_date=2024-01-15

# Get metrics trends
GET /api/v1/analytics/metrics/trends?start_date=2024-01-01&end_date=2024-01-31

# Get salary analysis
GET /api/v1/analytics/salary-analysis?experience_level=senior

# Get skills trends
GET /api/v1/analytics/skills-trends?limit=20

# Manual sync
POST /api/v1/analytics/sync/sqlite-to-mongodb
```

## ⏰ Automated Tasks

The system includes automated scheduled tasks:

- **Daily Sync** (2 AM): SQLite → MongoDB
- **Daily Snapshot** (3 AM): Create data lake snapshots
- **Daily Analytics** (4 AM): Generate metrics
- **Weekly Cleanup** (Sunday 1 AM): Remove old data
- **Hourly Sync** (9 AM-6 PM, Mon-Fri): Real-time updates

## 🔍 Monitoring & Management

### MongoDB Express
- URL: http://localhost:8081
- View collections, run queries, monitor performance

### MinIO Console
- URL: http://localhost:9001
- Manage buckets, view snapshots, monitor storage

### Application Logs
```bash
# View application logs
tail -f backend/logs/app.log

# View specific service logs
docker-compose -f docker-compose.data-stack.yml logs mongodb
docker-compose -f docker-compose.data-stack.yml logs minio
```

## 📈 Data Flow

### 1. Job Ingestion
```
New Job → SQLite → MongoDB (via ETL) → Data Lake (daily snapshot)
```

### 2. Search Operations
```
User Query → MongoDB (full-text search) → Results
```

### 3. Analytics
```
Daily Snapshots → Analytics Pipeline → Metrics → Dashboard
```

## 🛠️ Development

### Local Development
```bash
# Start only MongoDB for development
docker run -d --name mongodb -p 27017:27017 mongo:7.0

# Use local file system for data lake
DATA_LAKE_TYPE=local
DATA_LAKE_LOCAL_PATH=./data_lake
```

### Testing
```bash
# Test MongoDB connection
python -c "
import asyncio
from app.core.mongodb import mongodb_manager
asyncio.run(mongodb_manager.connect())
print('MongoDB connected successfully!')
"

# Test data lake
python -c "
import asyncio
from app.core.data_lake import data_lake_manager
print('Data lake initialized:', data_lake_manager.storage_type)
"
```

## 🔧 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   ```bash
   # Check if MongoDB is running
   docker ps | grep mongodb
   
   # Check MongoDB logs
   docker logs remote-jobs-mongodb
   ```

2. **MinIO Connection Failed**
   ```bash
   # Check MinIO status
   curl http://localhost:9000/minio/health/live
   
   # Check MinIO logs
   docker logs remote-jobs-minio
   ```

3. **ETL Pipeline Errors**
   ```bash
   # Check application logs
   tail -f backend/logs/app.log | grep ETL
   
   # Manual sync test
   curl -X POST http://localhost:8000/api/v1/analytics/sync/sqlite-to-mongodb
   ```

### Performance Tuning

1. **MongoDB Indexes**
   - Text search indexes for job search
   - Compound indexes for filtering
   - TTL indexes for automatic cleanup

2. **Data Lake Optimization**
   - Compressed snapshots (gzip)
   - Partitioned by date
   - Efficient storage formats

3. **ETL Pipeline**
   - Batch processing
   - Error handling and retries
   - Monitoring and alerting

## 📚 Additional Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [MinIO Documentation](https://docs.min.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 🆘 Support

If you encounter issues:

1. Check the logs: `tail -f backend/logs/app.log`
2. Verify services: `docker-compose -f docker-compose.data-stack.yml ps`
3. Test connections: Use the test scripts above
4. Check environment variables: Ensure all required variables are set

---

**Your data architecture is now ready for production-scale remote job operations!** 🚀
