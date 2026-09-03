"""
backend/app/api/v1/gigs.py
REPLACES the Phase 2 stub.
Pipeline: Verified Skill -> Eligible Gigs -> Apply -> Client Selects ->
Work Submission -> Mentor Review -> Client Approval. (Payment = Phase 10)
"""
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.learning import SkillBadge
from app.models.marketplace import GigListing, GigApplication, GigSubmission, GigReview
from app.schemas.gigs import (
    GigCreateRequest, GigResponse, GigApplicationRequest, GigApplicationResponse,
    GigApplicationDecisionRequest, GigSubmissionRequest, GigSubmissionResponse,
    GigReviewRequest, GigReviewResponse,
)

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "gigs", "status": "ok"}


# ---------- Gig listing (client-side creation) ----------

@router.post("/", response_model=GigResponse, status_code=201)
async def create_gig(
    payload: GigCreateRequest,
    current_user: User = Depends(get_current_user),  # any authenticated role can act as a client for now
    db: AsyncSession = Depends(get_db),
):
    gig = GigListing(
        id=str(uuid.uuid4()),
        client_id=current_user.id,
        title=payload.title,
        description=payload.description,
        budget=payload.budget,
        required_skills=json.dumps(payload.required_skill_ids),
        deadline=payload.deadline,
        difficulty=payload.difficulty,
        status="open",
    )
    db.add(gig)
    await db.commit()
    await db.refresh(gig)
    return gig


# ---------- Skill-gated marketplace browsing ----------

@router.get("/", response_model=list[GigResponse])
async def list_eligible_gigs(
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """Only returns gigs where the student holds ALL required verified skill badges."""
    badges_result = await db.execute(
        select(SkillBadge.skill_id).where(SkillBadge.user_id == current_user.id, SkillBadge.status == "verified")
    )
    verified_skill_ids = {row[0] for row in badges_result.all()}

    gigs_result = await db.execute(select(GigListing).where(GigListing.status == "open"))
    all_gigs = gigs_result.scalars().all()

    eligible = []
    for gig in all_gigs:
        required = set(json.loads(gig.required_skills)) if gig.required_skills else set()
        if required.issubset(verified_skill_ids):
            eligible.append(gig)
    return eligible


@router.get("/{gig_id}", response_model=GigResponse)
async def get_gig_details(
    gig_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GigListing).where(GigListing.id == gig_id))
    gig = result.scalar_one_or_none()
    if gig is None:
        raise HTTPException(status_code=404, detail="Gig not found")
    return gig


# ---------- Apply ----------

@router.post("/{gig_id}/apply", response_model=GigApplicationResponse, status_code=201)
async def apply_to_gig(
    gig_id: str,
    payload: GigApplicationRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    gig_result = await db.execute(select(GigListing).where(GigListing.id == gig_id))
    gig = gig_result.scalar_one_or_none()
    if gig is None:
        raise HTTPException(status_code=404, detail="Gig not found")
    if gig.status != "open":
        raise HTTPException(status_code=400, detail="Gig is not open for applications")

    existing = await db.execute(
        select(GigApplication).where(
            GigApplication.gig_id == gig_id, GigApplication.student_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already applied to this gig")

    application = GigApplication(
        id=str(uuid.uuid4()),
        gig_id=gig_id,
        student_id=current_user.id,
        proposal=payload.proposal,
        price=payload.price,
        status="pending",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/{gig_id}/applications", response_model=list[GigApplicationResponse])
async def list_gig_applications(
    gig_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gig_result = await db.execute(select(GigListing).where(GigListing.id == gig_id))
    gig = gig_result.scalar_one_or_none()
    if gig is None:
        raise HTTPException(status_code=404, detail="Gig not found")
    if gig.client_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only the gig's client can view applications")

    result = await db.execute(select(GigApplication).where(GigApplication.gig_id == gig_id))
    return result.scalars().all()


@router.get("/applications/mine", response_model=list[GigApplicationResponse])
async def my_applications(
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GigApplication).where(GigApplication.student_id == current_user.id))
    return result.scalars().all()


# ---------- Client selects ----------

@router.post("/applications/{application_id}/decision", response_model=GigApplicationResponse)
async def decide_application(
    application_id: str,
    payload: GigApplicationDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GigApplication).where(GigApplication.id == application_id))
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    gig_result = await db.execute(select(GigListing).where(GigListing.id == application.gig_id))
    gig = gig_result.scalar_one_or_none()
    if gig.client_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only the gig's client can decide on applications")

    application.status = "accepted" if payload.accept else "rejected"
    if payload.accept:
        gig.status = "in_progress"
    await db.commit()
    await db.refresh(application)
    return application


# ---------- Work submission ----------

@router.post("/applications/{application_id}/submit", response_model=GigSubmissionResponse, status_code=201)
async def submit_gig_work(
    application_id: str,
    payload: GigSubmissionRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GigApplication).where(GigApplication.id == application_id))
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if application.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your application")
    if application.status != "accepted":
        raise HTTPException(status_code=400, detail="Application must be accepted before submitting work")

    submission = GigSubmission(
        id=str(uuid.uuid4()),
        application_id=application_id,
        file_url=payload.file_url,
        github_url=payload.github_url,
        notes=payload.notes,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


# ---------- Mentor review + client approval ----------

@router.post("/submissions/{submission_id}/mentor-review", response_model=GigReviewResponse)
async def mentor_review_submission(
    submission_id: str,
    payload: GigReviewRequest,
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GigSubmission).where(GigSubmission.id == submission_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    review = GigReview(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        reviewer_type="mentor",
        reviewer_id=current_user.id,
        rating=payload.rating,
        feedback=payload.feedback,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.post("/submissions/{submission_id}/client-review", response_model=GigReviewResponse)
async def client_review_submission(
    submission_id: str,
    payload: GigReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub_result = await db.execute(select(GigSubmission).where(GigSubmission.id == submission_id))
    submission = sub_result.scalar_one_or_none()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    app_result = await db.execute(select(GigApplication).where(GigApplication.id == submission.application_id))
    application = app_result.scalar_one_or_none()
    gig_result = await db.execute(select(GigListing).where(GigListing.id == application.gig_id))
    gig = gig_result.scalar_one_or_none()

    if gig.client_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only the gig's client can approve this submission")

    review = GigReview(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        reviewer_type="client",
        reviewer_id=current_user.id,
        rating=payload.rating,
        feedback=payload.feedback,
    )
    db.add(review)

    if payload.approve:
        application.status = "completed"
        gig.status = "completed"
        from app.services.portfolio import add_portfolio_item
        await add_portfolio_item(
            db, application.student_id, "gig", gig.id, gig.title,
            description=gig.description, rating=float(payload.rating),
        )
        # Phase 10 (Payments) hooks in here: trigger Razorpay payout on approval.

    await db.commit()
    await db.refresh(review)
    return review
