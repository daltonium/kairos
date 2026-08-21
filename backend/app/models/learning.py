"""
backend/app/models/learning.py
Skills, roadmaps, learning modules, quizzes, projects, badges.
Used by Phases 5-6 (AI Roadmap Engine, Learning & Skill Verification).
"""
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin


class Skill(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class UserSkill(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "user_skills"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id"))
    proficiency_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Roadmap(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "roadmaps"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    interest: Mapped[str] = mapped_column(String(100))
    skill_level: Mapped[str] = mapped_column(String(20))
    career_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="generating")  # generating | ready | failed
    raw_ai_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # cached JSON from OpenRouter

    items: Mapped[list["RoadmapItem"]] = relationship(back_populates="roadmap")


class RoadmapItem(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "roadmap_items"

    roadmap_id: Mapped[str] = mapped_column(String(36), ForeignKey("roadmaps.id"))
    week_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    prerequisite_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    roadmap: Mapped["Roadmap"] = relationship(back_populates="items")


class LearningModule(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "learning_modules"

    roadmap_item_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("roadmap_items.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reading_material: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ModuleProgress(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "module_progress"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_modules.id"))
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started|in_progress|completed


class Quiz(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quizzes"

    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_modules.id"))
    title: Mapped[str] = mapped_column(String(255))

    questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="quiz")


class QuizQuestion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quiz_questions"

    quiz_id: Mapped[str] = mapped_column(String(36), ForeignKey("quizzes.id"))
    question_type: Mapped[str] = mapped_column(String(20))  # mcq | code | fill_blank
    question_text: Mapped[str] = mapped_column(Text)
    options: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded
    correct_answer: Mapped[str] = mapped_column(Text)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")


class QuizAttempt(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quiz_attempts"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    quiz_id: Mapped[str] = mapped_column(String(36), ForeignKey("quizzes.id"))
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)


class Project(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "projects"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    module_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("learning_modules.id"), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    zip_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # S3 key
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="submitted")  # submitted|ai_reviewed|mentor_approved|rejected

    reviews: Mapped[list["ProjectReview"]] = relationship(back_populates="project")


class ProjectReview(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "project_reviews"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"))
    reviewer_type: Mapped[str] = mapped_column(String(10))  # ai | mentor
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # null if AI
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="reviews")


class SkillBadge(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "skill_badges"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    skill_id: Mapped[str] = mapped_column(String(36), ForeignKey("skills.id"))
    status: Mapped[str] = mapped_column(String(20), default="locked")  # locked|pending|verified
