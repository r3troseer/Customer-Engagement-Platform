"""
FR4 — ESG & SDG Management
Service layer for the simplified ESG model design.

Tables supported:
- esg_objectives
- esg_metric_values
- esg_activities
- esg_reports
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import User
from app.models.esg import EsgActivity, EsgMetricValue, EsgObjective, EsgReport
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


DEFAULT_OFFSET = 0
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class BaseEsgService:
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
        return await BaseEsgService._get_one_or_404(db, stmt, f"User {user_id} not found.")

    @staticmethod
    async def _ensure_org_exists(db: AsyncSession, organization_id: int) -> Organization:
        stmt = select(Organization).where(Organization.id == organization_id)
        return await BaseEsgService._get_one_or_404(db, stmt, f"Organization {organization_id} not found.")

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
        return await BaseEsgService._get_one_or_404(
            db,
            stmt,
            f"Location {location_id} not found for organization {organization_id}.",
        )

    @staticmethod
    async def _ensure_objective_exists(db: AsyncSession, objective_id: int) -> EsgObjective:
        stmt = select(EsgObjective).where(EsgObjective.id == objective_id)
        return await BaseEsgService._get_one_or_404(db, stmt, f"ESG objective {objective_id} not found.")

    @staticmethod
    def _validate_date_range(start_date, end_date, start_label: str = "start_date", end_label: str = "end_date") -> None:
        if start_date and end_date and end_date < start_date:
            raise BadRequestException(f"{end_label} cannot be earlier than {start_label}.")

    @staticmethod
    def _validate_category(category: str) -> None:
        allowed = {"environmental", "social", "governance"}
        if category not in allowed:
            raise BadRequestException(
                "category must be one of: environmental, social, governance."
            )

    @staticmethod
    def _validate_sdg_goal_numbers(sdg_goal_numbers: list[int] | None) -> None:
        if sdg_goal_numbers is None:
            return
        if not isinstance(sdg_goal_numbers, list):
            raise BadRequestException("sdg_goal_numbers must be a list of integers.")
        for number in sdg_goal_numbers:
            if not isinstance(number, int):
                raise BadRequestException("sdg_goal_numbers must contain only integers.")
            if number < 1 or number > 17:
                raise BadRequestException("Each SDG goal number must be between 1 and 17.")


class EsgObjectiveService(BaseEsgService):
    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> EsgObjective:
        await cls._ensure_org_exists(db, payload["organization_id"])

        if payload.get("created_by") is not None:
            await cls._ensure_user_exists(db, payload["created_by"])

        cls._validate_category(payload["category"])
        cls._validate_sdg_goal_numbers(payload.get("sdg_goal_numbers"))
        cls._validate_date_range(payload.get("start_date"), payload.get("end_date"))

        obj = EsgObjective(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, objective_id: int) -> EsgObjective:
        stmt = (
            select(EsgObjective)
            .where(EsgObjective.id == objective_id)
            .options(
                selectinload(EsgObjective.metric_values),
                selectinload(EsgObjective.activities),
            )
        )
        return await cls._get_one_or_404(db, stmt, f"ESG objective {objective_id} not found.")

    @classmethod
    async def get_detail(cls, db: AsyncSession, objective_id: int) -> EsgObjective:
        return await cls.get_by_id(db, objective_id)

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        category: str | None = None,
        status: str | None = None,
        created_by: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[EsgObjective]:
        offset, limit = cls._normalize_pagination(offset, limit)
        stmt = select(EsgObjective).order_by(EsgObjective.id.desc())

        if organization_id is not None:
            stmt = stmt.where(EsgObjective.organization_id == organization_id)
        if category:
            stmt = stmt.where(EsgObjective.category == category)
        if status:
            stmt = stmt.where(EsgObjective.status == status)
        if created_by is not None:
            stmt = stmt.where(EsgObjective.created_by == created_by)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, objective_id: int, payload: dict[str, Any]) -> EsgObjective:
        obj = await cls.get_by_id(db, objective_id)

        if "organization_id" in payload and payload["organization_id"] != obj.organization_id:
            raise BadRequestException("Changing objective organization_id is not allowed.")

        if "created_by" in payload and payload["created_by"] is not None:
            raise BadRequestException("Changing created_by is not allowed.")

        if "category" in payload and payload["category"] is not None:
            cls._validate_category(payload["category"])

        if "sdg_goal_numbers" in payload:
            cls._validate_sdg_goal_numbers(payload["sdg_goal_numbers"])

        cls._validate_date_range(
            payload.get("start_date", obj.start_date),
            payload.get("end_date", obj.end_date),
        )

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, objective_id: int) -> None:
        obj = await cls.get_by_id(db, objective_id)
        await db.delete(obj)
        await db.commit()


class EsgMetricValueService(BaseEsgService):
    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> EsgMetricValue:
        await cls._ensure_org_exists(db, payload["organization_id"])
        cls._validate_category(payload["category"])

        if payload.get("location_id") is not None:
            await cls._ensure_location_belongs_to_org(
                db,
                payload["location_id"],
                payload["organization_id"],
            )

        if payload.get("esg_objective_id") is not None:
            objective = await cls._ensure_objective_exists(db, payload["esg_objective_id"])
            if objective.organization_id != payload["organization_id"]:
                raise BadRequestException(
                    "Metric value esg_objective_id must belong to the same organization."
                )
            if objective.category != payload["category"]:
                raise BadRequestException(
                    "Metric value category must match the linked ESG objective category."
                )

        if payload.get("recorded_by") is not None:
            await cls._ensure_user_exists(db, payload["recorded_by"])

        await cls._validate_unique_metric_value(
            db,
            organization_id=payload["organization_id"],
            location_id=payload.get("location_id"),
            metric_code=payload["metric_code"],
            value_date=payload["value_date"],
        )

        obj = EsgMetricValue(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, value_id: int) -> EsgMetricValue:
        stmt = (
            select(EsgMetricValue)
            .where(EsgMetricValue.id == value_id)
            .options(selectinload(EsgMetricValue.objective))
        )
        return await cls._get_one_or_404(db, stmt, f"ESG metric value {value_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        location_id: int | None = None,
        esg_objective_id: int | None = None,
        metric_code: str | None = None,
        category: str | None = None,
        source_type: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[EsgMetricValue]:
        offset, limit = cls._normalize_pagination(offset, limit)
        stmt = select(EsgMetricValue).order_by(EsgMetricValue.value_date.desc(), EsgMetricValue.id.desc())

        if organization_id is not None:
            stmt = stmt.where(EsgMetricValue.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(EsgMetricValue.location_id == location_id)
        if esg_objective_id is not None:
            stmt = stmt.where(EsgMetricValue.esg_objective_id == esg_objective_id)
        if metric_code:
            stmt = stmt.where(EsgMetricValue.metric_code == metric_code)
        if category:
            stmt = stmt.where(EsgMetricValue.category == category)
        if source_type:
            stmt = stmt.where(EsgMetricValue.source_type == source_type)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, value_id: int, payload: dict[str, Any]) -> EsgMetricValue:
        obj = await cls.get_by_id(db, value_id)

        if "organization_id" in payload and payload["organization_id"] != obj.organization_id:
            raise BadRequestException("Changing organization_id is not allowed.")

        if "recorded_by" in payload and payload["recorded_by"] is not None:
            await cls._ensure_user_exists(db, payload["recorded_by"])

        if "location_id" in payload and payload["location_id"] is not None:
            await cls._ensure_location_belongs_to_org(db, payload["location_id"], obj.organization_id)

        final_category = payload.get("category", obj.category)
        cls._validate_category(final_category)

        final_objective_id = payload.get("esg_objective_id", obj.esg_objective_id)
        if final_objective_id is not None:
            objective = await cls._ensure_objective_exists(db, final_objective_id)
            if objective.organization_id != obj.organization_id:
                raise BadRequestException(
                    "Metric value esg_objective_id must belong to the same organization."
                )
            if objective.category != final_category:
                raise BadRequestException(
                    "Metric value category must match the linked ESG objective category."
                )

        final_location_id = payload.get("location_id", obj.location_id)
        final_metric_code = payload.get("metric_code", obj.metric_code)
        final_value_date = payload.get("value_date", obj.value_date)

        await cls._validate_unique_metric_value(
            db,
            organization_id=obj.organization_id,
            location_id=final_location_id,
            metric_code=final_metric_code,
            value_date=final_value_date,
            exclude_id=value_id,
        )

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, value_id: int) -> None:
        obj = await cls.get_by_id(db, value_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_unique_metric_value(
        cls,
        db: AsyncSession,
        *,
        organization_id: int,
        location_id: int | None,
        metric_code: str,
        value_date,
        exclude_id: int | None = None,
    ) -> None:
        stmt = select(EsgMetricValue).where(
            EsgMetricValue.organization_id == organization_id,
            EsgMetricValue.location_id == location_id,
            EsgMetricValue.metric_code == metric_code,
            EsgMetricValue.value_date == value_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(EsgMetricValue.id != exclude_id)

        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                "A metric value already exists for this organization/location/metric_code/value_date combination."
            )


class EsgActivityService(BaseEsgService):
    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> EsgActivity:
        await cls._ensure_org_exists(db, payload["organization_id"])

        if payload.get("location_id") is not None:
            await cls._ensure_location_belongs_to_org(db, payload["location_id"], payload["organization_id"])

        if payload.get("esg_objective_id") is not None:
            objective = await cls._ensure_objective_exists(db, payload["esg_objective_id"])
            if objective.organization_id != payload["organization_id"]:
                raise BadRequestException("Activity objective must belong to the same organization.")

        if payload.get("created_by") is not None:
            await cls._ensure_user_exists(db, payload["created_by"])

        cls._validate_date_range(payload.get("start_date"), payload.get("end_date"))

        obj = EsgActivity(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, activity_id: int) -> EsgActivity:
        stmt = (
            select(EsgActivity)
            .where(EsgActivity.id == activity_id)
            .options(selectinload(EsgActivity.objective))
        )
        return await cls._get_one_or_404(db, stmt, f"ESG activity {activity_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        location_id: int | None = None,
        esg_objective_id: int | None = None,
        activity_type: str | None = None,
        status: str | None = None,
        created_by: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[EsgActivity]:
        offset, limit = cls._normalize_pagination(offset, limit)
        stmt = select(EsgActivity).order_by(EsgActivity.id.desc())

        if organization_id is not None:
            stmt = stmt.where(EsgActivity.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(EsgActivity.location_id == location_id)
        if esg_objective_id is not None:
            stmt = stmt.where(EsgActivity.esg_objective_id == esg_objective_id)
        if activity_type:
            stmt = stmt.where(EsgActivity.activity_type == activity_type)
        if status:
            stmt = stmt.where(EsgActivity.status == status)
        if created_by is not None:
            stmt = stmt.where(EsgActivity.created_by == created_by)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, activity_id: int, payload: dict[str, Any]) -> EsgActivity:
        obj = await cls.get_by_id(db, activity_id)

        if "organization_id" in payload and payload["organization_id"] != obj.organization_id:
            raise BadRequestException("Changing activity organization_id is not allowed.")

        if "created_by" in payload and payload["created_by"] is not None:
            raise BadRequestException("Changing created_by is not allowed.")

        if "location_id" in payload and payload["location_id"] is not None:
            await cls._ensure_location_belongs_to_org(db, payload["location_id"], obj.organization_id)

        if "esg_objective_id" in payload and payload["esg_objective_id"] is not None:
            objective = await cls._ensure_objective_exists(db, payload["esg_objective_id"])
            if objective.organization_id != obj.organization_id:
                raise BadRequestException("Activity objective must belong to the same organization.")

        cls._validate_date_range(
            payload.get("start_date", obj.start_date),
            payload.get("end_date", obj.end_date),
        )

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, activity_id: int) -> None:
        obj = await cls.get_by_id(db, activity_id)
        await db.delete(obj)
        await db.commit()


class EsgReportService(BaseEsgService):
    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> EsgReport:
        await cls._ensure_org_exists(db, payload["organization_id"])

        if payload.get("location_id") is not None:
            await cls._ensure_location_belongs_to_org(db, payload["location_id"], payload["organization_id"])

        if payload.get("generated_by") is not None:
            await cls._ensure_user_exists(db, payload["generated_by"])

        cls._validate_date_range(
            payload.get("period_start"),
            payload.get("period_end"),
            start_label="period_start",
            end_label="period_end",
        )

        obj = EsgReport(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, report_id: int) -> EsgReport:
        stmt = select(EsgReport).where(EsgReport.id == report_id)
        return await cls._get_one_or_404(db, stmt, f"ESG report {report_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        location_id: int | None = None,
        report_type: str | None = None,
        status: str | None = None,
        generated_by: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[EsgReport]:
        offset, limit = cls._normalize_pagination(offset, limit)
        stmt = select(EsgReport).order_by(EsgReport.id.desc())

        if organization_id is not None:
            stmt = stmt.where(EsgReport.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(EsgReport.location_id == location_id)
        if report_type:
            stmt = stmt.where(EsgReport.report_type == report_type)
        if status:
            stmt = stmt.where(EsgReport.status == status)
        if generated_by is not None:
            stmt = stmt.where(EsgReport.generated_by == generated_by)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, report_id: int, payload: dict[str, Any]) -> EsgReport:
        obj = await cls.get_by_id(db, report_id)

        if "organization_id" in payload and payload["organization_id"] != obj.organization_id:
            raise BadRequestException("Changing report organization_id is not allowed.")

        if "location_id" in payload and payload["location_id"] is not None:
            await cls._ensure_location_belongs_to_org(db, payload["location_id"], obj.organization_id)

        if "generated_by" in payload and payload["generated_by"] is not None:
            await cls._ensure_user_exists(db, payload["generated_by"])

        cls._validate_date_range(
            payload.get("period_start", obj.period_start),
            payload.get("period_end", obj.period_end),
            start_label="period_start",
            end_label="period_end",
        )

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, report_id: int) -> None:
        obj = await cls.get_by_id(db, report_id)
        await db.delete(obj)
        await db.commit()