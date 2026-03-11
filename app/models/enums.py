"""
All PostgreSQL ENUM types for the platform.
Declared once here; imported by every model file that needs them.
create_type=True ensures Alembic creates the PG ENUM type before the table.
"""
from sqlalchemy.dialects.postgresql import ENUM

# ── Auth ──────────────────────────────────────────────────────────────────────
UserStatusEnum = ENUM(
    "active", "inactive", "suspended",
    name="user_status_enum", create_type=True,
)
SecurityEventEnum = ENUM(
    "login_success", "login_failed", "logout", "password_reset",
    "password_changed", "mfa_enabled", "mfa_disabled",
    "account_suspended", "account_reactivated",
    name="security_event_enum", create_type=True,
)
AccessLevelEnum = ENUM(
    "view", "manage", "admin",
    name="access_level_enum", create_type=True,
)

# ── Org ───────────────────────────────────────────────────────────────────────
OrgStatusEnum = ENUM(
    "active", "inactive", "suspended",
    name="org_status_enum", create_type=True,
)
LocationStatusEnum = ENUM(
    "active", "inactive", "closed",
    name="location_status_enum", create_type=True,
)
EmploymentStatusEnum = ENUM(
    "active", "inactive", "terminated", "on_leave",
    name="employment_status_enum", create_type=True,
)

# ── Compliance ────────────────────────────────────────────────────────────────
FrameworkTypeEnum = ENUM(
    "esg", "sdg", "supplier", "internal_policy",
    "sustainability", "operational", "other",
    name="framework_type_enum", create_type=True,
)
FrameworkStatusEnum = ENUM(
    "active", "inactive", "archived",
    name="framework_status_enum", create_type=True,
)
PriorityEnum = ENUM(
    "low", "medium", "high", "critical",
    name="priority_enum", create_type=True,
)
AppliesToEnum = ENUM(
    "organization", "location",
    name="applies_to_enum", create_type=True,
)
ComplianceStatusEnum = ENUM(
    "not_started", "in_progress", "pending_verification",
    "compliant", "non_compliant", "expired",
    name="compliance_status_enum", create_type=True,
)
EvidenceTypeEnum = ENUM(
    "document", "certificate", "report", "image", "manual_entry", "other",
    name="evidence_type_enum", create_type=True,
)
EvidenceStatusEnum = ENUM(
    "submitted", "under_review", "approved", "rejected",
    name="evidence_status_enum", create_type=True,
)
AlertTypeEnum = ENUM(
    "expiry", "missing_document", "overdue", "review_required", "status_change",
    name="alert_type_enum", create_type=True,
)
SeverityEnum = ENUM(
    "low", "medium", "high", "critical",
    name="severity_enum", create_type=True,
)
DocTypeEnum = ENUM(
    "certificate", "report", "proof", "policy", "image", "other",
    name="doc_type_enum", create_type=True,
)
DocStatusEnum = ENUM(
    "active", "expired", "archived",
    name="doc_status_enum", create_type=True,
)

# ── ESG ───────────────────────────────────────────────────────────────────────
EsgObjectiveStatusEnum = ENUM(
    "draft", "active", "completed", "archived",
    name="esg_objective_status_enum", create_type=True,
)
MetricSourceEnum = ENUM(
    "manual", "integration", "calculated",
    name="metric_source_enum", create_type=True,
)
ActivityTypeEnum = ENUM(
    "sustainability_initiative", "carbon_reduction", "community_program",
    "training", "donation", "awareness_campaign", "other",
    name="activity_type_enum", create_type=True,
)
ActivityStatusEnum = ENUM(
    "planned", "active", "completed", "cancelled",
    name="activity_status_enum", create_type=True,
)
ReportTypeEnum = ENUM(
    "esg", "compliance", "supplier", "customer", "employee", "custom",
    name="report_type_enum", create_type=True,
)

# ── Suppliers ─────────────────────────────────────────────────────────────────
SupplierStatusEnum = ENUM(
    "active", "inactive", "suspended",
    name="supplier_status_enum", create_type=True,
)
ContractStatusEnum = ENUM(
    "active", "inactive", "terminated",
    name="contract_status_enum", create_type=True,
)

