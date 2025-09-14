"""
MongoDB service for real-time job operations.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.mongodb import mongodb_manager
from app.models.mongodb_models import JobDocument, SearchQuery

logger = logging.getLogger(__name__)

class MongoDBService:
    def __init__(self):
        self.jobs_collection: Optional[AsyncIOMotorCollection] = None
        self.search_queries_collection: Optional[AsyncIOMotorCollection] = None
    
    async def initialize(self):
        """Initialize MongoDB collections"""
        await mongodb_manager.connect()
        self.jobs_collection = mongodb_manager.get_collection("jobs")
        self.search_queries_collection = mongodb_manager.get_collection("search_queries")
    
    async def search_jobs(self, 
                         query: str = "",
                         filters: Dict[str, Any] = None,
                         skip: int = 0,
                         limit: int = 50,
                         sort_by: str = "created_at",
                         sort_order: int = -1) -> Dict[str, Any]:
        """Search jobs with MongoDB text search and filters"""
        try:
            if not self.jobs_collection:
                await self.initialize()
            
            # Build MongoDB query
            mongo_query = {"is_active": True}
            
            # Add text search if query provided
            if query.strip():
                mongo_query["$text"] = {"$search": query}
            
            # Add filters
            if filters:
                if filters.get("min_salary"):
                    mongo_query["salary_max"] = {"$gte": float(filters["min_salary"])}
                
                if filters.get("max_salary"):
                    mongo_query["salary_min"] = {"$lte": float(filters["max_salary"])}
                
                if filters.get("experience_level"):
                    mongo_query["experience_level"] = filters["experience_level"]
                
                if filters.get("job_type"):
                    mongo_query["job_type"] = filters["job_type"]
                
                if filters.get("days_old"):
                    cutoff_date = datetime.utcnow() - timedelta(days=int(filters["days_old"]))
                    mongo_query["created_at"] = {"$gte": cutoff_date}
            
            # Execute search
            cursor = self.jobs_collection.find(mongo_query)
            
            # Add sorting
            if sort_by == "relevance" and query.strip():
                # Use text score for relevance
                cursor = cursor.sort([("score", {"$meta": "textScore"})])
            else:
                cursor = cursor.sort(sort_by, sort_order)
            
            # Apply pagination
            cursor = cursor.skip(skip).limit(limit)
            
            # Execute query
            jobs = []
            async for job_doc in cursor:
                job_dict = dict(job_doc)
                job_dict.pop('_id', None)  # Remove MongoDB ObjectId
                jobs.append(job_dict)
            
            # Get total count
            total_count = await self.jobs_collection.count_documents(mongo_query)
            
            # Log search query for analytics
            await self._log_search_query(query, len(jobs), filters)
            
            return {
                "jobs": jobs,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "query": query,
                "filters": filters or {}
            }
            
        except Exception as e:
            logger.error(f"MongoDB search failed: {e}")
            raise
    
    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID (source_url)"""
        try:
            if not self.jobs_collection:
                await self.initialize()
            
            job_doc = await self.jobs_collection.find_one({"source_url": job_id})
            if job_doc:
                job_dict = dict(job_doc)
                job_dict.pop('_id', None)
                return job_dict
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job by ID: {e}")
            raise
    
    async def get_jobs_by_company(self, company: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jobs by company"""
        try:
            if not self.jobs_collection:
                await self.initialize()
            
            cursor = self.jobs_collection.find({
                "company": {"$regex": company, "$options": "i"},
                "is_active": True
            }).limit(limit)
            
            jobs = []
            async for job_doc in cursor:
                job_dict = dict(job_doc)
                job_dict.pop('_id', None)
                jobs.append(job_dict)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get jobs by company: {e}")
            raise
    
    async def get_similar_jobs(self, job_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar jobs based on skills and experience level"""
        try:
            if not self.jobs_collection:
                await self.initialize()
            
            # Get the reference job
            reference_job = await self.get_job_by_id(job_id)
            if not reference_job:
                return []
            
            # Build similarity query
            similarity_query = {
                "is_active": True,
                "source_url": {"$ne": job_id}  # Exclude the reference job
            }
            
            # Add experience level filter
            if reference_job.get("experience_level"):
                similarity_query["experience_level"] = reference_job["experience_level"]
            
            # Add skills filter (at least one matching skill)
            if reference_job.get("skills_required"):
                similarity_query["skills_required"] = {
                    "$in": reference_job["skills_required"]
                }
            
            cursor = self.jobs_collection.find(similarity_query).limit(limit)
            
            jobs = []
            async for job_doc in cursor:
                job_dict = dict(job_doc)
                job_dict.pop('_id', None)
                jobs.append(job_dict)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get similar jobs: {e}")
            raise
    
    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics for dashboard"""
        try:
            if not self.jobs_collection:
                await self.initialize()
            
            # Get total active jobs
            total_jobs = await self.jobs_collection.count_documents({"is_active": True})
            
            # Get jobs by experience level
            experience_pipeline = [
                {"$match": {"is_active": True}},
                {"$group": {"_id": "$experience_level", "count": {"$sum": 1}}}
            ]
            experience_stats = await self.jobs_collection.aggregate(experience_pipeline).to_list(None)
            
            # Get jobs by company
            company_pipeline = [
                {"$match": {"is_active": True}},
                {"$group": {"_id": "$company", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            company_stats = await self.jobs_collection.aggregate(company_pipeline).to_list(None)
            
            # Get salary statistics
            salary_pipeline = [
                {"$match": {"is_active": True, "salary_min": {"$exists": True, "$ne": None}}},
                {"$group": {
                    "_id": None,
                    "avg_salary": {"$avg": "$salary_min"},
                    "min_salary": {"$min": "$salary_min"},
                    "max_salary": {"$max": "$salary_max"}
                }}
            ]
            salary_stats = await self.jobs_collection.aggregate(salary_pipeline).to_list(None)
            
            # Get recent jobs (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_jobs = await self.jobs_collection.count_documents({
                "is_active": True,
                "created_at": {"$gte": week_ago}
            })
            
            return {
                "total_jobs": total_jobs,
                "recent_jobs": recent_jobs,
                "experience_distribution": {item["_id"] or "unknown": item["count"] for item in experience_stats},
                "top_companies": [{"company": item["_id"], "job_count": item["count"]} for item in company_stats],
                "salary_stats": salary_stats[0] if salary_stats else {"avg_salary": 0, "min_salary": 0, "max_salary": 0}
            }
            
        except Exception as e:
            logger.error(f"Failed to get job statistics: {e}")
            raise
    
    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on job titles and companies"""
        try:
            if not self.jobs_collection:
                await self.initialize()
            
            # Search for matching job titles and companies
            pipeline = [
                {
                    "$match": {
                        "is_active": True,
                        "$or": [
                            {"title": {"$regex": query, "$options": "i"}},
                            {"company": {"$regex": query, "$options": "i"}}
                        ]
                    }
                },
                {
                    "$group": {
                        "_id": "$title",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            
            results = await self.jobs_collection.aggregate(pipeline).to_list(None)
            return [item["_id"] for item in results]
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    async def _log_search_query(self, query: str, results_count: int, filters: Dict[str, Any] = None):
        """Log search query for analytics"""
        try:
            if not self.search_queries_collection:
                await self.initialize()
            
            search_log = SearchQuery(
                query=query,
                results_count=results_count,
                filters=filters or {}
            )
            
            await self.search_queries_collection.insert_one(search_log.dict(by_alias=True))
            
        except Exception as e:
            logger.error(f"Failed to log search query: {e}")

# Global MongoDB service instance
mongodb_service = MongoDBService()
