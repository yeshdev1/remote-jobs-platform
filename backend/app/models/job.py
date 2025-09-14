from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="USD")
    salary_period = Column(String(20), default="yearly")  # yearly, monthly, hourly
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    job_type = Column(String(50), nullable=True)  # full-time, part-time, contract
    experience_level = Column(String(50), nullable=True)  # entry, mid, senior, lead
    remote_type = Column(String(50), default="remote")  # Only remote jobs accepted
    source_url = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)  # Direct job URL
    source_platform = Column(String(100), nullable=False)  # linkedin, indeed, etc.
    posted_date = Column(DateTime, nullable=True)
    application_url = Column(String(500), nullable=True)
    company_logo = Column(String(500), nullable=True)
    company_description = Column(Text, nullable=True)
    company_size = Column(String(100), nullable=True)
    company_industry = Column(String(100), nullable=True)
    skills_required = Column(JSON, nullable=True)  # List of required skills
    ai_generated_summary = Column(Text, nullable=True)
    ai_processed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Job(title='{self.title}', company='{self.company}', salary='{self.salary_min}-{self.salary_max} {self.salary_currency}')>"
