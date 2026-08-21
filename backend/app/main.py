"""
backend/app/main.py
FastAPI application factory — Phase 2 skeleton.
Run with: uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import (
    auth, users, roadmaps, learning, gigs,
    mentors, companies, payments, notifications, admin,
)

app = FastAPI(title="Kairos API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",   # VS Code Live Server default
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
