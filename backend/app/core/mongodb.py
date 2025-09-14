"""
MongoDB configuration and connection management for real-time operations.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.connection_string = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
        self.database_name = os.getenv('MONGODB_DATABASE', 'remote_jobs_platform')
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.database = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.database_name}")
            
            # Create indexes for better performance
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Jobs collection indexes
            jobs_collection = self.database.jobs
            
            # Text search index for job search
            await jobs_collection.create_index([
                ("title", "text"),
                ("company", "text"),
                ("description", "text"),
                ("skills_required", "text")
            ])
            
            # Compound indexes for filtering
            await jobs_collection.create_index([
                ("remote_type", 1),
                ("experience_level", 1),
                ("salary_min", 1),
                ("created_at", -1)
            ])
            
            # Unique index on source_url
            await jobs_collection.create_index("source_url", unique=True)
            
            # TTL index for automatic cleanup of old jobs
            await jobs_collection.create_index("created_at", expireAfterSeconds=90*24*60*60)  # 90 days
            
            # Job snapshots collection indexes
            snapshots_collection = self.database.job_snapshots
            await snapshots_collection.create_index([
                ("snapshot_date", -1),
                ("job_id", 1)
            ])
            
            # Analytics collection indexes
            analytics_collection = self.database.analytics
            await analytics_collection.create_index([
                ("date", -1),
                ("metric_type", 1)
            ])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        if not self.database:
            raise Exception("MongoDB not connected")
        return self.database[collection_name]

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()

async def get_mongodb():
    """Dependency to get MongoDB database"""
    if not mongodb_manager.database:
        await mongodb_manager.connect()
    return mongodb_manager.database
