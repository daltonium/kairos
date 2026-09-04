"""
backend/app/schemas/mentors_jobs.py
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MentorProfileRequest(BaseModel):
    domain: Optional[str] = Field(default=None, max_length=100)
    experience_years: Optional[int] = Field(default=None, ge=0)
    is_available: bool = True


class MentorResponse(BaseModel):
    id: str
    user_id: str
    domain: Optional[str] = None
    experience_years: Optional[int] = None
    rating: Optional[float] = None
    is_available: bool

    class Config:
        from_attributes = True


class MentorBookingRequest(BaseModel):
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=180)
    message: Optional[str] = None


class MentorSessionResponse(BaseModel):
    id: str
    mentor_id: str
    student_id: str
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    message: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class MentorDashboardResponse(BaseModel):
    total_students: int
    pending_reviews: int
    upcoming_sessions: int
    average_rating: Optional[float] = None


# ---------- Company / Jobs ----------

class CompanyProfileRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=500)


class CompanyResponse(BaseModel):
    id: str
    company_name: str
    industry: Optional[str] = None
    website: Optional[str] = None

    class Config:
        from_attributes = True


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    required_skills: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    deadline: Optional[datetime] = None
    experience_required: Optional[str] = Field(default=None, max_length=50)


class JobResponse(BaseModel):
    id: str
    company_id: str
    title: str
    description: Optional[str] = None
    required_skills: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    experience_required: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class JobApplyRequest(BaseModel):
    pass  # student applies with no body -- their profile/portfolio is looked up server-side


class JobApplicationResponse(BaseModel):
    id: str
    job_id: str
    student_id: str
    ai_summary: Optional[str] = None
    score: Optional[int] = None
    status: str

    class Config:
        from_attributes = True


class JobApplicationDecisionRequest(BaseModel):
    status: str = Field(pattern="^(shortlisted|rejected|hired)$")


class HiringAnalyticsResponse(BaseModel):
    total_jobs: int
    total_applicants: int
    shortlisted: int
    hired: int
    rejected: int
