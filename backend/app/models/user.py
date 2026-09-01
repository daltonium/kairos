"""
backend/app/models/user.py
User, Profile, and career-interest models. Used by Phases 2-4 (auth, onboarding).
"""
from typing import Optional
from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.db.base import Base, UUIDPKMixin, TimestampMixin



class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"


    full_name: Mapped[str] = mapped_column(String(150))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(20))  # student | mentor | company | admin
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


    profile: Mapped[Optional["Profile"]] = relationship(back_populates="user", uselist=False)
    interests: Mapped[list["UserSkillInterest"]] = relationship(back_populates="user")



class Profile(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "profiles"


    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    college: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    year: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skill_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # beginner/intermediate/advanced
    known_languages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_available: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    career_goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


    user: Mapped["User"] = relationship(back_populates="profile")



class UserSkillInterest(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "user_skill_interests"


    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    domain: Mapped[str] = mapped_column(String(50))  # AI, Web Development, Cyber Security, etc.


    user: Mapped["User"] = relationship(back_populates="interests")