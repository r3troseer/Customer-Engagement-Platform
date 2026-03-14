"""
FR12 — Notification & Alert service.
Called internally by other services — never exposed as a public endpoint.
Dispatches in-app, email (SMTP), and push (FCM) notifications.
"""
import asyncio
import json
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notifications import Notification, NotificationLog, NotificationPreference
from app.models.org import Employee
from app.services.auth_service import get_user_by_id

logger = logging.getLogger(__name__)


# ── Category helper ───────────────────────────────────────────────────────────

def _category_enabled(prefs, notification_type: str) -> bool:
    """Return True if this notification_type is enabled in user's preferences."""
    mapping = {
        "token_reward": prefs.reward_notifications_enabled,
        "leaderboard": prefs.reward_notifications_enabled,
        "compliance": prefs.compliance_alerts_enabled,
        "expiry": prefs.compliance_alerts_enabled,
        "report": prefs.report_notifications_enabled,
        "challenge": prefs.challenge_notifications_enabled,
    }
    return mapping.get(notification_type, True)


# ── Transport helpers ─────────────────────────────────────────────────────────

def _send_email_sync(to_email: str, subject: str, body_html: str) -> None:
    """Synchronous SMTP send — run in executor to avoid blocking the event loop."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured — skipping email to %s", to_email)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, msg.as_string())


async def send_email(to_email: str, subject: str, body_html: str) -> None:
    """Async wrapper around SMTP send. Never raises — logs on failure."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_email_sync, to_email, subject, body_html)
        logger.info("Email sent to %s — subject: %s", to_email, subject)
    except Exception as exc:
        logger.error("Email delivery failed to %s: %s", to_email, exc)


async def send_push(
    device_token: str | None,
    title: str,
    body: str,
    data: dict | None = None,
) -> None:
    """
    FCM push notification via legacy HTTP API.
    Silently skips if device_token or FCM_SERVER_KEY is not configured.
    Never raises — logs on failure.
    """
    if not device_token or not settings.FCM_SERVER_KEY:
        return

    payload: dict = {
        "to": device_token,
        "notification": {"title": title, "body": body},
    }
    if data:
        payload["data"] = data

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://fcm.googleapis.com/fcm/send",
                headers={
                    "Authorization": f"key={settings.FCM_SERVER_KEY}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(payload),
            )
            resp.raise_for_status()
            logger.info("Push notification sent to device %s…", device_token[:8])
    except Exception as exc:
        logger.error("Push delivery failed: %s", exc)


# ── Core dispatcher ───────────────────────────────────────────────────────────

async def create_and_dispatch(
    db: AsyncSession,
    recipient_id: int,
    notification_type: str,
    title: str,
    body: str,
    ref_type: str | None = None,
    ref_id: int | None = None,
    org_id: int | None = None,
) -> Notification:
    """
    FR-12.1 / FR-12.3: Create an in-app notification and optionally
    dispatch email and push based on the user's preferences.
    """
    # 1. Load preferences — fall back to permissive defaults if no row exists
    prefs_result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == recipient_id)
    )
    prefs = prefs_result.scalar_one_or_none()

    class _DefaultPrefs:
        email_enabled = True
        push_enabled = True
        in_app_enabled = True
        reward_notifications_enabled = True
        compliance_alerts_enabled = True
        report_notifications_enabled = True
        challenge_notifications_enabled = True

    if prefs is None:
        prefs = _DefaultPrefs()  # type: ignore[assignment]

    # 2. Always insert in-app Notification row
    notification = Notification(
        user_id=recipient_id,
        organization_id=org_id,
        title=title,
        message=body,
        notification_type=notification_type,
        related_type=ref_type,
        related_id=ref_id,
        is_read=False,
    )
    db.add(notification)
    await db.flush()  # get notification.id

    now = datetime.now(timezone.utc)

    # 3. Email dispatch
    if prefs.email_enabled and _category_enabled(prefs, notification_type):
        user = await get_user_by_id(db, recipient_id)
        if user and user.email:
            await send_email(user.email, title, body)
            db.add(NotificationLog(
                notification_id=notification.id,
                delivery_channel="email",
                delivery_status="sent",
                sent_at=now,
            ))

    # 4. Push dispatch (device_token column not yet on User — skips silently)
    if prefs.push_enabled and _category_enabled(prefs, notification_type):
        device_token: str | None = getattr(prefs, "device_token", None)
        await send_push(device_token, title, body)
        if device_token:
            db.add(NotificationLog(
                notification_id=notification.id,
                delivery_channel="push",
                delivery_status="sent",
                sent_at=now,
            ))

    await db.commit()
    await db.refresh(notification)
    return notification


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_user_id_for_employee(db: AsyncSession, employee_id: int) -> int | None:
    result = await db.execute(
        select(Employee.user_id).where(Employee.id == employee_id)
    )
    return result.scalar_one_or_none()


