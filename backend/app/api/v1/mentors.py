"""
backend/app/api/v1/mentors.py
REPLACES the Phase 2 stub. Mentor directory, booking, dashboard.
Mentor matching uses a simple weighted score (domain match + availability +
rating) rather than a true priority queue -- documented as an MVP
simplification per the build plan.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.marketplace import Mentor, MentorSession
from app.models.learning import ProjectReview
from app.schemas.mentors_jobs import (
    MentorProfileRequest, MentorResponse, MentorBookingRequest,
    MentorSessionResponse, MentorDashboardResponse,
)

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "mentors", "status": "ok"}


@router.post("/me/profile", response_model=MentorResponse)
async def upsert_mentor_profile(
    payload: MentorProfileRequest,
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mentor).where(Mentor.user_id == current_user.id))
    mentor = result.scalar_one_or_none()
    if mentor is None:
        mentor = Mentor(id=str(uuid.uuid4()), user_id=current_user.id)
        db.add(mentor)

    mentor.domain = payload.domain
    mentor.experience_years = payload.experience_years
    mentor.is_available = payload.is_available
    await db.commit()
    await db.refresh(mentor)
    return mentor


@router.get("/", response_model=list[MentorResponse])
async def list_mentors(
    domain: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Directory browse with simple domain filter + weighted ranking:
    available mentors first, then by rating descending, then by experience.
    This is the MVP stand-in for the concept doc's priority-queue matching --
    a real priority queue can replace the ORDER BY once usage data exists.
    """
    query = select(Mentor)
    if domain:
        query = query.where(Mentor.domain == domain)
    result = await db.execute(query)
    mentors = result.scalars().all()

    mentors_sorted = sorted(
        mentors,
        key=lambda m: (not m.is_available, -(m.rating or 0), -(m.experience_years or 0)),
    )
    return mentors_sorted


@router.get("/{mentor_id}", response_model=MentorResponse)
async def get_mentor_profile(
    mentor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Mentor).where(Mentor.id == mentor_id))
    mentor = result.scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="Mentor not found")
    return mentor


@router.post("/{mentor_id}/book", response_model=MentorSessionResponse, status_code=201)
async def book_mentor(
    mentor_id: str,
    payload: MentorBookingRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    mentor_result = await db.execute(select(Mentor).where(Mentor.id == mentor_id))
    mentor = mentor_result.scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="Mentor not found")
    if not mentor.is_available:
        raise HTTPException(status_code=400, detail="Mentor is not currently available")

    session = MentorSession(
        id=str(uuid.uuid4()),
        mentor_id=mentor_id,
        student_id=current_user.id,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        message=payload.message,
        status="booked",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/me/schedule", response_model=list[MentorSessionResponse])
async def get_my_schedule(
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db),
):
    mentor_result = await db.execute(select(Mentor).where(Mentor.user_id == current_user.id))
    mentor = mentor_result.scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="Mentor profile not set up yet")

    result = await db.execute(select(MentorSession).where(MentorSession.mentor_id == mentor.id))
    return result.scalars().all()


@router.get("/me/dashboard", response_model=MentorDashboardResponse)
async def get_mentor_dashboard(
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db),
):
    mentor_result = await db.execute(select(Mentor).where(Mentor.user_id == current_user.id))
    mentor = mentor_result.scalar_one_or_none()
    if mentor is None:
        raise HTTPException(status_code=404, detail="Mentor profile not set up yet")

    sessions_result = await db.execute(
        select(func.count(MentorSession.id)).where(
            MentorSession.mentor_id == mentor.id, MentorSession.status == "booked"
        )
    )
    upcoming_sessions = sessions_result.scalar() or 0

    students_result = await db.execute(
        select(func.count(func.distinct(MentorSession.student_id))).where(MentorSession.mentor_id == mentor.id)
    )
    total_students = students_result.scalar() or 0

    reviews_result = await db.execute(
        select(func.count(ProjectReview.id)).where(
            ProjectReview.reviewer_type == "mentor",
            ProjectReview.reviewer_id == current_user.id,
            ProjectReview.score.is_(None),
        )
    )
    pending_reviews = reviews_result.scalar() or 0

    return MentorDashboardResponse(
        total_students=total_students,
        pending_reviews=pending_reviews,
        upcoming_sessions=upcoming_sessions,
        average_rating=mentor.rating,
    )
