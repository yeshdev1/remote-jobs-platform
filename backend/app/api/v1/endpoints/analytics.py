from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, case, select
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.database_sqlite import get_db
from app.models.job import Job

router = APIRouter()

@router.get("/overview")
async def get_analytics_overview(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get overview analytics including total jobs, growth rate, and key metrics"""
    
    try:
        # Total jobs
        total_jobs_result = await db.execute(select(func.count(Job.id)).filter(Job.is_active == True))
        total_jobs = total_jobs_result.scalar()
        
        # Jobs from last 30 days for growth calculation
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_jobs_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                Job.created_at >= thirty_days_ago
            )
        )
        recent_jobs = recent_jobs_result.scalar()
        
        # Jobs from 30-60 days ago for comparison
        sixty_days_ago = datetime.now() - timedelta(days=60)
        previous_period_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                Job.created_at >= sixty_days_ago,
                Job.created_at < thirty_days_ago
            )
        )
        previous_period_jobs = previous_period_result.scalar()
        
        # Calculate growth rate
        if previous_period_jobs > 0:
            growth_rate = ((recent_jobs - previous_period_jobs) / previous_period_jobs) * 100
        else:
            growth_rate = 100.0 if recent_jobs > 0 else 0.0
        
        # Average salary calculation
        avg_salary_result = await db.execute(
            select(
                func.avg(case(
                    (Job.salary_min.isnot(None) & Job.salary_max.isnot(None), 
                     (Job.salary_min + Job.salary_max) / 2),
                    (Job.salary_min.isnot(None), Job.salary_min),
                    (Job.salary_max.isnot(None), Job.salary_max),
                    else_=None
                ))
            ).filter(Job.is_active == True)
        )
        avg_salary_value = avg_salary_result.scalar()
        avg_salary = int(avg_salary_value) if avg_salary_value else 0
        
        # Count unique job boards
        job_boards_result = await db.execute(
            select(func.count(func.distinct(Job.source_platform))).filter(Job.is_active == True)
        )
        job_boards_count = job_boards_result.scalar()
        
        return {
            "total_jobs": total_jobs or 0,
            "growth_rate": round(growth_rate, 1),
            "avg_salary": avg_salary,
            "job_boards_count": job_boards_count or 0,
            "recent_jobs_30_days": recent_jobs or 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics overview: {str(e)}")


@router.get("/job-boards")
async def get_job_board_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get analytics for each job board platform"""
    
    try:
        # Job distribution by platform
        platform_stats = db.query(
            Job.source_platform,
            func.count(Job.id).label('job_count'),
            func.avg(case(
                (Job.salary_min.isnot(None) & Job.salary_max.isnot(None), 
                 (Job.salary_min + Job.salary_max) / 2),
                (Job.salary_min.isnot(None), Job.salary_min),
                (Job.salary_max.isnot(None), Job.salary_max),
                else_=None
            )).label('avg_salary')
        ).filter(Job.is_active == True).group_by(Job.source_platform).order_by(desc('job_count')).all()
        
        total_jobs = sum(stat.job_count for stat in platform_stats)
        
        platforms = []
        for stat in platform_stats:
            percentage = (stat.job_count / total_jobs * 100) if total_jobs > 0 else 0
            platforms.append({
                "platform": stat.source_platform,
                "job_count": stat.job_count,
                "percentage": round(percentage, 1),
                "avg_salary": int(stat.avg_salary) if stat.avg_salary else 0
            })
        
        # Recent activity by platform (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_activity = db.query(
            Job.source_platform,
            func.count(Job.id).label('recent_jobs')
        ).filter(
            Job.is_active == True,
            Job.created_at >= seven_days_ago
        ).group_by(Job.source_platform).all()
        
        recent_dict = {activity.source_platform: activity.recent_jobs for activity in recent_activity}
        
        # Add recent activity to platforms
        for platform in platforms:
            platform["recent_jobs_7_days"] = recent_dict.get(platform["platform"], 0)
        
        return {
            "platforms": platforms,
            "total_jobs": total_jobs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job board analytics: {str(e)}")


@router.get("/job-categories")
async def get_job_category_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get analytics for job categories and types"""
    
    try:
        # Job type distribution (based on AI validation or title analysis)
        job_type_stats = db.query(
            Job.job_type,
            func.count(Job.id).label('job_count'),
            func.avg(case(
                (Job.salary_min.isnot(None) & Job.salary_max.isnot(None), 
                 (Job.salary_min + Job.salary_max) / 2),
                (Job.salary_min.isnot(None), Job.salary_min),
                (Job.salary_max.isnot(None), Job.salary_max),
                else_=None
            )).label('avg_salary')
        ).filter(
            Job.is_active == True,
            Job.job_type.isnot(None)
        ).group_by(Job.job_type).order_by(desc('job_count')).all()
        
        # If no job_type data, analyze by title keywords
        if not job_type_stats:
            # Fallback to title-based analysis
            software_jobs = db.query(Job).filter(
                Job.is_active == True,
                Job.title.ilike('%developer%') | Job.title.ilike('%engineer%') | Job.title.ilike('%software%')
            ).count()
            
            design_jobs = db.query(Job).filter(
                Job.is_active == True,
                Job.title.ilike('%designer%') | Job.title.ilike('%ux%') | Job.title.ilike('%ui%')
            ).count()
            
            product_jobs = db.query(Job).filter(
                Job.is_active == True,
                Job.title.ilike('%product%') | Job.title.ilike('%manager%')
            ).count()
            
            total_categorized = software_jobs + design_jobs + product_jobs
            total_jobs = db.query(Job).filter(Job.is_active == True).count()
            other_jobs = total_jobs - total_categorized
            
            categories = [
                {
                    "category": "Software Development",
                    "job_count": software_jobs,
                    "percentage": round((software_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0,
                    "avg_salary": 0  # Would need more complex query for title-based salary avg
                },
                {
                    "category": "UX/UI Design", 
                    "job_count": design_jobs,
                    "percentage": round((design_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0,
                    "avg_salary": 0
                },
                {
                    "category": "Product Management",
                    "job_count": product_jobs, 
                    "percentage": round((product_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0,
                    "avg_salary": 0
                },
                {
                    "category": "Other",
                    "job_count": other_jobs,
                    "percentage": round((other_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0,
                    "avg_salary": 0
                }
            ]
        else:
            total_jobs = sum(stat.job_count for stat in job_type_stats)
            categories = []
            for stat in job_type_stats:
                percentage = (stat.job_count / total_jobs * 100) if total_jobs > 0 else 0
                categories.append({
                    "category": stat.job_type,
                    "job_count": stat.job_count,
                    "percentage": round(percentage, 1),
                    "avg_salary": int(stat.avg_salary) if stat.avg_salary else 0
                })
        
        # Experience level distribution
        experience_stats = db.query(
            Job.experience_level,
            func.count(Job.id).label('job_count')
        ).filter(
            Job.is_active == True,
            Job.experience_level.isnot(None)
        ).group_by(Job.experience_level).order_by(desc('job_count')).all()
        
        experience_levels = []
        total_exp_jobs = sum(stat.job_count for stat in experience_stats) if experience_stats else 0
        
        for stat in experience_stats:
            percentage = (stat.job_count / total_exp_jobs * 100) if total_exp_jobs > 0 else 0
            experience_levels.append({
                "level": stat.experience_level,
                "job_count": stat.job_count,
                "percentage": round(percentage, 1)
            })
        
        return {
            "categories": categories,
            "experience_levels": experience_levels,
            "total_jobs": total_jobs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job category analytics: {str(e)}")


@router.get("/salary-ranges")
async def get_salary_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get salary range analytics"""
    
    try:
        # Define salary ranges
        salary_ranges = [
            {"min": 0, "max": 80000, "label": "Under $80K"},
            {"min": 80000, "max": 100000, "label": "$80K - $100K"},
            {"min": 100000, "max": 150000, "label": "$100K - $150K"},
            {"min": 150000, "max": 999999, "label": "$150K+"}
        ]
        
        range_stats = []
        total_jobs_with_salary = 0
        
        for salary_range in salary_ranges:
            # Count jobs in this salary range
            if salary_range["max"] == 999999:  # For $150K+
                count = db.query(Job).filter(
                    Job.is_active == True,
                    ((Job.salary_min >= salary_range["min"]) | 
                     (Job.salary_max >= salary_range["min"]))
                ).count()
            else:
                count = db.query(Job).filter(
                    Job.is_active == True,
                    ((Job.salary_min >= salary_range["min"]) & (Job.salary_min < salary_range["max"])) |
                    ((Job.salary_max >= salary_range["min"]) & (Job.salary_max < salary_range["max"])) |
                    ((Job.salary_min < salary_range["min"]) & (Job.salary_max >= salary_range["max"]))
                ).count()
            
            total_jobs_with_salary += count
            range_stats.append({
                "range": salary_range["label"],
                "job_count": count,
                "percentage": 0  # Will calculate after we have total
            })
        
        # Calculate percentages
        for stat in range_stats:
            stat["percentage"] = round((stat["job_count"] / total_jobs_with_salary * 100), 1) if total_jobs_with_salary > 0 else 0
        
        # Overall salary statistics
        salary_stats = db.query(
            func.min(Job.salary_min).label('min_salary'),
            func.max(Job.salary_max).label('max_salary'),
            func.avg(case(
                (Job.salary_min.isnot(None) & Job.salary_max.isnot(None), 
                 (Job.salary_min + Job.salary_max) / 2),
                (Job.salary_min.isnot(None), Job.salary_min),
                (Job.salary_max.isnot(None), Job.salary_max),
                else_=None
            )).label('avg_salary')
        ).filter(
            Job.is_active == True,
            (Job.salary_min.isnot(None) | Job.salary_max.isnot(None))
        ).first()
        
        return {
            "salary_ranges": range_stats,
            "total_jobs_with_salary": total_jobs_with_salary,
            "min_salary": int(salary_stats.min_salary) if salary_stats.min_salary else 0,
            "max_salary": int(salary_stats.max_salary) if salary_stats.max_salary else 0,
            "avg_salary": int(salary_stats.avg_salary) if salary_stats.avg_salary else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching salary analytics: {str(e)}")


@router.get("/trends")
async def get_trend_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get trend analytics showing job posting activity over time"""
    
    try:
        # Jobs posted by day for the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        daily_stats = db.query(
            func.date(Job.created_at).label('date'),
            func.count(Job.id).label('job_count'),
            Job.source_platform
        ).filter(
            Job.is_active == True,
            Job.created_at >= thirty_days_ago
        ).group_by(
            func.date(Job.created_at),
            Job.source_platform
        ).order_by('date').all()
        
        # Organize by date and platform
        trends = {}
        for stat in daily_stats:
            date_str = stat.date.strftime('%Y-%m-%d')
            if date_str not in trends:
                trends[date_str] = {}
            trends[date_str][stat.source_platform] = stat.job_count
        
        # Fill in missing days with 0
        trend_data = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).date()
            date_str = date.strftime('%Y-%m-%d')
            
            day_data = {
                "date": date_str,
                "total": 0
            }
            
            # Add platform-specific counts
            if date_str in trends:
                for platform, count in trends[date_str].items():
                    day_data[platform] = count
                    day_data["total"] += count
            
            trend_data.append(day_data)
        
        return {
            "daily_trends": trend_data,
            "period_days": 30
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trend analytics: {str(e)}")