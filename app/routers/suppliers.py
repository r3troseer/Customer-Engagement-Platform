"""
FR5 — Supplier Transparency & Compliance
Endpoints for registering suppliers, uploading/reviewing certifications,
tracking compliance history, and exposing public ESG data to customers.
"""
from fastapi import APIRouter, Form, UploadFile, File

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
    SupplierLocationIn,
    SupplierLocationOut,
    SupplierOut,
    SupplierUpdate,
)
import app.services.supplier_service as svc

router = APIRouter()


# ── FR-5.1: Supplier CRUD ──────────────────────────────────────────────────────

@router.post("/", response_model=SupplierOut, status_code=201, summary="FR-5.1 Register a new supplier")
async def create_supplier(body: SupplierCreate, db: DBSession, current_user: AdminUser):
    supplier = await svc.create_supplier(db, body, current_user)
    return SupplierOut.model_validate(supplier)


@router.get("/", response_model=PaginatedResponse[SupplierOut], summary="FR-5.1 List suppliers (paginated)")
async def list_suppliers(db: DBSession, current_user: AdminUser, pagination: Pagination):
    items, total = await svc.list_suppliers(db, pagination)
    return PaginatedResponse.create(
        items=[SupplierOut.model_validate(s) for s in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/public", response_model=PaginatedResponse[PublicSupplierOut], summary="FR-5.6 Public supplier ESG info (customers)")
async def list_public_suppliers(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    items, total = await svc.get_public_suppliers(db, pagination)
    return PaginatedResponse.create(
        items=[PublicSupplierOut.model_validate(s) for s in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{supplier_id}", response_model=SupplierOut, summary="FR-5.1 Get supplier detail")
async def get_supplier(supplier_id: int, db: DBSession, current_user: AdminUser):
    supplier = await svc.get_supplier(db, supplier_id)
    return SupplierOut.model_validate(supplier)


@router.patch("/{supplier_id}", response_model=SupplierOut, summary="FR-5.1 Update supplier")
async def update_supplier(supplier_id: int, body: SupplierUpdate, db: DBSession, current_user: AdminUser):
    supplier = await svc.update_supplier(db, supplier_id, body, current_user)
    return SupplierOut.model_validate(supplier)


@router.delete("/{supplier_id}", response_model=MessageResponse, summary="FR-5.1 Soft-delete supplier")
async def delete_supplier(supplier_id: int, db: DBSession, current_user: AdminUser):
    await svc.delete_supplier(db, supplier_id, current_user)
    return MessageResponse(message="Supplier deactivated successfully", detail=f"supplier_id={supplier_id}")


# ── FR-5.2: Document upload ────────────────────────────────────────────────────

@router.post("/{supplier_id}/documents", response_model=SupplierDocumentOut, status_code=201, summary="FR-5.2 Upload sustainability cert/doc")
async def upload_document(
    supplier_id: int,
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form(...),
    db: DBSession = None,
    current_user: AdminUser = None,
):
    doc = await svc.upload_document(
        db,
        supplier_id=supplier_id,
        file=file,
        title=title,
        doc_type=doc_type,
        uploader_id=current_user["user_id"],
    )
    return SupplierDocumentOut.model_validate(doc)


@router.get("/{supplier_id}/documents", response_model=PaginatedResponse[SupplierDocumentOut], summary="FR-5.2 List supplier documents")
async def list_documents(supplier_id: int, db: DBSession, current_user: AdminUser, pagination: Pagination):
    docs = await svc.list_documents(db, supplier_id)
    page_docs = docs[pagination.offset: pagination.offset + pagination.page_size]
    return PaginatedResponse.create(
        items=[SupplierDocumentOut.model_validate(d) for d in page_docs],
        total=len(docs),
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.delete("/{supplier_id}/documents/{doc_id}", response_model=MessageResponse, summary="FR-5.2 Delete document")
async def delete_document(supplier_id: int, doc_id: int, db: DBSession, current_user: AdminUser):
    await svc.delete_document(db, supplier_id, doc_id, current_user)
    return MessageResponse(message="Document deleted successfully", detail=f"doc_id={doc_id}")


# ── FR-5.3: Certification review ─────────────────────────────────────────────

@router.post("/{supplier_id}/documents/{doc_id}/review", response_model=SupplierDocumentOut, summary="FR-5.3 Approve or reject certification")
async def review_document(supplier_id: int, doc_id: int, body: DocumentReviewIn, db: DBSession, current_user: AdminUser):
    doc = await svc.review_document(
        db,
        supplier_id=supplier_id,
        doc_id=doc_id,
        action=body.action,
        reviewer_id=current_user["user_id"],
        feedback=body.feedback,
    )
    return SupplierDocumentOut.model_validate(doc)


# ── FR-5.4 / FR-5.5: Compliance status & history ──────────────────────────────

@router.get("/{supplier_id}/compliance", response_model=ComplianceStatusOut, summary="FR-5.4 Current compliance status")
async def get_compliance(supplier_id: int, db: DBSession, current_user: AdminUser):
    return await svc.get_compliance_status(db, supplier_id)


@router.patch("/{supplier_id}/compliance", response_model=ComplianceStatusOut, summary="FR-5.4 Update compliance status")
async def update_compliance(supplier_id: int, body: ComplianceUpdateIn, db: DBSession, current_user: AdminUser):
    return await svc.update_compliance_status(
        db,
        supplier_id=supplier_id,
        new_status=body.status,
        esg_score=body.esg_score,
        notes=body.notes,
        reviewer_id=current_user["user_id"],
    )


@router.get("/{supplier_id}/compliance/history", response_model=PaginatedResponse[ComplianceHistoryEntry], summary="FR-5.5 Compliance change history")
async def compliance_history(supplier_id: int, db: DBSession, current_user: AdminUser, pagination: Pagination):
    entries, total = await svc.get_compliance_history(db, supplier_id, pagination)
    return PaginatedResponse.create(
        items=entries,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


# ── FR-5.7: Supplier location linking ────────────────────────────────────────

@router.post(
    "/{supplier_id}/locations",
    response_model=SupplierLocationOut,
    status_code=201,
    summary="FR-5.7 Link a supplier to an organisation/location",
)
async def add_supplier_location(supplier_id: int, body: SupplierLocationIn, db: DBSession, current_user: AdminUser):
    sl = await svc.add_supplier_location(
        db,
        supplier_id=supplier_id,
        organization_id=body.organization_id,
        location_id=body.location_id,
        service_type=body.service_type,
        relationship_type=body.relationship_type,
    )
    return SupplierLocationOut.model_validate(sl)


# ── FR-5.6: Public ESG view for customers ─────────────────────────────────────

@router.get("/{supplier_id}/public", response_model=PublicSupplierOut, summary="FR-5.6 Single supplier public ESG view")
async def get_public_supplier(supplier_id: int, db: DBSession, current_user: CurrentUser):
    supplier = await svc.get_supplier(db, supplier_id)
    return PublicSupplierOut.model_validate(supplier)
