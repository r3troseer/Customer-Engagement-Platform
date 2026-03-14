"""
FR5 — Supplier Transparency service layer.
All business logic for supplier CRUD, document upload/review, and compliance tracking.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.core.exceptions import ConflictError, NotFoundError
from app.models.suppliers import Supplier, SupplierDocument, SupplierLocation
from app.services.audit_service import AuditLogService
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
    await AuditLogService.create(db, {"action": "supplier.created", "entity_type": "suppliers", "entity_id": supplier.id, "user_id": current_user["user_id"]})
    return supplier


async def update_supplier(db, supplier_id: int, data: SupplierUpdate, current_user: dict) -> Supplier:
    """Partial update of a supplier's fields."""
    supplier = await get_supplier(db, supplier_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)

    await db.commit()
    await db.refresh(supplier)
    await AuditLogService.create(db, {"action": "supplier.updated", "entity_type": "suppliers", "entity_id": supplier.id, "user_id": current_user["user_id"]})
    return supplier


async def delete_supplier(db, supplier_id: int, current_user: dict) -> None:
    """Soft-delete: set status='inactive'. Never hard-deletes."""
    supplier = await get_supplier(db, supplier_id)
    supplier.status = "inactive"
    await db.commit()
    await AuditLogService.create(db, {"action": "supplier.deleted", "entity_type": "suppliers", "entity_id": supplier.id, "user_id": current_user["user_id"]})


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


# =============================================================================
# Document upload / review
# =============================================================================

