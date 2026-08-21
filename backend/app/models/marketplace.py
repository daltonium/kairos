"""
backend/app/models/marketplace.py
Gigs, mentors, portfolios, companies, jobs, payments, notifications.
Used by Phases 7-10.
"""
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, Boolean, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin


class GigListing(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "gig_listings"

    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    required_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # comma/JSON list of skill ids
    deadline: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open|in_progress|completed|cancelled


class GigApplication(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "gig_applications"

    gig_id: Mapped[str] = mapped_column(String(36), ForeignKey("gig_listings.id"))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    proposal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|accepted|rejected|completed


class GigSubmission(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "gig_submissions"

    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("gig_applications.id"))
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class GigReview(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "gig_reviews"

    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("gig_submissions.id"))
    reviewer_type: Mapped[str] = mapped_column(String(10))  # client | mentor
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Mentor(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "mentors"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)


class MentorSession(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "mentor_sessions"

    mentor_id: Mapped[str] = mapped_column(String(36), ForeignKey("mentors.id"))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    scheduled_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="booked")  # booked|completed|cancelled


class Portfolio(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "portfolios"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    resume_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    items: Mapped[list["PortfolioItem"]] = relationship(back_populates="portfolio")


class PortfolioItem(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "portfolio_items"

    portfolio_id: Mapped[str] = mapped_column(String(36), ForeignKey("portfolios.id"))
    source_type: Mapped[str] = mapped_column(String(20))  # gig | project
    source_id: Mapped[str] = mapped_column(String(36))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_urls: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of S3 urls
    rating: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="items")


class Company(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "companies"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    company_name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class JobListing(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "job_listings"

    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    deadline: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    experience_required: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|closed


class JobApplication(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "job_applications"

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("job_listings.id"))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # OpenRouter-generated
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="applied")  # applied|shortlisted|rejected|hired


class Wallet(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "wallets"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    pending_balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0)


class Payment(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "payments"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    gig_application_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("gig_applications.id"), nullable=True)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="created")  # created|captured|failed


class Notification(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    category: Mapped[str] = mapped_column(String(20))  # learning|marketplace|payments|messages|system
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
