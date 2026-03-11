"""
Compliance models — owned by Sunny (FR3).
Tables: compliance_frameworks, compliance_requirements, compliance_records,
        compliance_evidence, compliance_alerts
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    AlertTypeEnum,
    AppliesToEnum,
    ComplianceStatusEnum,
    EvidenceStatusEnum,
    EvidenceTypeEnum,
    FrameworkStatusEnum,
    FrameworkTypeEnum,
    PriorityEnum,
    SeverityEnum,
)


class ComplianceFramework(Base, TimestampMixin):
    __tablename__ = "compliance_frameworks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    framework_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    framework_type: Mapped[str] = mapped_column(FrameworkTypeEnum, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(FrameworkStatusEnum, nullable=False, default="active")
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Seed: Restaurant ESG Framework (ESG-R1, v1.0)

    requirements: Mapped[list["ComplianceRequirement"]] = relationship(
        "ComplianceRequirement", back_populates="framework", lazy="selectin"
    )


class ComplianceRequirement(Base, TimestampMixin):
    __tablename__ = "compliance_requirements"
    __table_args__ = (UniqueConstraint("framework_id", "requirement_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    framework_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False)
    requirement_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    applies_to: Mapped[str] = mapped_column(AppliesToEnum, nullable=False)
    priority: Mapped[str] = mapped_column(PriorityEnum, nullable=False, default="medium")
    requires_document: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allows_expiry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(FrameworkStatusEnum, nullable=False, default="active")
    # Seed: ESG-001 Track Food Waste, ESG-002 Employee Sustainability Training

    framework: Mapped["ComplianceFramework"] = relationship("ComplianceFramework", back_populates="requirements", lazy="selectin")


class ComplianceRecord(Base, TimestampMixin):
    """Merges organization_compliance + location_compliance.
    CHECK: organization_id IS NOT NULL OR location_id IS NOT NULL (enforced at service layer).
    """
    __tablename__ = "compliance_records"
    __table_args__ = (
        CheckConstraint(
            "organization_id IS NOT NULL OR location_id IS NOT NULL",
            name="ck_compliance_records_org_or_location",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="CASCADE"), nullable=True)
    requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("compliance_requirements.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(ComplianceStatusEnum, nullable=False, default="not_started")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ComplianceEvidence(Base):
    __tablename__ = "compliance_evidence"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    compliance_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("compliance_records.id", ondelete="CASCADE"), nullable=False)
    submitted_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[str] = mapped_column(EvidenceTypeEnum, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(EvidenceStatusEnum, nullable=False, default="submitted")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Absorbs compliance_reviews
    reviewer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="CASCADE"), nullable=True)
    requirement_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("compliance_requirements.id", ondelete="SET NULL"), nullable=True)
    compliance_record_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("compliance_records.id", ondelete="SET NULL"), nullable=True)
    alert_type: Mapped[str] = mapped_column(AlertTypeEnum, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    severity: Mapped[str] = mapped_column(SeverityEnum, nullable=False, default="medium")
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
