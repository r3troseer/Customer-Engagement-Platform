"""
Compliance models — owned by Sunny (FR3).

Tables:
- compliance_frameworks
- compliance_requirements
- organization_compliance
- location_compliance
- compliance_evidence
- compliance_reviews
- compliance_documents
- compliance_document_versions
- compliance_status_history
- compliance_alerts
- compliance_scores

Notes:
- This file matches the existing schemas, services, routers, and app/models/__init__.py
- restaurant location FK points to restaurant_locations.id from FR2 org models
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    ComplianceAlertTypeEnum,
    ComplianceAppliesToEnum,
    ComplianceDocStatusEnum,
    ComplianceDocTypeEnum,
    ComplianceEvidenceStatusEnum,
    ComplianceEvidenceTypeEnum,
    ComplianceFrameworkStatusEnum,
    ComplianceFrameworkTypeEnum,
    CompliancePriorityEnum,
    ComplianceReviewStatusEnum,
    ComplianceSeverityEnum,
    ComplianceStatusEnum,
)


class ComplianceFramework(Base, TimestampMixin):
    __tablename__ = "compliance_frameworks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    framework_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    framework_type: Mapped[str] = mapped_column(ComplianceFrameworkTypeEnum, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        ComplianceFrameworkStatusEnum,
        nullable=False,
        default="active",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    requirements: Mapped[list["ComplianceRequirement"]] = relationship(
        "ComplianceRequirement",
        back_populates="framework",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    scores: Mapped[list["ComplianceScore"]] = relationship(
        "ComplianceScore",
        back_populates="framework",
        lazy="selectin",
    )


class ComplianceRequirement(Base, TimestampMixin):
    __tablename__ = "compliance_requirements"
    __table_args__ = (
        UniqueConstraint(
            "framework_id",
            "requirement_code",
            name="uq_compliance_requirement_framework_code",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    framework_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[str | None] = mapped_column(
        CompliancePriorityEnum,
        nullable=True,
        default="medium",
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    applies_to: Mapped[str] = mapped_column(
        ComplianceAppliesToEnum,
        nullable=False,
        default="organization",
    )
    status: Mapped[str] = mapped_column(
        ComplianceFrameworkStatusEnum,
        nullable=False,
        default="active",
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    framework: Mapped["ComplianceFramework"] = relationship(
        "ComplianceFramework",
        back_populates="requirements",
        lazy="selectin",
    )
    organization_compliance_items: Mapped[list["OrganizationCompliance"]] = relationship(
        "OrganizationCompliance",
        back_populates="requirement",
        lazy="selectin",
    )
    location_compliance_items: Mapped[list["LocationCompliance"]] = relationship(
        "LocationCompliance",
        back_populates="requirement",
        lazy="selectin",
    )
    alerts: Mapped[list["ComplianceAlert"]] = relationship(
        "ComplianceAlert",
        back_populates="requirement",
        lazy="selectin",
    )
    documents: Mapped[list["ComplianceDocument"]] = relationship(
        "ComplianceDocument",
        back_populates="requirement",
        lazy="selectin",
    )


class OrganizationCompliance(Base, TimestampMixin):
    __tablename__ = "organization_compliance"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "requirement_id",
            name="uq_organization_compliance_org_requirement",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("compliance_requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        ComplianceStatusEnum,
        nullable=False,
        default="not_started",
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    requirement: Mapped["ComplianceRequirement"] = relationship(
        "ComplianceRequirement",
        back_populates="organization_compliance_items",
        lazy="selectin",
    )
    evidence_items: Mapped[list["ComplianceEvidence"]] = relationship(
        "ComplianceEvidence",
        back_populates="organization_compliance",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[list["ComplianceStatusHistory"]] = relationship(
        "ComplianceStatusHistory",
        back_populates="organization_compliance",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class LocationCompliance(Base, TimestampMixin):
    __tablename__ = "location_compliance"
    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "requirement_id",
            name="uq_location_compliance_location_requirement",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("compliance_requirements.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        ComplianceStatusEnum,
        nullable=False,
        default="not_started",
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    location: Mapped["RestaurantLocation"] = relationship(
        "RestaurantLocation",
        lazy="selectin",
    )
    requirement: Mapped["ComplianceRequirement"] = relationship(
        "ComplianceRequirement",
        back_populates="location_compliance_items",
        lazy="selectin",
    )
    evidence_items: Mapped[list["ComplianceEvidence"]] = relationship(
        "ComplianceEvidence",
        back_populates="location_compliance",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[list["ComplianceStatusHistory"]] = relationship(
        "ComplianceStatusHistory",
        back_populates="location_compliance",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class ComplianceEvidence(Base, TimestampMixin):
    __tablename__ = "compliance_evidence"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    organization_compliance_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organization_compliance.id", ondelete="CASCADE"),
        nullable=True,
    )
    location_compliance_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("location_compliance.id", ondelete="CASCADE"),
        nullable=True,
    )
    document_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("compliance_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[str] = mapped_column(
        ComplianceEvidenceTypeEnum,
        nullable=False,
        default="document",
    )
    status: Mapped[str] = mapped_column(
        ComplianceEvidenceStatusEnum,
        nullable=False,
        default="submitted",
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization_compliance: Mapped["OrganizationCompliance | None"] = relationship(
        "OrganizationCompliance",
        back_populates="evidence_items",
        lazy="selectin",
    )
    location_compliance: Mapped["LocationCompliance | None"] = relationship(
        "LocationCompliance",
        back_populates="evidence_items",
        lazy="selectin",
    )
    reviews: Mapped[list["ComplianceReview"]] = relationship(
        "ComplianceReview",
        back_populates="evidence",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    document: Mapped["ComplianceDocument | None"] = relationship(
        "ComplianceDocument",
        back_populates="evidence_items",
        lazy="selectin",
        foreign_keys=[document_id],
    )


class ComplianceReview(Base, TimestampMixin):
    __tablename__ = "compliance_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    evidence_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("compliance_evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(
        ComplianceReviewStatusEnum,
        nullable=False,
        default="pending",
    )
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence: Mapped["ComplianceEvidence"] = relationship(
        "ComplianceEvidence",
        back_populates="reviews",
        lazy="selectin",
    )


class ComplianceDocument(Base, TimestampMixin):
    __tablename__ = "compliance_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    evidence_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("compliance_evidence.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="CASCADE"),
        nullable=True,
    )
    requirement_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("compliance_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    document_type: Mapped[str | None] = mapped_column(ComplianceDocTypeEnum, nullable=True)
    document_status: Mapped[str] = mapped_column(
        ComplianceDocStatusEnum,
        nullable=False,
        default="active",
    )
    uploaded_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence_items: Mapped[list["ComplianceEvidence"]] = relationship(
        "ComplianceEvidence",
        back_populates="document",
        lazy="selectin",
        foreign_keys="ComplianceEvidence.document_id",
    )
    requirement: Mapped["ComplianceRequirement | None"] = relationship(
        "ComplianceRequirement",
        back_populates="documents",
        lazy="selectin",
    )
    versions: Mapped[list["ComplianceDocumentVersion"]] = relationship(
        "ComplianceDocumentVersion",
        back_populates="document",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["ComplianceAlert"]] = relationship(
        "ComplianceAlert",
        back_populates="document",
        lazy="selectin",
    )


class ComplianceDocumentVersion(Base):
    __tablename__ = "compliance_document_versions"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_compliance_document_version_document_number",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("compliance_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    changed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    document: Mapped["ComplianceDocument"] = relationship(
        "ComplianceDocument",
        back_populates="versions",
        lazy="selectin",
    )


class ComplianceStatusHistory(Base):
    __tablename__ = "compliance_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_compliance_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organization_compliance.id", ondelete="CASCADE"),
        nullable=True,
    )
    location_compliance_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("location_compliance.id", ondelete="CASCADE"),
        nullable=True,
    )
    old_status: Mapped[str | None] = mapped_column(ComplianceStatusEnum, nullable=True)
    new_status: Mapped[str] = mapped_column(ComplianceStatusEnum, nullable=False)
    changed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    organization_compliance: Mapped["OrganizationCompliance | None"] = relationship(
        "OrganizationCompliance",
        back_populates="status_history",
        lazy="selectin",
    )
    location_compliance: Mapped["LocationCompliance | None"] = relationship(
        "LocationCompliance",
        back_populates="status_history",
        lazy="selectin",
    )


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="CASCADE"),
        nullable=True,
    )
    requirement_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("compliance_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("compliance_documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    alert_type: Mapped[str] = mapped_column(ComplianceAlertTypeEnum, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    severity: Mapped[str] = mapped_column(
        ComplianceSeverityEnum,
        nullable=False,
        default="medium",
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        lazy="selectin",
    )
    location: Mapped["RestaurantLocation | None"] = relationship(
        "RestaurantLocation",
        lazy="selectin",
    )
    requirement: Mapped["ComplianceRequirement | None"] = relationship(
        "ComplianceRequirement",
        back_populates="alerts",
        lazy="selectin",
    )
    document: Mapped["ComplianceDocument | None"] = relationship(
        "ComplianceDocument",
        back_populates="alerts",
        lazy="selectin",
    )


class ComplianceScore(Base):
    __tablename__ = "compliance_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="CASCADE"),
        nullable=True,
    )
    framework_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    compliant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    non_compliant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expired_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization | None"] = relationship(
        "Organization",
        lazy="selectin",
    )
    location: Mapped["RestaurantLocation | None"] = relationship(
        "RestaurantLocation",
        lazy="selectin",
    )
    framework: Mapped["ComplianceFramework"] = relationship(
        "ComplianceFramework",
        back_populates="scores",
        lazy="selectin",
    )