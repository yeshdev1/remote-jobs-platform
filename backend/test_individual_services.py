#!/usr/bin/env python3
"""
Test individual AI services to verify API keys and track costs
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.ai_processor.cost_effective_processor import CostEffectiveAIProcessor

async def test_individual_services():
    """Test each AI service individually"""
    
    print("🧪 Testing Individual AI Services")
    print("=" * 50)
    
    # Initialize processor
    try:
        processor = CostEffectiveAIProcessor()
        print("✅ AI Processor initialized successfully")
        
        # Show initial status
        initial_status = processor.get_daily_cost_summary()
        print(f"💰 Initial costs: ${initial_status['total_cost']:.4f}")
        print(f"📊 Strategy: {initial_status['strategy']}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to initialize AI Processor: {e}")
        return
    
    # Test job data
    test_job = {
        'title': 'Senior Software Engineer',
        'company': 'TechCorp',
        'description': 'Build scalable web applications using Python, React, and AWS. Remote position with competitive salary.',
        'salary_min': 120000,
        'salary_max': 180000,
        'requirements': 'Python, React, AWS, Docker, 5+ years experience',
        'source_platform': 'linkedin'
    }
    
    print("🔍 Test Job Data:")
    print(f"   Title: {test_job['title']}")
    print(f"   Company: {test_job['company']}")
    print(f"   Salary: ${test_job['salary_min']:,} - ${test_job['salary_max']:,}")
    print()
    
    # Test 1: Google Gemini 1.5 Flash (Simple jobs)
    print("🟢 TEST 1: Google Gemini 1.5 Flash")
    print("-" * 40)
    
    try:
        print("Testing Gemini 1.5 Flash...")
        result = await processor.validate_job_with_gemini(test_job)
        
        print(f"   ✅ Success!")
        print(f"   Model Used: {result.model_used}")
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Cost: ${result.cost:.4f}")
        print(f"   Remote Type: {result.remote_type}")
        print(f"   Experience Level: {result.experience_level}")
        print(f"   Skills: {result.skills}")
        
    except Exception as e:
        print(f"   ❌ Gemini Error: {e}")
    
    # Show costs after Gemini test
    gemini_costs = processor.get_daily_cost_summary()
    print(f"   💰 Total costs after Gemini: ${gemini_costs['total_cost']:.4f}")
    print(f"   📊 Google costs: ${gemini_costs['breakdown']['google']:.4f}")
    print()
    
    # Test 2: OpenAI GPT-4o Mini (Medium jobs)
    print("🔵 TEST 2: OpenAI GPT-4o Mini")
    print("-" * 40)
    
    try:
        print("Testing GPT-4o Mini...")
        result = await processor.validate_job_with_openai(test_job)
        
        print(f"   ✅ Success!")
        print(f"   Model Used: {result.model_used}")
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Cost: ${result.cost:.4f}")
        print(f"   Remote Type: {result.remote_type}")
        print(f"   Experience Level: {result.experience_level}")
        print(f"   Skills: {result.skills}")
        
    except Exception as e:
        print(f"   ❌ OpenAI Error: {e}")
    
    # Show costs after OpenAI test
    openai_costs = processor.get_daily_cost_summary()
    print(f"   💰 Total costs after OpenAI: ${openai_costs['total_cost']:.4f}")
    print(f"   📊 OpenAI costs: ${openai_costs['breakdown']['openai']:.4f}")
    print()
    
    # Test 3: Anthropic Claude 3.5 Sonnet (Complex jobs)
    print("🟣 TEST 3: Anthropic Claude 3.5 Sonnet")
    print("-" * 40)
    
    try:
        print("Testing Claude 3.5 Sonnet...")
        result = await processor.validate_job_with_claude(test_job)
        
        print(f"   ✅ Success!")
        print(f"   Model Used: {result.model_used}")
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Cost: ${result.cost:.4f}")
        print(f"   Remote Type: {result.remote_type}")
        print(f"   Experience Level: {result.experience_level}")
        print(f"   Skills: {result.skills}")
        
    except Exception as e:
        print(f"   ❌ Claude Error: {e}")
    
    # Show final costs
    final_costs = processor.get_daily_cost_summary()
    print(f"   💰 Total costs after Claude: ${final_costs['total_cost']:.4f}")
    print(f"   📊 Claude costs: ${final_costs['breakdown']['anthropic']:.4f}")
    print()
    
    # Final Summary
    print("📊 FINAL COST SUMMARY")
    print("=" * 50)
    
    summary = processor.get_daily_cost_summary()
    print(f"💰 Total Daily Cost: ${summary['total_cost']:.4f}")
    print(f"📈 Jobs Processed: {summary['jobs_processed']}")
    print(f"💵 Cost per Job: ${summary['cost_per_job']:.4f}")
    print(f"🎯 Budget Remaining: ${summary['budget_remaining']:.2f}")
    print(f"🔧 Strategy Used: {summary['strategy']}")
    print()
    print("📊 Provider Breakdown:")
    for provider, cost in summary['breakdown'].items():
        if cost > 0:
            print(f"   {provider.capitalize()}: ${cost:.4f}")
        else:
            print(f"   {provider.capitalize()}: $0.0000 (no usage)")
    
    print()
    print("🎉 Individual service testing completed!")
    print("💡 Check your provider dashboards to see the actual charges")

if __name__ == "__main__":
    asyncio.run(test_individual_services())
