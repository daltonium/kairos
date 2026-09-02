"""
backend/app/schemas/learning.py
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class QuizQuestionResponse(BaseModel):
    id: str
    question_type: str
    question_text: str
    options: Optional[str] = None

    class Config:
        from_attributes = True


class QuizSubmitRequest(BaseModel):
    answers: dict[str, str]  # {question_id: submitted_answer}


class QuizResultResponse(BaseModel):
    score: int
    passed: bool
    total_questions: int
    correct_count: int


class ProjectSubmitRequest(BaseModel):
    github_url: Optional[str] = Field(default=None, max_length=500)
    live_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    module_id: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    description: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ProjectReviewResponse(BaseModel):
    id: str
    reviewer_type: str
    feedback: Optional[str] = None
    score: Optional[int] = None

    class Config:
        from_attributes = True


class SkillBadgeResponse(BaseModel):
    id: str
    skill_id: str
    status: str

    class Config:
        from_attributes = True


class MentorApprovalRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
