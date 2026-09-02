"""
backend/app/api/v1/learning.py
REPLACES the Phase 2 stub.
Pipeline: Quiz -> Coding Challenge -> Project -> AI Evaluation -> Mentor
Approval -> Skill Badge.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.learning import (
    Quiz, QuizQuestion, QuizAttempt, Project, ProjectReview, SkillBadge, Skill,
)
from app.schemas.learning import (
    QuizQuestionResponse, QuizSubmitRequest, QuizResultResponse,
    ProjectSubmitRequest, ProjectResponse, ProjectReviewResponse,
    SkillBadgeResponse, MentorApprovalRequest,
)
from app.services.ai.code_review import review_project

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "learning", "status": "ok"}


# ---------- Quiz ----------

@router.get("/quizzes/{quiz_id}/questions", response_model=list[QuizQuestionResponse])
async def get_quiz_questions(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id))
    questions = result.scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail="Quiz not found or has no questions")
    return questions


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResultResponse)
async def submit_quiz(
    quiz_id: str,
    payload: QuizSubmitRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id))
    questions = result.scalars().all()
    if not questions:
        raise HTTPException(status_code=404, detail="Quiz not found")

    correct_count = 0
    for q in questions:
        submitted = payload.answers.get(q.id, "").strip().lower()
        if submitted == q.correct_answer.strip().lower():
            correct_count += 1

    total = len(questions)
    score = round((correct_count / total) * 100) if total else 0
    passed = score >= 70  # checkpoint threshold

    attempt = QuizAttempt(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=score,
        passed=passed,
    )
    db.add(attempt)
    await db.commit()

    return QuizResultResponse(score=score, passed=passed, total_questions=total, correct_count=correct_count)


# ---------- Project submission & AI review ----------

@router.post("/projects/submit", response_model=ProjectResponse, status_code=202)
async def submit_project(
    payload: ProjectSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    project = Project(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        module_id=payload.module_id,
        github_url=payload.github_url,
        live_url=payload.live_url,
        description=payload.description,
        status="submitted",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    async def _run_ai_review():
        async with AsyncSessionLocal() as bg_db:
            result = await bg_db.execute(select(Project).where(Project.id == project.id))
            proj = result.scalar_one_or_none()
            if proj is None:
                return
            review_data = await review_project(proj.description or "", proj.github_url or "", proj.id)
            review = ProjectReview(
                id=str(uuid.uuid4()),
                project_id=proj.id,
                reviewer_type="ai",
                reviewer_id=None,
                feedback=review_data.get("summary") or review_data.get("error"),
                score=review_data.get("score"),
            )
            bg_db.add(review)
            proj.status = "ai_reviewed" if review_data.get("score") is not None else "submitted"
            await bg_db.commit()

    background_tasks.add_task(_run_ai_review)
    return project


@router.get("/projects/{project_id}/reviews", response_model=list[ProjectReviewResponse])
async def get_project_reviews(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ProjectReview).where(ProjectReview.project_id == project_id))
    return result.scalars().all()


# ---------- Mentor approval -> Skill Badge ----------

@router.post("/projects/{project_id}/mentor-review", response_model=ProjectReviewResponse)
async def mentor_review_project(
    project_id: str,
    payload: MentorApprovalRequest,
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    review = ProjectReview(
        id=str(uuid.uuid4()),
        project_id=project_id,
        reviewer_type="mentor",
        reviewer_id=current_user.id,
        feedback=payload.feedback,
        score=payload.score,
    )
    db.add(review)
    project.status = "mentor_approved" if payload.approved else "rejected"
    await db.commit()
    await db.refresh(review)
    return review


@router.post("/skills/{skill_id}/badge", response_model=SkillBadgeResponse)
async def award_skill_badge(
    skill_id: str,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    skill_result = await db.execute(select(Skill).where(Skill.id == skill_id))
    if skill_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    existing = await db.execute(
        select(SkillBadge).where(SkillBadge.user_id == current_user.id, SkillBadge.skill_id == skill_id)
    )
    badge = existing.scalar_one_or_none()
    if badge is None:
        badge = SkillBadge(id=str(uuid.uuid4()), user_id=current_user.id, skill_id=skill_id, status="verified")
        db.add(badge)
    else:
        badge.status = "verified"
    await db.commit()
    await db.refresh(badge)
    return badge


@router.get("/skills/my-badges", response_model=list[SkillBadgeResponse])
async def get_my_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SkillBadge).where(SkillBadge.user_id == current_user.id))
    return result.scalars().all()
