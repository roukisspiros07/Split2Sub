# Group Subscription Manager

A web app for groups to track shared subscriptions, split costs, and stop the awkward "did you pay?" texts.

---

## Overview

When friends share a Spotify Family plan, someone (the owner) fronts the whole bill and spends every month chasing payments. The product:

1. **Tracks** each group's subscriptions and who owes what (equal or custom shares)
2. **Generates** monthly bills automatically per membership
3. **Reminds** — day 0 "bill due", day +3 "still unpaid", day +7 "overdue"
4. **Shames gently** — a per-group scoreboard shows who hasn't paid (the feature that actually gets people to pay)

**Current stage: backend foundation.** FastAPI scaffold, the core data model, and the first database migration are done. Auth, billing flows, and the React frontend are next (see [Roadmap](#roadmap)).

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **Database** | PostgreSQL 17 (Docker Compose) |
| **Cache** | Redis (Docker Compose — reserved for later) |
| **Auth** | JWT + bcrypt (planned) |
| **Scheduler** | APScheduler (planned) |
| **Frontend** | React + Tailwind CSS, Vite (planned) |
| **Testing** | pytest, httpx |

---

## Quick Start

### Prerequisites
- Python 3.14+
- Docker Desktop
- Node.js 18+ (frontend, when built)

### Backend

```bash
# 1. Start Postgres (and Redis)
docker compose up -d db

# 2. Set up the environment
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env   # set your credentials

# 3. Apply migrations
.venv\Scripts\python.exe -m alembic upgrade head

# 4. Run the API
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Health check: `http://localhost:8000/health`

### Tests

```bash
cd backend
.venv\Scripts\python.exe -m pytest
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│            Frontend (planned)               │
│   React + Tailwind (Vite)                   │
│   dashboard | billing | scoreboard          │
└─────────────────────────────────────────────┘
                      │ REST API
                      ▼
┌─────────────────────────────────────────────┐
│               FastAPI Backend               │
│   routers → services → models / schemas     │
│   (layered: API handlers, business logic,   │
│    ORM models, Pydantic DTOs)               │
└─────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│    PostgreSQL    │      │      Redis       │
│  users, groups,  │      │  cache/real-time  │
│  group_members   │      │   (planned)       │
└──────────────────┘      └──────────────────┘
```

Bold = built. The billing spine (`Subscription → Bill → BillItem → Payment`) and the scheduler slot in between the API and the database as the project grows.

---

## Project Structure

```
Split2Sub/
├── backend/
│   ├── app/
│   │   ├── routers/    # API endpoints (health)
│   │   ├── services/   # business logic — filled as features land
│   │   ├── models/     # SQLAlchemy models: User, Group, GroupMember
│   │   ├── schemas/    # Pydantic DTOs
│   │   ├── base.py     # shared DeclarativeBase
│   │   ├── config.py   # settings, loaded from .env
│   │   ├── database.py # async engine + session dependency
│   │   └── main.py     # FastAPI app factory
│   ├── alembic/        # schema migrations
│   ├── tests/          # pytest suite
│   ├── pyproject.toml  # deps + Ruff + pytest config
│   └── .env.example    # config template
├── docker-compose.yml  # Postgres + Redis
└── README.md
```

---

## Roadmap

- [x] **Backend scaffold** — FastAPI (async), layered app, health endpoint, Ruff + pytest
- [x] **Models + migrations** — User / Group / GroupMember, partial unique owner index
- [ ] **Auth** — register/login, bcrypt, JWT
- [ ] **Groups + members + invites**
- [ ] **Subscriptions + membership shares** (Decimal money, never float)
- [ ] **Bill generation + balances / scoreboard**
- [ ] **React frontend** — dashboard, billing views, scoreboard
- [ ] **APScheduler** — automatic bills + reminders
- [ ] **Recommendation engine** — catalog + "why this match" scoring (v2)