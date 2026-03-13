"""
FR3 — Compliance Core

Service layer for:
- compliance frameworks
- compliance requirements
- organization compliance
- location compliance
- compliance evidence
- compliance reviews
- compliance documents
- compliance document versions
- compliance status history
- compliance alerts
- compliance scores

Notes:
- Business logic only, no HTTP concerns.
- Async SQLAlchemy 2.x style.
- Includes common validation, filtering, and status-history syncing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import User
from app.models.compliance import (
    ComplianceAlert,
    ComplianceDocument,
    ComplianceDocumentVersion,
    ComplianceEvidence,
    ComplianceFramework,
    ComplianceRequirement,
    ComplianceReview,
    ComplianceScore,
    ComplianceStatusHistory,
    LocationCompliance,
    OrganizationCompliance,
)
from app.models.org import Organization, RestaurantLocation

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


# ── Base Helpers ──────────────────────────────────────────────────────────────


class BaseComplianceService:
    """Shared DB helpers for FR3 services."""

    @staticmethod
    def _normalize_pagination(offset: int = DEFAULT_OFFSET, limit: int = DEFAULT_LIMIT) -> tuple[int, int]:
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
        return await BaseComplianceService._get_one_or_404(db, stmt, f"User {user_id} not found.")

    @staticmethod
    async def _ensure_organization_exists(db: AsyncSession, organization_id: int) -> Organization:
        stmt = select(Organization).where(Organization.id == organization_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Organization {organization_id} not found.",
        )

    @staticmethod
    async def _ensure_location_exists(db: AsyncSession, location_id: int) -> RestaurantLocation:
        stmt = select(RestaurantLocation).where(RestaurantLocation.id == location_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Location {location_id} not found.",
        )

    @staticmethod
    async def _ensure_framework_exists(db: AsyncSession, framework_id: int) -> ComplianceFramework:
        stmt = select(ComplianceFramework).where(ComplianceFramework.id == framework_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Compliance framework {framework_id} not found.",
        )

    @staticmethod
    async def _ensure_requirement_exists(db: AsyncSession, requirement_id: int) -> ComplianceRequirement:
        stmt = select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Compliance requirement {requirement_id} not found.",
        )

    @staticmethod
    async def _ensure_org_compliance_exists(
        db: AsyncSession,
        organization_compliance_id: int,
    ) -> OrganizationCompliance:
        stmt = select(OrganizationCompliance).where(
            OrganizationCompliance.id == organization_compliance_id
        )
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Organization compliance {organization_compliance_id} not found.",
        )

    @staticmethod
    async def _ensure_location_compliance_exists(
        db: AsyncSession,
        location_compliance_id: int,
    ) -> LocationCompliance:
        stmt = select(LocationCompliance).where(LocationCompliance.id == location_compliance_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Location compliance {location_compliance_id} not found.",
        )

    @staticmethod
    async def _ensure_evidence_exists(db: AsyncSession, evidence_id: int) -> ComplianceEvidence:
        stmt = select(ComplianceEvidence).where(ComplianceEvidence.id == evidence_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Compliance evidence {evidence_id} not found.",
        )

    @staticmethod
    async def _ensure_review_exists(db: AsyncSession, review_id: int) -> ComplianceReview:
        stmt = select(ComplianceReview).where(ComplianceReview.id == review_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Compliance review {review_id} not found.",
        )

    @staticmethod
    async def _ensure_document_exists(db: AsyncSession, document_id: int) -> ComplianceDocument:
        stmt = select(ComplianceDocument).where(ComplianceDocument.id == document_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Compliance document {document_id} not found.",
        )

    @staticmethod
    async def _ensure_score_exists(db: AsyncSession, score_id: int) -> ComplianceScore:
        stmt = select(ComplianceScore).where(ComplianceScore.id == score_id)
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Compliance score {score_id} not found.",
        )

    @staticmethod
    async def _ensure_location_belongs_to_org(
        db: AsyncSession,
        location_id: int,
        organization_id: int,
    ) -> RestaurantLocation:
        stmt = select(RestaurantLocation).where(
            RestaurantLocation.id == location_id,
            RestaurantLocation.organization_id == organization_id,
        )
        return await BaseComplianceService._get_one_or_404(
            db,
            stmt,
            f"Location {location_id} not found for organization {organization_id}.",
        )


# ── Compliance Frameworks ─────────────────────────────────────────────────────


class ComplianceFrameworkService(BaseComplianceService):
    """Business logic for compliance frameworks."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ComplianceFramework:
        await cls._validate_create(db, payload)
        obj = ComplianceFramework(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, framework_id: int) -> ComplianceFramework:
        stmt = (
            select(ComplianceFramework)
            .where(ComplianceFramework.id == framework_id)
            .options(selectinload(ComplianceFramework.requirements))
        )
        return await cls._get_one_or_404(db, stmt, f"Compliance framework {framework_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        framework_type: str | None = None,
        status: str | None = None,
        created_by: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceFramework]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceFramework).order_by(ComplianceFramework.id.desc())

        if framework_type:
            stmt = stmt.where(ComplianceFramework.framework_type == framework_type)
        if status:
            stmt = stmt.where(ComplianceFramework.status == status)
        if created_by is not None:
            stmt = stmt.where(ComplianceFramework.created_by == created_by)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        framework_id: int,
        payload: dict[str, Any],
    ) -> ComplianceFramework:
        obj = await cls.get_by_id(db, framework_id)
        await cls._validate_update(db, framework_id, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, framework_id: int) -> None:
        obj = await cls.get_by_id(db, framework_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_requirements(
        cls,
        db: AsyncSession,
        framework_id: int,
        *,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceRequirement]:
        await cls._ensure_framework_exists(db, framework_id)
        return await ComplianceRequirementService.list(
            db,
            framework_id=framework_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        created_by = payload.get("created_by")
        if created_by is not None:
            await cls._ensure_user_exists(db, created_by)

        framework_code = payload.get("framework_code")
        if framework_code:
            await cls._validate_unique_framework_code(db, framework_code)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        framework_id: int,
        payload: dict[str, Any],
    ) -> None:
        if "created_by" in payload and payload["created_by"] is not None:
            await cls._ensure_user_exists(db, payload["created_by"])

        if "framework_code" in payload and payload["framework_code"]:
            await cls._validate_unique_framework_code(
                db,
                payload["framework_code"],
                exclude_id=framework_id,
            )

    @classmethod
    async def _validate_unique_framework_code(
        cls,
        db: AsyncSession,
        framework_code: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        stmt = select(ComplianceFramework).where(
            ComplianceFramework.framework_code == framework_code
        )
        if exclude_id is not None:
            stmt = stmt.where(ComplianceFramework.id != exclude_id)

        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(f"Framework code '{framework_code}' already exists.")


# ── Compliance Requirements ───────────────────────────────────────────────────


class ComplianceRequirementService(BaseComplianceService):
    """Business logic for framework requirements."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ComplianceRequirement:
        await cls._validate_create(db, payload)
        obj = ComplianceRequirement(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, requirement_id: int) -> ComplianceRequirement:
        stmt = select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id)
        return await cls._get_one_or_404(db, stmt, f"Compliance requirement {requirement_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        framework_id: int | None = None,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceRequirement]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceRequirement).order_by(ComplianceRequirement.id.desc())

        if framework_id is not None:
            stmt = stmt.where(ComplianceRequirement.framework_id == framework_id)
        if status:
            stmt = stmt.where(ComplianceRequirement.status == status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        requirement_id: int,
        payload: dict[str, Any],
    ) -> ComplianceRequirement:
        obj = await cls.get_by_id(db, requirement_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, requirement_id: int) -> None:
        obj = await cls.get_by_id(db, requirement_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        framework_id = payload.get("framework_id")
        if framework_id is None:
            raise BadRequestException("framework_id is required for compliance requirements.")

        await cls._ensure_framework_exists(db, framework_id)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        requirement: ComplianceRequirement,
        payload: dict[str, Any],
    ) -> None:
        if "framework_id" in payload and payload["framework_id"] != requirement.framework_id:
            await cls._ensure_framework_exists(db, payload["framework_id"])


# ── Organization Compliance ───────────────────────────────────────────────────


class OrganizationComplianceService(BaseComplianceService):
    """Business logic for organization-level compliance tracking."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> OrganizationCompliance:
        await cls._validate_create(db, payload)
        obj = OrganizationCompliance(**payload)
        db.add(obj)
        await db.flush()
        await cls._create_status_history(
            db=db,
            organization_compliance_id=obj.id,
            location_compliance_id=None,
            old_status=None,
            new_status=obj.status,
            changed_by=payload.get("assigned_to"),
            change_reason="Initial compliance status created.",
        )
        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def get_by_id(cls, db: AsyncSession, compliance_id: int) -> OrganizationCompliance:
        stmt = (
            select(OrganizationCompliance)
            .where(OrganizationCompliance.id == compliance_id)
            .options(
                selectinload(OrganizationCompliance.evidence_items),
                selectinload(OrganizationCompliance.status_history),
            )
        )
        return await cls._get_one_or_404(db, stmt, f"Organization compliance {compliance_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        requirement_id: int | None = None,
        status: str | None = None,
        assigned_to: int | None = None,
        due_before: datetime | None = None,
        expiry_before: datetime | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[OrganizationCompliance]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(OrganizationCompliance).order_by(OrganizationCompliance.id.desc())

        if organization_id is not None:
            stmt = stmt.where(OrganizationCompliance.organization_id == organization_id)
        if requirement_id is not None:
            stmt = stmt.where(OrganizationCompliance.requirement_id == requirement_id)
        if status:
            stmt = stmt.where(OrganizationCompliance.status == status)
        if assigned_to is not None:
            stmt = stmt.where(OrganizationCompliance.assigned_to == assigned_to)
        if due_before is not None:
            stmt = stmt.where(OrganizationCompliance.due_date <= due_before.date())
        if expiry_before is not None:
            stmt = stmt.where(OrganizationCompliance.expiry_date <= expiry_before.date())

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        compliance_id: int,
        payload: dict[str, Any],
        *,
        changed_by: int | None = None,
        change_reason: str | None = None,
    ) -> OrganizationCompliance:
        obj = await cls.get_by_id(db, compliance_id)
        await cls._validate_update(db, obj, payload)

        old_status = obj.status

        for key, value in payload.items():
            setattr(obj, key, value)

        await db.flush()

        if "status" in payload and payload["status"] != old_status:
            await cls._create_status_history(
                db=db,
                organization_compliance_id=obj.id,
                location_compliance_id=None,
                old_status=old_status,
                new_status=obj.status,
                changed_by=changed_by or payload.get("assigned_to"),
                change_reason=change_reason or "Organization compliance status updated.",
            )

        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def delete(cls, db: AsyncSession, compliance_id: int) -> None:
        obj = await cls.get_by_id(db, compliance_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_evidence(
        cls,
        db: AsyncSession,
        compliance_id: int,
        *,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceEvidence]:
        await cls._ensure_org_compliance_exists(db, compliance_id)
        return await ComplianceEvidenceService.list(
            db,
            organization_compliance_id=compliance_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_status_history(
        cls,
        db: AsyncSession,
        compliance_id: int,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceStatusHistory]:
        await cls._ensure_org_compliance_exists(db, compliance_id)
        return await ComplianceStatusHistoryService.list(
            db,
            organization_compliance_id=compliance_id,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload.get("organization_id")
        requirement_id = payload.get("requirement_id")
        assigned_to = payload.get("assigned_to")

        if organization_id is None or requirement_id is None:
            raise BadRequestException("organization_id and requirement_id are required.")

        await cls._ensure_organization_exists(db, organization_id)
        await cls._ensure_requirement_exists(db, requirement_id)

        if assigned_to is not None:
            await cls._ensure_user_exists(db, assigned_to)

        await cls._validate_unique_org_requirement(db, organization_id, requirement_id)
        cls._validate_dates(payload)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        obj: OrganizationCompliance,
        payload: dict[str, Any],
    ) -> None:
        if "organization_id" in payload and payload["organization_id"] != obj.organization_id:
            raise BadRequestException("Changing organization_id is not allowed.")

        if "requirement_id" in payload and payload["requirement_id"] != obj.requirement_id:
            raise BadRequestException("Changing requirement_id is not allowed.")

        if "assigned_to" in payload and payload["assigned_to"] is not None:
            await cls._ensure_user_exists(db, payload["assigned_to"])

        cls._validate_dates(
            {
                "due_date": payload.get("due_date", obj.due_date),
                "expiry_date": payload.get("expiry_date", obj.expiry_date),
            }
        )

    @classmethod
    async def _validate_unique_org_requirement(
        cls,
        db: AsyncSession,
        organization_id: int,
        requirement_id: int,
    ) -> None:
        stmt = select(OrganizationCompliance).where(
            OrganizationCompliance.organization_id == organization_id,
            OrganizationCompliance.requirement_id == requirement_id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                f"Organization compliance already exists for organization {organization_id} "
                f"and requirement {requirement_id}."
            )

    @classmethod
    def _validate_dates(cls, payload: dict[str, Any]) -> None:
        due_date = payload.get("due_date")
        expiry_date = payload.get("expiry_date")

        if due_date and expiry_date and expiry_date < due_date:
            raise BadRequestException("expiry_date cannot be earlier than due_date.")

    @classmethod
    async def _create_status_history(
        cls,
        db: AsyncSession,
        *,
        organization_compliance_id: int | None,
        location_compliance_id: int | None,
        old_status: str | None,
        new_status: str,
        changed_by: int | None,
        change_reason: str | None,
    ) -> ComplianceStatusHistory:
        if changed_by is not None:
            await cls._ensure_user_exists(db, changed_by)

        history = ComplianceStatusHistory(
            organization_compliance_id=organization_compliance_id,
            location_compliance_id=location_compliance_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        db.add(history)
        await db.flush()
        return history


# ── Location Compliance ───────────────────────────────────────────────────────


class LocationComplianceService(BaseComplianceService):
    """Business logic for location-level compliance tracking."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> LocationCompliance:
        await cls._validate_create(db, payload)
        obj = LocationCompliance(**payload)
        db.add(obj)
        await db.flush()
        await cls._create_status_history(
            db=db,
            organization_compliance_id=None,
            location_compliance_id=obj.id,
            old_status=None,
            new_status=obj.status,
            changed_by=payload.get("assigned_to"),
            change_reason="Initial location compliance status created.",
        )
        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def get_by_id(cls, db: AsyncSession, compliance_id: int) -> LocationCompliance:
        stmt = (
            select(LocationCompliance)
            .where(LocationCompliance.id == compliance_id)
            .options(
                selectinload(LocationCompliance.evidence_items),
                selectinload(LocationCompliance.status_history),
            )
        )
        return await cls._get_one_or_404(db, stmt, f"Location compliance {compliance_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        location_id: int | None = None,
        requirement_id: int | None = None,
        status: str | None = None,
        assigned_to: int | None = None,
        due_before: datetime | None = None,
        expiry_before: datetime | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[LocationCompliance]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(LocationCompliance).order_by(LocationCompliance.id.desc())

        if organization_id is not None:
            stmt = stmt.where(LocationCompliance.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(LocationCompliance.location_id == location_id)
        if requirement_id is not None:
            stmt = stmt.where(LocationCompliance.requirement_id == requirement_id)
        if status:
            stmt = stmt.where(LocationCompliance.status == status)
        if assigned_to is not None:
            stmt = stmt.where(LocationCompliance.assigned_to == assigned_to)
        if due_before is not None:
            stmt = stmt.where(LocationCompliance.due_date <= due_before.date())
        if expiry_before is not None:
            stmt = stmt.where(LocationCompliance.expiry_date <= expiry_before.date())

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        compliance_id: int,
        payload: dict[str, Any],
        *,
        changed_by: int | None = None,
        change_reason: str | None = None,
    ) -> LocationCompliance:
        obj = await cls.get_by_id(db, compliance_id)
        await cls._validate_update(db, obj, payload)

        old_status = obj.status

        for key, value in payload.items():
            setattr(obj, key, value)

        await db.flush()

        if "status" in payload and payload["status"] != old_status:
            await cls._create_status_history(
                db=db,
                organization_compliance_id=None,
                location_compliance_id=obj.id,
                old_status=old_status,
                new_status=obj.status,
                changed_by=changed_by or payload.get("assigned_to"),
                change_reason=change_reason or "Location compliance status updated.",
            )

        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def delete(cls, db: AsyncSession, compliance_id: int) -> None:
        obj = await cls.get_by_id(db, compliance_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_evidence(
        cls,
        db: AsyncSession,
        compliance_id: int,
        *,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceEvidence]:
        await cls._ensure_location_compliance_exists(db, compliance_id)
        return await ComplianceEvidenceService.list(
            db,
            location_compliance_id=compliance_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_status_history(
        cls,
        db: AsyncSession,
        compliance_id: int,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceStatusHistory]:
        await cls._ensure_location_compliance_exists(db, compliance_id)
        return await ComplianceStatusHistoryService.list(
            db,
            location_compliance_id=compliance_id,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload.get("organization_id")
        location_id = payload.get("location_id")
        requirement_id = payload.get("requirement_id")
        assigned_to = payload.get("assigned_to")

        if organization_id is None or location_id is None or requirement_id is None:
            raise BadRequestException("organization_id, location_id, and requirement_id are required.")

        await cls._ensure_organization_exists(db, organization_id)
        await cls._ensure_location_belongs_to_org(db, location_id, organization_id)
        await cls._ensure_requirement_exists(db, requirement_id)

        if assigned_to is not None:
            await cls._ensure_user_exists(db, assigned_to)

        await cls._validate_unique_location_requirement(db, location_id, requirement_id)
        cls._validate_dates(payload)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        obj: LocationCompliance,
        payload: dict[str, Any],
    ) -> None:
        if "organization_id" in payload and payload["organization_id"] != obj.organization_id:
            raise BadRequestException("Changing organization_id is not allowed.")

        if "location_id" in payload and payload["location_id"] != obj.location_id:
            raise BadRequestException("Changing location_id is not allowed.")

        if "requirement_id" in payload and payload["requirement_id"] != obj.requirement_id:
            raise BadRequestException("Changing requirement_id is not allowed.")

        if "assigned_to" in payload and payload["assigned_to"] is not None:
            await cls._ensure_user_exists(db, payload["assigned_to"])

        cls._validate_dates(
            {
                "due_date": payload.get("due_date", obj.due_date),
                "expiry_date": payload.get("expiry_date", obj.expiry_date),
            }
        )

    @classmethod
    async def _validate_unique_location_requirement(
        cls,
        db: AsyncSession,
        location_id: int,
        requirement_id: int,
    ) -> None:
        stmt = select(LocationCompliance).where(
            LocationCompliance.location_id == location_id,
            LocationCompliance.requirement_id == requirement_id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                f"Location compliance already exists for location {location_id} "
                f"and requirement {requirement_id}."
            )

    @classmethod
    def _validate_dates(cls, payload: dict[str, Any]) -> None:
        due_date = payload.get("due_date")
        expiry_date = payload.get("expiry_date")

        if due_date and expiry_date and expiry_date < due_date:
            raise BadRequestException("expiry_date cannot be earlier than due_date.")

    @classmethod
    async def _create_status_history(
        cls,
        db: AsyncSession,
        *,
        organization_compliance_id: int | None,
        location_compliance_id: int | None,
        old_status: str | None,
        new_status: str,
        changed_by: int | None,
        change_reason: str | None,
    ) -> ComplianceStatusHistory:
        if changed_by is not None:
            await cls._ensure_user_exists(db, changed_by)

        history = ComplianceStatusHistory(
            organization_compliance_id=organization_compliance_id,
            location_compliance_id=location_compliance_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            change_reason=change_reason,
        )
        db.add(history)
        await db.flush()
        return history


# ── Compliance Evidence ───────────────────────────────────────────────────────


class ComplianceEvidenceService(BaseComplianceService):
    """Business logic for compliance evidence submissions."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ComplianceEvidence:
        await cls._validate_create(db, payload)

        if payload.get("submitted_at") is None:
            payload["submitted_at"] = datetime.utcnow()

        obj = ComplianceEvidence(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, evidence_id: int) -> ComplianceEvidence:
        stmt = (
            select(ComplianceEvidence)
            .where(ComplianceEvidence.id == evidence_id)
            .options(
                selectinload(ComplianceEvidence.reviews),
                selectinload(ComplianceEvidence.documents),
            )
        )
        return await cls._get_one_or_404(db, stmt, f"Compliance evidence {evidence_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_compliance_id: int | None = None,
        location_compliance_id: int | None = None,
        submitted_by: int | None = None,
        status: str | None = None,
        evidence_type: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceEvidence]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceEvidence).order_by(ComplianceEvidence.id.desc())

        if organization_compliance_id is not None:
            stmt = stmt.where(
                ComplianceEvidence.organization_compliance_id == organization_compliance_id
            )
        if location_compliance_id is not None:
            stmt = stmt.where(ComplianceEvidence.location_compliance_id == location_compliance_id)
        if submitted_by is not None:
            stmt = stmt.where(ComplianceEvidence.submitted_by == submitted_by)
        if status:
            stmt = stmt.where(ComplianceEvidence.status == status)
        if evidence_type:
            stmt = stmt.where(ComplianceEvidence.evidence_type == evidence_type)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        evidence_id: int,
        payload: dict[str, Any],
    ) -> ComplianceEvidence:
        obj = await cls.get_by_id(db, evidence_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, evidence_id: int) -> None:
        obj = await cls.get_by_id(db, evidence_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_reviews(
        cls,
        db: AsyncSession,
        evidence_id: int,
        *,
        review_status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceReview]:
        await cls._ensure_evidence_exists(db, evidence_id)
        return await ComplianceReviewService.list(
            db,
            evidence_id=evidence_id,
            review_status=review_status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_documents(
        cls,
        db: AsyncSession,
        evidence_id: int,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceDocument]:
        await cls._ensure_evidence_exists(db, evidence_id)
        return await ComplianceDocumentService.list(
            db,
            evidence_id=evidence_id,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        org_compliance_id = payload.get("organization_compliance_id")
        location_compliance_id = payload.get("location_compliance_id")
        document_id = payload.get("document_id")
        submitted_by = payload.get("submitted_by")

        if not org_compliance_id and not location_compliance_id:
            raise BadRequestException(
                "Evidence must be linked to organization_compliance_id or location_compliance_id."
            )

        if org_compliance_id and location_compliance_id:
            raise BadRequestException(
                "Evidence cannot be linked to both organization and location compliance at the same time."
            )

        if org_compliance_id:
            await cls._ensure_org_compliance_exists(db, org_compliance_id)

        if location_compliance_id:
            await cls._ensure_location_compliance_exists(db, location_compliance_id)

        if document_id is not None:
            await cls._ensure_document_exists(db, document_id)

        if submitted_by is not None:
            await cls._ensure_user_exists(db, submitted_by)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        evidence: ComplianceEvidence,
        payload: dict[str, Any],
    ) -> None:
        if "organization_compliance_id" in payload and payload["organization_compliance_id"] != evidence.organization_compliance_id:
            raise BadRequestException("Changing organization_compliance_id is not allowed.")

        if "location_compliance_id" in payload and payload["location_compliance_id"] != evidence.location_compliance_id:
            raise BadRequestException("Changing location_compliance_id is not allowed.")

        if "document_id" in payload and payload["document_id"] is not None:
            await cls._ensure_document_exists(db, payload["document_id"])

        if "submitted_by" in payload and payload["submitted_by"] is not None:
            await cls._ensure_user_exists(db, payload["submitted_by"])


# ── Compliance Reviews ────────────────────────────────────────────────────────


class ComplianceReviewService(BaseComplianceService):
    """Business logic for evidence reviews."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ComplianceReview:
        await cls._validate_create(db, payload)

        if payload.get("reviewed_at") is None and payload.get("review_status") != "pending":
            payload["reviewed_at"] = datetime.utcnow()

        obj = ComplianceReview(**payload)
        db.add(obj)
        await db.flush()

        evidence = await cls._ensure_evidence_exists(db, obj.evidence_id)
        evidence.status = cls._map_review_status_to_evidence_status(obj.review_status)

        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def get_by_id(cls, db: AsyncSession, review_id: int) -> ComplianceReview:
        stmt = select(ComplianceReview).where(ComplianceReview.id == review_id)
        return await cls._get_one_or_404(db, stmt, f"Compliance review {review_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        evidence_id: int | None = None,
        reviewer_id: int | None = None,
        review_status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceReview]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceReview).order_by(ComplianceReview.id.desc())

        if evidence_id is not None:
            stmt = stmt.where(ComplianceReview.evidence_id == evidence_id)
        if reviewer_id is not None:
            stmt = stmt.where(ComplianceReview.reviewer_id == reviewer_id)
        if review_status:
            stmt = stmt.where(ComplianceReview.review_status == review_status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        review_id: int,
        payload: dict[str, Any],
    ) -> ComplianceReview:
        obj = await cls.get_by_id(db, review_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        if "review_status" in payload and payload["review_status"] != "pending" and obj.reviewed_at is None:
            obj.reviewed_at = datetime.utcnow()

        await db.flush()

        if "review_status" in payload:
            evidence = await cls._ensure_evidence_exists(db, obj.evidence_id)
            evidence.status = cls._map_review_status_to_evidence_status(obj.review_status)

        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def delete(cls, db: AsyncSession, review_id: int) -> None:
        obj = await cls.get_by_id(db, review_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        evidence_id = payload.get("evidence_id")
        reviewer_id = payload.get("reviewer_id")

        if evidence_id is None or reviewer_id is None:
            raise BadRequestException("evidence_id and reviewer_id are required.")

        await cls._ensure_evidence_exists(db, evidence_id)
        await cls._ensure_user_exists(db, reviewer_id)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        review: ComplianceReview,
        payload: dict[str, Any],
    ) -> None:
        if "evidence_id" in payload and payload["evidence_id"] != review.evidence_id:
            raise BadRequestException("Changing evidence_id is not allowed.")

        if "reviewer_id" in payload and payload["reviewer_id"] != review.reviewer_id:
            raise BadRequestException("Changing reviewer_id is not allowed.")

    @classmethod
    def _map_review_status_to_evidence_status(cls, review_status: str) -> str:
        mapping = {
            "pending": "under_review",
            "approved": "approved",
            "rejected": "rejected",
            "needs_update": "under_review",
        }
        return mapping.get(review_status, "under_review")


# ── Compliance Documents ──────────────────────────────────────────────────────


class ComplianceDocumentService(BaseComplianceService):
    """Business logic for compliance documents."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ComplianceDocument:
        await cls._validate_create(db, payload)
        obj = ComplianceDocument(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, document_id: int) -> ComplianceDocument:
        stmt = (
            select(ComplianceDocument)
            .where(ComplianceDocument.id == document_id)
            .options(selectinload(ComplianceDocument.versions))
        )
        return await cls._get_one_or_404(db, stmt, f"Compliance document {document_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        evidence_id: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceDocument]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceDocument).order_by(ComplianceDocument.id.desc())

        if evidence_id is not None:
            stmt = stmt.where(ComplianceDocument.evidence_id == evidence_id)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        document_id: int,
        payload: dict[str, Any],
    ) -> ComplianceDocument:
        obj = await cls.get_by_id(db, document_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, document_id: int) -> None:
        obj = await cls.get_by_id(db, document_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_versions(
        cls,
        db: AsyncSession,
        document_id: int,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceDocumentVersion]:
        await cls._ensure_document_exists(db, document_id)
        return await ComplianceDocumentVersionService.list(
            db,
            document_id=document_id,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        evidence_id = payload.get("evidence_id")
        if evidence_id is not None:
            await cls._ensure_evidence_exists(db, evidence_id)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        document: ComplianceDocument,
        payload: dict[str, Any],
    ) -> None:
        if "evidence_id" in payload and payload["evidence_id"] != document.evidence_id:
            await cls._ensure_evidence_exists(db, payload["evidence_id"])


# ── Compliance Document Versions ──────────────────────────────────────────────


class ComplianceDocumentVersionService(BaseComplianceService):
    """Business logic for document version history."""

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        payload: dict[str, Any],
    ) -> ComplianceDocumentVersion:
        await cls._validate_create(db, payload)
        obj = ComplianceDocumentVersion(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        version_id: int,
    ) -> ComplianceDocumentVersion:
        stmt = select(ComplianceDocumentVersion).where(ComplianceDocumentVersion.id == version_id)
        return await cls._get_one_or_404(
            db,
            stmt,
            f"Compliance document version {version_id} not found.",
        )

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        document_id: int | None = None,
        changed_by: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceDocumentVersion]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceDocumentVersion).order_by(
            ComplianceDocumentVersion.id.desc()
        )

        if document_id is not None:
            stmt = stmt.where(ComplianceDocumentVersion.document_id == document_id)
        if changed_by is not None:
            stmt = stmt.where(ComplianceDocumentVersion.changed_by == changed_by)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def delete(cls, db: AsyncSession, version_id: int) -> None:
        obj = await cls.get_by_id(db, version_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        document_id = payload.get("document_id")
        changed_by = payload.get("changed_by")
        version_number = payload.get("version_number")

        if document_id is None or version_number is None:
            raise BadRequestException("document_id and version_number are required.")

        await cls._ensure_document_exists(db, document_id)

        if changed_by is not None:
            await cls._ensure_user_exists(db, changed_by)

        await cls._validate_unique_version_number(db, document_id, version_number)

    @classmethod
    async def _validate_unique_version_number(
        cls,
        db: AsyncSession,
        document_id: int,
        version_number: int,
    ) -> None:
        stmt = select(ComplianceDocumentVersion).where(
            ComplianceDocumentVersion.document_id == document_id,
            ComplianceDocumentVersion.version_number == version_number,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                f"Document version {version_number} already exists for document {document_id}."
            )


# ── Compliance Status History ─────────────────────────────────────────────────


class ComplianceStatusHistoryService(BaseComplianceService):
    """Read-focused service for compliance status history."""

    @classmethod
    async def get_by_id(cls, db: AsyncSession, history_id: int) -> ComplianceStatusHistory:
        stmt = select(ComplianceStatusHistory).where(ComplianceStatusHistory.id == history_id)
        return await cls._get_one_or_404(
            db,
            stmt,
            f"Compliance status history {history_id} not found.",
        )

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_compliance_id: int | None = None,
        location_compliance_id: int | None = None,
        changed_by: int | None = None,
        new_status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceStatusHistory]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceStatusHistory).order_by(ComplianceStatusHistory.id.desc())

        if organization_compliance_id is not None:
            stmt = stmt.where(
                ComplianceStatusHistory.organization_compliance_id == organization_compliance_id
            )
        if location_compliance_id is not None:
            stmt = stmt.where(
                ComplianceStatusHistory.location_compliance_id == location_compliance_id
            )
        if changed_by is not None:
            stmt = stmt.where(ComplianceStatusHistory.changed_by == changed_by)
        if new_status:
            stmt = stmt.where(ComplianceStatusHistory.new_status == new_status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())


# ── Compliance Alerts ─────────────────────────────────────────────────────────


class ComplianceAlertService(BaseComplianceService):
    """Business logic for compliance alerts."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ComplianceAlert:
        await cls._validate_create(db, payload)

        if payload.get("is_resolved") is None:
            payload["is_resolved"] = False

        if payload.get("alert_date") is None:
            payload["alert_date"] = datetime.utcnow()

        obj = ComplianceAlert(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, alert_id: int) -> ComplianceAlert:
        stmt = select(ComplianceAlert).where(ComplianceAlert.id == alert_id)
        return await cls._get_one_or_404(db, stmt, f"Compliance alert {alert_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        location_id: int | None = None,
        requirement_id: int | None = None,
        document_id: int | None = None,
        alert_type: str | None = None,
        severity: str | None = None,
        is_resolved: bool | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceAlert]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceAlert).order_by(ComplianceAlert.id.desc())

        if organization_id is not None:
            stmt = stmt.where(ComplianceAlert.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(ComplianceAlert.location_id == location_id)
        if requirement_id is not None:
            stmt = stmt.where(ComplianceAlert.requirement_id == requirement_id)
        if document_id is not None:
            stmt = stmt.where(ComplianceAlert.document_id == document_id)
        if alert_type:
            stmt = stmt.where(ComplianceAlert.alert_type == alert_type)
        if severity:
            stmt = stmt.where(ComplianceAlert.severity == severity)
        if is_resolved is not None:
            stmt = stmt.where(ComplianceAlert.is_resolved == is_resolved)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        alert_id: int,
        payload: dict[str, Any],
    ) -> ComplianceAlert:
        obj = await cls.get_by_id(db, alert_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        if payload.get("is_resolved") is True and obj.resolved_at is None:
            obj.resolved_at = datetime.utcnow()

        if payload.get("is_resolved") is False:
            obj.resolved_at = None
            obj.resolved_by = None

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def resolve(
        cls,
        db: AsyncSession,
        alert_id: int,
        *,
        resolved_by: int,
    ) -> ComplianceAlert:
        obj = await cls.get_by_id(db, alert_id)
        await cls._ensure_user_exists(db, resolved_by)

        obj.is_resolved = True
        obj.resolved_by = resolved_by
        obj.resolved_at = datetime.utcnow()

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, alert_id: int) -> None:
        obj = await cls.get_by_id(db, alert_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload.get("organization_id")
        location_id = payload.get("location_id")
        requirement_id = payload.get("requirement_id")
        document_id = payload.get("document_id")
        resolved_by = payload.get("resolved_by")

        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)

        if location_id is not None:
            await cls._ensure_location_exists(db, location_id)

        if requirement_id is not None:
            await cls._ensure_requirement_exists(db, requirement_id)

        if document_id is not None:
            await cls._ensure_document_exists(db, document_id)

        if resolved_by is not None:
            await cls._ensure_user_exists(db, resolved_by)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        alert: ComplianceAlert,
        payload: dict[str, Any],
    ) -> None:
        if "organization_id" in payload and payload["organization_id"] is not None:
            await cls._ensure_organization_exists(db, payload["organization_id"])

        if "location_id" in payload and payload["location_id"] is not None:
            await cls._ensure_location_exists(db, payload["location_id"])

        if "requirement_id" in payload and payload["requirement_id"] is not None:
            await cls._ensure_requirement_exists(db, payload["requirement_id"])

        if "document_id" in payload and payload["document_id"] is not None:
            await cls._ensure_document_exists(db, payload["document_id"])

        if "resolved_by" in payload and payload["resolved_by"] is not None:
            await cls._ensure_user_exists(db, payload["resolved_by"])


# ── Compliance Scores ─────────────────────────────────────────────────────────


class ComplianceScoreService(BaseComplianceService):
    """Business logic for compliance summary scores."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> ComplianceScore:
        await cls._validate_create(db, payload)
        obj = ComplianceScore(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, score_id: int) -> ComplianceScore:
        stmt = select(ComplianceScore).where(ComplianceScore.id == score_id)
        return await cls._get_one_or_404(db, stmt, f"Compliance score {score_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        location_id: int | None = None,
        framework_id: int | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ComplianceScore]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(ComplianceScore).order_by(ComplianceScore.id.desc())

        if organization_id is not None:
            stmt = stmt.where(ComplianceScore.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(ComplianceScore.location_id == location_id)
        if framework_id is not None:
            stmt = stmt.where(ComplianceScore.framework_id == framework_id)
        if period_start is not None:
            stmt = stmt.where(ComplianceScore.period_start >= period_start.date())
        if period_end is not None:
            stmt = stmt.where(ComplianceScore.period_end <= period_end.date())

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        score_id: int,
        payload: dict[str, Any],
    ) -> ComplianceScore:
        obj = await cls.get_by_id(db, score_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, score_id: int) -> None:
        obj = await cls.get_by_id(db, score_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload.get("organization_id")
        location_id = payload.get("location_id")
        framework_id = payload.get("framework_id")

        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)

        if location_id is not None:
            await cls._ensure_location_exists(db, location_id)

        if organization_id is not None and location_id is not None:
            await cls._ensure_location_belongs_to_org(db, location_id, organization_id)

        if framework_id is not None:
            await cls._ensure_framework_exists(db, framework_id)

        cls._validate_period_dates(payload)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        score: ComplianceScore,
        payload: dict[str, Any],
    ) -> None:
        organization_id = payload.get("organization_id", score.organization_id)
        location_id = payload.get("location_id", score.location_id)

        if organization_id is not None:
            await cls._ensure_organization_exists(db, organization_id)

        if location_id is not None:
            await cls._ensure_location_exists(db, location_id)

        if organization_id is not None and location_id is not None:
            await cls._ensure_location_belongs_to_org(db, location_id, organization_id)

        if "framework_id" in payload and payload["framework_id"] is not None:
            await cls._ensure_framework_exists(db, payload["framework_id"])

        cls._validate_period_dates(
            {
                "period_start": payload.get("period_start", score.period_start),
                "period_end": payload.get("period_end", score.period_end),
            }
        )

    @classmethod
    def _validate_period_dates(cls, payload: dict[str, Any]) -> None:
        period_start = payload.get("period_start")
        period_end = payload.get("period_end")

        if period_start and period_end and period_end < period_start:
            raise BadRequestException("period_end cannot be earlier than period_start.")