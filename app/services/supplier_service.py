"""
FR5 — Supplier Transparency service layer.
All business logic for supplier CRUD, document upload/review, and compliance tracking.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.core.exceptions import ConflictError, NotFoundError
from app.models.suppliers import Supplier, SupplierDocument, SupplierLocation
from app.schemas.suppliers import (
    ComplianceHistoryEntry,
    ComplianceStatusOut,
    SupplierCreate,
    SupplierUpdate,
)


# =============================================================================
# Pure helpers — no I/O, fully unit-testable
# =============================================================================

def _aggregate_compliance_status(documents: list) -> str:
    """
    Derive a single compliance status from a supplier's document list.

    Priority (highest → lowest):
      non_compliant  — any doc is rejected
      pending_verification — any doc is pending or needs_update
      compliant      — all docs are approved
      not_started    — no documents at all
    """
    if not documents:
        return "not_started"

    statuses = {d.review_status for d in documents}

    if "rejected" in statuses:
        return "non_compliant"
    if statuses & {"pending", "needs_update"}:
        return "pending_verification"
    return "compliant"


def _recalculate_esg_score(documents: list) -> Decimal | None:
    """
    Return an updated ESG score only when ALL documents are approved.
    Uses a simple base score of 100 minus a deduction per document type
    to give a meaningful number without requiring external data.
    Returns None if any document is not yet approved (score stays unchanged).
    """
    if not documents:
        return None

    statuses = {d.review_status for d in documents}
    if statuses != {"approved"}:
        return None

    # Base score: 100, reduced proportionally by number of docs
    # (placeholder formula — replace with real ESG weighting logic)
    base = Decimal("100.00")
    doc_count = len(documents)
    # Each additional document beyond the first adds confidence (diminishing deduction)
    score = base - Decimal("5.00") / Decimal(str(max(doc_count, 1)))
    return score.quantize(Decimal("0.01"))


# =============================================================================
# Internal DB helpers
# =============================================================================

async def get_supplier(db, supplier_id: int) -> Supplier:
    """Load a Supplier by PK or raise 404."""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalars().first()
    if not supplier:
        raise NotFoundError(f"Supplier {supplier_id} not found")
    return supplier


async def _get_document(db, supplier_id: int, doc_id: int) -> SupplierDocument:
    """Load a SupplierDocument ensuring it belongs to the given supplier."""
    result = await db.execute(
        select(SupplierDocument).where(
            SupplierDocument.id == doc_id,
            SupplierDocument.supplier_id == supplier_id,
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise NotFoundError(f"Document {doc_id} not found for supplier {supplier_id}")
    return doc


# =============================================================================
# Supplier CRUD
# =============================================================================

async def list_suppliers(
    db,
    pagination,
    org_id: int | None = None,
    status: str | None = None,
) -> tuple[list[Supplier], int]:
    """Return (items, total) with optional org/status filters."""
    query = select(Supplier)

    if status:
        query = query.where(Supplier.status == status)
    # org_id filter via SupplierLocation join when needed
    if org_id:
        query = query.join(SupplierLocation, SupplierLocation.supplier_id == Supplier.id).where(
            SupplierLocation.organization_id == org_id
        )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    return result.scalars().all(), total


async def create_supplier(db, data: SupplierCreate, current_user: dict) -> Supplier:
    """Register a new supplier."""
    # Check for duplicate supplier_code
    existing = await db.execute(
        select(Supplier).where(Supplier.supplier_code == data.supplier_code)
    )
    if existing.scalars().first():
        raise ConflictError(f"Supplier code '{data.supplier_code}' already exists")

    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    # TODO: audit — audit_service.log_action("supplier.created", supplier.id, current_user)
    return supplier


async def update_supplier(db, supplier_id: int, data: SupplierUpdate, current_user: dict) -> Supplier:
    """Partial update of a supplier's fields."""
    supplier = await get_supplier(db, supplier_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)

    await db.commit()
    await db.refresh(supplier)
    # TODO: audit — audit_service.log_action("supplier.updated", supplier.id, current_user)
    return supplier


async def delete_supplier(db, supplier_id: int, current_user: dict) -> None:
    """Soft-delete: set status='inactive'. Never hard-deletes."""
    supplier = await get_supplier(db, supplier_id)
    supplier.status = "inactive"
    await db.commit()
    # TODO: audit — audit_service.log_action("supplier.deleted", supplier.id, current_user)


async def get_public_suppliers(db, pagination) -> tuple[list[Supplier], int]:
    """Return only suppliers with is_public=True and status='active'."""
    query = select(Supplier).where(
        Supplier.is_public == True,  # noqa: E712
        Supplier.status == "active",
    )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    return result.scalars().all(), total
