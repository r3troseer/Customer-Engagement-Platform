

"""
FR13 — Audit and Governance
Service layer for audit logs, change history, and approvals.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Approval, AuditLog, ChangeHistory
from app.models.auth import User
from app.models.org import Organization, RestaurantLocation

try:
    from app.core.exceptions import BadRequestException, NotFoundException
except Exception:
    class NotFoundException(Exception):
        pass

    class BadRequestException(Exception):
        pass


DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class BaseAuditService:
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
        return await BaseAuditService._get_one_or_404(db, stmt, f"User {user_id} not found.")

    @staticmethod
    async def _ensure_organization_exists(db: AsyncSession, organization_id: int) -> Organization:
        stmt = select(Organization).where(Organization.id == organization_id)
        return await BaseAuditService._get_one_or_404(
            db,
            stmt,
            f"Organization {organization_id} not found.",
        )

    @staticmethod
    async def _ensure_location_exists(db: AsyncSession, location_id: int) -> RestaurantLocation:
        stmt = select(RestaurantLocation).where(RestaurantLocation.id == location_id)
        return await BaseAuditService._get_one_or_404(
            db,
            stmt,
            f"Location {location_id} not found.",
        )


class AuditLogService(BaseAuditService):
    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> AuditLog:
        await cls._validate_fk_refs(db, payload)
        obj = AuditLog(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, audit_log_id: int) -> AuditLog:
        stmt = select(AuditLog).where(AuditLog.id == audit_log_id)
        return await cls._get_one_or_404(db, stmt, f"Audit log {audit_log_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        user_id: int | None = None,
        organization_id: int | None = None,
        location_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[AuditLog]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(AuditLog).order_by(AuditLog.id.desc())

        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if organization_id is not None:
            stmt = stmt.where(AuditLog.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(AuditLog.location_id == location_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def delete(cls, db: AsyncSession, audit_log_id: int) -> None:
        obj = await cls.get_by_id(db, audit_log_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_fk_refs(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        user_id = payload.get("user_id")
        organization_id = payload.get("organization_id")
        location_id = payload.get("location_id")

        if user_id is not None:
            await cls._ensure_user_exists(db, user_id)
        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)
        if location_id is not None:
            await cls._ensure_location_exists(db, location_id)


class ChangeHistoryService(BaseAuditService):
    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ChangeHistory:
        if payload.get("user_id") is not None:
            await cls._ensure_user_exists(db, payload["user_id"])

        obj = ChangeHistory(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, change_id: int) -> ChangeHistory:
        stmt = select(ChangeHistory).where(ChangeHistory.id == change_id)
        return await cls._get_one_or_404(db, stmt, f"Change history {change_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        field_name: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ChangeHistory]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ChangeHistory).order_by(ChangeHistory.id.desc())

        if user_id is not None:
            stmt = stmt.where(ChangeHistory.user_id == user_id)
        if entity_type:
            stmt = stmt.where(ChangeHistory.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(ChangeHistory.entity_id == entity_id)
        if field_name:
            stmt = stmt.where(ChangeHistory.field_name == field_name)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, change_id: int, payload: dict[str, Any]) -> ChangeHistory:
        obj = await cls.get_by_id(db, change_id)

        if "user_id" in payload and payload["user_id"] != obj.user_id:
            raise BadRequestException("Changing change_history user_id is not allowed.")

        if "entity_type" in payload and payload["entity_type"] != obj.entity_type:
            raise BadRequestException("Changing change_history entity_type is not allowed.")

        if "entity_id" in payload and payload["entity_id"] != obj.entity_id:
            raise BadRequestException("Changing change_history entity_id is not allowed.")

        if "field_name" in payload and payload["field_name"] != obj.field_name:
            raise BadRequestException("Changing change_history field_name is not allowed.")

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, change_id: int) -> None:
        obj = await cls.get_by_id(db, change_id)
        await db.delete(obj)
        await db.commit()


class ApprovalService(BaseAuditService):
    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> Approval:
        await cls._validate_users(db, payload)
        await cls._validate_status_logic(payload)
        obj = Approval(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, approval_id: int) -> Approval:
        stmt = select(Approval).where(Approval.id == approval_id)
        return await cls._get_one_or_404(db, stmt, f"Approval {approval_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        approval_type: str | None = None,
        related_type: str | None = None,
        related_id: int | None = None,
        requested_by: int | None = None,
        approved_by: int | None = None,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Approval]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(Approval).order_by(Approval.id.desc())

        if approval_type:
            stmt = stmt.where(Approval.approval_type == approval_type)
        if related_type:
            stmt = stmt.where(Approval.related_type == related_type)
        if related_id is not None:
            stmt = stmt.where(Approval.related_id == related_id)
        if requested_by is not None:
            stmt = stmt.where(Approval.requested_by == requested_by)
        if approved_by is not None:
            stmt = stmt.where(Approval.approved_by == approved_by)
        if status:
            stmt = stmt.where(Approval.status == status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, approval_id: int, payload: dict[str, Any]) -> Approval:
        obj = await cls.get_by_id(db, approval_id)

        if "approval_type" in payload and payload["approval_type"] != obj.approval_type:
            raise BadRequestException("Changing approval_type is not allowed.")

        if "related_type" in payload and payload["related_type"] != obj.related_type:
            raise BadRequestException("Changing related_type is not allowed.")

        if "related_id" in payload and payload["related_id"] != obj.related_id:
            raise BadRequestException("Changing related_id is not allowed.")

        if "requested_by" in payload and payload["requested_by"] != obj.requested_by:
            raise BadRequestException("Changing requested_by is not allowed.")

        merged = {
            "status": payload.get("status", obj.status),
            "approved_by": payload.get("approved_by", obj.approved_by),
            "decided_at": payload.get("decided_at", obj.decided_at),
        }

        await cls._validate_users(db, payload)
        await cls._validate_status_logic(merged)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, approval_id: int) -> None:
        obj = await cls.get_by_id(db, approval_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_users(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        requested_by = payload.get("requested_by")
        approved_by = payload.get("approved_by")

        if requested_by is not None:
            await cls._ensure_user_exists(db, requested_by)
        if approved_by is not None:
            await cls._ensure_user_exists(db, approved_by)

    @classmethod
    async def _validate_status_logic(cls, payload: dict[str, Any]) -> None:
        status = payload.get("status")
        approved_by = payload.get("approved_by")
        decided_at = payload.get("decided_at")

        if status in {"approved", "rejected"}:
            if approved_by is None:
                raise BadRequestException("approved_by is required when status is approved or rejected.")
            if decided_at is None:
                raise BadRequestException("decided_at is required when status is approved or rejected.")



