"""
Analytics endpoints for historical data and insights.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import logging

from app.core.data_lake import data_lake_manager
from app.core.mongodb import mongodb_manager
from app.services.etl_pipeline import etl_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/daily-snapshot")
async def create_daily_snapshot(target_date: Optional[date] = None):
    """
    Create a daily snapshot of all jobs for analytics.
    """
    try:
        snapshot_path = await etl_pipeline.create_daily_snapshot(target_date)
        return {
            "message": "Daily snapshot created successfully",
            "snapshot_path": snapshot_path,
            "date": target_date or date.today()
        }
        
    except Exception as e:
        logger.error(f"Failed to create daily snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create daily snapshot: {str(e)}")

@router.get("/metrics/daily")
async def get_daily_metrics(target_date: Optional[date] = None):
    """
    Get daily analytics metrics.
    """
    try:
        if target_date is None:
            target_date = date.today()
        
        # Try to get from MongoDB first
        await mongodb_manager.connect()
        analytics_collection = mongodb_manager.get_collection("analytics")
        
        metrics_doc = await analytics_collection.find_one({
            "metric_type": "daily_metrics",
            "date": target_date
        })
        
        if metrics_doc:
            return {
                "date": target_date,
                "metrics": metrics_doc["data"],
                "source": "mongodb"
            }
        
        # If not found in MongoDB, try data lake
        snapshot_data = await data_lake_manager.retrieve_daily_snapshot("analytics", target_date)
        if snapshot_data:
            return {
                "date": target_date,
                "metrics": snapshot_data["data"],
                "source": "data_lake"
            }
        
        # Generate new metrics if not found
        metrics = await etl_pipeline.generate_analytics_metrics(target_date)
        return {
            "date": target_date,
            "metrics": metrics,
            "source": "generated"
        }
        
    except Exception as e:
        logger.error(f"Failed to get daily metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get daily metrics: {str(e)}")

@router.get("/metrics/trends")
async def get_metrics_trends(
    start_date: date = Query(..., description="Start date for trends"),
    end_date: date = Query(..., description="End date for trends"),
    metric_type: str = Query("daily_metrics", description="Type of metrics to analyze")
):
    """
    Get metrics trends over a date range.
    """
    try:
        await mongodb_manager.connect()
        analytics_collection = mongodb_manager.get_collection("analytics")
        
        # Get metrics for date range
        cursor = analytics_collection.find({
            "metric_type": metric_type,
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("date", 1)
        
        trends = []
        async for doc in cursor:
            trends.append({
                "date": doc["date"],
                "data": doc["data"]
            })
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "metric_type": metric_type,
            "trends": trends,
            "count": len(trends)
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics trends: {str(e)}")

@router.get("/snapshots/list")
async def list_snapshots(
    data_type: str = Query("jobs", description="Type of data snapshots"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date")
):
    """
    List available snapshots for a date range.
    """
    try:
        snapshots = await data_lake_manager.list_snapshots(data_type, start_date, end_date)
        return {
            "data_type": data_type,
            "start_date": start_date,
            "end_date": end_date,
            "snapshots": snapshots,
            "count": len(snapshots)
        }
        
    except Exception as e:
        logger.error(f"Failed to list snapshots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {str(e)}")

@router.get("/snapshots/{snapshot_date}")
async def get_snapshot(
    snapshot_date: date,
    data_type: str = Query("jobs", description="Type of data snapshot")
):
    """
    Get a specific snapshot by date.
    """
    try:
        snapshot_data = await data_lake_manager.retrieve_daily_snapshot(data_type, snapshot_date)
        if not snapshot_data:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        
        return {
            "date": snapshot_date,
            "data_type": data_type,
            "snapshot": snapshot_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get snapshot: {str(e)}")

@router.get("/salary-analysis")
async def get_salary_analysis(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    experience_level: Optional[str] = None
):
    """
    Get salary analysis and trends.
    """
    try:
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        await mongodb_manager.connect()
        jobs_collection = mongodb_manager.get_collection("jobs")
        
        # Build query
        query = {
            "is_active": True,
            "salary_min": {"$exists": True, "$ne": None},
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        if experience_level:
            query["experience_level"] = experience_level
        
        # Aggregate salary data
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": {
                    "experience_level": "$experience_level",
                    "job_type": "$job_type"
                },
                "avg_salary": {"$avg": "$salary_min"},
                "min_salary": {"$min": "$salary_min"},
                "max_salary": {"$max": "$salary_max"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"avg_salary": -1}}
        ]
        
        results = await jobs_collection.aggregate(pipeline).to_list(None)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "experience_level": experience_level,
            "salary_analysis": results
        }
        
    except Exception as e:
        logger.error(f"Failed to get salary analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get salary analysis: {str(e)}")

@router.get("/skills-trends")
async def get_skills_trends(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get trending skills analysis.
    """
    try:
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
        
        await mongodb_manager.connect()
        jobs_collection = mongodb_manager.get_collection("jobs")
        
        # Aggregate skills data
        pipeline = [
            {
                "$match": {
                    "is_active": True,
                    "skills_required": {"$exists": True, "$ne": []},
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {"$unwind": "$skills_required"},
            {"$group": {
                "_id": "$skills_required",
                "count": {"$sum": 1},
                "avg_salary": {"$avg": "$salary_min"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        results = await jobs_collection.aggregate(pipeline).to_list(None)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "skills_trends": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Failed to get skills trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get skills trends: {str(e)}")

@router.post("/sync/sqlite-to-mongodb")
async def sync_sqlite_to_mongodb(batch_size: int = Query(100, ge=1, le=1000)):
    """
    Manually trigger sync from SQLite to MongoDB.
    """
    try:
        result = await etl_pipeline.sync_sqlite_to_mongodb(batch_size)
        return {
            "message": "Sync completed successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to sync SQLite to MongoDB: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_data(days_to_keep: int = Query(90, ge=1, le=365)):
    """
    Clean up old data from MongoDB.
    """
    try:
        await etl_pipeline.cleanup_old_data(days_to_keep)
        return {
            "message": f"Cleanup completed successfully",
            "days_kept": days_to_keep
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")
