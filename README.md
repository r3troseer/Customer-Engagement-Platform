# Customer Engagement Platform

**ESG & SDG Workforce and Customer Engagement Platform for Hospitality**
UEL Centre of FinTech — Hackathon Phase 3

---

## Project Overview

A multi-tenant SaaS platform that helps restaurant chains track ESG (Environmental, Social, Governance) and UN Sustainable Development Goals (SDGs), engage employees through token-based incentives, and build customer loyalty through sustainable behaviour rewards.

Key capabilities:
- ESG objective setting, metric tracking, and report generation
- Compliance management with evidence upload and blockchain verification
- Employee leaderboards with weekly reset and automated bonus token awards
- Customer rewards through dining visits and walking/step tracking
- Supplier transparency with public ESG certification visibility
- Full audit trail and notification system

---

## Team & Functional Requirements Ownership

| Developer | Functional Requirements |
|-----------|------------------------|
| **Pius** | **FR5** – Supplier Transparency & Compliance · **FR6** – Workforce Engagement & Incentive · **FR11** – Reporting & Analytics · **FR12** – Notification & Alert System |
| **Omar** | **FR1** – User Roles & Access Control · **FR7** – Customer Engagement & Rewards · **FR8** – Token Economy & Reward System · **FR10** – Blockchain Verification & Transparency |
| **Sunny** | **FR2** – Organisation & Restaurant Management · **FR3** – Compliance Management · **FR4** – ESG & SDG Management · **FR9** – Donation & ESG Offset · **FR13** – Audit & Governance |

### FR Summary

| FR | Module | Owner |
|----|--------|-------|
| FR1 | User Roles & Access Control (RBAC, MFA, sessions) | Omar |
| FR2 | Organisation & Restaurant Management | Sunny |
| FR3 | Compliance Management (frameworks, evidence, alerts) | Sunny |
| FR4 | ESG & SDG Management (objectives, metrics, activities) | Sunny |
| FR5 | Supplier Transparency & Compliance | **Pius** |
| FR6 | Workforce Engagement & Incentive (leaderboard, tokens) | **Pius** |
| FR7 | Customer Engagement & Rewards (visits, steps, challenges) | Omar |
| FR8 | Token Economy & Reward System (wallets, rules) | Omar |
| FR9 | Donation & ESG Offset (token donations, impact) | Sunny |
| FR10 | Blockchain Verification & Transparency | Omar |
| FR11 | Reporting & Analytics (ESG/compliance reports, PDF/CSV) | **Pius** |
| FR12 | Notification & Alert System (email, push, in-app) | **Pius** |
| FR13 | Audit & Governance (audit logs, change history) | Sunny |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115+ |
| Database | PostgreSQL (via asyncpg async driver) |
| ORM | SQLAlchemy 2.x (async, `Mapped[T]` style) |
| Migrations | Alembic |
| Auth | JWT (PyJWT) — issued by Omar's FR1 router |
| Scheduling | APScheduler 3.x (AsyncIOScheduler) |
| PDF export | reportlab |
| CSV/Excel export | openpyxl |
| File storage | Local filesystem (dev) / S3 (production) |
| Email | emails (SMTP) |
| Push notifications | FCM via httpx |
| Package manager | uv |
| Deployment | Docker on Railway |

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- `uv` installed (`pip install uv`)
- PostgreSQL running locally

### Steps

