"""
FR6 — Workforce Engagement & Incentive
Endpoints for work logs, sustainability activity, wallet, leaderboard, rewards.
"""
from fastapi import APIRouter

from app.dependencies.auth import AdminUser, CurrentUser, ManagerUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination

router = APIRouter()


# ── FR-6.1: Work log ──────────────────────────────────────────────────────────

@router.post("/work-logs", summary="FR-6.1 Log working hours and activity")
async def create_work_log(db: DBSession, current_user: CurrentUser):
    # TODO: implement workforce_service.create_work_log()
    # Auto-awards tokens via leaderboard_service.calculate_tokens()
    # Updates leaderboard entry, sends token notification
    raise NotImplementedError


@router.get("/work-logs", summary="FR-6.1 My work logs")
async def my_work_logs(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: implement workforce_service.get_my_work_logs()
    raise NotImplementedError


@router.get("/work-logs/admin", summary="FR-6.1 All org work logs (admin)")
async def all_work_logs(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: implement workforce_service.get_all_work_logs()
    raise NotImplementedError


# ── FR-6.2: Sustainability log ────────────────────────────────────────────────

@router.post("/sustainability-logs", summary="FR-6.2 Log sustainability initiative participation")
async def create_sustainability_log(db: DBSession, current_user: CurrentUser):
    # TODO: reuses create_work_log with sustainability_initiative=True flag
    raise NotImplementedError


# ── FR-6.4: Wallet ────────────────────────────────────────────────────────────

@router.get("/wallet", summary="FR-6.4 My token wallet balance and recent transactions")
async def my_wallet(db: DBSession, current_user: CurrentUser):
    # TODO: query Wallet + WalletTransaction for current user
    # Wallet model owned by Omar; read-only here
    raise NotImplementedError


# ── FR-6.5: Leaderboard ──────────────────────────────────────────────────────

@router.get("/leaderboard", summary="FR-6.5 Current week leaderboard (org-scoped)")
async def current_leaderboard(db: DBSession, current_user: CurrentUser):
    # TODO: implement leaderboard_service.get_leaderboard()
    raise NotImplementedError


@router.get("/leaderboard/history", summary="FR-6.5 Historical leaderboard snapshots")
async def leaderboard_history(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: query LeaderboardSnapshot table
    raise NotImplementedError


# ── FR-6.8: Rewards and redemptions ──────────────────────────────────────────

@router.get("/rewards", summary="FR-6.8 Browse rewards catalog")
async def list_rewards(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: query RewardsCatalog filtered by applicable_to=employee or all
    raise NotImplementedError


@router.post("/redemptions", summary="FR-6.8 Redeem tokens for voucher")
async def create_redemption(db: DBSession, current_user: CurrentUser):
    # TODO: implement workforce_service.create_redemption()
    # Checks wallet balance, deducts tokens, creates Redemption + RewardVoucher rows
    # Calls Omar's wallet_service.debit_tokens()
    raise NotImplementedError


@router.get("/redemptions", summary="FR-6.8 My redemption history")
async def my_redemptions(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: query Redemption filtered by employee_id = current employee
    raise NotImplementedError


@router.get("/redemptions/admin", summary="FR-6.8 All org redemptions (admin)")
async def all_redemptions(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: query all Redemption rows for org
    raise NotImplementedError
