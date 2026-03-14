"""
FR6 — Workforce Engagement service layer.
Work log creation, sustainability logging, token auto-award, wallet read, redemptions.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, UnprocessableError
from app.models.org import Employee
from app.models.tokens import RewardsCatalog, RewardVoucher
from app.models.workforce import Redemption, WorkLog
from app.schemas.workforce import WalletOut, TransactionOut
from app.services import leaderboard_service
from app.services.audit_service import AuditLogService
from app.services.token_service import credit_tokens, debit_tokens, get_transactions, get_wallet_by_user


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_employee(db: AsyncSession, user_id: int) -> Employee:
    """Resolve the active Employee record for the given user_id. Raises 404 if not found."""
    result = await db.execute(
        select(Employee).where(
            Employee.user_id == user_id,
            Employee.employment_status == "active",
        )
    )
    employee = result.scalar_one_or_none()
    if employee is None:
        raise NotFoundError("Employee", user_id)
    return employee


# ── Work logs ─────────────────────────────────────────────────────────────────

async def create_work_log(
    db: AsyncSession,
    data,  # WorkLogCreate
    current_user: dict,
) -> WorkLog:
    """
    FR-6.1: Create a work log entry and auto-award tokens.
    1. Resolve employee from JWT user_id.
    2. Insert WorkLog row.
    3. Calculate tokens + score via leaderboard_service.
    4. Update WorkLog.tokens_awarded.
    5. Upsert leaderboard entry.
    6. Commit.
    """
    employee = await _get_employee(db, current_user["user_id"])

    log = WorkLog(
        employee_id=employee.id,
        location_id=data.location_id,
        work_date=data.work_date,
        department=data.department,
        check_in_time=data.check_in_time,
        check_out_time=data.check_out_time,
        hours_worked=data.hours_worked,
        activity_notes=data.activity_notes,
        sustainability_initiative=data.sustainability_initiative,
        initiative_details=data.initiative_details,
        tokens_awarded=0,
        logged_by=current_user["user_id"],
    )
    db.add(log)
    await db.flush()  # get log.id

    tokens, score = await leaderboard_service.calculate_and_award_tokens(
        db,
        org_id=employee.organization_id,
        hours_worked=data.hours_worked,
        is_sustainability=data.sustainability_initiative,
    )

    log.tokens_awarded = tokens

    if tokens > 0:
        await leaderboard_service.update_leaderboard_entry(
            db,
            employee_id=employee.id,
            org_id=employee.organization_id,
            score_delta=score,
            token_delta=tokens,
        )
        wallet = await get_wallet_by_user(db, current_user["user_id"])
        if wallet:
            await credit_tokens(
                db, wallet.id, tokens,
                tx_type="earn",
                description=f"Work log — {data.work_date}",
                reference_type="work_logs",
                reference_id=log.id,
            )
        from app.services import notification_service
        await notification_service.notify_token_awarded(db, employee.id, tokens)

    await db.commit()
    await db.refresh(log)
    await AuditLogService.create(db, {"action": "work_log.created", "entity_type": "work_logs", "entity_id": log.id, "user_id": current_user["user_id"]})
    return log


async def create_sustainability_log(
    db: AsyncSession,
    data,  # SustainabilityLogCreate
    current_user: dict,
) -> WorkLog:
    """FR-6.2: Convenience wrapper — forces sustainability_initiative=True."""
    from app.schemas.workforce import WorkLogCreate
    work_data = WorkLogCreate(
        employee_id=0,  # ignored — resolved from JWT
        location_id=data.location_id,
        work_date=data.work_date,
        hours_worked=data.hours_worked,
        initiative_details=data.initiative_details,
        sustainability_initiative=True,
    )
    return await create_work_log(db, work_data, current_user)


async def get_my_work_logs(
    db: AsyncSession,
    current_user: dict,
    offset: int,
    limit: int,
) -> tuple[list[WorkLog], int]:
    """FR-6.1: Return paginated work logs for the current employee."""
    employee = await _get_employee(db, current_user["user_id"])

    base = select(WorkLog).where(WorkLog.employee_id == employee.id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.order_by(WorkLog.work_date.desc()).offset(offset).limit(limit))).scalars().all()
    return list(rows), total


async def get_all_work_logs(
    db: AsyncSession,
    org_id: int,
    offset: int,
    limit: int,
) -> tuple[list[WorkLog], int]:
    """FR-6.1 (admin): Return paginated work logs for the entire org."""
    base = (
        select(WorkLog)
        .join(Employee, WorkLog.employee_id == Employee.id)
        .where(Employee.organization_id == org_id)
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.order_by(WorkLog.work_date.desc()).offset(offset).limit(limit))).scalars().all()
    return list(rows), total


# ── Wallet ────────────────────────────────────────────────────────────────────

async def get_wallet(db: AsyncSession, user_id: int) -> WalletOut:
    """FR-6.4: Read the employee's wallet balance and recent transactions."""
    wallet = await get_wallet_by_user(db, user_id)
    if wallet is None:
        raise NotFoundError("Wallet", user_id)

    transactions = await get_transactions(db, wallet.id, limit=10)

    return WalletOut(
        wallet_id=wallet.id,
        wallet_type=wallet.wallet_type,
        balance=wallet.balance,
        currency="GreenToken",
        status=wallet.status,
        recent_transactions=[
            TransactionOut(
                id=tx.id,
                transaction_type=tx.transaction_type,
                direction=tx.direction,
                amount=tx.amount,
                description=tx.description,
                created_at=tx.created_at,
            )
            for tx in transactions
        ],
    )


