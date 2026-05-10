# TechKraft — Candidate Scoring & Review Dashboard

An enterprise-grade internal recruitment tool for managing candidate assessments, scoring, and AI-generated summaries. Built with **FastAPI**, **Next.js**, and **PostgreSQL**.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Next.js](https://img.shields.io/badge/Next.js-15-black) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue) ![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Run Instructions](#setup--run-instructions)
- [API Documentation](#api-documentation)
- [Example API Calls](#example-api-calls)
- [Debugging Signal — Bug Identification](#debugging-signal--bug-identification)
- [Architecture Decision Records](#architecture-decision-records)
- [Learning Reflection](#learning-reflection)
- [Testing](#testing)

---

## Features

- **JWT Authentication** with role-based access control (Admin / Reviewer)
- **Candidate Management** — CRUD with filtering by status, role, skill, and keyword search
- **Offset-based Pagination** — configurable page size (1–50, default 20)
- **Scoring System** — reviewers rate candidates 1–5 across categories
- **AI Summary Generation** — mock async LLM call with 2s delay, loading/error states
- **SSE Streaming** — real-time score update notifications (stretch goal)
- **Internal Notes** — admin-only editable notes per candidate
- **Soft Delete** — candidates are never hard-deleted; `deleted_at` timestamp is set
- **Seed Data** — pre-populated with 10 sample candidates, scores, admin & reviewer accounts

---

## Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Frontend  | Next.js 15, TypeScript, Tailwind CSS    |
| Backend   | Python 3.12, FastAPI, SQLAlchemy 2.0    |
| Database  | PostgreSQL 16                           |
| Auth      | JWT (python-jose), bcrypt               |
| Infra     | Docker Compose                          |
| Testing   | pytest, pytest-asyncio, httpx           |

---

## Project Structure

```
/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Pydantic settings from env
│   │   ├── database.py          # Async SQLAlchemy engine & session
│   │   ├── models.py            # ORM models (User, Candidate, Score, Summary)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── auth.py              # JWT + password hashing utilities
│   │   ├── seed.py              # Database seeder script
│   │   ├── routers/
│   │   │   ├── auth.py          # /auth/register, /auth/login, /auth/me
│   │   │   └── candidates.py   # /candidates CRUD, scores, summary, SSE
│   │   └── services/
│   │       └── candidate_service.py  # Business logic layer
│   └── tests/
│       ├── conftest.py          # Shared fixtures (in-memory SQLite)
│       └── test_api.py          # API + auth enforcement tests
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Redirect to login/dashboard
│   │   │   ├── login/page.tsx   # Login/register page
│   │   │   ├── dashboard/page.tsx  # Candidate list + filters
│   │   │   └── candidates/[id]/page.tsx  # Candidate detail + scoring
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── Pagination.tsx
│   │   │   └── ScoreStars.tsx
│   │   └── lib/
│   │       ├── api.ts           # API client
│   │       └── types.ts         # TypeScript interfaces
│   └── ...
```

---

## Setup & Run Instructions

### Prerequisites

- Docker & Docker Compose installed
- Git

### Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/techkraft-candidate-dashboard.git
cd techkraft-candidate-dashboard

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker compose up --build

# 4. Seed the database (in a separate terminal)
docker compose exec backend python -m app.seed

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs (Swagger): http://localhost:8000/docs
```

### Demo Credentials

| Role     | Email                   | Password    |
|----------|-------------------------|-------------|
| Admin    | admin@techkraft.com     | admin123    |
| Reviewer | reviewer@techkraft.com  | reviewer123 |

### Manual Setup (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Set DATABASE_URL to your PostgreSQL instance
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000/api npm run dev
```

---

## API Documentation

Interactive Swagger docs available at: `http://localhost:8000/docs`

| Method | Endpoint                        | Auth     | Description                                     |
|--------|---------------------------------|----------|-------------------------------------------------|
| POST   | `/api/auth/register`            | Public   | Register (role hardcoded to `reviewer`)          |
| POST   | `/api/auth/login`               | Public   | Login, returns JWT                               |
| GET    | `/api/auth/me`                  | Required | Current user profile                             |
| GET    | `/api/candidates`               | Required | List candidates + filters + pagination           |
| POST   | `/api/candidates`               | Admin    | Create candidate                                 |
| GET    | `/api/candidates/{id}`          | Required | Candidate detail (scores filtered by role)       |
| PATCH  | `/api/candidates/{id}`          | Required | Update candidate (internal_notes admin-only)     |
| DELETE | `/api/candidates/{id}`          | Admin    | Soft delete (sets `deleted_at`)                  |
| POST   | `/api/candidates/{id}/scores`   | Required | Submit score (1–5, category, optional note)      |
| POST   | `/api/candidates/{id}/summary`  | Required | Trigger mock AI summary (2s async delay)         |
| GET    | `/api/candidates/{id}/stream`   | Required | SSE stream for real-time score updates           |
| GET    | `/api/health`                   | Public   | Health check                                     |

---

## Example API Calls

```bash
# Register a new reviewer
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "new@techkraft.com", "password": "password123", "full_name": "New User"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@techkraft.com", "password": "admin123"}'
# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# List candidates with filters
TOKEN="<your-token-here>"
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/candidates?status=new&page=1&page_size=5"

# Get candidate detail
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/candidates/<candidate-id>"

# Submit a score
curl -X POST http://localhost:8000/api/candidates/<candidate-id>/scores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category": "Technical Skills", "score": 4, "note": "Strong Python expertise"}'

# Generate AI summary
curl -X POST http://localhost:8000/api/candidates/<candidate-id>/summary \
  -H "Authorization: Bearer $TOKEN"

# Soft delete a candidate (admin only)
curl -X DELETE http://localhost:8000/api/candidates/<candidate-id> \
  -H "Authorization: Bearer $TOKEN"
```

---

## Debugging Signal — Bug Identification

### The Buggy Code

```python
def search_candidates(status: str, keyword: str, page: int, page_size: int):
    all_candidates = db.execute("SELECT * FROM candidates").fetchall()
    filtered = [c for c in all_candidates if c["status"] == status]
    # ... also filter by keyword in Python ...
    offset = (page - 1) * page_size
    return filtered[offset : offset + page_size]
```

### The Issue

**The code fetches the entire `candidates` table into application memory, then filters and paginates in Python.** This is fundamentally flawed for several reasons:

1. **Full table scan on every request** — `SELECT * FROM candidates` loads all rows into memory regardless of how many are needed. With 100K+ candidates, this causes massive memory spikes, slow response times, and potential OOM crashes.

2. **Database indexes are completely bypassed** — even though indexes exist on `status` and `role_applied`, they are never used because the query has no WHERE clause. Filtering happens in Python, making those indexes worthless.

3. **N+1 inefficiency at scale** — every paginated request re-fetches and re-filters the entire dataset. For 100 concurrent users browsing page 1 of 10, the database serves 100 full scans instead of 100 lightweight indexed queries.

4. **No SQL injection protection** — the raw string query is vulnerable if extended with user input interpolation.

### The Correct Approach

Push filtering, ordering, and pagination into the SQL query:

```python
def search_candidates(status: str, keyword: str, page: int, page_size: int):
    query = select(Candidate).where(Candidate.deleted_at.is_(None))

    if status:
        query = query.where(Candidate.status == status)       # Uses ix_candidates_status
    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            or_(Candidate.name.ilike(pattern), Candidate.email.ilike(pattern))
        )

    offset = (page - 1) * page_size
    query = query.order_by(Candidate.created_at.desc()).offset(offset).limit(page_size)

    return db.execute(query).scalars().all()
```

This leverages database indexes, transfers only the required rows, and scales linearly with page size — not dataset size.

---

## Architecture Decision Records

### ADR 1: PostgreSQL over SQLite/DynamoDB

- **Context:** The assignment suggested SQLite or DynamoDB-style storage. We need a database that supports concurrent access, ACID transactions, and rich querying.
- **Decision:** PostgreSQL with SQLAlchemy async (asyncpg driver).
- **Trade-off:** Requires a separate database service (added to Docker Compose), but provides production-grade reliability, ARRAY column support for skills, proper indexing, and concurrent async connections. SQLite would struggle with concurrent writes; DynamoDB would complicate local development.

### ADR 2: Next.js (App Router) over React + Vite

- **Context:** The assignment specified React + Vite. The requirement is a modern, production-ready frontend.
- **Decision:** Next.js 15 with App Router, TypeScript, and Tailwind CSS.
- **Trade-off:** Slightly heavier framework than Vite SPA, but provides file-based routing, server-side rendering capabilities, built-in TypeScript support, and a more enterprise-aligned architecture. For an internal tool that may grow to include server-rendered pages or API routes, Next.js is the stronger foundation.

### ADR 3: JWT with HTTP Bearer over Cookie-Based Sessions

- **Context:** Authentication is needed for RBAC between admin and reviewer roles.
- **Decision:** Stateless JWT tokens sent via `Authorization: Bearer` header. Tokens encode user ID and role with expiration.
- **Trade-off:** No server-side session storage required (simpler horizontal scaling), but tokens cannot be revoked before expiry without a blacklist. For an internal tool with a small user base, this trade-off is acceptable. Registration always hardcodes `role="reviewer"` to prevent privilege escalation.

---

## Learning Reflection

This project was an opportunity to build an end-to-end async system with FastAPI's dependency injection for RBAC — particularly the pattern of separating `get_current_user` from `require_admin` as composable dependencies. I also deepened my understanding of SSE (Server-Sent Events) as a lightweight alternative to WebSockets for real-time updates. Given more time, I would explore implementing a proper background task queue (e.g., Celery or ARQ) for the AI summary generation instead of `asyncio.sleep`, and add comprehensive E2E tests with Playwright to cover the full user journey from login through scoring.

---

## Testing

```bash
# Run tests (requires aiosqlite for in-memory test DB)
cd backend
pip install aiosqlite
pytest tests/ -v

# Tests cover:
# - Candidate creation (admin can create, reviewer cannot)
# - Listing candidates with pagination
# - Fetching candidate detail
# - Submitting scores
# - Auth enforcement (reviewer cannot see other reviewers' scores)
# - Admin sees all scores
# - Registration always sets role to "reviewer"
# - Unauthenticated access is denied
# - Soft delete behavior
```

---

## Responsibility & Detail Checks

- [x] Credentials NOT committed (`.env.example` with dummy values only)
- [x] README ports match Docker Compose (backend: 8000, frontend: 3000)
- [x] Mock AI summary shows loading + error states in frontend
- [x] Soft delete implemented (`deleted_at` timestamp, never hard-delete)
- [x] Registration hardcodes `role="reviewer"` — never accepts role from client
- [x] Role-based score visibility (reviewer: own scores only; admin: all)
- [x] Internal notes visible/editable only by admin
