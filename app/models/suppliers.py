"""
Supplier models — owned by Pius (FR5).
Tables: suppliers, supplier_locations, supplier_documents
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ContractStatusEnum, DocStatusEnum, DocTypeEnum, SupplierStatusEnum


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    company_registration_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    tax_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supplier_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(SupplierStatusEnum, nullable=False, default="active")
    # Absorbs supplier_compliance.score
    esg_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    # Absorbs supplier_public_info — FR-5.6 customer-facing fields
    public_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    esg_highlights: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Seed: EcoFarm Produce (SUP001)

    locations: Mapped[list["SupplierLocation"]] = relationship("SupplierLocation", back_populates="supplier", lazy="selectin")
    documents: Mapped[list["SupplierDocument"]] = relationship("SupplierDocument", back_populates="supplier", lazy="selectin")


class SupplierLocation(Base, TimestampMixin):
    """Merges organization_suppliers + location_suppliers."""
    __tablename__ = "supplier_locations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    service_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    relationship_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contract_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(ContractStatusEnum, nullable=False, default="active")

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="locations", lazy="selectin")


class SupplierDocument(Base, TimestampMixin):
    __tablename__ = "supplier_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    document_type: Mapped[str] = mapped_column(DocTypeEnum, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(DocStatusEnum, nullable=False, default="active")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Absorbs supplier_reviews
    reviewer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # pending | approved | rejected | needs_update
    review_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="documents", lazy="selectin")
