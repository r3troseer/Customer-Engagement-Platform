"""
FR8 — Token Economy service layer (Omar).
Wallet management, transactions, token rules, rewards catalog, vouchers.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tokens import (
    RewardRule,
    RewardVoucher,
    RewardsCatalog,
    TokenRule,
    Wallet,
    WalletTransaction,
)


# ── Wallets ───────────────────────────────────────────────────────────────────

async def create_wallet(db: AsyncSession, user_id: int, wallet_type: str) -> Wallet:
    wallet = Wallet(user_id=user_id, wallet_type=wallet_type)
    db.add(wallet)
    await db.flush()
    await db.refresh(wallet)
    return wallet


async def get_wallet_by_user(db: AsyncSession, user_id: int) -> Wallet | None:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    return result.scalar_one_or_none()


async def credit_tokens(
    db: AsyncSession, wallet_id: int, amount: Decimal,
    tx_type: str = "earn", description: str | None = None,
    reference_type: str | None = None, reference_id: int | None = None,
    created_by: int | None = None,
) -> WalletTransaction:
    wallet = await db.get(Wallet, wallet_id)
    if not wallet:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Wallet", wallet_id)

    balance_before = wallet.balance
    wallet.balance += amount
    balance_after = wallet.balance

    tx = WalletTransaction(
        wallet_id=wallet_id,
        transaction_type=tx_type,
        direction="credit",
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
        transaction_date=datetime.now(timezone.utc),
        created_by=created_by,
    )
    db.add(tx)
    await db.flush()
    await db.refresh(tx)
    return tx


async def debit_tokens(
    db: AsyncSession, wallet_id: int, amount: Decimal,
    tx_type: str = "redeem", description: str | None = None,
    reference_type: str | None = None, reference_id: int | None = None,
    created_by: int | None = None,
) -> WalletTransaction:
    wallet = await db.get(Wallet, wallet_id)
    if not wallet:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Wallet", wallet_id)

    if wallet.balance < amount:
        from app.core.exceptions import InsufficientTokensError
        raise InsufficientTokensError(float(wallet.balance), float(amount))

    balance_before = wallet.balance
    wallet.balance -= amount
    balance_after = wallet.balance

    tx = WalletTransaction(
        wallet_id=wallet_id,
        transaction_type=tx_type,
        direction="debit",
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_type=reference_type,
        reference_id=reference_id,
        description=description,
        transaction_date=datetime.now(timezone.utc),
        created_by=created_by,
    )
    db.add(tx)
    await db.flush()
    await db.refresh(tx)
    return tx


async def get_transactions(
    db: AsyncSession, wallet_id: int, offset: int = 0, limit: int = 50,
) -> list[WalletTransaction]:
    result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet_id)
        .order_by(WalletTransaction.transaction_date.desc())
        .offset(offset).limit(limit)
    )
    return list(result.scalars().all())


# ── Token Rules ───────────────────────────────────────────────────────────────

async def create_token_rule(db: AsyncSession, data: dict, created_by: int | None = None) -> TokenRule:
    rule = TokenRule(**data, created_by=created_by)
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


async def list_token_rules(
    db: AsyncSession, org_id: int | None = None, offset: int = 0, limit: int = 50,
) -> list[TokenRule]:
    stmt = select(TokenRule)
    if org_id:
        stmt = stmt.where(TokenRule.organization_id == org_id)
    result = await db.execute(stmt.offset(offset).limit(limit))
    return list(result.scalars().all())


# ── Rewards Catalog ───────────────────────────────────────────────────────────

async def create_catalog_item(db: AsyncSession, data: dict) -> RewardsCatalog:
    item = RewardsCatalog(**data)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def list_catalog(
    db: AsyncSession, org_id: int | None = None, offset: int = 0, limit: int = 50,
) -> list[RewardsCatalog]:
    stmt = select(RewardsCatalog).where(RewardsCatalog.status == "active")
    if org_id:
        stmt = stmt.where(RewardsCatalog.organization_id == org_id)
    result = await db.execute(stmt.offset(offset).limit(limit))
    return list(result.scalars().all())


async def get_catalog_item(db: AsyncSession, item_id: int) -> RewardsCatalog | None:
    return await db.get(RewardsCatalog, item_id)


# ── Redeem → Voucher ─────────────────────────────────────────────────────────

async def redeem_reward(
    db: AsyncSession, user_id: int, reward_id: int,
) -> RewardVoucher:
    reward = await get_catalog_item(db, reward_id)
    if not reward:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Reward", reward_id)

    wallet = await get_wallet_by_user(db, user_id)
    if not wallet:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Wallet for user", user_id)

    # Debit tokens
    await debit_tokens(
        db, wallet.id, reward.token_cost,
        tx_type="redeem", description=f"Redeemed: {reward.title}",
        reference_type="rewards_catalog", reference_id=reward.id,
    )

    # Decrement quantity if limited
    if reward.quantity_available is not None:
        if reward.quantity_available <= 0:
            from app.core.exceptions import UnprocessableError
            raise UnprocessableError("Reward out of stock")
        reward.quantity_available -= 1

    voucher = RewardVoucher(
        reward_id=reward_id,
        user_id=user_id,
        voucher_code=uuid.uuid4().hex[:12].upper(),
        issued_at=datetime.now(timezone.utc),
    )
    db.add(voucher)
    await db.flush()
    await db.refresh(voucher)
    return voucher