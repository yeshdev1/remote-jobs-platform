#!/usr/bin/env python3
"""
Test script for the Cost-Effective AI Processor
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor

async def test_ai_processor():
    """Test the AI processor with sample job data"""
    
    print("🤖 Testing Cost-Effective AI Processor")
    print("=" * 50)
    
    # Initialize processor
    try:
        processor = CostEffectiveAIProcessor()
        print("✅ AI Processor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI Processor: {e}")
        return
    
    # Test job data samples
    test_jobs = [
        {
            'title': 'Senior Software Engineer',
            'company': 'TechCorp',
            'description': 'Build scalable web applications using Python, React, and AWS. Remote position with competitive salary.',
            'salary_min': 120000,
            'salary_max': 180000,
            'requirements': 'Python, React, AWS, Docker, 5+ years experience',
            'source_platform': 'linkedin'
        },
        {
            'title': 'Frontend Developer',
            'company': 'WebSolutions',
            'description': 'Create beautiful user interfaces with React and TypeScript. Work from anywhere.',
            'salary_min': 80000,
            'salary_max': 120000,
            'requirements': 'React, TypeScript, CSS, Git',
            'source_platform': 'indeed'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataCorp',
            'description': 'Competitive salary based on experience. Commission-based opportunities available. Work from home.',
            'salary_min': None,
            'salary_max': None,
            'requirements': 'Python, Machine Learning, Statistics',
            'source_platform': 'stackoverflow'
        }
    ]
    
    print(f"\n📊 Testing with {len(test_jobs)} sample jobs")
    print("-" * 30)
    
    # Test individual job validation
    for i, job_data in enumerate(test_jobs, 1):
        print(f"\n🔍 Testing Job {i}: {job_data['title']} at {job_data['company']}")
        
        try:
            result = await processor.validate_job(job_data)
            
            print(f"   Model Used: {result.model_used}")
            print(f"   Valid: {result.is_valid}")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Cost: ${result.cost:.4f}")
            print(f"   Remote Type: {result.remote_type}")
            print(f"   Experience Level: {result.experience_level}")
            print(f"   Skills: {result.skills}")
            print(f"   Summary: {result.summary[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test batch processing
    print(f"\n🔄 Testing batch processing")
    print("-" * 30)
    
    try:
        batch_results = await processor.validate_jobs_batch(test_jobs)
        print(f"✅ Batch processing completed: {len(batch_results)} jobs processed")
        
        valid_jobs = [r for r in batch_results if r.is_valid]
        print(f"   Valid jobs: {len(valid_jobs)}/{len(batch_results)}")
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
    
    # Show cost summary
    print(f"\n💰 Daily Cost Summary")
    print("-" * 30)
    
    summary = processor.get_daily_cost_summary()
    print(f"Total Cost: ${summary['total_cost']:.2f}")
    print(f"Jobs Processed: {summary['jobs_processed']}")
    print(f"Cost per Job: ${summary['cost_per_job']:.4f}")
    print(f"Budget Remaining: ${summary['budget_remaining']:.2f}")
    print(f"Strategy: {summary['strategy']}")
    print(f"Provider Breakdown:")
    for provider, cost in summary['breakdown'].items():
        if cost > 0:
            print(f"  {provider}: ${cost:.4f}")
    
    print(f"\n🎉 AI Processor test completed!")

if __name__ == "__main__":
    asyncio.run(test_ai_processor())
