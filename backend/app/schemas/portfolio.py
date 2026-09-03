"""
backend/app/schemas/portfolio.py
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class PortfolioItemResponse(BaseModel):
    id: str
    source_type: str
    source_id: str
    title: str
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    screenshot_urls: Optional[str] = None
    rating: Optional[float] = None

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    id: str
    resume_url: Optional[str] = None
    items: List[PortfolioItemResponse] = []

    class Config:
        from_attributes = True


class PortfolioItemUpdateRequest(BaseModel):
    tech_stack: Optional[str] = None
    screenshot_urls: Optional[List[str]] = None


class ResumeGenerateRequest(BaseModel):
    template: str = Field(default="standard", pattern="^(standard|modern|minimal)$")


class ResumeImproveRequest(BaseModel):
    section_text: str = Field(min_length=1)


class ResumeImproveResponse(BaseModel):
    improved_text: str


class ResumeResponse(BaseModel):
    resume_url: Optional[str] = None
    content_preview: Optional[str] = None
