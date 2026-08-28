"""
backend/app/schemas/profile.py
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    college: Optional[str] = Field(default=None, max_length=255)
    degree: Optional[str] = Field(default=None, max_length=255)
    year: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)
    bio: Optional[str] = None


class InterestsRequest(BaseModel):
    domains: List[
        Literal["AI", "Web Development", "Cyber Security", "Blockchain", "UI/UX", "Cloud", "Mobile", "Data Science"]
    ]


class SkillAssessmentRequest(BaseModel):
    skill_level: Literal["beginner", "intermediate", "advanced"]
    known_languages: Optional[str] = None
    time_available: Optional[str] = Field(default=None, max_length=50)
    career_goal: Optional[str] = None


class ProfileResponse(BaseModel):
    photo_url: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    year: Optional[str] = None
    country: Optional[str] = None
    bio: Optional[str] = None
    skill_level: Optional[str] = None
    known_languages: Optional[str] = None
    time_available: Optional[str] = None
    career_goal: Optional[str] = None

    class Config:
        from_attributes = True


class PhotoUploadUrlResponse(BaseModel):
    upload_url: str
    file_url: str
