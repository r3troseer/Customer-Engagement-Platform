"""
FR5 — Supplier Transparency & Compliance
Endpoints for registering suppliers, uploading/reviewing certifications,
tracking compliance history, and exposing public ESG data to customers.
"""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, UploadFile, File

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.suppliers import (
    ComplianceHistoryEntry,
    ComplianceStatusOut,
    ComplianceUpdateIn,
    DocumentReviewIn,
    PublicSupplierOut,
    SupplierCreate,
    SupplierDocumentOut,
    SupplierOut,
    SupplierUpdate,
)

router = APIRouter()

# ── Stub helpers ──────────────────────────────────────────────────────────────

_STUB_SUPPLIER = SupplierOut(
    id=1,
    supplier_name="EcoFarm Produce",
    supplier_code="SUP001",
    company_registration_number="12345678",
    tax_number="GB123456789",
    contact_name="Jane Farmer",
    contact_email="jane@ecofarm.com",
    contact_phone="+44 7700 900000",
    website="https://ecofarm.example.com",
    address_line_1="1 Green Lane",
    address_line_2=None,
    city="London",
    state_region="England",
    postcode="EC1A 1BB",
    country="United Kingdom",
    supplier_type="Food & Beverage",
    description="Organic produce supplier with full carbon-neutral certification.",
    status="active",
    esg_score=Decimal("87.50"),
    is_public=True,
    public_summary="Award-winning sustainable farm supplying restaurants across London.",
    esg_highlights="Carbon neutral since 2022. 100% renewable energy. Zero food waste policy.",
    created_at=datetime(2024, 1, 15, 9, 0, 0),
    updated_at=datetime(2024, 6, 1, 12, 0, 0),
)

_STUB_DOCUMENT = SupplierDocumentOut(
    id=1,
    supplier_id=1,
    uploaded_by=1,
    document_type="certificate",
    title="ISO 14001 Environmental Certificate",
    file_name="ecofarm_iso14001_2024.pdf",
    file_path="/uploads/suppliers/1/ecofarm_iso14001_2024.pdf",
    mime_type="application/pdf",
    file_size=204800,
    issue_date=None,
    expiry_date=None,
    status="active",
    notes="Renewed annually.",
    reviewer_id=None,
    review_status="pending",
    reviewed_at=None,
    review_feedback=None,
    created_at=datetime(2024, 3, 10, 10, 0, 0),
    updated_at=datetime(2024, 3, 10, 10, 0, 0),
)

_STUB_COMPLIANCE = ComplianceStatusOut(
    supplier_id=1,
    supplier_name="EcoFarm Produce",
    status="compliant",
    esg_score=Decimal("87.50"),
    last_updated=datetime(2024, 6, 1, 12, 0, 0),
)

_STUB_PUBLIC = PublicSupplierOut(
    id=1,
    supplier_name="EcoFarm Produce",
    supplier_type="Food & Beverage",
    country="United Kingdom",
    esg_score=Decimal("87.50"),
    public_summary="Award-winning sustainable farm supplying restaurants across London.",
    esg_highlights="Carbon neutral since 2022. 100% renewable energy. Zero food waste policy.",
)


# ── FR-5.1: Supplier CRUD ──────────────────────────────────────────────────────

