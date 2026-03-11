"""
FR-11.6: Scheduled report generation cron job.
run_scheduled_reports — daily 02:00
"""
import logging

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def run_scheduled_reports() -> None:
    """
    FR-11.6: Execute all report templates with schedule_enabled=True.
    Called daily at 02:00 by APScheduler.
    """
    # TODO:
    # async with AsyncSessionLocal() as db:
    #     templates = await reporting_service.get_scheduled_templates(db)
    #     for template in templates:
    #         try:
    #             run = await reporting_service.execute_report_run(db, template)
    #             await db.commit()
    #             if template.notify_on_complete:
    #                 await notification_service.notify_report_ready(db, run)
    #         except Exception as exc:
    #             await db.rollback()
    #             logger.error("Scheduled report %s failed: %s", template.id, exc)
    logger.info("run_scheduled_reports triggered (not yet implemented)")