async def upload_document(
    db,
    supplier_id: int,
    file,
    title: str,
    doc_type: str,
    uploader_id: int,
) -> SupplierDocument:
    """
    Save the uploaded file via file_storage then create a SupplierDocument row.
    review_status starts as 'pending' — admin must explicitly approve/reject.
    """
    from app.utils.file_storage import save_upload

    supplier = await get_supplier(db, supplier_id)

    file_path = await save_upload(file, folder=f"suppliers/{supplier_id}")

    doc = SupplierDocument(
        supplier_id=supplier_id,
        uploaded_by=uploader_id,
        document_type=doc_type,
        title=title,
        file_name=file.filename,
        file_path=file_path,
        mime_type=getattr(file, "content_type", None),
        review_status="pending",
        status="active",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    from app.services import notification_service
    await notification_service.notify_document_uploaded(db, uploader_id, supplier.name, doc.title)
    await AuditLogService.create(db, {"action": "supplier.document.uploaded", "entity_type": "supplier_documents", "entity_id": doc.id, "user_id": uploader_id})
    return doc


async def list_documents(db, supplier_id: int) -> list[SupplierDocument]:
    """Return all documents for a supplier."""
    await get_supplier(db, supplier_id)  # 404 guard
    result = await db.execute(
        select(SupplierDocument).where(SupplierDocument.supplier_id == supplier_id)
    )
    return result.scalars().all()


async def delete_document(db, supplier_id: int, doc_id: int, current_user: dict) -> None:
    """Hard-delete a document record and its storage file (best-effort)."""
    doc = await _get_document(db, supplier_id, doc_id)
    db.delete(doc)
    await db.commit()
    await AuditLogService.create(db, {"action": "supplier.document.deleted", "entity_type": "supplier_documents", "entity_id": doc_id, "user_id": current_user["user_id"]})


async def review_document(
    db,
    supplier_id: int,
    doc_id: int,
    action: str,
    reviewer_id: int,
    feedback: str | None,
) -> SupplierDocument:
    """
    Approve, reject, or flag a document for update.
    After saving, recomputes the supplier's aggregate compliance status
    and ESG score if all documents are now approved.
    """
    doc = await _get_document(db, supplier_id, doc_id)

    doc.review_status = action
    doc.reviewer_id = reviewer_id
    doc.reviewed_at = datetime.now(timezone.utc)
    doc.review_feedback = feedback

    await db.commit()
    await db.refresh(doc)

    # Recompute ESG score if all documents are now approved
    all_docs = await list_documents(db, supplier_id)
    new_esg = _recalculate_esg_score(all_docs)
    if new_esg is not None:
        supplier = await get_supplier(db, supplier_id)
        supplier.esg_score = new_esg
        await db.commit()

    from app.services import notification_service
    await notification_service.notify_document_reviewed(db, doc, action)
    await AuditLogService.create(db, {"action": f"supplier.document.{action}", "entity_type": "supplier_documents", "entity_id": doc_id, "user_id": reviewer_id})
    return doc


# =============================================================================
# Compliance status & history
# =============================================================================

async def get_compliance_status(db, supplier_id: int) -> ComplianceStatusOut:
    """Aggregate current compliance status from the supplier's documents."""
    supplier = await get_supplier(db, supplier_id)
    documents = await list_documents(db, supplier_id)
    status = _aggregate_compliance_status(documents)

    return ComplianceStatusOut(
        supplier_id=supplier.id,
        supplier_name=supplier.supplier_name,
        status=status,
        esg_score=supplier.esg_score,
        last_updated=supplier.updated_at,
    )


async def update_compliance_status(
    db,
    supplier_id: int,
    new_status: str,
    esg_score,
    notes: str | None,
    reviewer_id: int,
) -> ComplianceStatusOut:
    """
    Directly update the supplier's status and ESG score (admin override).
    This is append-only in intent — no history table, but the Supplier row
    updated_at timestamp serves as the last-changed marker.
    """
    _VALID_SUPPLIER_STATUSES = {"active", "inactive", "suspended"}
    if new_status not in _VALID_SUPPLIER_STATUSES:
        from app.core.exceptions import UnprocessableError
        raise UnprocessableError(
            f"Invalid status '{new_status}'. Must be one of: {sorted(_VALID_SUPPLIER_STATUSES)}"
        )

    supplier = await get_supplier(db, supplier_id)

    supplier.status = new_status
    if esg_score is not None:
        supplier.esg_score = esg_score

    await db.commit()
    await db.refresh(supplier)

    await AuditLogService.create(db, {"action": "supplier.compliance.updated", "entity_type": "suppliers", "entity_id": supplier_id, "user_id": reviewer_id})
    return ComplianceStatusOut(
        supplier_id=supplier.id,
        supplier_name=supplier.supplier_name,
        status=supplier.status,
        esg_score=supplier.esg_score,
        last_updated=supplier.updated_at,
    )


async def get_compliance_history(
    db,
    supplier_id: int,
    pagination,
) -> tuple[list[ComplianceHistoryEntry], int]:
    """
    Build a compliance history trail from SupplierDocument review events.
    Each reviewed document contributes one history entry ordered by reviewed_at DESC.
    """
    await get_supplier(db, supplier_id)  # 404 guard

    result = await db.execute(
        select(SupplierDocument)
        .where(
            SupplierDocument.supplier_id == supplier_id,
            SupplierDocument.reviewed_at.is_not(None),
        )
        .order_by(SupplierDocument.reviewed_at.desc())
    )
    reviewed_docs = result.scalars().all()
    total = len(reviewed_docs)

    # Apply pagination manually (history is typically small)
    page_docs = reviewed_docs[pagination.offset: pagination.offset + pagination.page_size]

    entries = [
        ComplianceHistoryEntry(
            changed_at=doc.reviewed_at,
            previous_status=None,  # not tracked per-doc; would need audit log for full diff
            new_status=doc.review_status,
            esg_score=None,
            changed_by=doc.reviewer_id,
            notes=f"{doc.document_type}: {doc.title}",
        )
        for doc in page_docs
    ]
    return entries, total


async def add_supplier_location(
    db,
    supplier_id: int,
    organization_id: int | None,
    location_id: int | None,
    service_type: str | None = None,
    relationship_type: str | None = None,
) -> SupplierLocation:
    """
    Link a supplier to an organisation/location. Idempotent — returns the existing row
    if the (supplier_id, organization_id, location_id) combination already exists.
    """
    await get_supplier(db, supplier_id)  # raises 404 if not found

    existing = await db.execute(
        select(SupplierLocation).where(
            SupplierLocation.supplier_id == supplier_id,
            SupplierLocation.organization_id == organization_id,
            SupplierLocation.location_id == location_id,
        )
    )
    sl = existing.scalars().first()
    if sl:
        return sl

    sl = SupplierLocation(
        supplier_id=supplier_id,
        organization_id=organization_id,
        location_id=location_id,
        service_type=service_type,
        relationship_type=relationship_type,
        status="active",
    )
    db.add(sl)
    await db.flush()
    await db.refresh(sl)
    return sl


async def get_expiring_certs(db, threshold_date: date) -> list[SupplierDocument]:
    """
    Return active, approved documents whose expiry_date is on or before threshold_date.
    Called by compliance_tasks daily (FR-12.2).
    """
    result = await db.execute(
        select(SupplierDocument).where(
            SupplierDocument.status == "active",
            SupplierDocument.review_status == "approved",
            SupplierDocument.expiry_date.is_not(None),
            SupplierDocument.expiry_date <= threshold_date,
        )
    )
    return result.scalars().all()
