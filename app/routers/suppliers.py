"""
FR5 — Supplier Transparency & Compliance
Endpoints for registering suppliers, uploading/reviewing certifications,
tracking compliance history, and exposing public ESG data to customers.
"""
from fastapi import APIRouter, UploadFile, File

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter()


# ── FR-5.1: Supplier CRUD ──────────────────────────────────────────────────────

@router.post("/", summary="FR-5.1 Register a new supplier")
async def create_supplier(db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.create_supplier()
    raise NotImplementedError


@router.get("/", summary="FR-5.1 List suppliers (paginated)")
async def list_suppliers(db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: implement supplier_service.list_suppliers()
    raise NotImplementedError


@router.get("/{supplier_id}", summary="FR-5.1 Get supplier detail")
async def get_supplier(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.get_supplier()
    raise NotImplementedError


@router.patch("/{supplier_id}", summary="FR-5.1 Update supplier")
async def update_supplier(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.update_supplier()
    raise NotImplementedError


@router.delete("/{supplier_id}", summary="FR-5.1 Soft-delete supplier")
async def delete_supplier(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.delete_supplier()
    raise NotImplementedError


# ── FR-5.2: Document upload ────────────────────────────────────────────────────

@router.post("/{supplier_id}/documents", summary="FR-5.2 Upload sustainability cert/doc")
async def upload_document(
    supplier_id: int,
    file: UploadFile = File(...),
    db: DBSession = None,
    current_user: AdminUser = None,
):
    # TODO: implement supplier_service.upload_document()
    # Calls file_storage.save_upload() then creates SupplierDocument row
    # Notifies admins via notification_service
    raise NotImplementedError


@router.get("/{supplier_id}/documents", summary="FR-5.2 List supplier documents")
async def list_documents(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.list_documents()
    raise NotImplementedError


@router.delete("/{supplier_id}/documents/{doc_id}", summary="FR-5.2 Delete document")
async def delete_document(supplier_id: int, doc_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.delete_document()
    raise NotImplementedError


# ── FR-5.3: Certification review ─────────────────────────────────────────────

@router.post("/{supplier_id}/documents/{doc_id}/review", summary="FR-5.3 Approve or reject certification")
async def review_document(supplier_id: int, doc_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.review_document()
    # Updates review_status, writes audit log, sends notification
    raise NotImplementedError


# ── FR-5.4 / FR-5.5: Compliance status & history ──────────────────────────────

@router.get("/{supplier_id}/compliance", summary="FR-5.4 Current compliance status")
async def get_compliance(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.get_compliance_status()
    raise NotImplementedError


@router.patch("/{supplier_id}/compliance", summary="FR-5.4 Update compliance status")
async def update_compliance(supplier_id: int, db: DBSession, current_user: AdminUser):
    # TODO: implement supplier_service.update_compliance_status()
    raise NotImplementedError


@router.get("/{supplier_id}/compliance/history", summary="FR-5.5 Compliance change history")
async def compliance_history(supplier_id: int, db: DBSession, current_user: AdminUser, pagination: Pagination):
    # TODO: implement supplier_service.get_compliance_history() — append-only records
    raise NotImplementedError


# ── FR-5.6: Public ESG view for customers ─────────────────────────────────────

@router.get("/public", summary="FR-5.6 Public supplier ESG info (customers)")
async def list_public_suppliers(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: implement supplier_service.get_public_suppliers()
    # Filters is_public=True AND status='active', returns limited fields only
    raise NotImplementedError


@router.get("/{supplier_id}/public", summary="FR-5.6 Single supplier public ESG view")
async def get_public_supplier(supplier_id: int, db: DBSession, current_user: CurrentUser):
    # TODO: implement supplier_service.get_public_supplier()
    raise NotImplementedError
