"""
FR10 — Blockchain Verification & Transparency (Omar).
Record anchoring, hash management, Polygon integration, public verification.
"""
from fastapi import APIRouter, Query, status

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.blockchain import (
    AnchorRequest,
    AnchorResponse,
    BlockchainHashCreate,
    BlockchainHashOut,
    BlockchainRecordCreate,
    BlockchainRecordOut,
    BlockchainRecordUpdate,
    BlockchainTxOut,
    PublicVerificationOut,
)
from app.schemas.common import MessageResponse
import app.services.blockchain_service as svc

router = APIRouter()


# ── FR-10.1: Blockchain Records ──────────────────────────────────────────────

@router.post("/records", response_model=BlockchainRecordOut, status_code=status.HTTP_201_CREATED, summary="FR-10.1 Create blockchain record")
async def create_record(body: BlockchainRecordCreate, db: DBSession, current_user: AdminUser):
    record = await svc.create_record(db, body.model_dump(), created_by=current_user["user_id"])
    return BlockchainRecordOut.model_validate(record)


@router.get("/records", response_model=list[BlockchainRecordOut], summary="FR-10.1 List blockchain records")
async def list_records(
    db: DBSession, current_user: AdminUser, pagination: Pagination,
    organization_id: int | None = Query(None),
):
    records = await svc.list_records(db, org_id=organization_id, offset=pagination.offset, limit=pagination.page_size)
    return [BlockchainRecordOut.model_validate(r) for r in records]


@router.get("/records/{record_id}", response_model=BlockchainRecordOut, summary="FR-10.1 Get blockchain record")
async def get_record(record_id: int, db: DBSession, current_user: CurrentUser):
    record = await svc.get_record(db, record_id)
    if not record:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("BlockchainRecord", record_id)
    return BlockchainRecordOut.model_validate(record)


# ── FR-10.2: Anchor on Polygon ───────────────────────────────────────────────

@router.post("/anchor", response_model=AnchorResponse, summary="FR-10.2 Anchor record hash on Polygon")
async def anchor_record(body: AnchorRequest, db: DBSession, current_user: AdminUser):
    result = await svc.anchor_record(db, body.record_id)
    return AnchorResponse(**result)


# ── FR-10.3: Public Verification ─────────────────────────────────────────────

@router.get("/verify/{reference_code}", response_model=PublicVerificationOut, summary="FR-10.3 Public verification (no auth)")
async def verify_public(reference_code: str, db: DBSession):
    result = await svc.get_public_verification(db, reference_code)
    if not result:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Public verification", reference_code)
    return PublicVerificationOut(**result)