@router.post("/", response_model=SupplierOut, status_code=201, summary="FR-5.1 Register a new supplier")
async def create_supplier(body: SupplierCreate, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.create_supplier()
    return _STUB_SUPPLIER


@router.get("/", response_model=PaginatedResponse[SupplierOut], summary="FR-5.1 List suppliers (paginated)")
async def list_suppliers(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: implement supplier_service.list_suppliers()
    return PaginatedResponse.create(items=[_STUB_SUPPLIER], total=1, page=pagination.page, page_size=pagination.page_size)


@router.get("/public", response_model=PaginatedResponse[PublicSupplierOut], summary="FR-5.6 Public supplier ESG info (customers)")
async def list_public_suppliers(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: implement supplier_service.get_public_suppliers()
    # Filters is_public=True AND status='active', returns limited fields only
    return PaginatedResponse.create(items=[_STUB_PUBLIC], total=1, page=pagination.page, page_size=pagination.page_size)


@router.get("/{supplier_id}", response_model=SupplierOut, summary="FR-5.1 Get supplier detail")
async def get_supplier(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.get_supplier()
    return SupplierOut(**{**_STUB_SUPPLIER.model_dump(), "id": supplier_id})


@router.patch("/{supplier_id}", response_model=SupplierOut, summary="FR-5.1 Update supplier")
async def update_supplier(supplier_id: int, body: SupplierUpdate, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.update_supplier()
    return SupplierOut(**{**_STUB_SUPPLIER.model_dump(), "id": supplier_id})


@router.delete("/{supplier_id}", response_model=MessageResponse, summary="FR-5.1 Soft-delete supplier")
async def delete_supplier(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.delete_supplier()
    return MessageResponse(message="Supplier deactivated successfully", detail=f"supplier_id={supplier_id}")


# ── FR-5.2: Document upload ────────────────────────────────────────────────────

@router.post("/{supplier_id}/documents", response_model=SupplierDocumentOut, status_code=201, summary="FR-5.2 Upload sustainability cert/doc")
async def upload_document(
    supplier_id: int,
    file: UploadFile = File(...),
    db: DBSession = None,
    current_user: AdminUser = None,
):
    # TODO: implement supplier_service.upload_document()
    # Calls file_storage.save_upload() then creates SupplierDocument row
    # Notifies admins via notification_service
    return SupplierDocumentOut(**{**_STUB_DOCUMENT.model_dump(), "supplier_id": supplier_id, "file_name": file.filename or "uploaded_file.pdf"})


@router.get("/{supplier_id}/documents", response_model=PaginatedResponse[SupplierDocumentOut], summary="FR-5.2 List supplier documents")
async def list_documents(supplier_id: int, db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: implement supplier_service.list_documents()
    stub = SupplierDocumentOut(**{**_STUB_DOCUMENT.model_dump(), "supplier_id": supplier_id})
    return PaginatedResponse.create(items=[stub], total=1, page=pagination.page, page_size=pagination.page_size)


@router.delete("/{supplier_id}/documents/{doc_id}", response_model=MessageResponse, summary="FR-5.2 Delete document")
async def delete_document(supplier_id: int, doc_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.delete_document()
    return MessageResponse(message="Document deleted successfully", detail=f"doc_id={doc_id}")


# ── FR-5.3: Certification review ─────────────────────────────────────────────

@router.post("/{supplier_id}/documents/{doc_id}/review", response_model=SupplierDocumentOut, summary="FR-5.3 Approve or reject certification")
async def review_document(supplier_id: int, doc_id: int, body: DocumentReviewIn, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.review_document()
    # Updates review_status, writes audit log, sends notification
    return SupplierDocumentOut(**{
        **_STUB_DOCUMENT.model_dump(),
        "id": doc_id,
        "supplier_id": supplier_id,
        "review_status": body.action,
        "review_feedback": body.feedback,
        "reviewed_at": datetime.utcnow(),
        "reviewer_id": 1,
    })


# ── FR-5.4 / FR-5.5: Compliance status & history ──────────────────────────────

@router.get("/{supplier_id}/compliance", response_model=ComplianceStatusOut, summary="FR-5.4 Current compliance status")
async def get_compliance(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.get_compliance_status()
    return ComplianceStatusOut(**{**_STUB_COMPLIANCE.model_dump(), "supplier_id": supplier_id})


@router.patch("/{supplier_id}/compliance", response_model=ComplianceStatusOut, summary="FR-5.4 Update compliance status")
async def update_compliance(supplier_id: int, body: ComplianceUpdateIn, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.update_compliance_status()
    return ComplianceStatusOut(
        supplier_id=supplier_id,
        supplier_name="EcoFarm Produce",
        status=body.status,
        esg_score=body.esg_score or Decimal("87.50"),
        last_updated=datetime.utcnow(),
    )


@router.get("/{supplier_id}/compliance/history", response_model=PaginatedResponse[ComplianceHistoryEntry], summary="FR-5.5 Compliance change history")
async def compliance_history(supplier_id: int, db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: implement supplier_service.get_compliance_history() — append-only records
    stub = ComplianceHistoryEntry(
        changed_at=datetime(2024, 5, 1, 10, 0, 0),
        previous_status="pending_verification",
        new_status="compliant",
        esg_score=Decimal("87.50"),
        changed_by=1,
        notes="Annual audit passed.",
    )
    return PaginatedResponse.create(items=[stub], total=1, page=pagination.page, page_size=pagination.page_size)


# ── FR-5.6: Public ESG view for customers ─────────────────────────────────────

@router.get("/{supplier_id}/public", response_model=PublicSupplierOut, summary="FR-5.6 Single supplier public ESG view")
async def get_public_supplier(supplier_id: int, db: DBSession, current_user: CurrentUser):
    # TODO: implement supplier_service.get_public_supplier()
    return PublicSupplierOut(**{**_STUB_PUBLIC.model_dump(), "id": supplier_id})