# ── Tokens / Wallet ───────────────────────────────────────────────────────────
WalletTypeEnum = ENUM(
    "employee", "customer", "admin", "supplier", "platform",
    name="wallet_type_enum", create_type=True,
)
WalletStatusEnum = ENUM(
    "active", "inactive", "frozen",
    name="wallet_status_enum", create_type=True,
)
TransactionTypeEnum = ENUM(
    "earn", "redeem", "donate", "transfer", "expire", "bonus", "adjustment",
    name="transaction_type_enum", create_type=True,
)
TransactionDirEnum = ENUM(
    "credit", "debit",
    name="transaction_dir_enum", create_type=True,
)
TokenRuleTypeEnum = ENUM(
    "visit", "steps", "employee_activity", "leaderboard_bonus",
    "manual", "donation_bonus", "other",
    name="token_rule_type_enum", create_type=True,
)
RewardTypeEnum = ENUM(
    "voucher", "coupon", "discount", "offer",
    name="reward_type_enum", create_type=True,
)
VoucherStatusEnum = ENUM(
    "issued", "redeemed", "expired", "cancelled",
    name="voucher_status_enum", create_type=True,
)
ApplicableToEnum = ENUM(
    "employee", "customer", "all",
    name="applicable_to_enum", create_type=True,
)

# ── Donations ─────────────────────────────────────────────────────────────────
CauseTypeEnum = ENUM(
    "environment", "social", "community", "offset", "other",
    name="cause_type_enum", create_type=True,
)
DonationStatusEnum = ENUM(
    "pending", "completed", "cancelled",
    name="donation_status_enum", create_type=True,
)
ImpactTypeEnum = ENUM(
    "trees_planted", "co2_offset", "social_support", "meals_funded", "other",
    name="impact_type_enum", create_type=True,
)

# ── Blockchain ────────────────────────────────────────────────────────────────
BlockchainRecordTypeEnum = ENUM(
    "compliance_document", "compliance_evidence", "wallet_transaction",
    "donation", "esg_report", "supplier_document", "other",
    name="blockchain_record_type_enum", create_type=True,
)
BlockchainStatusEnum = ENUM(
    "pending", "anchored", "failed",
    name="blockchain_status_enum", create_type=True,
)
TxStatusEnum = ENUM(
    "pending", "confirmed", "failed",
    name="tx_status_enum", create_type=True,
)

# ── Workforce ─────────────────────────────────────────────────────────────────
LeaderboardTypeEnum = ENUM(
    "weekly", "monthly",
    name="leaderboard_type_enum", create_type=True,
)
LeaderboardStatusEnum = ENUM(
    "open", "closed", "archived",
    name="leaderboard_status_enum", create_type=True,
)
RedemptionStatusEnum = ENUM(
    "pending", "completed", "cancelled",
    name="redemption_status_enum", create_type=True,
)
RedemptionActorEnum = ENUM(
    "employee", "customer",
    name="redemption_actor_enum", create_type=True,
)

# ── Customers ─────────────────────────────────────────────────────────────────
CustomerStatusEnum = ENUM(
    "active", "inactive", "blocked",
    name="customer_status_enum", create_type=True,
)
ChallengeTypeEnum = ENUM(
    "steps", "visits", "spend", "donation", "esg_action", "other",
    name="challenge_type_enum", create_type=True,
)
ChallengeStatusEnum = ENUM(
    "draft", "active", "completed", "cancelled",
    name="challenge_status_enum", create_type=True,
)
ParticipationStatusEnum = ENUM(
    "joined", "in_progress", "completed", "withdrawn",
    name="participation_status_enum", create_type=True,
)

# ── Reporting ─────────────────────────────────────────────────────────────────
SnapshotTypeEnum = ENUM(
    "daily", "weekly", "monthly", "custom",
    name="snapshot_type_enum", create_type=True,
)
ReportRunStatusEnum = ENUM(
    "queued", "running", "completed", "failed",
    name="report_run_status_enum", create_type=True,
)
ExportFormatEnum = ENUM(
    "pdf", "csv", "xlsx", "json",
    name="export_format_enum", create_type=True,
)

# ── Notifications ─────────────────────────────────────────────────────────────
NotificationTypeEnum = ENUM(
    "token_reward", "leaderboard", "challenge", "compliance",
    "expiry", "system", "report",
    name="notification_type_enum", create_type=True,
)
DeliveryChannelEnum = ENUM(
    "email", "push", "in_app",
    name="delivery_channel_enum", create_type=True,
)
DeliveryStatusEnum = ENUM(
    "queued", "sent", "failed", "read",
    name="delivery_status_enum", create_type=True,
)
