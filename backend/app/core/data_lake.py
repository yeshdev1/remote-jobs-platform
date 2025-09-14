"""
Data Lake integration for daily snapshots and analytics.
Supports AWS S3, MinIO, and local file system.
"""
import os
import json
import gzip
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

logger = logging.getLogger(__name__)

class DataLakeManager:
    def __init__(self):
        self.storage_type = os.getenv('DATA_LAKE_TYPE', 'local')  # 's3', 'minio', 'local'
        self.bucket_name = os.getenv('DATA_LAKE_BUCKET', 'remote-jobs-data')
        self.local_path = os.getenv('DATA_LAKE_LOCAL_PATH', './data_lake')
        
        # S3/MinIO configuration
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.s3_endpoint = os.getenv('S3_ENDPOINT_URL')  # For MinIO
        
        self.s3_client = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage client based on type"""
        if self.storage_type in ['s3', 'minio'] and S3_AVAILABLE:
            try:
                session = boto3.Session(
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key
                )
                
                if self.storage_type == 'minio' and self.s3_endpoint:
                    self.s3_client = session.client(
                        's3',
                        endpoint_url=self.s3_endpoint
                    )
                else:
                    self.s3_client = session.client('s3')
                
                # Create bucket if it doesn't exist
                self._ensure_bucket_exists()
                logger.info(f"Data lake initialized: {self.storage_type}")
                
            except Exception as e:
                logger.error(f"Failed to initialize {self.storage_type}: {e}")
                self.storage_type = 'local'
                self._initialize_local_storage()
        
        elif self.storage_type == 'local':
            self._initialize_local_storage()
    
    def _initialize_local_storage(self):
        """Initialize local file system storage"""
        Path(self.local_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Local data lake initialized: {self.local_path}")
    
    def _ensure_bucket_exists(self):
        """Ensure S3/MinIO bucket exists"""
        if self.s3_client:
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
            except ClientError:
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                except ClientError as e:
                    logger.error(f"Failed to create bucket: {e}")
    
    def _get_daily_path(self, data_type: str, target_date: date = None) -> str:
        """Generate daily path for data storage"""
        if target_date is None:
            target_date = date.today()
        
        year = target_date.year
        month = target_date.month
        day = target_date.day
        
        return f"{data_type}/year={year}/month={month:02d}/day={day:02d}"
    
    async def store_daily_snapshot(self, 
                                 data_type: str, 
                                 data: List[Dict[str, Any]], 
                                 target_date: date = None) -> str:
        """Store daily snapshot of data"""
        try:
            # Generate file path
            daily_path = self._get_daily_path(data_type, target_date)
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{data_type}_snapshot_{timestamp}.json.gz"
            file_path = f"{daily_path}/{filename}"
            
            # Prepare data
            snapshot_data = {
                "snapshot_date": target_date.isoformat() if target_date else date.today().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "data_type": data_type,
                "record_count": len(data),
                "data": data
            }
            
            # Compress and store
            json_data = json.dumps(snapshot_data, default=str)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            if self.storage_type in ['s3', 'minio'] and self.s3_client:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                    Body=compressed_data,
                    ContentType='application/gzip'
                )
            else:
                # Local storage
                local_file_path = Path(self.local_path) / file_path
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                local_file_path.write_bytes(compressed_data)
            
            logger.info(f"Daily snapshot stored: {file_path} ({len(data)} records)")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to store daily snapshot: {e}")
            raise
    
    async def retrieve_daily_snapshot(self, 
                                    data_type: str, 
                                    target_date: date) -> Optional[Dict[str, Any]]:
        """Retrieve daily snapshot"""
        try:
            daily_path = self._get_daily_path(data_type, target_date)
            
            if self.storage_type in ['s3', 'minio'] and self.s3_client:
                # List objects in the daily path
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=daily_path
                )
                
                if 'Contents' not in response:
                    return None
                
                # Get the most recent file
                latest_file = max(response['Contents'], key=lambda x: x['LastModified'])
                file_key = latest_file['Key']
                
                # Download and decompress
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
                compressed_data = response['Body'].read()
                
            else:
                # Local storage
                local_path = Path(self.local_path) / daily_path
                if not local_path.exists():
                    return None
                
                # Find the most recent file
                files = list(local_path.glob(f"{data_type}_snapshot_*.json.gz"))
                if not files:
                    return None
                
                latest_file = max(files, key=lambda x: x.stat().st_mtime)
                compressed_data = latest_file.read_bytes()
            
            # Decompress and parse
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            return json.loads(json_data)
            
        except Exception as e:
            logger.error(f"Failed to retrieve daily snapshot: {e}")
            return None
    
    async def store_analytics_data(self, 
                                 metric_type: str, 
                                 data: Dict[str, Any], 
                                 target_date: date = None) -> str:
        """Store analytics data"""
        try:
            daily_path = self._get_daily_path("analytics", target_date)
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{metric_type}_{timestamp}.json"
            file_path = f"{daily_path}/{filename}"
            
            analytics_data = {
                "metric_type": metric_type,
                "date": target_date.isoformat() if target_date else date.today().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "data": data
            }
            
            json_data = json.dumps(analytics_data, default=str, indent=2)
            
            if self.storage_type in ['s3', 'minio'] and self.s3_client:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_path,
                    Body=json_data,
                    ContentType='application/json'
                )
            else:
                # Local storage
                local_file_path = Path(self.local_path) / file_path
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                local_file_path.write_text(json_data)
            
            logger.info(f"Analytics data stored: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to store analytics data: {e}")
            raise
    
    async def list_snapshots(self, 
                           data_type: str, 
                           start_date: date, 
                           end_date: date) -> List[str]:
        """List available snapshots for a date range"""
        try:
            snapshots = []
            
            if self.storage_type in ['s3', 'minio'] and self.s3_client:
                # List objects with date range
                for current_date in self._date_range(start_date, end_date):
                    daily_path = self._get_daily_path(data_type, current_date)
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=daily_path
                    )
                    
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            snapshots.append(obj['Key'])
            
            else:
                # Local storage
                for current_date in self._date_range(start_date, end_date):
                    daily_path = self._get_daily_path(data_type, current_date)
                    local_path = Path(self.local_path) / daily_path
                    
                    if local_path.exists():
                        for file_path in local_path.glob("*"):
                            snapshots.append(str(file_path.relative_to(Path(self.local_path))))
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
            return []
    
    def _date_range(self, start_date: date, end_date: date):
        """Generate date range"""
        current = start_date
        while current <= end_date:
            yield current
            current = date(current.year, current.month, current.day + 1)

# Global data lake manager
data_lake_manager = DataLakeManager()
