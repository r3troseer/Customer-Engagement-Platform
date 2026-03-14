
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.tasks.scheduler import start_scheduler, stop_scheduler

# ── Pius's routers (FR5, FR6, FR11, FR12) ────────────────────────────────────
from app.routers import notifications, reporting, suppliers, workforce

# ── Omar's routers ──────────────────────────────────────────────────────────────
from app.routers import auth, customers, tokens, blockchain

# ── Sunny's routers ───────────────────────────────────────────────────────────
from app.routers.audit import router as audit_router
from app.routers.compliance import router as compliance_router
from app.routers.donations import router as donations_router
from app.routers.esg import router as esg_router
from app.routers.org import router as org_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting scheduler...")
    start_scheduler()
    yield
    print("Stopping scheduler...")
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
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.API_V1_PREFIX

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(
    suppliers.router,
    prefix=f"{PREFIX}/suppliers",
    tags=["FR5 – Suppliers"],
)

app.include_router(
    workforce.router,
    prefix=f"{PREFIX}/workforce",
    tags=["FR6 – Workforce"],
)

app.include_router(
    reporting.router,
    prefix=f"{PREFIX}/reports",
    tags=["FR11 – Reporting"],
)

app.include_router(
    notifications.router,
    prefix=f"{PREFIX}/notifications",
    tags=["FR12 – Notifications"],
)

# ── Sunny routers ─────────────────────────────────────────────────────────────
# These routers already define their own internal prefixes:
# org_router         -> /org
# compliance_router  -> /compliance
# esg_router         -> /esg
# donations_router   -> /donations
# audit_router       -> /audit
app.include_router(org_router, prefix=PREFIX)
app.include_router(compliance_router, prefix=PREFIX)
app.include_router(esg_router, prefix=PREFIX)
app.include_router(donations_router, prefix=PREFIX)
app.include_router(audit_router, prefix=PREFIX)

# ── Omar routers ──────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix=f"{PREFIX}/auth", tags=["FR1 – Auth"])
app.include_router(customers.router, prefix=f"{PREFIX}/customers", tags=["FR7 – Customers"])
app.include_router(tokens.router, prefix=f"{PREFIX}/tokens", tags=["FR8 – Tokens"])
app.include_router(blockchain.router, prefix=f"{PREFIX}/blockchain", tags=["FR10 – Blockchain"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }


# ── Debug: print registered routes on startup/import ─────────────────────────
print("ORG ROUTER LOADED:", org_router)
print("COMPLIANCE ROUTER LOADED:", compliance_router)
print("ESG ROUTER LOADED:", esg_router)
print("DONATIONS ROUTER LOADED:", donations_router)
print("AUDIT ROUTER LOADED:", audit_router)

for route in app.routes:
    try:
        print("ROUTE:", route.path)
    except Exception:
        pass