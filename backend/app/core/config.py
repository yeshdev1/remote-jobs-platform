from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Remote Jobs Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://remote_user:remote_password@localhost:5432/remote_jobs"
    POSTGRES_DB: str = "remote_jobs"
    POSTGRES_USER: str = "remote_user"
    POSTGRES_PASSWORD: str = "remote_password"
    
    # AI APIs
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # MongoDB
    MONGODB_URL: Optional[str] = None
    MONGODB_DATABASE: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Scraping
    SCRAPER_DELAY: int = 2
    MAX_JOBS_PER_UPDATE: int = 1000
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Job Sources
    LINKEDIN_SCRAPE_ENABLED: bool = True
    INDEED_SCRAPE_ENABLED: bool = True
    REMOTE_CO_SCRAPE_ENABLED: bool = True
    WEWORKREMOTELY_SCRAPE_ENABLED: bool = True
    STACKOVERFLOW_SCRAPE_ENABLED: bool = True
    
    # Salary Filtering
    MIN_USD_SALARY: int = 50000
    MAX_USD_SALARY: int = 500000
    CURRENCY_FILTERS: List[str] = ["USD", "US$", "$", "dollars"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
