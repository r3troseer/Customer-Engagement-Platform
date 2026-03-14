"""
FR6 — Leaderboard service.
Token calculation, leaderboard upsert, weekly snapshot reset, Monday bonus awards.
"""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org import Employee
from app.models.tokens import TokenRule
from app.models.workforce import LeaderboardEntry, LeaderboardSnapshot
from app.services.audit_service import AuditLogService
from app.services.token_service import credit_tokens, get_wallet_by_user


# ── Pure helpers (no I/O) ─────────────────────────────────────────────────────

def _calculate_tokens(
    token_rule: TokenRule | None,
    hours_worked: Decimal | None,
) -> Decimal:
    """
    Calculate tokens to award for a work log entry.

    Formula: tokens_awarded * hours_worked (per-hour rate).
    Falls back to flat tokens_awarded when hours_worked is None.

    NOTE: TokenRule.condition_details (JSONB) is intentionally ignored here.
    The JSONB schema is undefined until Omar's branch merges. Revisit in FR6 phase 2.
    """
    if token_rule is None:
        return Decimal("0")
    if hours_worked is None:
        return token_rule.tokens_awarded
    return token_rule.tokens_awarded * hours_worked


def _calculate_score(
    tokens: Decimal,
    is_sustainability: bool,
    bonus_rule: TokenRule | None,
) -> Decimal:
    """
    Calculate leaderboard score.

    Score = tokens + sustainability bonus (Option C).
    Regular logs: score == tokens.
    Sustainability logs: score += bonus_rule.tokens_awarded if a bonus rule exists.
    """
    if is_sustainability and bonus_rule is not None:
        return tokens + bonus_rule.tokens_awarded
    return tokens


def _assign_ranks(entries: list[LeaderboardEntry]) -> list[LeaderboardEntry]:
    """Sort entries by score DESC and assign rank_position (1-indexed)."""
    sorted_entries = sorted(entries, key=lambda e: e.score, reverse=True)
    for i, entry in enumerate(sorted_entries, start=1):
        entry.rank_position = i
    return sorted_entries


def _current_week_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())  # ISO: Monday = 0


# ── Async DB functions ────────────────────────────────────────────────────────

