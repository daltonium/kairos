"""
backend/app/api/v1/companies.py
Merged Phase 8 (portfolio+resume) + new company profile, job posting,
applicant pipeline with AI summaries.
"""
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.marketplace import Company, JobListing, JobApplication, Portfolio, PortfolioItem
from app.models.learning import SkillBadge, Skill
from app.schemas.mentors_jobs import (
    CompanyProfileRequest, CompanyResponse, JobCreateRequest, JobResponse,
    JobApplicationResponse, JobApplicationDecisionRequest, HiringAnalyticsResponse,
)
from app.schemas.portfolio import (
    PortfolioResponse, PortfolioItemUpdateRequest, ResumeGenerateRequest,
    ResumeImproveRequest, ResumeImproveResponse, ResumeResponse,
)
from app.services.ai.applicant_summary import generate_applicant_summary
from app.services.portfolio import _get_or_create_portfolio
from app.services.ai.resume import improve_resume_section


router = APIRouter()


# ---------- Ping ----------

@router.get("/ping")
async def ping():
    return {"router": "companies", "status": "ok"}


# ---------- Portfolio (Phase 8) ----------

@router.get("/portfolio/me", response_model=PortfolioResponse)
async def get_my_portfolio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await _get_or_create_portfolio(db, current_user.id)
    items_result = await db.execute(select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id))
    items = items_result.scalars().all()
    return PortfolioResponse(id=portfolio.id, resume_url=portfolio.resume_url, items=items)


@router.post("/portfolio/items/{item_id}", response_model=PortfolioItemUpdateRequest)
async def update_portfolio_item(
    item_id: str,
    payload: PortfolioItemUpdateRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PortfolioItem).where(PortfolioItem.id == item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    portfolio_result = await db.execute(select(Portfolio).where(Portfolio.id == item.portfolio_id))
    portfolio = portfolio_result.scalar_one_or_none()
    if portfolio.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your portfolio item")

    if payload.tech_stack is not None:
        item.tech_stack = payload.tech_stack
    if payload.screenshot_urls is not None:
        item.screenshot_urls = json.dumps(payload.screenshot_urls)

    await db.commit()
    return payload


# ---------- Resume (Phase 8) ----------

@router.post("/resume/generate", response_model=ResumeResponse)
async def generate_resume(
    payload: ResumeGenerateRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    """
    Builds a plain-text resume preview from portfolio items + profile.
    PDF export is intentionally simple (client-side print-to-PDF is
    recommended per the build plan) -- this endpoint returns structured
    text content the frontend renders and prints.
    """
    portfolio = await _get_or_create_portfolio(db, current_user.id)
    items_result = await db.execute(select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id))
    items = items_result.scalars().all()

    lines = [f"RESUME — {current_user.full_name}", f"Email: {current_user.email}", ""]
    lines.append("PROJECTS & GIGS")
    for item in items:
        lines.append(f"- {item.title}" + (f" (rating: {item.rating})" if item.rating else ""))
        if item.description:
            lines.append(f"  {item.description}")
        if item.tech_stack:
            lines.append(f"  Tech: {item.tech_stack}")

    content_preview = "\n".join(lines)
    return ResumeResponse(resume_url=portfolio.resume_url, content_preview=content_preview)


@router.post("/resume/ai-improve", response_model=ResumeImproveResponse)
async def ai_improve_resume_section(
    payload: ResumeImproveRequest,
    current_user: User = Depends(require_role("student")),
):
    improved = await improve_resume_section(payload.section_text)
    return ResumeImproveResponse(improved_text=improved)


# ---------- Company Profile, Jobs, Applicants (NEW) ----------

@router.post("/me/profile", response_model=CompanyResponse)
async def upsert_company_profile(
    payload: CompanyProfileRequest,
    current_user: User = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.user_id == current_user.id))
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(id=str(uuid.uuid4()), user_id=current_user.id, company_name=payload.company_name)
        db.add(company)

    company.company_name = payload.company_name
    company.industry = payload.industry
    company.website = payload.website
    await db.commit()
    await db.refresh(company)
    return company


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    payload: JobCreateRequest,
    current_user: User = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    company_result = await db.execute(select(Company).where(Company.user_id == current_user.id))
    company = company_result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=400, detail="Set up your company profile first")

    job = JobListing(
        id=str(uuid.uuid4()),
        company_id=company.id,
        title=payload.title,
        description=payload.description,
        required_skills=payload.required_skills,
        budget=payload.budget,
        deadline=payload.deadline,
        experience_required=payload.experience_required,
        status="active",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/jobs", response_model=list[JobResponse])
async def list_active_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(JobListing).where(JobListing.status == "active"))
    return result.scalars().all()


