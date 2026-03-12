"""
FR6 — Workforce Engagement & Incentive
Endpoints for work logs, sustainability activity, wallet, leaderboard, rewards.
"""
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter

from app.dependencies.auth import AdminUser, CurrentUser, ManagerUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.workforce import (
    LeaderboardEntryOut,
    LeaderboardOut,
    RedemptionCreate,
    RedemptionOut,
    RewardOut,
    SustainabilityLogCreate,
    TransactionOut,
    WalletOut,
    WorkLogCreate,
    WorkLogOut,
)

router = APIRouter()

# ── Stub helpers ──────────────────────────────────────────────────────────────

_STUB_WORK_LOG = WorkLogOut(
    id=1,
    employee_id=1,
    location_id=1,
    department="Kitchen",
    work_date=date(2024, 6, 3),
    check_in_time=datetime(2024, 6, 3, 8, 0, 0),
    check_out_time=datetime(2024, 6, 3, 16, 0, 0),
    hours_worked=Decimal("8.00"),
    activity_notes="Full shift — prep and service.",
    sustainability_initiative=False,
    initiative_details=None,
    tokens_awarded=Decimal("50.00"),
    logged_by=1,
    created_at=datetime(2024, 6, 3, 16, 5, 0),
    updated_at=datetime(2024, 6, 3, 16, 5, 0),
)

_STUB_TRANSACTION = TransactionOut(
    id=1,
    transaction_type="earn",
    direction="credit",
    amount=Decimal("50.00"),
    description="Work log bonus — 8h shift on 2024-06-03",
    created_at=datetime(2024, 6, 3, 16, 5, 0),
)

_STUB_WALLET = WalletOut(
    wallet_id=1,
    wallet_type="employee",
    balance=Decimal("350.00"),
    currency="GreenToken",
    status="active",
    recent_transactions=[_STUB_TRANSACTION],
)

_STUB_LEADERBOARD_ENTRY = LeaderboardEntryOut(
    id=1,
    rank_position=1,
    employee_id=1,
    employee_name="Alice Johnson",
    score=Decimal("420.00"),
    total_tokens=Decimal("350.00"),
    bonus_tokens=Decimal("70.00"),
    bonus_paid=True,
)

_STUB_LEADERBOARD = LeaderboardOut(
    snapshot_id=1,
    organization_id=1,
    leaderboard_type="weekly",
    period_start=date(2024, 5, 27),
    period_end=date(2024, 6, 2),
    status="closed",
    entries=[_STUB_LEADERBOARD_ENTRY],
)

_STUB_REWARD = RewardOut(
    id=1,
    reward_name="Free Coffee Voucher",
    description="Redeem for one free coffee at any branch.",
    token_cost=Decimal("50.00"),
    reward_type="voucher",
    applicable_to="employee",
    is_active=True,
)

_STUB_REDEMPTION = RedemptionOut(
    id=1,
    actor_type="employee",
    employee_id=1,
    reward_id=1,
    tokens_used=Decimal("50.00"),
    status="completed",
    redeemed_at=datetime(2024, 6, 3, 17, 0, 0),
    voucher_code="VCHR-2024-00001",
    notes=None,
)


# ── FR-6.1: Work log ──────────────────────────────────────────────────────────

@router.post("/work-logs", response_model=WorkLogOut, status_code=201, summary="FR-6.1 Log working hours and activity")
async def create_work_log(body: WorkLogCreate, db: DBSession, current_user: CurrentUser):
    # TODO: implement workforce_service.create_work_log()
    # Auto-awards tokens via leaderboard_service.calculate_tokens()
    # Updates leaderboard entry, sends token notification
    return WorkLogOut(**{
        **_STUB_WORK_LOG.model_dump(),
        "employee_id": body.employee_id,
        "location_id": body.location_id,
        "work_date": body.work_date,
        "hours_worked": body.hours_worked,
        "activity_notes": body.activity_notes,
        "sustainability_initiative": body.sustainability_initiative,
        "initiative_details": body.initiative_details,
    })


