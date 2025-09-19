// Demo file to showcase the intelligent search capabilities
import { Job } from './types';
import { intelligentSearch } from './searchUtils';

// Example jobs for demonstration
const sampleJobs: Job[] = [
  {
    id: 1,
    title: "Senior React Developer",
    company: "TechCorp",
    location: "Remote",
    description: "We're looking for an experienced React developer to join our team. Must have 5+ years of experience with React, TypeScript, and modern web development practices.",
    salary_min: 120000,
    salary_max: 180000,
    experience_level: "senior",
    remote_type: "fully_remote",
    job_type: "full_time",
    skills_required: ["React", "TypeScript", "JavaScript", "CSS", "HTML"],
    source_url: "https://example.com/job1",
    source_platform: "LinkedIn",
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-01-15T10:00:00Z",
    is_active: true,
    ai_processed: true,
    ai_generated_summary: "Senior React developer position with competitive salary and full remote work."
  },
  {
    id: 2,
    title: "Python Data Scientist",
    company: "DataCorp",
    location: "San Francisco, CA",
    description: "Join our data science team to build machine learning models and analyze large datasets. Experience with Python, pandas, scikit-learn required.",
    salary_min: 130000,
    salary_max: 200000,
    experience_level: "mid",
    remote_type: "hybrid",
    job_type: "full_time",
    skills_required: ["Python", "Machine Learning", "Pandas", "Scikit-learn", "SQL"],
    source_url: "https://example.com/job2",
    source_platform: "Indeed",
    created_at: "2024-01-14T15:30:00Z",
    updated_at: "2024-01-14T15:30:00Z",
    is_active: true,
    ai_processed: true,
    ai_generated_summary: "Data scientist role focusing on ML and data analysis with Python."
  },
  {
    id: 3,
    title: "Frontend Engineer",
    company: "StartupXYZ",
    location: "Remote",
    description: "Looking for a frontend engineer to build beautiful user interfaces. Experience with modern JavaScript frameworks preferred.",
    salary_min: 80000,
    salary_max: 120000,
    experience_level: "mid",
    remote_type: "fully_remote",
    job_type: "full_time",
    skills_required: ["JavaScript", "React", "Vue.js", "CSS", "UI/UX"],
    source_url: "https://example.com/job3",
    source_platform: "AngelList",
    created_at: "2024-01-13T09:15:00Z",
    updated_at: "2024-01-13T09:15:00Z",
    is_active: true,
    ai_processed: false,
    ai_generated_summary: "Frontend engineering position with focus on modern web technologies."
  }
];

// Demo function to showcase search capabilities
export function demonstrateIntelligentSearch() {
  console.log("🔍 Intelligent Search Algorithm Demo");
  console.log("=====================================");

  const testQueries = [
    "React developer",
    "Python data science",
    "frontend web development",
    "remote work",
    "machine learning engineer",
    "JavaScript frameworks"
  ];

  testQueries.forEach(query => {
    console.log(`\n📝 Query: "${query}"`);
    const results = intelligentSearch(sampleJobs, query);
    console.log(`📊 Found ${results.length} relevant jobs:`);
    
    results.forEach((job, index) => {
      console.log(`  ${index + 1}. ${job.title} at ${job.company}`);
      console.log(`     Skills: ${job.skills_required?.join(', ')}`);
    });
  });

  console.log("\n✨ Key Features:");
  console.log("• Cosine similarity for semantic matching");
  console.log("• TF-IDF for term importance weighting");
  console.log("• Text preprocessing and stemming");
  console.log("• Stop word removal");
  console.log("• Exact match boosting");
  console.log("• Skill-based relevance scoring");
  console.log("• Recency boosting for fresh jobs");
}

// Example usage patterns
export const searchExamples = {
  // These queries will find relevant jobs even without exact keyword matches
  semanticQueries: [
    "frontend development", // Will match "Frontend Engineer" and "React Developer"
    "data analysis", // Will match "Python Data Scientist"
    "web development", // Will match frontend positions
    "ML engineer", // Will match "Python Data Scientist"
    "remote position", // Will match all remote jobs
    "senior role", // Will match "Senior React Developer"
  ],
  
  // These show the algorithm's understanding of tech stacks
  techStackQueries: [
    "React TypeScript", // Will prioritize React + TypeScript jobs
    "Python pandas", // Will find data science roles
    "JavaScript frameworks", // Will match frontend positions
    "machine learning", // Will find ML/data science roles
  ],
  
  // These demonstrate skill-based matching
  skillQueries: [
    "CSS HTML", // Will find frontend positions
    "SQL database", // Will find data roles
    "UI UX design", // Will match frontend with design skills
  ]
};