@router.post("/jobs/{job_id}/apply", response_model=JobApplicationResponse, status_code=201)
async def apply_to_job(
    job_id: str,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    job_result = await db.execute(select(JobListing).where(JobListing.id == job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = await db.execute(
        select(JobApplication).where(JobApplication.job_id == job_id, JobApplication.student_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already applied to this job")

    application = JobApplication(
        id=str(uuid.uuid4()), job_id=job_id, student_id=current_user.id, status="applied",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/jobs/{job_id}/applicants", response_model=list[JobApplicationResponse])
async def list_applicants(
    job_id: str,
    current_user: User = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    job_result = await db.execute(select(JobListing).where(JobListing.id == job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    company_result = await db.execute(select(Company).where(Company.id == job.company_id))
    company = company_result.scalar_one_or_none()
    if company.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only this job's company can view applicants")

    result = await db.execute(select(JobApplication).where(JobApplication.job_id == job_id))
    return result.scalars().all()


@router.post("/applications/{application_id}/generate-summary", response_model=JobApplicationResponse)
async def generate_applicant_ai_summary(
    application_id: str,
    current_user: User = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    app_result = await db.execute(select(JobApplication).where(JobApplication.id == application_id))
    application = app_result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    student_result = await db.execute(select(User).where(User.id == application.student_id))
    student = student_result.scalar_one_or_none()

    badges_result = await db.execute(
        select(Skill.name).join(SkillBadge, SkillBadge.skill_id == Skill.id).where(
            SkillBadge.user_id == student.id, SkillBadge.status == "verified"
        )
    )
    skills = ", ".join(row[0] for row in badges_result.all())

    portfolio_result = await db.execute(select(Portfolio).where(Portfolio.user_id == student.id))
    portfolio = portfolio_result.scalar_one_or_none()
    portfolio_text = ""
    if portfolio:
        items_result = await db.execute(select(PortfolioItem).where(PortfolioItem.portfolio_id == portfolio.id))
        portfolio_text = "; ".join(item.title for item in items_result.scalars().all())

    summary = await generate_applicant_summary(
        application_id, student.full_name, skills, portfolio_text, student.profile.career_goal if student.profile else None
    )

    application.ai_summary = summary
    await db.commit()
    await db.refresh(application)
    return application


@router.post("/applications/{application_id}/decision", response_model=JobApplicationResponse)
async def decide_job_application(
    application_id: str,
    payload: JobApplicationDecisionRequest,
    current_user: User = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    app_result = await db.execute(select(JobApplication).where(JobApplication.id == application_id))
    application = app_result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    job_result = await db.execute(select(JobListing).where(JobListing.id == application.job_id))
    job = job_result.scalar_one_or_none()
    company_result = await db.execute(select(Company).where(Company.id == job.company_id))
    company = company_result.scalar_one_or_none()
    if company.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only this job's company can decide on applicants")

    application.status = payload.status
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/dashboard/analytics", response_model=HiringAnalyticsResponse)
async def hiring_analytics(
    current_user: User = Depends(require_role("company")),
    db: AsyncSession = Depends(get_db),
):
    company_result = await db.execute(select(Company).where(Company.user_id == current_user.id))
    company = company_result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Company profile not set up yet")

    jobs_result = await db.execute(select(JobListing.id).where(JobListing.company_id == company.id))
    job_ids = [row[0] for row in jobs_result.all()]

    if not job_ids:
        return HiringAnalyticsResponse(total_jobs=0, total_applicants=0, shortlisted=0, hired=0, rejected=0)

    total_applicants = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.job_id.in_(job_ids))
    )
    shortlisted = await db.execute(
        select(func.count(JobApplication.id)).where(
            JobApplication.job_id.in_(job_ids), JobApplication.status == "shortlisted"
        )
    )
    hired = await db.execute(
        select(func.count(JobApplication.id)).where(
            JobApplication.job_id.in_(job_ids), JobApplication.status == "hired"
        )
    )
    rejected = await db.execute(
        select(func.count(JobApplication.id)).where(
            JobApplication.job_id.in_(job_ids), JobApplication.status == "rejected"
        )
    )

    return HiringAnalyticsResponse(
        total_jobs=len(job_ids),
        total_applicants=total_applicants.scalar() or 0,
        shortlisted=shortlisted.scalar() or 0,
        hired=hired.scalar() or 0,
        rejected=rejected.scalar() or 0,
    )