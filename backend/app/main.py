"""
backend/app/main.py
FastAPI application factory — Phase 2 skeleton.
Run with: uvicorn app.main:app --reload --port 8000
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import (
    auth, users, roadmaps, learning, gigs,
    mentors, companies, payments, notifications, admin,
)

from starlette.middleware.sessions import SessionMiddleware

from contextlib import asynccontextmanager
from app.services.ai.throttle import close_redis
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Kairos API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)


# Build allowed origins from environment variable, with sensible defaults
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(roadmaps.router, prefix="/api/v1/roadmaps", tags=["roadmaps"])
app.include_router(learning.router, prefix="/api/v1/learning", tags=["learning"])
app.include_router(gigs.router, prefix="/api/v1/gigs", tags=["gigs"])
app.include_router(mentors.router, prefix="/api/v1/mentors", tags=["mentors"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "app": "Kairos", "env": "local"}


@app.get("/", tags=["system"])
async def root():
    return {"message": "Kairos API is running. Visit /docs for Swagger UI."}