# ── Rewards catalog ───────────────────────────────────────────────────────────

async def list_rewards(
    db: AsyncSession,
    offset: int,
    limit: int,
) -> tuple[list[RewardsCatalog], int]:
    """FR-6.8: Browse active rewards applicable to employees."""
    base = select(RewardsCatalog).where(
        RewardsCatalog.applicable_to.in_(["employee", "both"]),
        RewardsCatalog.status == "active",
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.order_by(RewardsCatalog.title).offset(offset).limit(limit))).scalars().all()
    return list(rows), total


# ── Redemptions ───────────────────────────────────────────────────────────────

async def create_redemption(
    db: AsyncSession,
    reward_id: int,
    current_user: dict,
) -> Redemption:
    """
    FR-6.8: Redeem tokens for a reward voucher.
    1. Resolve employee.
    2. Verify reward exists, is active, and is applicable to employees.
    3. Generate voucher code + create RewardVoucher row.
    4. Create Redemption row.
    5. Commit.
    """
    employee = await _get_employee(db, current_user["user_id"])

    reward = (await db.execute(
        select(RewardsCatalog).where(RewardsCatalog.id == reward_id)
    )).scalar_one_or_none()
    if reward is None:
        raise NotFoundError("Reward", reward_id)
    if reward.status != "active":
        raise UnprocessableError(f"Reward '{reward.title}' is not currently active.")
    if reward.applicable_to not in ("employee", "both"):
        raise UnprocessableError(f"Reward '{reward.title}' is not applicable to employees.")

    voucher_code = "VCHR-" + uuid4().hex[:12].upper()
    now = datetime.now(timezone.utc)

    voucher = RewardVoucher(
        reward_id=reward.id,
        user_id=current_user["user_id"],
        voucher_code=voucher_code,
        issued_at=now,
        status="issued",
    )
    db.add(voucher)
    await db.flush()  # get voucher.id

    redemption = Redemption(
        actor_type="employee",
        employee_id=employee.id,
        reward_id=reward.id,
        voucher_id=voucher.id,
        tokens_used=reward.token_cost,
        redeemed_at=now,
        status="completed",
    )
    db.add(redemption)
    await db.flush()  # get redemption.id; commit happens after wallet debit

    wallet = await get_wallet_by_user(db, current_user["user_id"])
    if wallet:
        await debit_tokens(
            db, wallet.id, reward.token_cost,
            tx_type="redeem",
            description=f"Redeemed: {reward.title}",
            reference_type="rewards_catalog",
            reference_id=reward.id,
        )
    from app.services import notification_service
    await notification_service.notify_redemption(db, employee.id, reward.title)
    await AuditLogService.create(db, {"action": "redemption.created", "entity_type": "redemptions", "entity_id": redemption.id, "user_id": current_user["user_id"]})
    await db.refresh(redemption)

    # Attach voucher_code for the response schema (not a column on Redemption)
    redemption.voucher_code = voucher_code  # type: ignore[attr-defined]
    return redemption


async def get_my_redemptions(
    db: AsyncSession,
    current_user: dict,
    offset: int,
    limit: int,
) -> tuple[list[Redemption], int]:
    """FR-6.8: Return paginated redemption history for the current employee."""
    employee = await _get_employee(db, current_user["user_id"])

    base = select(Redemption).where(Redemption.employee_id == employee.id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.order_by(Redemption.redeemed_at.desc()).offset(offset).limit(limit))).scalars().all()
    return list(rows), total


async def get_all_redemptions(
    db: AsyncSession,
    org_id: int,
    offset: int,
    limit: int,
) -> tuple[list[Redemption], int]:
    """FR-6.8 (admin): Return paginated redemption history for the entire org."""
    base = (
        select(Redemption)
        .join(Employee, Redemption.employee_id == Employee.id)
        .where(Employee.organization_id == org_id)
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.order_by(Redemption.redeemed_at.desc()).offset(offset).limit(limit))).scalars().all()
    return list(rows), total
