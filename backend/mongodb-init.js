// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the application database
db = db.getSiblingDB('remote_jobs_platform');

// Create collections with validation
db.createCollection('jobs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'company', 'source_url', 'source_platform'],
      properties: {
        title: { bsonType: 'string' },
        company: { bsonType: 'string' },
        source_url: { bsonType: 'string' },
        source_platform: { bsonType: 'string' },
        remote_type: { bsonType: 'string', enum: ['remote'] },
        is_active: { bsonType: 'bool' },
        created_at: { bsonType: 'date' },
        updated_at: { bsonType: 'date' }
      }
    }
  }
});

db.createCollection('job_snapshots');
db.createCollection('analytics');
db.createCollection('search_queries');

// Create indexes for optimal performance
db.jobs.createIndex({ "title": "text", "company": "text", "description": "text", "skills_required": "text" });
db.jobs.createIndex({ "remote_type": 1, "experience_level": 1, "salary_min": 1, "created_at": -1 });
db.jobs.createIndex({ "source_url": 1 }, { unique: true });
db.jobs.createIndex({ "created_at": 1 }, { expireAfterSeconds: 90 * 24 * 60 * 60 }); // 90 days TTL

db.job_snapshots.createIndex({ "snapshot_date": -1, "job_id": 1 });
db.analytics.createIndex({ "date": -1, "metric_type": 1 });
db.search_queries.createIndex({ "timestamp": -1 });

// Create a sample document to test the setup
db.jobs.insertOne({
  title: "Sample Remote Software Engineer",
  company: "Sample Company",
  location: "Remote",
  salary_min: 80000,
  salary_max: 120000,
  salary_currency: "USD",
  salary_period: "yearly",
  description: "This is a sample remote job posting for testing purposes.",
  requirements: "Experience with modern web technologies",
  benefits: "Health insurance, flexible hours, remote work",
  job_type: "full_time",
  experience_level: "mid",
  remote_type: "remote",
  source_url: "https://example.com/job/sample",
  source_platform: "sample",
  posted_date: new Date(),
  application_url: "https://example.com/apply",
  skills_required: ["JavaScript", "React", "Node.js"],
  ai_processed: true,
  is_active: true,
  created_at: new Date(),
  updated_at: new Date(),
  tags: ["level_mid", "type_full_time", "skill_javascript", "skill_react", "ai_verified"],
  metadata: {
    source: "initialization",
    sync_date: new Date().toISOString()
  }
});

print('MongoDB initialization completed successfully!');
print('Collections created: jobs, job_snapshots, analytics, search_queries');
print('Indexes created for optimal performance');
print('Sample job document inserted for testing');
