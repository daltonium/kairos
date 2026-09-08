# Kairos

**Learn • Build • Get Hired**

Kairos is an AI-powered career growth platform that connects students, mentors, and companies through personalized learning roadmaps, verified skill badges, mentorship, a skill-gated gig marketplace, portfolio and resume generation, and a full hiring pipeline.

Live demo:
- Frontend: https://kairos-five-smoky.vercel.app
- Backend API docs: https://kairos-o6a1.onrender.com/docs

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Backend](#running-the-backend)
- [Running the Frontend](#running-the-frontend)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Demo Accounts](#demo-accounts)
- [API Overview](#api-overview)
- [Built With IBM Bob](#built-with-ibm-bob)
- [License](#license)

---

## Problem Statement

Students and early-career learners face a fragmented career-development journey. Learning resources, project validation, mentorship, portfolios, and job/gig opportunities are scattered across disconnected platforms, making it difficult to turn learning into verified, employable proof of skill.

## Solution

Kairos unifies the entire career journey — **Discover → Learn → Build → Validate → Get Hired** — into a single platform with AI-generated roadmaps, structured learning and project review, verified skill badges, mentor booking, a skill-gated gig marketplace, portfolio/resume generation, and company hiring workflows.

---

## Key Features

### For Students
- AI-generated personalized career roadmaps (interest, skill level, career goal, duration)
- Learning modules, quizzes, and project submissions
- AI-based and mentor-based project review
- Verified skill badges
- Mentor discovery and booking
- Skill-gated gig marketplace (apply, submit, get reviewed, get paid)
- Auto-built portfolio from completed gigs/projects
- AI-assisted resume generation and improvement
- Wallet, payment history, and withdrawals
- In-app notifications

### For Mentors
- Mentor profile setup (domain, experience, availability)
- Discoverable in a ranked mentor directory
- Session booking and schedule management
- Mentor dashboard (students, pending reviews, ratings)
- Project and gig submission reviews

### For Companies
- Company profile setup
- Job posting and gig posting
- Applicant pipeline with AI-generated applicant summaries
- Hiring decision workflow (shortlist / hire / reject)
- Hiring analytics dashboard

### For Admins
- OpenRouter AI usage monitoring (daily quota tracking)

---

## Tech Stack

**Backend**
- FastAPI (Python 3.14)
- SQLAlchemy (async) + Alembic migrations
- PostgreSQL via Supabase
- Redis via Upstash (caching + AI rate-limiting)
- Argon2 password hashing
- JWT authentication + Google OAuth (Authlib)
- Razorpay (payments) · Resend (email) · AWS S3 (file storage)
- OpenRouter (AI reasoning + code models)
- Pytest + pytest-asyncio (automated testing)

**Frontend**
- HTML5, CSS3, Vanilla JavaScript (no framework)
- Centralized API client with JWT refresh handling

**Deployment**
- Backend: Render
- Frontend: Vercel
- Database: Supabase (PostgreSQL)
- Cache: Upstash (Redis)

**AI Development Partner**
- IBM Bob — used throughout planning, backend development, debugging, testing, and deployment (see [Built With IBM Bob](#built-with-ibm-bob))

---

## System Architecture

```
                    ┌────────────────────────┐
                    │   Frontend (Vercel)     │
                    │  HTML5 / CSS3 / JS      │
                    └────────────┬────────────┘
                                 │ HTTPS + JWT
                                 ▼
                    ┌────────────────────────┐
                    │   Backend (Render)      │
                    │   FastAPI (Python)      │
                    └──────┬───────────┬──────┘
                           │           │
                 ┌─────────▼───┐   ┌───▼─────────┐
                 │  Supabase    │   │  Upstash    │
                 │  PostgreSQL  │   │  Redis      │
                 └──────────────┘   └─────────────┘
                           │
              ┌────────────┼─────────────┬──────────────┐
              ▼            ▼              ▼              ▼
         OpenRouter    Razorpay        Resend         AWS S3
         (AI models)   (Payments)     (Email)      (File storage)
```

---

## Project Structure

```
kairos/
├── backend/
│   ├── app/
│   │   ├── alembic/            # DB migrations
│   │   ├── api/v1/             # Route handlers (auth, users, roadmaps,
│   │   │                         learning, gigs, mentors, companies,
│   │   │                         payments, notifications, admin)
│   │   ├── core/                # config, security, dependencies
│   │   ├── db/                  # session + base
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ai/               # roadmap, code review, resume,
│   │   │   │                       applicant summary, throttle, client
│   │   │   ├── razorpay_client.py
│   │   │   ├── email.py
│   │   │   ├── notifications.py
│   │   │   ├── portfolio.py
│   │   │   └── storage.py
│   │   └── main.py
│   ├── tests/                    # Pytest suite
│   ├── requirements.txt
│   └── render.yaml
├── frontend/
│   ├── index.html
│   ├── pages/                    # login, register, dashboard, roadmap,
│   │                                learning, mentors, companies, gigs,
│   │                                portfolio, resume, notifications,
│   │                                wallet, admin, etc.
│   ├── css/
│   ├── js/                       # api.js, app.js
│   └── assets/images/            # logo, favicon
└── .gitignore
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- A Supabase project (PostgreSQL)
- An Upstash Redis instance
- An OpenRouter API key
- (Optional) Razorpay, Resend, Google OAuth, and AWS S3 credentials

### Clone the repository

```bash
git clone https://github.com/<your-username>/kairos.git
cd kairos
```

---

## Environment Variables

Create a `.env` file inside `backend/` with the following keys:

```env
# Database
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:6543/postgres
ALEMBIC_DATABASE_URL=postgresql://<user>:<password>@<host>:5432/postgres

# Redis
REDIS_URL=rediss://<user>:<password>@<host>:6379

# Auth
JWT_SECRET=your-jwt-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AI
OPENROUTER_API_KEY=your-openrouter-api-key
AI_MODEL_REASONING=your-reasoning-model-name
AI_MODEL_CODE=your-code-model-name

# Payments
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
RAZORPAY_WEBHOOK_SECRET=your-razorpay-webhook-secret

# Email
RESEND_API_KEY=your-resend-api-key

# File storage
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=your-aws-region
AWS_S3_BUCKET=your-s3-bucket-name

# App
APP_URL=http://127.0.0.1:8000
CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
```

Never commit `.env` to version control.

---

## Database Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

alembic upgrade head
```

This creates the full 29-table schema (users, profiles, roadmaps, learning modules, quizzes, projects, mentors, companies, gigs, jobs, portfolios, payments, wallets, notifications, and more).

---

## Running the Backend

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Verify:
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

---

## Running the Frontend

```bash
cd frontend
python -m http.server 5500
```

Open: http://127.0.0.1:5500

Update `frontend/js/api.js` if pointing to a different backend URL:

```javascript
const API_BASE_URL =
  window.KAIROS_API_URL ||
  localStorage.getItem("kairos_api_url") ||
  "http://127.0.0.1:8000";
```

---

## Running Tests

```bash
cd backend
venv\Scripts\activate
pytest -v
```

The suite covers authentication, onboarding, gigs, learning, mentors, companies, payments, and portfolio workflows.

---

## Deployment

### Backend (Render)
1. Push the repository to GitHub.
2. Create a new Web Service on Render, root directory `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from the `.env` list above.

### Frontend (Vercel)
1. Import the same GitHub repository into Vercel.
2. Framework preset: **Other**
3. Root directory: `frontend`
4. Build command: (leave empty)
5. Output directory: `.`

### Post-deployment
- Update `CORS_ORIGINS` on Render to include your Vercel domain.
- Update `APP_URL` on Render to your Render backend URL.
- Add the Render callback URL to Google Cloud Console OAuth redirect URIs.
- Add the Render webhook URL to the Razorpay dashboard.

---

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Student | aditi@kairosdemo.com | Demo@1234 |
| Mentor | rohan@kairosdemo.com | Demo@1234 |
| Company | priya@kairosdemo.com | Demo@1234 |
| Student | karan@kairosdemo.com | Demo@1234 |

---

## API Overview

Base URL (local): `http://127.0.0.1:8000/api/v1`
Base URL (production): `https://kairos-o6a1.onrender.com/api/v1`

| Group | Example Endpoints |
|---|---|
| Auth | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/google/login` |
| Users | `/users/me`, `/users/me/profile`, `/users/me/interests` |
| Roadmaps | `/roadmaps/generate`, `/roadmaps/{id}` |
| Learning | `/learning/quizzes/{id}/questions`, `/learning/projects/submit` |
| Mentors | `/mentors`, `/mentors/{id}/book`, `/mentors/me/dashboard` |
| Companies | `/companies/jobs`, `/companies/portfolio/me`, `/companies/resume/generate` |
| Gigs | `/gigs`, `/gigs/{id}/apply`, `/gigs/applications/{id}/submit` |
| Payments | `/payments/wallet/me`, `/payments/history`, `/payments/webhook` |
| Notifications | `/notifications`, `/notifications/{id}/read` |
| Admin | `/admin/ai-usage` |

Full interactive documentation is available at `/docs` (Swagger UI) and `/redoc`.

---

## Built With IBM Bob

IBM Bob was used as an AI-powered SDLC partner throughout this project — supporting planning, backend development, AI workflow design, debugging, automated testing, frontend-backend integration, and deployment. See `IBM_Bob_Usage_Documentation.txt` for the full write-up.

---

## License

This project was built for educational/demonstration purposes.
