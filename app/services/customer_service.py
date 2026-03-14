"""
FR7 — Customer Engagement service layer (Omar).
"""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customers import (
    Challenge,
    ChallengeParticipation,
    Customer,
    CustomerVisit,
    MobilityLog,
)


async def create_customer(db: AsyncSession, data: dict) -> Customer:
    customer = Customer(
        **data,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    return customer


async def get_customer(db: AsyncSession, customer_id: int) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()


async def get_customer_by_user(db: AsyncSession, user_id: int) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.user_id == user_id))
    return result.scalar_one_or_none()


async def list_customers(
    db: AsyncSession, offset: int = 0, limit: int = 50,
) -> tuple[list[Customer], int]:
    count_result = await db.execute(select(func.count(Customer.id)))
    total = count_result.scalar() or 0
    result = await db.execute(select(Customer).offset(offset).limit(limit))
    return list(result.scalars().all()), total


async def update_customer(db: AsyncSession, customer_id: int, data: dict) -> Customer:
    customer = await get_customer(db, customer_id)
    if not customer:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Customer", customer_id)
    for key, value in data.items():
        if value is not None:
            setattr(customer, key, value)
    await db.flush()
    await db.refresh(customer)
    return customer


# ── Visits ────────────────────────────────────────────────────────────────────

async def record_visit(db: AsyncSession, data: dict) -> CustomerVisit:
    visit = CustomerVisit(**data, tokens_earned=Decimal("0"))
    db.add(visit)
    await db.flush()
    await db.refresh(visit)
    return visit


async def list_visits(
    db: AsyncSession, customer_id: int, offset: int = 0, limit: int = 50,
) -> list[CustomerVisit]:
    result = await db.execute(
        select(CustomerVisit)
        .where(CustomerVisit.customer_id == customer_id)
        .order_by(CustomerVisit.visit_datetime.desc())
        .offset(offset).limit(limit)
    )
    return list(result.scalars().all())


# ── Mobility Logs ─────────────────────────────────────────────────────────���───

async def log_mobility(db: AsyncSession, data: dict) -> MobilityLog:
    log = MobilityLog(**data, tokens_earned=Decimal("0"))
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def list_mobility_logs(
    db: AsyncSession, customer_id: int, offset: int = 0, limit: int = 50,
) -> list[MobilityLog]:
    result = await db.execute(
        select(MobilityLog)
        .where(MobilityLog.customer_id == customer_id)
        .order_by(MobilityLog.activity_date.desc())
        .offset(offset).limit(limit)
    )
    return list(result.scalars().all())


# ── Challenges ────────────────────────────────────────────────────────────────

async def create_challenge(db: AsyncSession, data: dict, created_by: int | None = None) -> Challenge:
    challenge = Challenge(**data, created_by=created_by)
    db.add(challenge)
    await db.flush()
    await db.refresh(challenge)
    return challenge


async def list_challenges(
    db: AsyncSession, offset: int = 0, limit: int = 50,
    status: str | None = None, org_id: int | None = None,
) -> list[Challenge]:
    stmt = select(Challenge)
    if status:
        stmt = stmt.where(Challenge.status == status)
    if org_id:
        stmt = stmt.where(Challenge.organization_id == org_id)
    result = await db.execute(stmt.offset(offset).limit(limit))
    return list(result.scalars().all())


async def get_challenge(db: AsyncSession, challenge_id: int) -> Challenge | None:
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    return result.scalar_one_or_none()


async def join_challenge(db: AsyncSession, customer_id: int, challenge_id: int) -> ChallengeParticipation:
    participation = ChallengeParticipation(
        challenge_id=challenge_id,
        customer_id=customer_id,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(participation)
    await db.flush()
    await db.refresh(participation)
    return participation