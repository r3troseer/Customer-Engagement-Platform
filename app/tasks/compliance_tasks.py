"""
FR-12.2: Compliance certification expiry alert cron job.
check_certification_expiry — daily 08:00
"""
import logging
from datetime import date, timedelta

from app.core.config import settings
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def check_certification_expiry() -> None:
    """
    FR-12.2: Find supplier certs expiring within warning/critical thresholds
    and send alerts to org employees.
    Called daily at 08:00 by APScheduler.
    """
    from app.services import notification_service, supplier_service

    async with AsyncSessionLocal() as db:
        today = date.today()
        warning_threshold = today + timedelta(days=settings.CERT_EXPIRY_WARNING_DAYS)

        try:
            expiring_docs = await supplier_service.get_expiring_certs(db, warning_threshold)
            for doc in expiring_docs:
                days_left = (doc.expiry_date - today).days
                severity = "critical" if days_left <= settings.CERT_EXPIRY_CRITICAL_DAYS else "warning"
                await notification_service.notify_admins_cert_expiry(db, doc, severity, days_left)
            await db.commit()
            logger.info("check_certification_expiry: processed %d expiring docs", len(expiring_docs))
        except Exception as exc:
            await db.rollback()
            logger.error("check_certification_expiry failed: %s", exc)
