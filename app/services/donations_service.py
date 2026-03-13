"""
FR9 — Donations and ESG Offset
Service layer for donation causes, donations, conversions, impacts,
and attributions.

Notes:
- Business logic only, no HTTP concerns.
- Uses async SQLAlchemy 2.x.
- Validates foreign keys and core consistency rules.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import User
from app.models.donations import (
    Donation,
    DonationAttribution,
    DonationCause,
    DonationConversion,
    DonationImpact,
)
from app.models.org import Organization

try:
    from app.models.tokens import WalletTransaction
except Exception:
    WalletTransaction = None

try:
    from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
except Exception:
    class NotFoundException(Exception):
        pass

    class ConflictException(Exception):
        pass

    class BadRequestException(Exception):
        pass


# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


# ── Helpers ───────────────────────────────────────────────────────────────────


class BaseDonationService:
    """Shared DB helpers for FR9 services."""

    @staticmethod
    def _normalize_pagination(
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> tuple[int, int]:
        offset = max(offset or 0, 0)
        limit = min(max(limit or DEFAULT_LIMIT, 1), MAX_LIMIT)
        return offset, limit

    @staticmethod
    async def _commit_refresh(db: AsyncSession, obj: Any) -> Any:
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def _get_one_or_404(db: AsyncSession, stmt: Select, message: str):
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundException(message)
        return obj

    @staticmethod
    async def _ensure_user_exists(db: AsyncSession, user_id: int) -> User:
        stmt = select(User).where(User.id == user_id)
        return await BaseDonationService._get_one_or_404(db, stmt, f"User {user_id} not found.")

    @staticmethod
    async def _ensure_organization_exists(db: AsyncSession, organization_id: int) -> Organization:
        stmt = select(Organization).where(Organization.id == organization_id)
        return await BaseDonationService._get_one_or_404(
            db,
            stmt,
            f"Organization {organization_id} not found.",
        )

    @staticmethod
    async def _ensure_cause_exists(db: AsyncSession, cause_id: int) -> DonationCause:
        stmt = select(DonationCause).where(DonationCause.id == cause_id)
        return await BaseDonationService._get_one_or_404(
            db,
            stmt,
            f"Donation cause {cause_id} not found.",
        )

    @staticmethod
    async def _ensure_donation_exists(db: AsyncSession, donation_id: int) -> Donation:
        stmt = (
            select(Donation)
            .where(Donation.id == donation_id)
            .options(
                selectinload(Donation.cause),
                selectinload(Donation.conversion),
                selectinload(Donation.impacts),
                selectinload(Donation.attributions),
            )
        )
        return await BaseDonationService._get_one_or_404(
            db,
            stmt,
            f"Donation {donation_id} not found.",
        )

    @staticmethod
    async def _ensure_wallet_transaction_exists(db: AsyncSession, wallet_transaction_id: int) -> None:
        if WalletTransaction is None:
            return

        stmt = select(WalletTransaction).where(WalletTransaction.id == wallet_transaction_id)
        await BaseDonationService._get_one_or_404(
            db,
            stmt,
            f"Wallet transaction {wallet_transaction_id} not found.",
        )

    @staticmethod
    async def _validate_positive_decimal(value: Decimal, field_name: str) -> None:
        if value <= 0:
            raise BadRequestException(f"{field_name} must be greater than zero.")

    @staticmethod
    async def _validate_non_negative_decimal(value: Decimal, field_name: str) -> None:
        if value < 0:
            raise BadRequestException(f"{field_name} cannot be negative.")


# ── Donation Cause Service ────────────────────────────────────────────────────


class DonationCauseService(BaseDonationService):
    """Business logic for donation causes."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> DonationCause:
        await cls._validate_create(db, payload)
        obj = DonationCause(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, cause_id: int) -> DonationCause:
        stmt = (
            select(DonationCause)
            .where(DonationCause.id == cause_id)
            .options(selectinload(DonationCause.donations))
        )
        return await cls._get_one_or_404(db, stmt, f"Donation cause {cause_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        cause_type: str | None = None,
        is_active: bool | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[DonationCause]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(DonationCause).order_by(DonationCause.id.desc())

        if organization_id is not None:
            stmt = stmt.where(DonationCause.organization_id == organization_id)
        if cause_type:
            stmt = stmt.where(DonationCause.cause_type == cause_type)
        if is_active is not None:
            stmt = stmt.where(DonationCause.is_active == is_active)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, cause_id: int, payload: dict[str, Any]) -> DonationCause:
        obj = await cls.get_by_id(db, cause_id)
        await cls._validate_update(db, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, cause_id: int) -> None:
        obj = await cls.get_by_id(db, cause_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_donations(
        cls,
        db: AsyncSession,
        cause_id: int,
        *,
        user_id: int | None = None,
        organization_id: int | None = None,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Donation]:
        await cls._ensure_cause_exists(db, cause_id)
        return await DonationService.list(
            db,
            cause_id=cause_id,
            user_id=user_id,
            organization_id=organization_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload.get("organization_id")
        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)

    @classmethod
    async def _validate_update(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload.get("organization_id")
        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)


# ── Donation Service ──────────────────────────────────────────────────────────


class DonationService(BaseDonationService):
    """Business logic for donations."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> Donation:
        await cls._validate_create(db, payload)
        obj = Donation(**payload)
        db.add(obj)
        created = await cls._commit_refresh(db, obj)
        return await cls.get_by_id(db, created.id)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, donation_id: int) -> Donation:
        return await cls._ensure_donation_exists(db, donation_id)

    @classmethod
    async def get_detail(cls, db: AsyncSession, donation_id: int) -> Donation:
        return await cls.get_by_id(db, donation_id)

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        user_id: int | None = None,
        cause_id: int | None = None,
        organization_id: int | None = None,
        wallet_transaction_id: int | None = None,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Donation]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(Donation).order_by(Donation.id.desc())

        if user_id is not None:
            stmt = stmt.where(Donation.user_id == user_id)
        if cause_id is not None:
            stmt = stmt.where(Donation.cause_id == cause_id)
        if organization_id is not None:
            stmt = stmt.where(Donation.organization_id == organization_id)
        if wallet_transaction_id is not None:
            stmt = stmt.where(Donation.wallet_transaction_id == wallet_transaction_id)
        if status:
            stmt = stmt.where(Donation.status == status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, donation_id: int, payload: dict[str, Any]) -> Donation:
        obj = await cls.get_by_id(db, donation_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        await cls._commit_refresh(db, obj)
        return await cls.get_by_id(db, donation_id)

    @classmethod
    async def delete(cls, db: AsyncSession, donation_id: int) -> None:
        obj = await cls.get_by_id(db, donation_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_conversion(cls, db: AsyncSession, donation_id: int) -> DonationConversion | None:
        await cls._ensure_donation_exists(db, donation_id)
        return await DonationConversionService.get_by_donation_id(db, donation_id)

    @classmethod
    async def get_impacts(
        cls,
        db: AsyncSession,
        donation_id: int,
        *,
        impact_type: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[DonationImpact]:
        await cls._ensure_donation_exists(db, donation_id)
        return await DonationImpactService.list(
            db,
            donation_id=donation_id,
            impact_type=impact_type,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_attributions(
        cls,
        db: AsyncSession,
        donation_id: int,
        *,
        user_id: int | None = None,
        organization_id: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[DonationAttribution]:
        await cls._ensure_donation_exists(db, donation_id)
        return await DonationAttributionService.list(
            db,
            donation_id=donation_id,
            user_id=user_id,
            organization_id=organization_id,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        await cls._ensure_user_exists(db, payload["user_id"])
        cause = await cls._ensure_cause_exists(db, payload["cause_id"])

        token_amount = payload["token_amount"]
        await cls._validate_positive_decimal(token_amount, "token_amount")

        organization_id = payload.get("organization_id")
        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)

        wallet_transaction_id = payload.get("wallet_transaction_id")
        if wallet_transaction_id is not None:
            await cls._ensure_wallet_transaction_exists(db, wallet_transaction_id)

        if cause.organization_id is not None and organization_id is not None:
            if cause.organization_id != organization_id:
                raise BadRequestException(
                    "Donation organization_id must match the cause organization_id."
                )

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        donation: Donation,
        payload: dict[str, Any],
    ) -> None:
        if "user_id" in payload and payload["user_id"] != donation.user_id:
            raise BadRequestException("Changing donation user_id is not allowed.")

        if "cause_id" in payload and payload["cause_id"] != donation.cause_id:
            raise BadRequestException("Changing donation cause_id is not allowed.")

        if "organization_id" in payload and payload["organization_id"] != donation.organization_id:
            raise BadRequestException("Changing donation organization_id is not allowed.")

        if "token_amount" in payload and payload["token_amount"] is not None:
            await cls._validate_positive_decimal(payload["token_amount"], "token_amount")

        if "wallet_transaction_id" in payload and payload["wallet_transaction_id"] is not None:
            await cls._ensure_wallet_transaction_exists(db, payload["wallet_transaction_id"])


# ── Donation Conversion Service ───────────────────────────────────────────────


class DonationConversionService(BaseDonationService):
    """Business logic for donation conversions."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> DonationConversion:
        await cls._validate_create(db, payload)
        obj = DonationConversion(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, conversion_id: int) -> DonationConversion:
        stmt = select(DonationConversion).where(DonationConversion.id == conversion_id)
        return await cls._get_one_or_404(
            db,
            stmt,
            f"Donation conversion {conversion_id} not found.",
        )

    @classmethod
    async def get_by_donation_id(cls, db: AsyncSession, donation_id: int) -> DonationConversion | None:
        stmt = select(DonationConversion).where(DonationConversion.donation_id == donation_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        donation_id: int | None = None,
        conversion_currency: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[DonationConversion]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(DonationConversion).order_by(DonationConversion.id.desc())

        if donation_id is not None:
            stmt = stmt.where(DonationConversion.donation_id == donation_id)
        if conversion_currency:
            stmt = stmt.where(DonationConversion.conversion_currency == conversion_currency)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        conversion_id: int,
        payload: dict[str, Any],
    ) -> DonationConversion:
        obj = await cls.get_by_id(db, conversion_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, conversion_id: int) -> None:
        obj = await cls.get_by_id(db, conversion_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        donation_id = payload["donation_id"]
        donation = await cls._ensure_donation_exists(db, donation_id)

        existing = await cls.get_by_donation_id(db, donation_id)
        if existing is not None:
            raise ConflictException(f"Donation {donation_id} already has a conversion.")

        await cls._validate_positive_decimal(payload["token_amount"], "token_amount")
        await cls._validate_non_negative_decimal(payload["cash_value"], "cash_value")
        await cls._validate_positive_decimal(payload["conversion_rate"], "conversion_rate")

        if payload["token_amount"] > donation.token_amount:
            raise BadRequestException("Conversion token_amount cannot exceed donation token_amount.")

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        conversion: DonationConversion,
        payload: dict[str, Any],
    ) -> None:
        if "donation_id" in payload and payload["donation_id"] != conversion.donation_id:
            raise BadRequestException("Changing conversion donation_id is not allowed.")

        donation = await cls._ensure_donation_exists(db, conversion.donation_id)

        token_amount = payload.get("token_amount", conversion.token_amount)
        cash_value = payload.get("cash_value", conversion.cash_value)
        conversion_rate = payload.get("conversion_rate", conversion.conversion_rate)

        await cls._validate_positive_decimal(token_amount, "token_amount")
        await cls._validate_non_negative_decimal(cash_value, "cash_value")
        await cls._validate_positive_decimal(conversion_rate, "conversion_rate")

        if token_amount > donation.token_amount:
            raise BadRequestException("Conversion token_amount cannot exceed donation token_amount.")


# ── Donation Impact Service ───────────────────────────────────────────────────


class DonationImpactService(BaseDonationService):
    """Business logic for donation impacts."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> DonationImpact:
        await cls._validate_create(db, payload)
        obj = DonationImpact(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, impact_id: int) -> DonationImpact:
        stmt = select(DonationImpact).where(DonationImpact.id == impact_id)
        return await cls._get_one_or_404(db, stmt, f"Donation impact {impact_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        donation_id: int | None = None,
        impact_type: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[DonationImpact]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(DonationImpact).order_by(DonationImpact.id.desc())

        if donation_id is not None:
            stmt = stmt.where(DonationImpact.donation_id == donation_id)
        if impact_type:
            stmt = stmt.where(DonationImpact.impact_type == impact_type)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, impact_id: int, payload: dict[str, Any]) -> DonationImpact:
        obj = await cls.get_by_id(db, impact_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, impact_id: int) -> None:
        obj = await cls.get_by_id(db, impact_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        await cls._ensure_donation_exists(db, payload["donation_id"])
        await cls._validate_positive_decimal(payload["quantity"], "quantity")

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        impact: DonationImpact,
        payload: dict[str, Any],
    ) -> None:
        if "donation_id" in payload and payload["donation_id"] != impact.donation_id:
            raise BadRequestException("Changing impact donation_id is not allowed.")

        quantity = payload.get("quantity")
        if quantity is not None:
            await cls._validate_positive_decimal(quantity, "quantity")


# ── Donation Attribution Service ──────────────────────────────────────────────


class DonationAttributionService(BaseDonationService):
    """Business logic for donation attributions."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> DonationAttribution:
        await cls._validate_create(db, payload)
        obj = DonationAttribution(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, attribution_id: int) -> DonationAttribution:
        stmt = select(DonationAttribution).where(DonationAttribution.id == attribution_id)
        return await cls._get_one_or_404(
            db,
            stmt,
            f"Donation attribution {attribution_id} not found.",
        )

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        donation_id: int | None = None,
        user_id: int | None = None,
        organization_id: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[DonationAttribution]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(DonationAttribution).order_by(DonationAttribution.id.desc())

        if donation_id is not None:
            stmt = stmt.where(DonationAttribution.donation_id == donation_id)
        if user_id is not None:
            stmt = stmt.where(DonationAttribution.user_id == user_id)
        if organization_id is not None:
            stmt = stmt.where(DonationAttribution.organization_id == organization_id)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        attribution_id: int,
        payload: dict[str, Any],
    ) -> DonationAttribution:
        obj = await cls.get_by_id(db, attribution_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, attribution_id: int) -> None:
        obj = await cls.get_by_id(db, attribution_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        donation = await cls._ensure_donation_exists(db, payload["donation_id"])
        await cls._ensure_user_exists(db, payload["user_id"])

        organization_id = payload.get("organization_id")
        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)

        attributed_tokens = payload["attributed_tokens"]
        attributed_impact_value = payload["attributed_impact_value"]

        await cls._validate_non_negative_decimal(attributed_tokens, "attributed_tokens")
        await cls._validate_non_negative_decimal(attributed_impact_value, "attributed_impact_value")

        if organization_id is not None and donation.organization_id is not None:
            if organization_id != donation.organization_id:
                raise BadRequestException(
                    "Attribution organization_id must match donation organization_id."
                )

        await cls._validate_attributed_tokens_total(
            db,
            donation_id=donation.id,
            incoming_tokens=attributed_tokens,
        )

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        attribution: DonationAttribution,
        payload: dict[str, Any],
    ) -> None:
        if "donation_id" in payload and payload["donation_id"] != attribution.donation_id:
            raise BadRequestException("Changing attribution donation_id is not allowed.")

        if "user_id" in payload and payload["user_id"] != attribution.user_id:
            raise BadRequestException("Changing attribution user_id is not allowed.")

        if "organization_id" in payload and payload["organization_id"] != attribution.organization_id:
            raise BadRequestException("Changing attribution organization_id is not allowed.")

        new_tokens = payload.get("attributed_tokens", attribution.attributed_tokens)
        new_impact_value = payload.get(
            "attributed_impact_value",
            attribution.attributed_impact_value,
        )

        await cls._validate_non_negative_decimal(new_tokens, "attributed_tokens")
        await cls._validate_non_negative_decimal(new_impact_value, "attributed_impact_value")

        await cls._validate_attributed_tokens_total(
            db,
            donation_id=attribution.donation_id,
            incoming_tokens=new_tokens,
            exclude_id=attribution.id,
        )

    @classmethod
    async def _validate_attributed_tokens_total(
        cls,
        db: AsyncSession,
        *,
        donation_id: int,
        incoming_tokens: Decimal,
        exclude_id: int | None = None,
    ) -> None:
        donation = await cls._ensure_donation_exists(db, donation_id)

        stmt = select(DonationAttribution).where(DonationAttribution.donation_id == donation_id)
        if exclude_id is not None:
            stmt = stmt.where(DonationAttribution.id != exclude_id)

        result = await db.execute(stmt)
        existing_rows = list(result.scalars().all())
        existing_total = sum((row.attributed_tokens for row in existing_rows), start=Decimal("0"))

        if existing_total + incoming_tokens > donation.token_amount:
            raise BadRequestException(
                "Total attributed_tokens cannot exceed donation token_amount."
            )