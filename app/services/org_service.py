"""
FR2 — Organization & Restaurant Structure
Service layer for organizations, restaurant locations, location settings,
departments, employees, and employee location assignments.

Notes:
- Contains business logic only, no HTTP/router concerns.
- Uses async SQLAlchemy 2.x patterns.
- Validates foreign keys and uniqueness constraints before writes.
- Supports filtered list queries and detail/nested reads.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import User
from app.models.org import (
    Department,
    Employee,
    EmployeeLocationAssignment,
    LocationSetting,
    Organization,
    RestaurantLocation,
)

try:
    from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
except Exception:
    # Fallbacks in case your project uses different exception wiring.
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


class BaseOrgService:
    """Shared DB helpers for FR2 services."""

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
    async def _flush_refresh(db: AsyncSession, obj: Any) -> Any:
        await db.flush()
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
        return await BaseOrgService._get_one_or_404(db, stmt, f"User {user_id} not found.")

    @staticmethod
    async def _ensure_organization_exists(db: AsyncSession, organization_id: int) -> Organization:
        stmt = select(Organization).where(Organization.id == organization_id)
        return await BaseOrgService._get_one_or_404(
            db,
            stmt,
            f"Organization {organization_id} not found.",
        )

    @staticmethod
    async def _ensure_location_exists(db: AsyncSession, location_id: int) -> RestaurantLocation:
        stmt = select(RestaurantLocation).where(RestaurantLocation.id == location_id)
        return await BaseOrgService._get_one_or_404(
            db,
            stmt,
            f"Restaurant location {location_id} not found.",
        )

    @staticmethod
    async def _ensure_department_exists(db: AsyncSession, department_id: int) -> Department:
        stmt = select(Department).where(Department.id == department_id)
        return await BaseOrgService._get_one_or_404(
            db,
            stmt,
            f"Department {department_id} not found.",
        )

    @staticmethod
    async def _ensure_employee_exists(db: AsyncSession, employee_id: int) -> Employee:
        stmt = select(Employee).where(Employee.id == employee_id)
        return await BaseOrgService._get_one_or_404(
            db,
            stmt,
            f"Employee {employee_id} not found.",
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
        return await BaseOrgService._get_one_or_404(
            db,
            stmt,
            f"Location {location_id} not found for organization {organization_id}.",
        )

    @staticmethod
    async def _ensure_department_belongs_to_org(
        db: AsyncSession,
        department_id: int,
        organization_id: int,
    ) -> Department:
        stmt = select(Department).where(
            Department.id == department_id,
            Department.organization_id == organization_id,
        )
        return await BaseOrgService._get_one_or_404(
            db,
            stmt,
            f"Department {department_id} not found for organization {organization_id}.",
        )

    @staticmethod
    async def _ensure_employee_belongs_to_org(
        db: AsyncSession,
        employee_id: int,
        organization_id: int,
    ) -> Employee:
        stmt = select(Employee).where(
            Employee.id == employee_id,
            Employee.organization_id == organization_id,
        )
        return await BaseOrgService._get_one_or_404(
            db,
            stmt,
            f"Employee {employee_id} not found for organization {organization_id}.",
        )


# ── Organization Service ──────────────────────────────────────────────────────


class OrganizationService(BaseOrgService):
    """Business logic for organizations."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> Organization:
        await cls._validate_create(db, payload)
        obj = Organization(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, organization_id: int) -> Organization:
        stmt = (
            select(Organization)
            .where(Organization.id == organization_id)
            .options(
                selectinload(Organization.locations),
                selectinload(Organization.departments),
                selectinload(Organization.employees),
            )
        )
        return await cls._get_one_or_404(db, stmt, f"Organization {organization_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Organization]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(Organization).order_by(Organization.id.desc())
        if status:
            stmt = stmt.where(Organization.status == status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, organization_id: int, payload: dict[str, Any]) -> Organization:
        obj = await cls.get_by_id(db, organization_id)
        await cls._validate_update(db, organization_id, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, organization_id: int) -> None:
        obj = await cls.get_by_id(db, organization_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_detail(cls, db: AsyncSession, organization_id: int) -> Organization:
        return await cls.get_by_id(db, organization_id)

    @classmethod
    async def get_locations(
        cls,
        db: AsyncSession,
        organization_id: int,
        *,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[RestaurantLocation]:
        await cls._ensure_organization_exists(db, organization_id)
        return await RestaurantLocationService.list(
            db,
            organization_id=organization_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_departments(
        cls,
        db: AsyncSession,
        organization_id: int,
        *,
        location_id: int | None = None,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Department]:
        await cls._ensure_organization_exists(db, organization_id)
        return await DepartmentService.list(
            db,
            organization_id=organization_id,
            location_id=location_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_employees(
        cls,
        db: AsyncSession,
        organization_id: int,
        *,
        department_id: int | None = None,
        primary_location_id: int | None = None,
        employment_status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Employee]:
        await cls._ensure_organization_exists(db, organization_id)
        return await EmployeeService.list(
            db,
            organization_id=organization_id,
            department_id=department_id,
            primary_location_id=primary_location_id,
            employment_status=employment_status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        await cls._validate_unique_name(db, payload["name"])

        registration_number = payload.get("registration_number")
        if registration_number:
            await cls._validate_unique_registration_number(db, registration_number)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        organization_id: int,
        payload: dict[str, Any],
    ) -> None:
        if "name" in payload and payload["name"]:
            await cls._validate_unique_name(db, payload["name"], exclude_id=organization_id)

        if "registration_number" in payload and payload["registration_number"]:
            await cls._validate_unique_registration_number(
                db,
                payload["registration_number"],
                exclude_id=organization_id,
            )

    @classmethod
    async def _validate_unique_name(
        cls,
        db: AsyncSession,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        stmt = select(Organization).where(Organization.name == name)
        if exclude_id is not None:
            stmt = stmt.where(Organization.id != exclude_id)

        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(f"Organization name '{name}' already exists.")

    @classmethod
    async def _validate_unique_registration_number(
        cls,
        db: AsyncSession,
        registration_number: str,
        *,
        exclude_id: int | None = None,
    ) -> None:
        stmt = select(Organization).where(Organization.registration_number == registration_number)
        if exclude_id is not None:
            stmt = stmt.where(Organization.id != exclude_id)

        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                f"Registration number '{registration_number}' already exists."
            )


# ── Restaurant Location Service ───────────────────────────────────────────────


class RestaurantLocationService(BaseOrgService):
    """Business logic for restaurant locations."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> RestaurantLocation:
        await cls._validate_create(db, payload)
        obj = RestaurantLocation(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, location_id: int) -> RestaurantLocation:
        stmt = (
            select(RestaurantLocation)
            .where(RestaurantLocation.id == location_id)
            .options(
                selectinload(RestaurantLocation.settings),
                selectinload(RestaurantLocation.departments),
                selectinload(RestaurantLocation.employee_assignments),
                selectinload(RestaurantLocation.primary_employees),
            )
        )
        return await cls._get_one_or_404(db, stmt, f"Restaurant location {location_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[RestaurantLocation]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(RestaurantLocation).order_by(RestaurantLocation.id.desc())

        if organization_id is not None:
            stmt = stmt.where(RestaurantLocation.organization_id == organization_id)
        if status:
            stmt = stmt.where(RestaurantLocation.status == status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, location_id: int, payload: dict[str, Any]) -> RestaurantLocation:
        obj = await cls.get_by_id(db, location_id)
        await cls._validate_update(db, location_id, payload, current_org_id=obj.organization_id)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, location_id: int) -> None:
        obj = await cls.get_by_id(db, location_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_detail(cls, db: AsyncSession, location_id: int) -> RestaurantLocation:
        return await cls.get_by_id(db, location_id)

    @classmethod
    async def get_settings(cls, db: AsyncSession, location_id: int) -> LocationSetting | None:
        await cls._ensure_location_exists(db, location_id)
        return await LocationSettingService.get_by_location_id(db, location_id)

    @classmethod
    async def get_departments(
        cls,
        db: AsyncSession,
        location_id: int,
        *,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Department]:
        await cls._ensure_location_exists(db, location_id)
        return await DepartmentService.list(
            db,
            location_id=location_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_assignments(
        cls,
        db: AsyncSession,
        location_id: int,
        *,
        employee_id: int | None = None,
        status: str | None = None,
        is_primary: bool | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[EmployeeLocationAssignment]:
        await cls._ensure_location_exists(db, location_id)
        return await EmployeeLocationAssignmentService.list(
            db,
            employee_id=employee_id,
            location_id=location_id,
            status=status,
            is_primary=is_primary,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def get_employees(
        cls,
        db: AsyncSession,
        location_id: int,
        *,
        employment_status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Employee]:
        await cls._ensure_location_exists(db, location_id)
        return await EmployeeService.list(
            db,
            primary_location_id=location_id,
            employment_status=employment_status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload["organization_id"]
        await cls._ensure_organization_exists(db, organization_id)
        await cls._validate_unique_location_code(
            db,
            organization_id=organization_id,
            location_code=payload["location_code"],
        )

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        location_id: int,
        payload: dict[str, Any],
        *,
        current_org_id: int,
    ) -> None:
        if "organization_id" in payload and payload["organization_id"] != current_org_id:
            raise BadRequestException("Changing location organization_id is not allowed.")

        if "location_code" in payload and payload["location_code"]:
            await cls._validate_unique_location_code(
                db,
                organization_id=current_org_id,
                location_code=payload["location_code"],
                exclude_id=location_id,
            )

    @classmethod
    async def _validate_unique_location_code(
        cls,
        db: AsyncSession,
        *,
        organization_id: int,
        location_code: str,
        exclude_id: int | None = None,
    ) -> None:
        stmt = select(RestaurantLocation).where(
            RestaurantLocation.organization_id == organization_id,
            RestaurantLocation.location_code == location_code,
        )
        if exclude_id is not None:
            stmt = stmt.where(RestaurantLocation.id != exclude_id)

        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                f"Location code '{location_code}' already exists for organization {organization_id}."
            )


# ── Location Setting Service ──────────────────────────────────────────────────


class LocationSettingService(BaseOrgService):
    """Business logic for location settings."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> LocationSetting:
        await cls._validate_create(db, payload)
        obj = LocationSetting(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, setting_id: int) -> LocationSetting:
        stmt = select(LocationSetting).where(LocationSetting.id == setting_id)
        return await cls._get_one_or_404(db, stmt, f"Location setting {setting_id} not found.")

    @classmethod
    async def get_by_location_id(cls, db: AsyncSession, location_id: int) -> LocationSetting | None:
        stmt = select(LocationSetting).where(LocationSetting.location_id == location_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        location_id: int | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[LocationSetting]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(LocationSetting).order_by(LocationSetting.id.desc())
        if location_id is not None:
            stmt = stmt.where(LocationSetting.location_id == location_id)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, setting_id: int, payload: dict[str, Any]) -> LocationSetting:
        obj = await cls.get_by_id(db, setting_id)

        if "location_id" in payload and payload["location_id"] != obj.location_id:
            raise BadRequestException("Changing location_id for an existing settings row is not allowed.")

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, setting_id: int) -> None:
        obj = await cls.get_by_id(db, setting_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        location_id = payload["location_id"]
        await cls._ensure_location_exists(db, location_id)

        existing = await cls.get_by_location_id(db, location_id)
        if existing is not None:
            raise ConflictException(f"Location {location_id} already has settings defined.")


# ── Department Service ────────────────────────────────────────────────────────


class DepartmentService(BaseOrgService):
    """Business logic for departments."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> Department:
        await cls._validate_create(db, payload)
        obj = Department(**payload)
        db.add(obj)
        return await cls._commit_refresh(db, obj)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, department_id: int) -> Department:
        stmt = (
            select(Department)
            .where(Department.id == department_id)
            .options(selectinload(Department.employees))
        )
        return await cls._get_one_or_404(db, stmt, f"Department {department_id} not found.")

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Department]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(Department).order_by(Department.id.desc())

        if organization_id is not None:
            stmt = stmt.where(Department.organization_id == organization_id)
        if location_id is not None:
            stmt = stmt.where(Department.location_id == location_id)
        if status:
            stmt = stmt.where(Department.status == status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, department_id: int, payload: dict[str, Any]) -> Department:
        obj = await cls.get_by_id(db, department_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        return await cls._commit_refresh(db, obj)

    @classmethod
    async def delete(cls, db: AsyncSession, department_id: int) -> None:
        obj = await cls.get_by_id(db, department_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_employees(
        cls,
        db: AsyncSession,
        department_id: int,
        *,
        employment_status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Employee]:
        await cls._ensure_department_exists(db, department_id)
        return await EmployeeService.list(
            db,
            department_id=department_id,
            employment_status=employment_status,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload["organization_id"]
        await cls._ensure_organization_exists(db, organization_id)

        location_id = payload.get("location_id")
        if location_id is not None:
            await cls._ensure_location_belongs_to_org(db, location_id, organization_id)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        department: Department,
        payload: dict[str, Any],
    ) -> None:
        if "organization_id" in payload and payload["organization_id"] != department.organization_id:
            raise BadRequestException("Changing department organization_id is not allowed.")

        if "location_id" in payload and payload["location_id"] is not None:
            await cls._ensure_location_belongs_to_org(
                db,
                payload["location_id"],
                department.organization_id,
            )


# ── Employee Service ──────────────────────────────────────────────────────────


class EmployeeService(BaseOrgService):
    """Business logic for employees."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> Employee:
        await cls._validate_create(db, payload)
        obj = Employee(**payload)
        db.add(obj)
        created = await cls._commit_refresh(db, obj)
        return await cls.get_by_id(db, created.id)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, employee_id: int) -> Employee:
        stmt = (
            select(Employee)
            .where(Employee.id == employee_id)
            .options(selectinload(Employee.location_assignments))
        )
        return await cls._get_one_or_404(db, stmt, f"Employee {employee_id} not found.")

    @classmethod
    async def get_detail(cls, db: AsyncSession, employee_id: int) -> Employee:
        return await cls.get_by_id(db, employee_id)

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        organization_id: int | None = None,
        department_id: int | None = None,
        primary_location_id: int | None = None,
        employment_status: str | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[Employee]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(Employee).order_by(Employee.id.desc())

        if organization_id is not None:
            stmt = stmt.where(Employee.organization_id == organization_id)
        if department_id is not None:
            stmt = stmt.where(Employee.department_id == department_id)
        if primary_location_id is not None:
            stmt = stmt.where(Employee.primary_location_id == primary_location_id)
        if employment_status:
            stmt = stmt.where(Employee.employment_status == employment_status)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(cls, db: AsyncSession, employee_id: int, payload: dict[str, Any]) -> Employee:
        obj = await cls.get_by_id(db, employee_id)
        await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        await cls._commit_refresh(db, obj)
        return await cls.get_by_id(db, employee_id)

    @classmethod
    async def delete(cls, db: AsyncSession, employee_id: int) -> None:
        obj = await cls.get_by_id(db, employee_id)
        await db.delete(obj)
        await db.commit()

    @classmethod
    async def get_assignments(
        cls,
        db: AsyncSession,
        employee_id: int,
        *,
        status: str | None = None,
        is_primary: bool | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[EmployeeLocationAssignment]:
        await cls._ensure_employee_exists(db, employee_id)
        return await EmployeeLocationAssignmentService.list(
            db,
            employee_id=employee_id,
            status=status,
            is_primary=is_primary,
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> None:
        organization_id = payload["organization_id"]
        user_id = payload["user_id"]
        employee_code = payload["employee_code"]

        await cls._ensure_organization_exists(db, organization_id)
        await cls._ensure_user_exists(db, user_id)

        await cls._validate_unique_user_id(db, user_id)
        await cls._validate_unique_employee_code(
            db,
            organization_id=organization_id,
            employee_code=employee_code,
        )

        department_id = payload.get("department_id")
        if department_id is not None:
            await cls._ensure_department_belongs_to_org(db, department_id, organization_id)

        primary_location_id = payload.get("primary_location_id")
        if primary_location_id is not None:
            await cls._ensure_location_belongs_to_org(db, primary_location_id, organization_id)

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        employee: Employee,
        payload: dict[str, Any],
    ) -> None:
        if "user_id" in payload and payload["user_id"] != employee.user_id:
            raise BadRequestException("Changing employee user_id is not allowed.")

        if "organization_id" in payload and payload["organization_id"] != employee.organization_id:
            raise BadRequestException("Changing employee organization_id is not allowed.")

        if "employee_code" in payload and payload["employee_code"]:
            await cls._validate_unique_employee_code(
                db,
                organization_id=employee.organization_id,
                employee_code=payload["employee_code"],
                exclude_id=employee.id,
            )

        if "department_id" in payload and payload["department_id"] is not None:
            await cls._ensure_department_belongs_to_org(
                db,
                payload["department_id"],
                employee.organization_id,
            )

        if "primary_location_id" in payload and payload["primary_location_id"] is not None:
            await cls._ensure_location_belongs_to_org(
                db,
                payload["primary_location_id"],
                employee.organization_id,
            )

    @classmethod
    async def _validate_unique_user_id(
        cls,
        db: AsyncSession,
        user_id: int,
        *,
        exclude_id: int | None = None,
    ) -> None:
        stmt = select(Employee).where(Employee.user_id == user_id)
        if exclude_id is not None:
            stmt = stmt.where(Employee.id != exclude_id)

        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(f"User {user_id} is already linked to an employee.")

    @classmethod
    async def _validate_unique_employee_code(
        cls,
        db: AsyncSession,
        *,
        organization_id: int,
        employee_code: str,
        exclude_id: int | None = None,
    ) -> None:
        stmt = select(Employee).where(
            Employee.organization_id == organization_id,
            Employee.employee_code == employee_code,
        )
        if exclude_id is not None:
            stmt = stmt.where(Employee.id != exclude_id)

        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                f"Employee code '{employee_code}' already exists for organization {organization_id}."
            )


# ── Employee Location Assignment Service ──────────────────────────────────────


class EmployeeLocationAssignmentService(BaseOrgService):
    """Business logic for employee-location assignments."""

    @classmethod
    async def create(cls, db: AsyncSession, payload: dict[str, Any]) -> EmployeeLocationAssignment:
        employee = await cls._validate_create(db, payload)

        obj = EmployeeLocationAssignment(**payload)
        db.add(obj)
        await db.flush()
        await cls._sync_primary_assignment_on_create_or_update(db, employee, obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def get_by_id(cls, db: AsyncSession, assignment_id: int) -> EmployeeLocationAssignment:
        stmt = select(EmployeeLocationAssignment).where(EmployeeLocationAssignment.id == assignment_id)
        return await cls._get_one_or_404(
            db,
            stmt,
            f"Employee location assignment {assignment_id} not found.",
        )

    @classmethod
    async def list(
        cls,
        db: AsyncSession,
        *,
        employee_id: int | None = None,
        location_id: int | None = None,
        status: str | None = None,
        is_primary: bool | None = None,
        offset: int = DEFAULT_OFFSET,
        limit: int = DEFAULT_LIMIT,
    ) -> list[EmployeeLocationAssignment]:
        offset, limit = cls._normalize_pagination(offset, limit)

        stmt = select(EmployeeLocationAssignment).order_by(EmployeeLocationAssignment.id.desc())

        if employee_id is not None:
            stmt = stmt.where(EmployeeLocationAssignment.employee_id == employee_id)
        if location_id is not None:
            stmt = stmt.where(EmployeeLocationAssignment.location_id == location_id)
        if status:
            stmt = stmt.where(EmployeeLocationAssignment.status == status)
        if is_primary is not None:
            stmt = stmt.where(EmployeeLocationAssignment.is_primary == is_primary)

        stmt = stmt.offset(offset).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        assignment_id: int,
        payload: dict[str, Any],
    ) -> EmployeeLocationAssignment:
        obj = await cls.get_by_id(db, assignment_id)
        employee = await cls._validate_update(db, obj, payload)

        for key, value in payload.items():
            setattr(obj, key, value)

        await db.flush()
        await cls._sync_primary_assignment_on_create_or_update(db, employee, obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def delete(cls, db: AsyncSession, assignment_id: int) -> None:
        obj = await cls.get_by_id(db, assignment_id)
        employee = await cls._ensure_employee_exists(db, obj.employee_id)

        await db.delete(obj)
        await db.flush()

        if employee.primary_location_id == obj.location_id:
            replacement_stmt = select(EmployeeLocationAssignment).where(
                EmployeeLocationAssignment.employee_id == employee.id,
                EmployeeLocationAssignment.status == "active",
                EmployeeLocationAssignment.is_primary.is_(True),
            )
            replacement_result = await db.execute(replacement_stmt)
            replacement = replacement_result.scalar_one_or_none()

            if replacement is None:
                employee.primary_location_id = None
            else:
                employee.primary_location_id = replacement.location_id

        await db.commit()

    @classmethod
    async def _validate_create(cls, db: AsyncSession, payload: dict[str, Any]) -> Employee:
        employee = await cls._ensure_employee_exists(db, payload["employee_id"])
        location = await cls._ensure_location_exists(db, payload["location_id"])

        if employee.organization_id != location.organization_id:
            raise BadRequestException(
                "Employee and location must belong to the same organization."
            )

        await cls._validate_assignment_dates(payload)
        return employee

    @classmethod
    async def _validate_update(
        cls,
        db: AsyncSession,
        assignment: EmployeeLocationAssignment,
        payload: dict[str, Any],
    ) -> Employee:
        employee = await cls._ensure_employee_exists(db, assignment.employee_id)

        if "employee_id" in payload and payload["employee_id"] != assignment.employee_id:
            raise BadRequestException("Changing assignment employee_id is not allowed.")

        if "location_id" in payload and payload["location_id"] != assignment.location_id:
            new_location = await cls._ensure_location_exists(db, payload["location_id"])
            if new_location.organization_id != employee.organization_id:
                raise BadRequestException(
                    "Employee and location must belong to the same organization."
                )

        combined_payload = {
            "assigned_from": payload.get("assigned_from", assignment.assigned_from),
            "assigned_to": payload.get("assigned_to", assignment.assigned_to),
        }
        await cls._validate_assignment_dates(combined_payload)
        return employee

    @classmethod
    async def _validate_assignment_dates(cls, payload: dict[str, Any]) -> None:
        assigned_from = payload.get("assigned_from")
        assigned_to = payload.get("assigned_to")

        if assigned_from and assigned_to and assigned_to < assigned_from:
            raise BadRequestException("assigned_to cannot be earlier than assigned_from.")

    @classmethod
    async def _sync_primary_assignment_on_create_or_update(
        cls,
        db: AsyncSession,
        employee: Employee,
        assignment: EmployeeLocationAssignment,
    ) -> None:
        """
        Ensures only one primary assignment per employee.
        Also mirrors primary assignment onto employee.primary_location_id.
        """
        if assignment.is_primary:
            stmt = select(EmployeeLocationAssignment).where(
                EmployeeLocationAssignment.employee_id == employee.id,
                EmployeeLocationAssignment.id != assignment.id,
                EmployeeLocationAssignment.is_primary.is_(True),
            )
            result = await db.execute(stmt)
            current_primary_rows = list(result.scalars().all())

            for row in current_primary_rows:
                row.is_primary = False

            employee.primary_location_id = assignment.location_id

        else:
            if employee.primary_location_id == assignment.location_id:
                other_primary_stmt = select(EmployeeLocationAssignment).where(
                    EmployeeLocationAssignment.employee_id == employee.id,
                    EmployeeLocationAssignment.id != assignment.id,
                    EmployeeLocationAssignment.is_primary.is_(True),
                    EmployeeLocationAssignment.status == "active",
                )
                other_primary_result = await db.execute(other_primary_stmt)
                other_primary = other_primary_result.scalar_one_or_none()

                if other_primary is None:
                    employee.primary_location_id = None
                else:
                    employee.primary_location_id = other_primary.location_id