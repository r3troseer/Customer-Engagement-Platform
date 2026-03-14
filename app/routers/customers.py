"""
FR7 — Customer Engagement & Rewards (Omar).
Visits, step tracking, challenges, impact summary.
"""
from fastapi import APIRouter, Query, status

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import PaginatedResponse
from app.schemas.customers import (
    ChallengeCreate,
    ChallengeOut,
    ChallengeUpdate,
    CustomerCreate,
    CustomerImpactOut,
    CustomerOut,
    CustomerUpdate,
    JoinChallengeRequest,
    MobilityLogCreate,
    MobilityLogOut,
    ParticipationOut,
    ProgressUpdate,
    VisitCreate,
    VisitOut,
)
import app.services.customer_service as svc

router = APIRouter()


# ── FR-7.1: Customer CRUD ────────────────────────────────────────────────────

@router.post("/", response_model=CustomerOut, status_code=status.HTTP_201_CREATED, summary="FR-7.1 Create customer profile")
async def create_customer(body: CustomerCreate, db: DBSession, current_user: AdminUser):
    customer = await svc.create_customer(db, body.model_dump())
    return CustomerOut.model_validate(customer)


@router.get("/", response_model=PaginatedResponse[CustomerOut], summary="FR-7.1 List customers")
async def list_customers(db: DBSession, current_user: AdminUser, pagination: Pagination):
    items, total = await svc.list_customers(db, offset=pagination.offset, limit=pagination.page_size)
    return PaginatedResponse.create(
        items=[CustomerOut.model_validate(c) for c in items],
        total=total, page=pagination.page, page_size=pagination.page_size,
    )


@router.get("/me", response_model=CustomerOut, summary="FR-7.1 Get my customer profile")
async def get_my_profile(db: DBSession, current_user: CurrentUser):
    customer = await svc.get_customer_by_user(db, current_user["user_id"])
    if not customer:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Customer profile for user", current_user["user_id"])
    return CustomerOut.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerOut, summary="FR-7.1 Get customer by ID")
async def get_customer(customer_id: int, db: DBSession, current_user: CurrentUser):
    customer = await svc.get_customer(db, customer_id)
    if not customer:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Customer", customer_id)
    return CustomerOut.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerOut, summary="FR-7.1 Update customer profile")
async def update_customer(customer_id: int, body: CustomerUpdate, db: DBSession, current_user: CurrentUser):
    customer = await svc.update_customer(db, customer_id, body.model_dump(exclude_unset=True))
    return CustomerOut.model_validate(customer)


# ── FR-7.2: Visits ───────────────────────────────────────────────────────────

@router.post("/visits", response_model=VisitOut, status_code=status.HTTP_201_CREATED, summary="FR-7.2 Record a dining visit")
async def record_visit(body: VisitCreate, db: DBSession, current_user: CurrentUser):
    visit = await svc.record_visit(db, body.model_dump())
    return VisitOut.model_validate(visit)


@router.get("/{customer_id}/visits", response_model=list[VisitOut], summary="FR-7.2 List customer visits")
async def list_visits(customer_id: int, db: DBSession, current_user: CurrentUser, pagination: Pagination):
    visits = await svc.list_visits(db, customer_id, offset=pagination.offset, limit=pagination.page_size)
    return [VisitOut.model_validate(v) for v in visits]


# ── FR-7.3: Mobility / Step Tracking ─────────────────────────────────────────

@router.post("/mobility", response_model=MobilityLogOut, status_code=status.HTTP_201_CREATED, summary="FR-7.3 Log steps/mobility")
async def log_mobility(body: MobilityLogCreate, db: DBSession, current_user: CurrentUser):
    log = await svc.log_mobility(db, body.model_dump())
    return MobilityLogOut.model_validate(log)


@router.get("/{customer_id}/mobility", response_model=list[MobilityLogOut], summary="FR-7.3 List mobility logs")
async def list_mobility(customer_id: int, db: DBSession, current_user: CurrentUser, pagination: Pagination):
    logs = await svc.list_mobility_logs(db, customer_id, offset=pagination.offset, limit=pagination.page_size)
    return [MobilityLogOut.model_validate(m) for m in logs]


# ── FR-7.4: Challenges ───────────────────────────────────────────���───────────

@router.post("/challenges", response_model=ChallengeOut, status_code=status.HTTP_201_CREATED, summary="FR-7.4 Create challenge")
async def create_challenge(body: ChallengeCreate, db: DBSession, current_user: AdminUser):
    challenge = await svc.create_challenge(db, body.model_dump(), created_by=current_user["user_id"])
    return ChallengeOut.model_validate(challenge)


@router.get("/challenges", response_model=list[ChallengeOut], summary="FR-7.4 List challenges")
async def list_challenges(
    db: DBSession, current_user: CurrentUser, pagination: Pagination,
    challenge_status: str | None = Query(None, alias="status"),
    organization_id: int | None = Query(None),
):
    items = await svc.list_challenges(
        db, offset=pagination.offset, limit=pagination.page_size,
        status=challenge_status, org_id=organization_id,
    )
    return [ChallengeOut.model_validate(c) for c in items]


@router.get("/challenges/{challenge_id}", response_model=ChallengeOut, summary="FR-7.4 Get challenge")
async def get_challenge(challenge_id: int, db: DBSession, current_user: CurrentUser):
    challenge = await svc.get_challenge(db, challenge_id)
    if not challenge:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Challenge", challenge_id)
    return ChallengeOut.model_validate(challenge)


@router.post("/challenges/join", response_model=ParticipationOut, status_code=status.HTTP_201_CREATED, summary="FR-7.4 Join a challenge")
async def join_challenge(body: JoinChallengeRequest, db: DBSession, current_user: CurrentUser):
    participation = await svc.join_challenge(db, body.customer_id, body.challenge_id)
    return ParticipationOut.model_validate(participation)


# ── FR-7.5: Impact Summary ───────────────────────────────────────────────────

@router.get("/{customer_id}/impact", response_model=CustomerImpactOut, summary="FR-7.5 Customer sustainability impact")
async def get_impact(customer_id: int, db: DBSession, current_user: CurrentUser):
    customer = await svc.get_customer(db, customer_id)
    if not customer:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Customer", customer_id)
    return CustomerImpactOut(
        customer_id=customer.id,
        total_tokens_earned=customer.total_tokens_earned,
        total_tokens_donated=customer.total_tokens_donated,
        total_steps=customer.total_steps,
        total_distance_km=customer.total_distance_km,
        total_co2_offset=customer.total_co2_offset,
    )