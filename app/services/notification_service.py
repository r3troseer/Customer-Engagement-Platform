"""
FR12 — Notification & Alert service.
Called internally by other services — never exposed as a public endpoint.
Dispatches in-app, email (SMTP), and push (FCM) notifications.
"""
# TODO: implement the following functions

# create_and_dispatch(db, recipient_id, notification_type, title, body,
#                     ref_type=None, ref_id=None, org_id=None) -> Notification
#   1. Load NotificationPreference for recipient (or use defaults if row missing)
#   2. Insert Notification row (always — drives in-app bell icon)
#   3. If prefs.email_enabled AND type in user's enabled categories:
#      - await send_email(to_email, title, body)
#      - Insert NotificationLog(channel=email, status=sent/failed)
#   4. If prefs.push_enabled:
#      - await send_push(device_token, title, body)
#      - Insert NotificationLog(channel=push, status=sent/failed)
#   Return created Notification row

# Convenience wrappers (called by other services):

# notify_token_awarded(db, employee_id, tokens, reason) -> None
#   - Calls create_and_dispatch(type="token_reward", ...)

# notify_leaderboard_rank(db, employee_id, rank, week_label) -> None
#   - Calls create_and_dispatch(type="leaderboard", ...)

# notify_document_uploaded(db, admin_ids, supplier_name, doc_title) -> None
#   - Calls create_and_dispatch for each admin (type="compliance")

# notify_admins_cert_expiry(db, doc, severity, days_left) -> None
#   FR-12.2: Called daily by compliance_tasks.check_certification_expiry()
#   - Query all admin users for doc.supplier's organization
#   - Calls create_and_dispatch for each admin (type="expiry")

# notify_report_ready(db, report_run) -> None
#   - Calls create_and_dispatch for report requestor (type="report")

# send_email(to_email, subject, body_html) -> None
#   - Use emails library with SMTP config from settings
#   - Wrap in try/except — email failure must never crash the main flow

# send_push(device_token, title, body, data=None) -> None
#   - POST to FCM endpoint using httpx
#   - Wrap in try/except
