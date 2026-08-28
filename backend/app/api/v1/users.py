"""
backend/app/api/v1/users.py
REPLACES the Phase 2 stub. Onboarding: profile, career interests, skill assessment.
All routes require a logged-in user (any role can hit /me; onboarding-specific
routes are student-gated per the Kairos onboarding flow).
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User, Profile, UserSkillInterest
from app.schemas.profile import (
    ProfileUpdateRequest, InterestsRequest, SkillAssessmentRequest,
    ProfileResponse, PhotoUploadUrlResponse,
)
from app.services.storage import generate_upload_url

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "users", "status": "ok"}


async def _get_or_create_profile(db: AsyncSession, user_id: str) -> Profile:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = Profile(id=str(uuid.uuid4()), user_id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("/me/profile", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user.id)
    return profile


@router.post("/me/profile", response_model=ProfileResponse)
async def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/me/profile/photo-upload-url", response_model=PhotoUploadUrlResponse)
async def get_photo_upload_url(current_user: User = Depends(get_current_user)):
    urls = generate_upload_url(current_user.id, file_extension="jpg")
    return urls


@router.post("/me/profile/photo-confirm", response_model=ProfileResponse)
async def confirm_photo_upload(
    file_url: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user.id)
    profile.photo_url = file_url
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/me/interests", status_code=204)
async def set_my_interests(
    payload: InterestsRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(UserSkillInterest).where(UserSkillInterest.user_id == current_user.id))
    for domain in payload.domains:
        db.add(UserSkillInterest(id=str(uuid.uuid4()), user_id=current_user.id, domain=domain))
    await db.commit()


@router.get("/me/interests")
async def get_my_interests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserSkillInterest).where(UserSkillInterest.user_id == current_user.id))
    return [row.domain for row in result.scalars().all()]


@router.post("/me/skill-assessment", response_model=ProfileResponse)
async def submit_skill_assessment(
    payload: SkillAssessmentRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user.id)
    profile.skill_level = payload.skill_level
    profile.known_languages = payload.known_languages
    profile.time_available = payload.time_available
    profile.career_goal = payload.career_goal
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/me", response_model=None)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
    }
