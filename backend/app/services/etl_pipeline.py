"""
ETL Pipeline for synchronizing data between SQLite, MongoDB, and Data Lake.
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database_sqlite import get_db
from app.core.mongodb import mongodb_manager
from app.core.data_lake import data_lake_manager
from app.models.job import Job as SQLiteJob
from app.models.mongodb_models import JobDocument, JobSnapshot, AnalyticsMetric
from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor

logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        self.ai_processor = CostEffectiveAIProcessor()
    
    async def sync_sqlite_to_mongodb(self, batch_size: int = 100) -> Dict[str, int]:
        """Sync jobs from SQLite to MongoDB"""
        try:
            # Get SQLite session
            async for db in get_db():
                # Get all active remote jobs from SQLite
                result = await db.execute(
                    select(SQLiteJob).where(
                        SQLiteJob.is_active == True,
                        SQLiteJob.remote_type == "remote"
                    )
                )
                sqlite_jobs = result.scalars().all()
                
                # Get MongoDB collection
                await mongodb_manager.connect()
                jobs_collection = mongodb_manager.get_collection("jobs")
                
                synced_count = 0
                updated_count = 0
                error_count = 0
                
                for i in range(0, len(sqlite_jobs), batch_size):
                    batch = sqlite_jobs[i:i + batch_size]
                    
                    for sqlite_job in batch:
                        try:
                            # Convert SQLite job to MongoDB document
                            job_doc = self._convert_sqlite_to_mongodb(sqlite_job)
                            
                            # Check if job already exists in MongoDB
                            existing_job = await jobs_collection.find_one(
                                {"source_url": sqlite_job.source_url}
                            )
                            
                            if existing_job:
                                # Update existing job
                                await jobs_collection.update_one(
                                    {"source_url": sqlite_job.source_url},
                                    {"$set": job_doc.dict(by_alias=True, exclude={"id"})}
                                )
                                updated_count += 1
                            else:
                                # Insert new job
                                await jobs_collection.insert_one(job_doc.dict(by_alias=True))
                                synced_count += 1
                                
                        except Exception as e:
                            logger.error(f"Error syncing job {sqlite_job.id}: {e}")
                            error_count += 1
                
                logger.info(f"SQLite to MongoDB sync completed: {synced_count} new, {updated_count} updated, {error_count} errors")
                return {
                    "synced": synced_count,
                    "updated": updated_count,
                    "errors": error_count
                }
                
        except Exception as e:
            logger.error(f"SQLite to MongoDB sync failed: {e}")
            raise
    
    async def create_daily_snapshot(self, target_date: date = None) -> str:
        """Create daily snapshot of all jobs for analytics"""
        try:
            if target_date is None:
                target_date = date.today()
            
            # Get all jobs from MongoDB
            await mongodb_manager.connect()
            jobs_collection = mongodb_manager.get_collection("jobs")
            
            # Get all active jobs
            cursor = jobs_collection.find({"is_active": True})
            jobs_data = []
            
            async for job_doc in cursor:
                # Convert MongoDB document to dict
                job_dict = dict(job_doc)
                job_dict.pop('_id', None)  # Remove MongoDB ObjectId
                jobs_data.append(job_dict)
            
            # Store snapshot in data lake
            snapshot_path = await data_lake_manager.store_daily_snapshot(
                "jobs", 
                jobs_data, 
                target_date
            )
            
            # Also store individual job snapshots in MongoDB for quick access
            snapshots_collection = mongodb_manager.get_collection("job_snapshots")
            
            for job_data in jobs_data:
                snapshot = JobSnapshot(
                    job_id=job_data.get('source_url', ''),
                    job_data=JobDocument(**job_data),
                    metrics={
                        "snapshot_date": target_date.isoformat(),
                        "total_jobs": len(jobs_data)
                    }
                )
                
                await snapshots_collection.insert_one(snapshot.dict(by_alias=True))
            
            logger.info(f"Daily snapshot created: {snapshot_path} ({len(jobs_data)} jobs)")
            return snapshot_path
            
        except Exception as e:
            logger.error(f"Failed to create daily snapshot: {e}")
            raise
    
    async def generate_analytics_metrics(self, target_date: date = None) -> Dict[str, Any]:
        """Generate analytics metrics for the day"""
        try:
            if target_date is None:
                target_date = date.today()
            
            await mongodb_manager.connect()
            jobs_collection = mongodb_manager.get_collection("jobs")
            
            # Get all active jobs
            cursor = jobs_collection.find({"is_active": True})
            jobs = [job async for job in cursor]
            
            # Calculate metrics
            metrics = {
                "total_jobs": len(jobs),
                "salary_stats": self._calculate_salary_stats(jobs),
                "experience_level_distribution": self._calculate_experience_distribution(jobs),
                "company_stats": self._calculate_company_stats(jobs),
                "skills_analysis": self._calculate_skills_analysis(jobs),
                "remote_work_indicators": self._calculate_remote_indicators(jobs),
                "ai_processing_stats": self._calculate_ai_stats(jobs)
            }
            
            # Store analytics in data lake
            await data_lake_manager.store_analytics_data(
                "daily_metrics", 
                metrics, 
                target_date
            )
            
            # Store in MongoDB for quick access
            analytics_collection = mongodb_manager.get_collection("analytics")
            analytics_doc = AnalyticsMetric(
                metric_type="daily_metrics",
                data=metrics
            )
            
            await analytics_collection.insert_one(analytics_doc.dict(by_alias=True))
            
            logger.info(f"Analytics metrics generated for {target_date}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to generate analytics metrics: {e}")
            raise
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data from MongoDB"""
        try:
            await mongodb_manager.connect()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Clean up old job snapshots
            snapshots_collection = mongodb_manager.get_collection("job_snapshots")
            result = await snapshots_collection.delete_many({
                "snapshot_date": {"$lt": cutoff_date}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old job snapshots")
            
            # Clean up old analytics
            analytics_collection = mongodb_manager.get_collection("analytics")
            result = await analytics_collection.delete_many({
                "date": {"$lt": cutoff_date}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old analytics records")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise
    
    def _convert_sqlite_to_mongodb(self, sqlite_job: SQLiteJob) -> JobDocument:
        """Convert SQLite job to MongoDB document"""
        return JobDocument(
            title=sqlite_job.title,
            company=sqlite_job.company,
            location=sqlite_job.location,
            salary_min=sqlite_job.salary_min,
            salary_max=sqlite_job.salary_max,
            salary_currency=sqlite_job.salary_currency or "USD",
            salary_period=sqlite_job.salary_period or "yearly",
            description=sqlite_job.description,
            requirements=sqlite_job.requirements,
            benefits=sqlite_job.benefits,
            job_type=sqlite_job.job_type,
            experience_level=sqlite_job.experience_level,
            remote_type="remote",  # Always remote for our platform
            source_url=sqlite_job.source_url,
            source_platform=sqlite_job.source_platform,
            posted_date=sqlite_job.posted_date,
            application_url=sqlite_job.application_url,
            company_logo=sqlite_job.company_logo,
            company_description=sqlite_job.company_description,
            company_size=sqlite_job.company_size,
            company_industry=sqlite_job.company_industry,
            skills_required=sqlite_job.skills_required,
            ai_generated_summary=sqlite_job.ai_generated_summary,
            ai_processed=sqlite_job.ai_processed or False,
            is_active=sqlite_job.is_active,
            created_at=sqlite_job.created_at,
            updated_at=sqlite_job.updated_at,
            tags=self._generate_tags(sqlite_job),
            metadata={
                "source": "sqlite_sync",
                "sync_date": datetime.utcnow().isoformat()
            }
        )
    
    def _generate_tags(self, job: SQLiteJob) -> List[str]:
        """Generate tags for job categorization"""
        tags = []
        
        if job.experience_level:
            tags.append(f"level_{job.experience_level}")
        
        if job.job_type:
            tags.append(f"type_{job.job_type}")
        
        if job.skills_required:
            tags.extend([f"skill_{skill.lower().replace(' ', '_')}" for skill in job.skills_required[:5]])
        
        if job.ai_processed:
            tags.append("ai_verified")
        
        return tags
    
    def _calculate_salary_stats(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Calculate salary statistics"""
        salaries = []
        for job in jobs:
            if job.get('salary_min') and job.get('salary_max'):
                salaries.append((job['salary_min'] + job['salary_max']) / 2)
            elif job.get('salary_min'):
                salaries.append(job['salary_min'])
            elif job.get('salary_max'):
                salaries.append(job['salary_max'])
        
        if not salaries:
            return {"count": 0, "average": 0, "median": 0, "min": 0, "max": 0}
        
        salaries.sort()
        return {
            "count": len(salaries),
            "average": sum(salaries) / len(salaries),
            "median": salaries[len(salaries) // 2],
            "min": min(salaries),
            "max": max(salaries)
        }
    
    def _calculate_experience_distribution(self, jobs: List[Dict]) -> Dict[str, int]:
        """Calculate experience level distribution"""
        distribution = {}
        for job in jobs:
            level = job.get('experience_level', 'unknown')
            distribution[level] = distribution.get(level, 0) + 1
        return distribution
    
    def _calculate_company_stats(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Calculate company statistics"""
        companies = {}
        for job in jobs:
            company = job.get('company', 'Unknown')
            if company not in companies:
                companies[company] = 0
            companies[company] += 1
        
        return {
            "total_companies": len(companies),
            "top_companies": sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def _calculate_skills_analysis(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Calculate skills analysis"""
        all_skills = []
        for job in jobs:
            if job.get('skills_required'):
                all_skills.extend(job['skills_required'])
        
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        return {
            "total_unique_skills": len(skill_counts),
            "most_demanded_skills": sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        }
    
    def _calculate_remote_indicators(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Calculate remote work indicators"""
        remote_keywords = ['remote', 'distributed', 'work from home', 'wfh', 'telecommute', 'virtual', 'online']
        
        indicators = {
            "explicitly_remote": 0,
            "has_remote_keywords": 0,
            "location_agnostic": 0
        }
        
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            
            if job.get('remote_type') == 'remote':
                indicators["explicitly_remote"] += 1
            
            if any(keyword in text for keyword in remote_keywords):
                indicators["has_remote_keywords"] += 1
            
            if not job.get('location') or job.get('location', '').lower() in ['remote', 'anywhere', 'global']:
                indicators["location_agnostic"] += 1
        
        return indicators
    
    def _calculate_ai_stats(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Calculate AI processing statistics"""
        total_jobs = len(jobs)
        ai_processed = sum(1 for job in jobs if job.get('ai_processed'))
        
        return {
            "total_jobs": total_jobs,
            "ai_processed": ai_processed,
            "ai_processing_rate": (ai_processed / total_jobs * 100) if total_jobs > 0 else 0
        }

# Global ETL pipeline instance
etl_pipeline = ETLPipeline()
