from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.tasks.scheduler import start_scheduler, stop_scheduler

# ── Pius's routers (FR5, FR6, FR11, FR12) ────────────────────────────────────
from app.routers import notifications, reporting, suppliers, workforce

# ── Omar's routers — uncomment when his branches are merged (FR1, FR7, FR8, FR10)
# from app.routers import auth, customers, tokens, blockchain

# ── Sunny's routers — uncomment when her branches are merged (FR2, FR3, FR4, FR9, FR13)
# from app.routers import org, compliance, esg, donations, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "ESG & SDG Workforce and Customer Engagement Platform for Hospitality. "
        "UEL Centre of FinTech Hackathon Phase 3."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.API_V1_PREFIX

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(suppliers.router,     prefix=f"{PREFIX}/suppliers",     tags=["FR5 – Suppliers"])
app.include_router(workforce.router,     prefix=f"{PREFIX}/workforce",     tags=["FR6 – Workforce"])
app.include_router(reporting.router,     prefix=f"{PREFIX}/reports",       tags=["FR11 – Reporting"])
app.include_router(notifications.router, prefix=f"{PREFIX}/notifications",  tags=["FR12 – Notifications"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