```bash
# 1. Clone the repo
git clone <repo-url>
cd Customer-Engagement-Platform

# 2. Install dependencies
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, DATABASE_SYNC_URL, JWT_SECRET_KEY, POLYGON_WALLET_PRIVATE_KEY 

# 4. Run database migrations
uv run alembic upgrade head

# 5. Start the dev server
uv run uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs
Health check: http://localhost:8000/health

---

## Docker Deployment (Railway)

### Build and run locally

```bash
docker build -t cep .
docker run -p 8000:8000 --env-file .env cep
```

### Railway deployment

1. Push to GitHub
2. Create a new Railway project → "Deploy from GitHub repo"
3. Railway auto-detects the `Dockerfile`
4. Add a **PostgreSQL** service in the Railway dashboard
5. Add a **Bucket** service in the Railway dashboard (S3-compatible object storage)
6. Set the following environment variables in Railway:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` — use Railway's `${{Postgres.DATABASE_URL}}` with driver prefix swapped to `asyncpg` |
| `DATABASE_SYNC_URL` | `postgresql+psycopg2://...` — same host, `psycopg2` prefix (Alembic only) |
| `JWT_SECRET_KEY` | Shared secret — **Omar sets this; all devs must use the same value** |
| `STORAGE_BACKEND` | `s3` |
| `AWS_S3_BUCKET_NAME` | From Railway Bucket → Connect tab |
| `AWS_ENDPOINT_URL` | From Railway Bucket → Connect tab (e.g. `https://t3.storageapi.dev`) |
| `AWS_ACCESS_KEY_ID` | From Railway Bucket → Connect tab |
| `AWS_SECRET_ACCESS_KEY` | From Railway Bucket → Connect tab |
| `AWS_REGION` | `auto` (Railway Buckets default) |
| `SMTP_USER` | Email sender credentials |
| `SMTP_PASSWORD` | Email sender password |
| `FCM_SERVER_KEY` | Firebase Cloud Messaging key (push notifications) |
| `SCHEDULER_TIMEZONE` | IANA timezone e.g. `Europe/London` |

> **Local dev:** copy the same `AWS_*` and `DATABASE_*` values into your local `.env` — all 3 devs share the same Railway Postgres and Bucket, so the integration state is always consistent.

The Docker CMD runs `alembic upgrade head` automatically on every deploy before starting Uvicorn.

---

## Project Structure

```
Customer-Engagement-Platform/
├── main.py                      # FastAPI app + router registration
├── Dockerfile                   # Railway-compatible multi-stage build
├── .env.example                 # Environment variable template (commit this)
├── alembic.ini                  # Alembic config
├── alembic/
│   ├── env.py                   # Alembic env — imports all models
│   └── versions/                # Migration files (auto-generated)
└── app/
    ├── core/
    │   ├── config.py            # Settings (pydantic-settings)
    │   ├── database.py          # Async SQLAlchemy engine + get_db
    │   ├── exceptions.py        # Custom HTTP exceptions
    │   └── security.py          # JWT decode utilities
    ├── dependencies/
    │   ├── auth.py              # get_current_user, require_role, type aliases
    │   ├── db.py                # DBSession type alias
    │   └── pagination.py        # PaginationParams
    ├── models/                  # SQLAlchemy 2.x ORM models (52 tables)
    │   ├── base.py              # Base, TimestampMixin
    │   ├── enums.py             # All PostgreSQL ENUM types
    │   ├── auth.py              # Omar  — users, roles, sessions
    │   ├── org.py               # Sunny — organizations, locations, employees
    │   ├── compliance.py        # Sunny — compliance frameworks + records
    │   ├── esg.py               # Sunny — ESG objectives + metrics
    │   ├── suppliers.py         # Pius  — suppliers + documents
    │   ├── workforce.py         # Pius  — work logs + leaderboard
    │   ├── customers.py         # Omar  — customers + visits + challenges
    │   ├── tokens.py            # Omar  — wallets + transactions
    │   ├── donations.py         # Sunny — donation causes + impacts
    │   ├── blockchain.py        # Omar  — blockchain records + hashes
    │   ├── reporting.py         # Pius  — report templates + runs
    │   └── notifications.py     # Pius + Sunny — notifications + audit_logs
    ├── routers/                 # FastAPI APIRouter per FR group
    ├── services/                # Business logic (no HTTP concerns)
    ├── tasks/                   # APScheduler cron jobs
    │   ├── scheduler.py         # Scheduler init + start/stop (wired into lifespan)
    │   ├── leaderboard_tasks.py # FR-6.6 reset + FR-6.7 Monday bonus
    │   ├── report_tasks.py      # FR-11.6 scheduled reports
    │   └── compliance_tasks.py  # FR-12.2 cert expiry alerts
    ├── schemas/                 # Pydantic v2 request/response models
    └── utils/
        ├── file_storage.py      # Local / S3 file upload helper
        └── date_helpers.py      # ISO week boundaries, Monday detection
```

