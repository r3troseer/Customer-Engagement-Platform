"""
APScheduler instance and lifecycle management.
Wired into FastAPI via lifespan context in main.py.

Cron jobs owned by this dev:
  FR-6.6  — Weekly leaderboard reset     (Sun 23:59)
  FR-6.7  — Monday bonus token award     (Mon 00:05)
  FR-11.6 — Scheduled report generation  (Daily 02:00)
  FR-12.2 — Compliance expiry alerts     (Daily 08:00)
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)


def start_scheduler() -> None:
    from app.tasks.leaderboard_tasks import award_monday_bonuses, reset_all_leaderboards
    from app.tasks.compliance_tasks import check_certification_expiry
    from app.tasks.report_tasks import run_scheduled_reports

    # FR-6.6: Weekly leaderboard reset — Sunday 23:59 local time
    scheduler.add_job(
        reset_all_leaderboards,
        CronTrigger(day_of_week="sun", hour=23, minute=59, timezone=settings.SCHEDULER_TIMEZONE),
        id="weekly_leaderboard_reset",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # FR-6.7: Monday bonus token award — Monday 00:05 (after midnight reset completes)
    scheduler.add_job(
        award_monday_bonuses,
        CronTrigger(day_of_week="mon", hour=0, minute=5, timezone=settings.SCHEDULER_TIMEZONE),
        id="monday_bonus_award",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # FR-11.6: Scheduled report generation — daily 02:00
    scheduler.add_job(
        run_scheduled_reports,
        CronTrigger(hour=2, minute=0, timezone=settings.SCHEDULER_TIMEZONE),
        id="scheduled_reports",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # FR-12.2: Compliance expiry alerts — daily 08:00
    scheduler.add_job(
        check_certification_expiry,
        CronTrigger(hour=8, minute=0, timezone=settings.SCHEDULER_TIMEZONE),
        id="compliance_expiry_check",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.start()
    logger.info("APScheduler started with %d jobs", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")