async def _fetch_token_rule(
    db: AsyncSession,
    rule_type: str,
    org_id: int,
) -> TokenRule | None:
    """
    Fetch the most specific active TokenRule for the given rule_type.
    Prefers org-specific rule over global (org_id IS NULL) rule.
    """
    result = await db.execute(
        select(TokenRule)
        .where(
            TokenRule.rule_type == rule_type,
            TokenRule.is_active.is_(True),
            (TokenRule.organization_id == org_id) | (TokenRule.organization_id.is_(None)),
        )
        .order_by(TokenRule.organization_id.nulls_last())  # org-specific first
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_or_create_open_snapshot(
    db: AsyncSession,
    org_id: int,
) -> LeaderboardSnapshot:
    """
    Return the current open LeaderboardSnapshot for the org.
    Creates a new one (current ISO week) if none exists.
    """
    result = await db.execute(
        select(LeaderboardSnapshot).where(
            LeaderboardSnapshot.organization_id == org_id,
            LeaderboardSnapshot.status == "open",
        )
    )
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        monday = _current_week_monday()
        sunday = monday + timedelta(days=6)
        snapshot = LeaderboardSnapshot(
            organization_id=org_id,
            leaderboard_type="weekly",
            period_start=monday,
            period_end=sunday,
            status="open",
        )
        db.add(snapshot)
        await db.flush()  # get snapshot.id without committing

    return snapshot


async def calculate_and_award_tokens(
    db: AsyncSession,
    org_id: int,
    hours_worked: Decimal | None,
    is_sustainability: bool,
) -> tuple[Decimal, Decimal]:
    """
    Calculate tokens and score for a work log entry.
    Returns (tokens, score) — does NOT write to DB.
    """
    work_rule = await _fetch_token_rule(db, "work_log", org_id)
    bonus_rule = await _fetch_token_rule(db, "sustainability_bonus", org_id)

    tokens = _calculate_tokens(work_rule, hours_worked)
    score = _calculate_score(tokens, is_sustainability, bonus_rule)
    return tokens, score


async def update_leaderboard_entry(
    db: AsyncSession,
    employee_id: int,
    org_id: int,
    score_delta: Decimal,
    token_delta: Decimal,
) -> None:
    """
    Upsert a LeaderboardEntry for the employee in the current open snapshot.
    Uses PostgreSQL INSERT ... ON CONFLICT DO UPDATE for atomic increment.
    """
    snapshot = await get_or_create_open_snapshot(db, org_id)

    stmt = (
        pg_insert(LeaderboardEntry)
        .values(
            leaderboard_id=snapshot.id,
            employee_id=employee_id,
            score=score_delta,
            total_tokens=token_delta,
            bonus_tokens=Decimal("0"),
            bonus_paid=False,
        )
        .on_conflict_do_update(
            index_elements=["leaderboard_id", "employee_id"],
            set_={
                "score": LeaderboardEntry.score + score_delta,
                "total_tokens": LeaderboardEntry.total_tokens + token_delta,
                "updated_at": func.now(),
            },
        )
    )
    await db.execute(stmt)


async def get_leaderboard(
    db: AsyncSession,
    org_id: int,
    week_start: date | None = None,
) -> LeaderboardSnapshot | None:
    """
    Return the leaderboard snapshot for the org.
    If week_start is given, returns the snapshot for that week.
    Otherwise returns the current open snapshot.
    Entries are sorted and ranked.
    """
    if week_start is not None:
        result = await db.execute(
            select(LeaderboardSnapshot).where(
                LeaderboardSnapshot.organization_id == org_id,
                LeaderboardSnapshot.period_start == week_start,
            )
        )
    else:
        result = await db.execute(
            select(LeaderboardSnapshot).where(
                LeaderboardSnapshot.organization_id == org_id,
                LeaderboardSnapshot.status == "open",
            )
        )

    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        return None

    snapshot.entries = _assign_ranks(list(snapshot.entries))
    return snapshot


async def get_leaderboard_history(
    db: AsyncSession,
    org_id: int,
    offset: int,
    limit: int,
) -> tuple[list[LeaderboardSnapshot], int]:
    """Return paginated closed leaderboard snapshots for the org, newest first."""
    base = select(LeaderboardSnapshot).where(
        LeaderboardSnapshot.organization_id == org_id,
        LeaderboardSnapshot.status == "closed",
    )
    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(
        base.order_by(LeaderboardSnapshot.period_start.desc())
        .offset(offset)
        .limit(limit)
    )
    snapshots = list(result.scalars().all())
    for s in snapshots:
        s.entries = _assign_ranks(list(s.entries))
    return snapshots, total


async def reset_leaderboard(
    db: AsyncSession,
    org_id: int,
) -> LeaderboardSnapshot:
    """
    FR-6.6: Close the current open snapshot and create a new one for next week.
    Returns the closed snapshot (used by award_monday_bonus).
    """
    snapshot = await get_or_create_open_snapshot(db, org_id)

    snapshot.status = "closed"
    snapshot.reset_date = date.today()

    # New snapshot: next Monday → following Sunday
    next_monday = _current_week_monday() + timedelta(weeks=1)
    next_sunday = next_monday + timedelta(days=6)
    new_snapshot = LeaderboardSnapshot(
        organization_id=org_id,
        leaderboard_type="weekly",
        period_start=next_monday,
        period_end=next_sunday,
        status="open",
    )
    db.add(new_snapshot)
    await AuditLogService.create(db, {"action": "leaderboard.reset", "entity_type": "leaderboard_snapshots", "entity_id": snapshot.id, "user_id": None})

    return snapshot


async def award_monday_bonus(
    db: AsyncSession,
    org_id: int,
    top_n: int,
) -> None:
    """
    FR-6.7: Award bonus tokens to the top-N employees from last week's closed snapshot.
    Called Monday 00:05 by APScheduler.
    """
    result = await db.execute(
        select(LeaderboardSnapshot)
        .where(
            LeaderboardSnapshot.organization_id == org_id,
            LeaderboardSnapshot.status == "closed",
        )
        .order_by(LeaderboardSnapshot.period_start.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        return

    bonus_rule = await _fetch_token_rule(db, "leaderboard_bonus", org_id)
    if bonus_rule is None:
        return

    ranked = _assign_ranks(list(snapshot.entries))
    winners = ranked[:top_n]

    for entry in winners:
        entry.bonus_tokens = entry.bonus_tokens + bonus_rule.tokens_awarded
        entry.bonus_paid = True

        emp_result = await db.execute(
            select(Employee.user_id).where(Employee.id == entry.employee_id)
        )
        user_id = emp_result.scalar_one_or_none()
        if user_id is not None:
            wallet = await get_wallet_by_user(db, user_id)
            if wallet:
                await credit_tokens(
                    db, wallet.id, bonus_rule.tokens_awarded,
                    tx_type="earn",
                    description="Leaderboard bonus",
                    reference_type="leaderboard_entries",
                    reference_id=entry.id,
                )
        # TODO: notify — notification_service.notify_leaderboard_rank(entry.employee_id, entry.rank_position)
        await AuditLogService.create(db, {"action": "tokens.bonus_awarded", "entity_type": "leaderboard_entries", "entity_id": entry.id, "user_id": user_id})