@router.get("/work-logs", response_model=PaginatedResponse[WorkLogOut], summary="FR-6.1 My work logs")
async def my_work_logs(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: implement workforce_service.get_my_work_logs()
    return PaginatedResponse.create(items=[_STUB_WORK_LOG], total=1, page=pagination.page, page_size=pagination.page_size)


@router.get("/work-logs/admin", response_model=PaginatedResponse[WorkLogOut], summary="FR-6.1 All org work logs (admin)")
async def all_work_logs(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: implement workforce_service.get_all_work_logs()
    return PaginatedResponse.create(items=[_STUB_WORK_LOG], total=1, page=pagination.page, page_size=pagination.page_size)


# ── FR-6.2: Sustainability log ────────────────────────────────────────────────

@router.post("/sustainability-logs", response_model=WorkLogOut, status_code=201, summary="FR-6.2 Log sustainability initiative participation")
async def create_sustainability_log(body: SustainabilityLogCreate, db: DBSession, current_user: CurrentUser):
    # TODO: reuses create_work_log with sustainability_initiative=True flag
    return WorkLogOut(**{
        **_STUB_WORK_LOG.model_dump(),
        "employee_id": body.employee_id,
        "location_id": body.location_id,
        "work_date": body.work_date,
        "hours_worked": body.hours_worked,
        "sustainability_initiative": True,
        "initiative_details": body.initiative_details,
    })


# ── FR-6.4: Wallet ────────────────────────────────────────────────────────────

@router.get("/wallet", response_model=WalletOut, summary="FR-6.4 My token wallet balance and recent transactions")
async def my_wallet(db: DBSession, current_user: CurrentUser):
    # TODO: query Wallet + WalletTransaction for current user
    # Wallet model owned by Omar; read-only here
    return _STUB_WALLET


# ── FR-6.5: Leaderboard ──────────────────────────────────────────────────────

@router.get("/leaderboard", response_model=LeaderboardOut, summary="FR-6.5 Current week leaderboard (org-scoped)")
async def current_leaderboard(db: DBSession, current_user: CurrentUser):
    # TODO: implement leaderboard_service.get_leaderboard()
    return LeaderboardOut(**{
        **_STUB_LEADERBOARD.model_dump(),
        "period_start": date.today().replace(day=date.today().day - date.today().weekday()),
        "status": "open",
    })


@router.get("/leaderboard/history", response_model=PaginatedResponse[LeaderboardOut], summary="FR-6.5 Historical leaderboard snapshots")
async def leaderboard_history(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: query LeaderboardSnapshot table
    return PaginatedResponse.create(items=[_STUB_LEADERBOARD], total=1, page=pagination.page, page_size=pagination.page_size)


# ── FR-6.8: Rewards and redemptions ──────────────────────────────────────────

@router.get("/rewards", response_model=PaginatedResponse[RewardOut], summary="FR-6.8 Browse rewards catalog")
async def list_rewards(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: query RewardsCatalog filtered by applicable_to=employee or all
    return PaginatedResponse.create(items=[_STUB_REWARD], total=1, page=pagination.page, page_size=pagination.page_size)


@router.post("/redemptions", response_model=RedemptionOut, status_code=201, summary="FR-6.8 Redeem tokens for voucher")
async def create_redemption(body: RedemptionCreate, db: DBSession, current_user: CurrentUser):
    # TODO: implement workforce_service.create_redemption()
    # Checks wallet balance, deducts tokens, creates Redemption + RewardVoucher rows
    # Calls Omar's wallet_service.debit_tokens()
    return RedemptionOut(**{**_STUB_REDEMPTION.model_dump(), "reward_id": body.reward_id})


@router.get("/redemptions", response_model=PaginatedResponse[RedemptionOut], summary="FR-6.8 My redemption history")
async def my_redemptions(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: query Redemption filtered by employee_id = current employee
    return PaginatedResponse.create(items=[_STUB_REDEMPTION], total=1, page=pagination.page, page_size=pagination.page_size)


@router.get("/redemptions/admin", response_model=PaginatedResponse[RedemptionOut], summary="FR-6.8 All org redemptions (admin)")
async def all_redemptions(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: query all Redemption rows for org
    return PaginatedResponse.create(items=[_STUB_REDEMPTION], total=1, page=pagination.page, page_size=pagination.page_size)
