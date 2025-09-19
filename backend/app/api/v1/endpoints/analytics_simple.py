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
        total_jobs = total_jobs_result.scalar() or 0
        
        # Jobs from last 30 days for growth calculation
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_jobs_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                Job.created_at >= thirty_days_ago
            )
        )
        recent_jobs = recent_jobs_result.scalar() or 0
        
        # Jobs from 30-60 days ago for comparison
        sixty_days_ago = datetime.now() - timedelta(days=60)
        previous_period_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                Job.created_at >= sixty_days_ago,
                Job.created_at < thirty_days_ago
            )
        )
        previous_period_jobs = previous_period_result.scalar() or 0
        
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
        job_boards_count = job_boards_result.scalar() or 0
        
        return {
            "total_jobs": total_jobs,
            "growth_rate": round(growth_rate, 1),
            "avg_salary": avg_salary,
            "job_boards_count": job_boards_count,
            "recent_jobs_30_days": recent_jobs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics overview: {str(e)}")


@router.get("/job-boards")
async def get_job_board_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get analytics for each job board platform"""
    
    try:
        # Get platform distribution
        platform_result = await db.execute(
            select(Job.source_platform, func.count(Job.id).label('job_count'))
            .filter(Job.is_active == True)
            .group_by(Job.source_platform)
            .order_by(desc('job_count'))
        )
        platform_stats = platform_result.all()
        
        total_jobs = sum(stat.job_count for stat in platform_stats)
        
        platforms = []
        for stat in platform_stats:
            percentage = (stat.job_count / total_jobs * 100) if total_jobs > 0 else 0
            platforms.append({
                "platform": stat.source_platform,
                "job_count": stat.job_count,
                "percentage": round(percentage, 1),
                "avg_salary": 0,  # Simplified - would need more complex query
                "recent_jobs_7_days": 0  # Simplified - would need more complex query
            })
        
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
        # Simple title-based categorization
        total_jobs_result = await db.execute(select(func.count(Job.id)).filter(Job.is_active == True))
        total_jobs = total_jobs_result.scalar() or 0
        
        # Software Development jobs
        software_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                (Job.title.ilike('%developer%') | Job.title.ilike('%engineer%') | Job.title.ilike('%software%'))
            )
        )
        software_jobs = software_result.scalar() or 0
        
        # Design jobs
        design_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                (Job.title.ilike('%designer%') | Job.title.ilike('%ux%') | Job.title.ilike('%ui%'))
            )
        )
        design_jobs = design_result.scalar() or 0
        
        # Product jobs
        product_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                (Job.title.ilike('%product%') | Job.title.ilike('%manager%'))
            )
        )
        product_jobs = product_result.scalar() or 0
        
        other_jobs = max(0, total_jobs - software_jobs - design_jobs - product_jobs)
        
        categories = [
            {
                "category": "Software Development",
                "job_count": software_jobs,
                "percentage": round((software_jobs / total_jobs * 100), 1) if total_jobs > 0 else 0,
                "avg_salary": 0
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
        
        return {
            "categories": categories,
            "experience_levels": [],  # Simplified
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
            if salary_range["max"] == 999999:  # For $150K+
                count_result = await db.execute(
                    select(func.count(Job.id)).filter(
                        Job.is_active == True,
                        ((Job.salary_min >= salary_range["min"]) | 
                         (Job.salary_max >= salary_range["min"]))
                    )
                )
            else:
                count_result = await db.execute(
                    select(func.count(Job.id)).filter(
                        Job.is_active == True,
                        ((Job.salary_min >= salary_range["min"]) & (Job.salary_min < salary_range["max"])) |
                        ((Job.salary_max >= salary_range["min"]) & (Job.salary_max < salary_range["max"])) |
                        ((Job.salary_min < salary_range["min"]) & (Job.salary_max >= salary_range["max"]))
                    )
                )
            
            count = count_result.scalar() or 0
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
        min_salary_result = await db.execute(
            select(func.min(Job.salary_min)).filter(
                Job.is_active == True,
                Job.salary_min.isnot(None)
            )
        )
        min_salary = min_salary_result.scalar() or 0
        
        max_salary_result = await db.execute(
            select(func.max(Job.salary_max)).filter(
                Job.is_active == True,
                Job.salary_max.isnot(None)
            )
        )
        max_salary = max_salary_result.scalar() or 0
        
        avg_salary_result = await db.execute(
            select(
                func.avg(case(
                    (Job.salary_min.isnot(None) & Job.salary_max.isnot(None), 
                     (Job.salary_min + Job.salary_max) / 2),
                    (Job.salary_min.isnot(None), Job.salary_min),
                    (Job.salary_max.isnot(None), Job.salary_max),
                    else_=None
                ))
            ).filter(
                Job.is_active == True,
                (Job.salary_min.isnot(None) | Job.salary_max.isnot(None))
            )
        )
        avg_salary = avg_salary_result.scalar() or 0
        
        return {
            "salary_ranges": range_stats,
            "total_jobs_with_salary": total_jobs_with_salary,
            "min_salary": int(min_salary),
            "max_salary": int(max_salary),
            "avg_salary": int(avg_salary)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching salary analytics: {str(e)}")


@router.get("/trends")
async def get_trend_analytics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get trend analytics showing job posting activity over time"""
    
    try:
        # Simplified trends - just return basic data for now
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        recent_jobs_result = await db.execute(
            select(func.count(Job.id)).filter(
                Job.is_active == True,
                Job.created_at >= thirty_days_ago
            )
        )
        recent_jobs = recent_jobs_result.scalar() or 0
        
        # Generate simple trend data
        trend_data = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).date()
            trend_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "total": recent_jobs // 30,  # Simplified distribution
                "RemoteOK": (recent_jobs // 30) // 2,
                "Remotive": (recent_jobs // 30) // 3,
                "WeWorkRemotely": (recent_jobs // 30) // 6
            })
        
        return {
            "daily_trends": trend_data,
            "period_days": 30
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trend analytics: {str(e)}")
