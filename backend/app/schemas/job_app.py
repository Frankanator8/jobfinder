"""
Schemas for job application data
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JobCategory(str, Enum):
    """Predefined job categories for filtering and personalisation."""
    SOFTWARE_ENGINEERING = "software_engineering"
    DATA_SCIENCE = "data_science"
    FINANCE = "finance"
    MARKETING = "marketing"
    DESIGN = "design"
    HEALTHCARE = "healthcare"
    SALES = "sales"
    OPERATIONS = "operations"
    EDUCATION = "education"
    LEGAL = "legal"
    HUMAN_RESOURCES = "human_resources"
    CUSTOMER_SERVICE = "customer_service"
    OTHER = "other"


class JobApplication(BaseModel):
    """Job application data structure."""
    application_id: str = Field(..., description="Unique identifier for the job application")
    job_url: str = Field(..., description="URL of the job posting")
    job_url_direct: Optional[str] = Field(None, description="Direct application URL (bypasses aggregator)")
    company_name: str = Field(..., description="Name of the company")
    position_title: str = Field(..., description="Title of the position")
    work_type: str = Field(..., description="Is remote?")
    location: Optional[str] = Field(None, description="Job location")
    job_type: str = Field(..., description="Type of job (full-time, part-time, contract)")
    date_posted: Optional[datetime] = Field(None, description="Date when the job was posted")
    compensation: str = Field(..., description="Compensation information")
    logo: str = Field(..., description="Company logo URL or path")
    description: str = Field(..., description="Description of the job application")
    category: Optional[str] = Field(None, description="Job category from JobCategory enum")


class JobApplicationCreate(BaseModel):
    """Schema for creating a new job application"""
    job_url: str = Field(..., description="URL of the job posting")
    job_url_direct: Optional[str] = Field(None, description="Direct application URL (bypasses aggregator)")
    company_name: str = Field(..., description="Name of the company")
    position_title: str = Field(..., description="Title of the position")
    work_type: str = Field(..., description="Type of work (remote, hybrid, on-site)")
    location: Optional[str] = Field(None, description="Job location")
    job_type: str = Field(..., description="Type of job (full-time, part-time, contract)")
    date_posted: Optional[datetime] = Field(None, description="Date when the job was posted")
    compensation: str = Field(..., description="Compensation information")
    logo: str = Field(..., description="Company logo URL or path")
    description: str = Field(..., description="Description of the job application")
    category: Optional[str] = Field(None, description="Job category from JobCategory enum")


# 67
class JobApplicationUpdate(BaseModel):
    """Schema for updating a job application"""
    job_url: Optional[str] = Field(None, description="URL of the job posting")
    job_url_direct: Optional[str] = Field(None, description="Direct application URL (bypasses aggregator)")
    company_name: Optional[str] = Field(None, description="Name of the company")
    position_title: Optional[str] = Field(None, description="Title of the position")
    work_type: Optional[str] = Field(None, description="Type of work (remote, hybrid, on-site)")
    location: Optional[str] = Field(None, description="Job location")
    job_type: Optional[str] = Field(None, description="Type of job (full-time, part-time, contract)")
    date_posted: Optional[datetime] = Field(None, description="Date when the job was posted")
    compensation: Optional[str] = Field(None, description="Compensation information")
    logo: Optional[str] = Field(None, description="Company logo URL or path")
    description: str = Field(..., description="Description of the job application")
    category: Optional[str] = Field(None, description="Job category from JobCategory enum")

