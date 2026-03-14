"""
FR-6.6 / FR-6.7: Leaderboard cron jobs.
reset_all_leaderboards — Sunday 23:59
award_monday_bonuses   — Monday 00:05
"""
import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.org import Organization
from app.services import leaderboard_service

logger = logging.getLogger(__name__)


async def _get_all_active_org_ids(db) -> list[int]:
    result = await db.execute(
        select(Organization.id).where(Organization.status == "active")
    )
    return list(result.scalars().all())


async def reset_all_leaderboards() -> None:
    """
    FR-6.6: Snapshot and reset the leaderboard for every active organisation.
    Called Sunday 23:59 by APScheduler.
    """
    async with AsyncSessionLocal() as db:
        org_ids = await _get_all_active_org_ids(db)
        for org_id in org_ids:
            try:
                await leaderboard_service.reset_leaderboard(db, org_id)
                await db.commit()
                logger.info("Leaderboard reset for org %s", org_id)
            except Exception as exc:
                await db.rollback()
                logger.error("Leaderboard reset failed for org %s: %s", org_id, exc)


async def award_monday_bonuses() -> None:
    """
    FR-6.7: Award bonus tokens to the top-N employees per org from last week.
    Called Monday 00:05 by APScheduler.
    """
    async with AsyncSessionLocal() as db:
        org_ids = await _get_all_active_org_ids(db)
        for org_id in org_ids:
            try:
                await leaderboard_service.award_monday_bonus(
                    db, org_id, top_n=settings.LEADERBOARD_TOP_N_BONUS
                )
                await db.commit()
                logger.info("Monday bonuses awarded for org %s", org_id)
            except Exception as exc:
                await db.rollback()
                logger.error("Monday bonus failed for org %s: %s", org_id, exc)