---

## Database Migrations

```bash
# Generate a migration after model changes (coordinate with team first)
uv run alembic revision --autogenerate -m "describe_change_here"

# Apply all pending migrations
uv run alembic upgrade head

# Roll back one migration
uv run alembic downgrade -1
```

> **Team coordination:** All 3 devs must merge their model files into `app/models/__init__.py`
> on the `feat/shared-models` branch before anyone runs `autogenerate`. One dev runs
> the migration and commits the generated file.

---

## API Endpoints

All endpoints prefixed with `/api/v1`. Interactive docs at `/docs` (Swagger UI).

### FR1 – User Roles & Access Control
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | none | Register a new user |
| POST | `/auth/login` | none | Login and get JWT |
| GET | `/auth/me` | any | Get current user profile |
| PATCH | `/auth/me` | any | Update current user profile |
| GET | `/auth/users` | admin | List users (paginated) |
| GET | `/auth/users/{user_id}` | admin | Get user by ID |
| POST | `/auth/change-password` | any | Change password |
| GET | `/auth/roles` | admin | List all roles |
| GET | `/auth/security-logs` | admin | Security audit logs |

### FR5 – Supplier Transparency
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/suppliers/` | admin | Register supplier |
| GET | `/suppliers/` | admin | List suppliers (paginated) |
| PATCH | `/suppliers/{id}` | admin | Update supplier |
| POST | `/suppliers/{id}/documents` | admin | Upload sustainability cert |
| POST | `/suppliers/{id}/documents/{doc_id}/review` | admin | Approve / reject cert |
| GET | `/suppliers/{id}/compliance/history` | admin | Compliance change history |
| GET | `/suppliers/public` | any | Public ESG info (customer-facing) |

### FR6 – Workforce Engagement
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/workforce/work-logs` | employee | Log hours — auto-awards tokens |
| GET | `/workforce/leaderboard` | employee | Current week leaderboard |
| GET | `/workforce/wallet` | employee | Token wallet balance |
| POST | `/workforce/redemptions` | employee | Redeem tokens for voucher |
| GET | `/workforce/redemptions` | employee | My redemption history |

### FR7 – Customer Engagement & Rewards
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/customers/` | admin | Create customer profile |
| GET | `/customers/` | admin | List customers (paginated) |
| GET | `/customers/me` | any | Get my customer profile |
| GET | `/customers/{customer_id}` | any | Get customer by ID |
| PATCH | `/customers/{customer_id}` | any | Update customer profile |
| POST | `/customers/visits` | any | Record a dining visit |
| GET | `/customers/{customer_id}/visits` | any | List customer visits |
| POST | `/customers/mobility` | any | Log steps/mobility |
| GET | `/customers/{customer_id}/mobility` | any | List mobility logs |
| POST | `/customers/challenges` | admin | Create challenge |
| GET | `/customers/challenges` | any | List challenges |
| GET | `/customers/challenges/{challenge_id}` | any | Get challenge |
| POST | `/customers/challenges/join` | any | Join a challenge |
| GET | `/customers/{customer_id}/impact` | any | Customer sustainability impact |

### FR8 – Token Economy & Reward System
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/tokens/wallets` | admin | Create wallet |
| GET | `/tokens/wallets/me` | any | Get my wallet |
| GET | `/tokens/wallets/{wallet_id}/transactions` | any | List wallet transactions |
| POST | `/tokens/rules` | admin | Create token rule |
| GET | `/tokens/rules` | admin | List token rules |
| POST | `/tokens/catalog` | admin | Add reward to catalog |
| GET | `/tokens/catalog` | any | Browse rewards catalog |
| GET | `/tokens/catalog/{item_id}` | any | Get catalog item |
| POST | `/tokens/redeem` | any | Redeem tokens for reward |

