"""
FR8 — Token Economy & Reward System (Omar).
Wallets, transactions, token rules, rewards catalog, voucher redemption.
"""
from fastapi import APIRouter, Query, status

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import PaginatedResponse
from app.schemas.tokens import (
    RedeemRequest,
    RewardCatalogCreate,
    RewardCatalogOut,
    RewardCatalogUpdate,
    TokenRuleCreate,
    TokenRuleOut,
    TokenRuleUpdate,
    TransactionCreate,
    TransactionOut,
    VoucherOut,
    WalletCreate,
    WalletOut,
)
import app.services.token_service as svc

router = APIRouter()


# ── FR-8.1: Wallet management ────────────────────────────────────────────────

@router.post("/wallets", response_model=WalletOut, status_code=status.HTTP_201_CREATED, summary="FR-8.1 Create wallet")
async def create_wallet(body: WalletCreate, db: DBSession, current_user: AdminUser):
    wallet = await svc.create_wallet(db, body.user_id, body.wallet_type)
    return WalletOut.model_validate(wallet)


@router.get("/wallets/me", response_model=WalletOut, summary="FR-8.1 Get my wallet")
async def get_my_wallet(db: DBSession, current_user: CurrentUser):
    wallet = await svc.get_wallet_by_user(db, current_user["user_id"])
    if not wallet:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Wallet for user", current_user["user_id"])
    return WalletOut.model_validate(wallet)


# ── FR-8.2: Transactions ───────────────────��─────────────────────────────────

@router.get("/wallets/{wallet_id}/transactions", response_model=list[TransactionOut], summary="FR-8.2 List wallet transactions")
async def list_transactions(wallet_id: int, db: DBSession, current_user: CurrentUser, pagination: Pagination):
    txs = await svc.get_transactions(db, wallet_id, offset=pagination.offset, limit=pagination.page_size)
    return [TransactionOut.model_validate(t) for t in txs]


# ── FR-8.3: Token Rules ──────────────────────────────────────────────────────

@router.post("/rules", response_model=TokenRuleOut, status_code=status.HTTP_201_CREATED, summary="FR-8.3 Create token rule")
async def create_rule(body: TokenRuleCreate, db: DBSession, current_user: AdminUser):
    rule = await svc.create_token_rule(db, body.model_dump(), created_by=current_user["user_id"])
    return TokenRuleOut.model_validate(rule)


@router.get("/rules", response_model=list[TokenRuleOut], summary="FR-8.3 List token rules")
async def list_rules(
    db: DBSession, current_user: AdminUser, pagination: Pagination,
    organization_id: int | None = Query(None),
):
    rules = await svc.list_token_rules(db, org_id=organization_id, offset=pagination.offset, limit=pagination.page_size)
    return [TokenRuleOut.model_validate(r) for r in rules]


# ── FR-8.4: Rewards Catalog ──────────────────────────────────────────────────

@router.post("/catalog", response_model=RewardCatalogOut, status_code=status.HTTP_201_CREATED, summary="FR-8.4 Add reward to catalog")
async def create_catalog_item(body: RewardCatalogCreate, db: DBSession, current_user: AdminUser):
    item = await svc.create_catalog_item(db, body.model_dump())
    return RewardCatalogOut.model_validate(item)


@router.get("/catalog", response_model=list[RewardCatalogOut], summary="FR-8.4 Browse rewards catalog")
async def list_catalog(
    db: DBSession, current_user: CurrentUser, pagination: Pagination,
    organization_id: int | None = Query(None),
):
    items = await svc.list_catalog(db, org_id=organization_id, offset=pagination.offset, limit=pagination.page_size)
    return [RewardCatalogOut.model_validate(i) for i in items]


@router.get("/catalog/{item_id}", response_model=RewardCatalogOut, summary="FR-8.4 Get catalog item")
async def get_catalog_item(item_id: int, db: DBSession, current_user: CurrentUser):
    item = await svc.get_catalog_item(db, item_id)
    if not item:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Reward", item_id)
    return RewardCatalogOut.model_validate(item)


# ── FR-8.5: Redeem ───────────────────────────────────────────────────────────

@router.post("/redeem", response_model=VoucherOut, status_code=status.HTTP_201_CREATED, summary="FR-8.5 Redeem tokens for reward")
async def redeem_reward(body: RedeemRequest, db: DBSession, current_user: CurrentUser):
    voucher = await svc.redeem_reward(db, body.user_id, body.reward_id)
    return VoucherOut.model_validate(voucher)