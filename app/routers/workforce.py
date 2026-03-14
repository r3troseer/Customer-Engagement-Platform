"""
FR6 — Workforce Engagement & Incentive
Endpoints for work logs, sustainability activity, wallet, leaderboard, rewards.
"""
from fastapi import APIRouter

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.models.workforce import LeaderboardEntry, LeaderboardSnapshot
from app.schemas.common import PaginatedResponse
from app.schemas.workforce import (
    LeaderboardEntryOut,
    LeaderboardOut,
    RedemptionCreate,
    RedemptionOut,
    RewardOut,
    SustainabilityLogCreate,
    WalletOut,
    WorkLogCreate,
    WorkLogOut,
)
from app.services import leaderboard_service, workforce_service

router = APIRouter()


# ── Mapping helpers ───────────────────────────────────────────────────────────

def _entry_to_out(entry: LeaderboardEntry) -> LeaderboardEntryOut:
    return LeaderboardEntryOut(
        id=entry.id,
        rank_position=entry.rank_position,
        employee_id=entry.employee_id,
        employee_name="",  # TODO: join Employee→User name when Omar's User model merges
        score=entry.score,
        total_tokens=entry.total_tokens,
        bonus_tokens=entry.bonus_tokens,
        bonus_paid=entry.bonus_paid,
    )


def _snapshot_to_out(snapshot: LeaderboardSnapshot) -> LeaderboardOut:
    return LeaderboardOut(
        snapshot_id=snapshot.id,
        organization_id=snapshot.organization_id,
        leaderboard_type=snapshot.leaderboard_type,
        period_start=snapshot.period_start,
        period_end=snapshot.period_end,
        status=snapshot.status,
        entries=[_entry_to_out(e) for e in snapshot.entries],
    )


# ── FR-6.1: Work logs ─────────────────────────────────────────────────────────

@router.post("/work-logs", response_model=WorkLogOut, status_code=201, summary="FR-6.1 Log working hours and activity")
async def create_work_log(body: WorkLogCreate, db: DBSession, current_user: CurrentUser):
    log = await workforce_service.create_work_log(db, body, current_user)
    return WorkLogOut.model_validate(log)


@router.get("/work-logs", response_model=PaginatedResponse[WorkLogOut], summary="FR-6.1 My work logs")
async def my_work_logs(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    logs, total = await workforce_service.get_my_work_logs(db, current_user, pagination.offset, pagination.page_size)
    return PaginatedResponse.create(
        items=[WorkLogOut.model_validate(l) for l in logs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/work-logs/admin", response_model=PaginatedResponse[WorkLogOut], summary="FR-6.1 All org work logs (admin)")
async def all_work_logs(db: DBSession, current_user: AdminUser, pagination: Pagination):
    org_id = current_user.get("org_id")  # TODO: resolve org_id from user when Sunny's org model merges
    logs, total = await workforce_service.get_all_work_logs(db, org_id, pagination.offset, pagination.page_size)
    return PaginatedResponse.create(
        items=[WorkLogOut.model_validate(l) for l in logs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


# ── FR-6.2: Sustainability log ────────────────────────────────────────────────

@router.post("/sustainability-logs", response_model=WorkLogOut, status_code=201, summary="FR-6.2 Log sustainability initiative participation")
async def create_sustainability_log(body: SustainabilityLogCreate, db: DBSession, current_user: CurrentUser):
    log = await workforce_service.create_sustainability_log(db, body, current_user)
    return WorkLogOut.model_validate(log)


# ── FR-6.4: Wallet ────────────────────────────────────────────────────────────

@router.get("/wallet", response_model=WalletOut, summary="FR-6.4 My token wallet balance and recent transactions")
async def my_wallet(db: DBSession, current_user: CurrentUser):
    return await workforce_service.get_wallet(db, current_user["user_id"])


# ── FR-6.5: Leaderboard ──────────────────────────────────────────────────────

@router.get("/leaderboard", response_model=LeaderboardOut, summary="FR-6.5 Current week leaderboard (org-scoped)")
async def current_leaderboard(db: DBSession, current_user: CurrentUser):
    employee = await workforce_service._get_employee(db, current_user["user_id"])
    snapshot = await leaderboard_service.get_leaderboard(db, org_id=employee.organization_id)
    if snapshot is None:
        snapshot = await leaderboard_service.get_or_create_open_snapshot(db, employee.organization_id)
        await db.commit()
        snapshot.entries = []
    return _snapshot_to_out(snapshot)


@router.get("/leaderboard/history", response_model=PaginatedResponse[LeaderboardOut], summary="FR-6.5 Historical leaderboard snapshots")
async def leaderboard_history(db: DBSession, current_user: AdminUser, pagination: Pagination):
    employee = await workforce_service._get_employee(db, current_user["user_id"])
    snapshots, total = await leaderboard_service.get_leaderboard_history(
        db, employee.organization_id, pagination.offset, pagination.page_size
    )
    return PaginatedResponse.create(
        items=[_snapshot_to_out(s) for s in snapshots],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


# ── FR-6.8: Rewards and redemptions ──────────────────────────────────────────

@router.get("/rewards", response_model=PaginatedResponse[RewardOut], summary="FR-6.8 Browse rewards catalog")
async def list_rewards(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    rewards, total = await workforce_service.list_rewards(db, pagination.offset, pagination.page_size)
    return PaginatedResponse.create(
        items=[RewardOut.model_validate(r) for r in rewards],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/redemptions", response_model=RedemptionOut, status_code=201, summary="FR-6.8 Redeem tokens for voucher")
async def create_redemption(body: RedemptionCreate, db: DBSession, current_user: CurrentUser):
    redemption = await workforce_service.create_redemption(db, body.reward_id, current_user)
    return RedemptionOut(
        id=redemption.id,
        actor_type=redemption.actor_type,
        employee_id=redemption.employee_id,
        reward_id=redemption.reward_id,
        tokens_used=redemption.tokens_used,
        status=redemption.status,
        redeemed_at=redemption.redeemed_at,
        voucher_code=getattr(redemption, "voucher_code", None),
        notes=redemption.notes,
    )


@router.get("/redemptions", response_model=PaginatedResponse[RedemptionOut], summary="FR-6.8 My redemption history")
async def my_redemptions(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    redemptions, total = await workforce_service.get_my_redemptions(db, current_user, pagination.offset, pagination.page_size)
    return PaginatedResponse.create(
        items=[RedemptionOut.model_validate(r) for r in redemptions],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/redemptions/admin", response_model=PaginatedResponse[RedemptionOut], summary="FR-6.8 All org redemptions (admin)")
async def all_redemptions(db: DBSession, current_user: AdminUser, pagination: Pagination):
    employee = await workforce_service._get_employee(db, current_user["user_id"])
    redemptions, total = await workforce_service.get_all_redemptions(
        db, employee.organization_id, pagination.offset, pagination.page_size
    )
    return PaginatedResponse.create(
        items=[RedemptionOut.model_validate(r) for r in redemptions],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