### FR10 – Blockchain Verification & Transparency
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/blockchain/records` | admin | Create blockchain record |
| GET | `/blockchain/records` | admin | List blockchain records |
| GET | `/blockchain/records/{record_id}` | any | Get blockchain record |
| POST | `/blockchain/anchor` | admin | Anchor record hash on Polygon |
| GET | `/blockchain/verify/{reference_code}` | none | Public verification (no auth) |

### FR11 – Reporting & Analytics
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/reports/esg` | admin | ESG performance report |
| GET | `/reports/compliance` | admin | Compliance report |
| GET | `/reports/suppliers` | admin | Supplier transparency report |
| GET | `/reports/dashboard` | admin | Real-time dashboard KPIs |
| POST | `/reports/export` | admin | Generate PDF / CSV export |
| POST | `/reports/templates` | admin | Create scheduled report template |
| POST | `/reports/templates/{id}/run` | admin | Manually trigger a report |

### FR12 – Notifications
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/notifications/` | any | My notifications (unread first) |
| PATCH | `/notifications/{id}/read` | any | Mark notification as read |
| PATCH | `/notifications/read-all` | any | Mark all as read |
| GET | `/notifications/preferences` | any | Get notification preferences |
| PATCH | `/notifications/preferences` | any | Update preferences |

---

## Scheduled Jobs

| Job | Schedule | FR | Description |
|-----|----------|----|-------------|
| `reset_all_leaderboards` | Sunday 23:59 | FR-6.6 | Snapshot + reset weekly leaderboard per org |
| `award_monday_bonuses` | Monday 00:05 | FR-6.7 | Award bonus tokens to top-3 employees per org |
| `run_scheduled_reports` | Daily 02:00 | FR-11.6 | Execute all scheduled report templates |
| `check_certification_expiry` | Daily 08:00 | FR-12.2 | Alert admins of expiring supplier certs |

Timezone configured via `SCHEDULER_TIMEZONE` env var (default: `Europe/London`).

---

## Git Branching Convention

```
main                    ← protected, PR required
feat/shared-models      ← all 3 devs: merge model files here FIRST
feat/fr5-suppliers      ← Pius
feat/fr6-workforce      ← Pius
feat/fr11-reporting     ← Pius
feat/fr12-notifications ← Pius
feat/fr1-auth           ← Omar
feat/fr7-customers      ← Omar
feat/fr8-tokens         ← Omar
feat/fr10-blockchain    ← Omar
feat/fr2-org            ← Sunny
feat/fr3-compliance     ← Sunny
feat/fr4-esg            ← Sunny
feat/fr9-donations      ← Sunny
feat/fr13-audit         ← Sunny
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full annotated list.

Critical variables:
- `DATABASE_URL` — async PostgreSQL connection string (asyncpg driver) — from Railway Postgres service
- `DATABASE_SYNC_URL` — sync PostgreSQL connection string (psycopg2, used by Alembic only)
- `JWT_SECRET_KEY` — **shared across all 3 devs; Omar sets the canonical value in Railway**
- `STORAGE_BACKEND` — `s3` for Railway Bucket (all environments), `local` only for offline dev
- `AWS_S3_BUCKET_NAME` / `AWS_ENDPOINT_URL` / `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — from Railway Bucket → Connect tab; copy into local `.env` for consistent dev state
- `AWS_REGION` — `auto` for Railway Buckets
- `SCHEDULER_TIMEZONE` — IANA timezone (e.g. `Europe/London`)
- `CERT_EXPIRY_WARNING_DAYS` — days before cert expiry for warning alert (default: 30)
- `CERT_EXPIRY_CRITICAL_DAYS` — days before cert expiry for critical alert (default: 7)