# ── Convenience wrappers ──────────────────────────────────────────────────────

async def notify_token_awarded(
    db: AsyncSession,
    employee_id: int,
    tokens,
    reason: str = "",
) -> None:
    """FR-12.1: Notify employee of token award."""
    user_id = await _get_user_id_for_employee(db, employee_id)
    if user_id is None:
        return
    await create_and_dispatch(
        db,
        recipient_id=user_id,
        notification_type="token_reward",
        title="Token Reward Earned",
        body=f"You earned {tokens} GreenTokens{' — ' + reason if reason else ''}.",
    )


async def notify_leaderboard_rank(
    db: AsyncSession,
    employee_id: int,
    rank: int,
    week_label: str = "",
) -> None:
    """FR-12.1: Notify employee of leaderboard position."""
    user_id = await _get_user_id_for_employee(db, employee_id)
    if user_id is None:
        return
    await create_and_dispatch(
        db,
        recipient_id=user_id,
        notification_type="leaderboard",
        title="Leaderboard Result",
        body=f"You finished rank #{rank} on the leaderboard{' for ' + week_label if week_label else ''}. Great work!",
    )


async def notify_document_uploaded(
    db: AsyncSession,
    uploader_id: int,
    supplier_name: str,
    doc_title: str,
) -> None:
    """Notify uploader that their document is pending review."""
    await create_and_dispatch(
        db,
        recipient_id=uploader_id,
        notification_type="compliance",
        title="Document Uploaded",
        body=f"Document '{doc_title}' for supplier '{supplier_name}' has been submitted and is pending review.",
    )


async def notify_admins_cert_expiry(
    db: AsyncSession,
    doc,  # SupplierDocument
    severity: str,
    days_left: int,
) -> None:
    """
    FR-12.2: Notify all employees in the supplier's organisation of an expiring cert.
    Called daily by compliance_tasks.check_certification_expiry().
    """
    from app.models.suppliers import SupplierLocation

    # Resolve org_id for this supplier
    loc_result = await db.execute(
        select(SupplierLocation.organization_id)
        .where(
            SupplierLocation.supplier_id == doc.supplier_id,
            SupplierLocation.organization_id.is_not(None),
        )
        .limit(1)
    )
    org_id = loc_result.scalar_one_or_none()
    if org_id is None:
        return

    # Notify all active employees in the org
    emp_result = await db.execute(
        select(Employee.user_id).where(
            Employee.organization_id == org_id,
            Employee.employment_status == "active",
        )
    )
    user_ids = [row[0] for row in emp_result.all()]

    severity_label = "CRITICAL" if severity == "critical" else "Warning"
    title = f"[{severity_label}] Certificate Expiry — {days_left} day{'s' if days_left != 1 else ''} left"
    body = (
        f"Supplier document '{doc.title}' (type: {doc.document_type}) "
        f"expires in {days_left} day{'s' if days_left != 1 else ''}. "
        "Please take action before expiry."
    )

    for user_id in user_ids:
        await create_and_dispatch(
            db,
            recipient_id=user_id,
            notification_type="expiry",
            title=title,
            body=body,
            org_id=org_id,
        )


async def notify_redemption(
    db: AsyncSession,
    employee_id: int,
    reward_title: str,
) -> None:
    """FR-12.1: Notify employee that their reward redemption was successful."""
    user_id = await _get_user_id_for_employee(db, employee_id)
    if user_id is None:
        return
    await create_and_dispatch(
        db,
        recipient_id=user_id,
        notification_type="token_reward",
        title="Reward Redeemed",
        body=f"You successfully redeemed '{reward_title}'.",
    )


async def notify_document_reviewed(
    db: AsyncSession,
    doc,  # SupplierDocument
    action: str,
) -> None:
    """FR-12.1: Notify document uploader of review outcome (approved/rejected/flagged)."""
    if doc.uploader_id is None:
        return
    await create_and_dispatch(
        db,
        recipient_id=doc.uploader_id,
        notification_type="compliance",
        title="Document Review Update",
        body=f"Your document '{doc.title}' has been {action}.",
    )


async def notify_report_ready(
    db: AsyncSession,
    report_run,  # ReportRun
) -> None:
    """FR-12.1: Notify the report requester that their report is ready."""
    if report_run.generated_by is None:
        return
    await create_and_dispatch(
        db,
        recipient_id=report_run.generated_by,
        notification_type="report",
        title="Report Ready",
        body=f"Your report '{report_run.report_name}' has been generated and is ready to download.",
        ref_type="report_runs",
        ref_id=report_run.id,
    )
