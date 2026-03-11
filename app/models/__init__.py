"""
Import ALL models here so Alembic's autogenerate can detect every table
via Base.metadata. Do not remove any import — even if the router for that
module hasn't been wired yet.

Ownership:
  Pius   — suppliers, workforce, reporting, notifications (incl. audit_logs)
  Omar   — auth, customers, tokens, blockchain
  Sunny  — org, compliance, esg, donations
"""
from app.models.base import Base, TimestampMixin  # noqa: F401

# Enums — must be imported first so PG ENUM types are registered
from app.models.enums import *  # noqa: F401, F403

# Auth (Omar — FR1)
from app.models.auth import (  # noqa: F401
    LoginSession,
    Permission,
    Role,
    RolePermission,
    SecurityLog,
    User,
    UserLocationAccess,
    UserRole,
)

# Org (Sunny — FR2)
from app.models.org import Employee, Location, Organization  # noqa: F401

# Compliance (Sunny — FR3)
from app.models.compliance import (  # noqa: F401
    ComplianceAlert,
    ComplianceEvidence,
    ComplianceFramework,
    ComplianceRecord,
    ComplianceRequirement,
)

# ESG (Sunny — FR4)
from app.models.esg import (  # noqa: F401
    EsgActivity,
    EsgMetricValue,
    EsgObjective,
    EsgReport,
)

# Suppliers (Pius — FR5)
from app.models.suppliers import Supplier, SupplierDocument, SupplierLocation  # noqa: F401

# Workforce (Pius — FR6)
from app.models.workforce import (  # noqa: F401
    LeaderboardEntry,
    LeaderboardSnapshot,
    Redemption,
    WorkLog,
)

# Customers (Omar — FR7)
from app.models.customers import (  # noqa: F401
    Challenge,
    ChallengeParticipation,
    Customer,
    CustomerVisit,
    MobilityLog,
)

# Tokens (Omar — FR8)
from app.models.tokens import (  # noqa: F401
    RewardRule,
    RewardVoucher,
    RewardsCatalog,
    TokenRule,
    Wallet,
    WalletTransaction,
)

# Donations (Sunny — FR9)
from app.models.donations import Donation, DonationCause, DonationImpact  # noqa: F401

# Blockchain (Omar — FR10)
from app.models.blockchain import (  # noqa: F401
    BlockchainHash,
    BlockchainRecord,
    BlockchainTransaction,
)

# Reporting (Pius — FR11)
from app.models.reporting import (  # noqa: F401
    AnalyticsSnapshot,
    DashboardKpi,
    ReportExport,
    ReportRun,
    ReportTemplate,
)

# Notifications + AuditLog (Pius FR12 / Sunny FR13)
from app.models.notifications import (  # noqa: F401
    AuditLog,
    Notification,
    NotificationLog,
    NotificationPreference,
)

__all__ = [
    "Base",
    "TimestampMixin",
    # Auth
    "User", "Role", "UserRole", "Permission", "RolePermission",
    "UserLocationAccess", "LoginSession", "SecurityLog",
    # Org
    "Organization", "Location", "Employee",
    # Compliance
    "ComplianceFramework", "ComplianceRequirement", "ComplianceRecord",
    "ComplianceEvidence", "ComplianceAlert",
    # ESG
    "EsgObjective", "EsgMetricValue", "EsgActivity", "EsgReport",
    # Suppliers
    "Supplier", "SupplierLocation", "SupplierDocument",
    # Workforce
    "WorkLog", "LeaderboardSnapshot", "LeaderboardEntry", "Redemption",
    # Customers
    "Customer", "CustomerVisit", "MobilityLog", "Challenge", "ChallengeParticipation",
    # Tokens
    "Wallet", "WalletTransaction", "TokenRule", "RewardRule", "RewardsCatalog", "RewardVoucher",
    # Donations
    "DonationCause", "Donation", "DonationImpact",
    # Blockchain
    "BlockchainTransaction", "BlockchainRecord", "BlockchainHash",
    # Reporting
    "ReportTemplate", "ReportRun", "ReportExport", "DashboardKpi", "AnalyticsSnapshot",
    # Notifications + Audit
    "Notification", "NotificationPreference", "NotificationLog", "AuditLog",
]
