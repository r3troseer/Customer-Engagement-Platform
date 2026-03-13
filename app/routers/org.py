"""
FR2 — Organization & Restaurant Structure
API router for organizations, restaurant locations, location settings,
departments, employees, and employee location assignments.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.dependencies.db import DBSession
from app.schemas.org import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeDetailOut,
    EmployeeLocationAssignmentCreate,
    EmployeeLocationAssignmentOut,
    EmployeeLocationAssignmentUpdate,
    EmployeeOut,
    EmployeeUpdate,
    LocationCreate,
    LocationDetailOut,
    LocationOut,
    LocationSettingCreate,
    LocationSettingOut,
    LocationSettingUpdate,
    LocationUpdate,
    OrganizationDetailOut,
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
)
from app.services.org_service import (
    DepartmentService,
    EmployeeLocationAssignmentService,
    EmployeeService,
    LocationSettingService,
    OrganizationService,
    RestaurantLocationService,
)

router = APIRouter(prefix="/org", tags=["FR2 — Organization & Restaurant Structure"])


# ── Organizations ─────────────────────────────────────────────────────────────

@router.post(
    "/organizations",
    response_model=OrganizationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(payload: OrganizationCreate, db: DBSession) -> OrganizationOut:
    return await OrganizationService.create(db, payload.model_dump())


@router.get(
    "/organizations",
    response_model=list[OrganizationOut],
)
async def list_organizations(
    db: DBSession,
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[OrganizationOut]:
    return await OrganizationService.list(
        db,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/organizations/{organization_id}",
    response_model=OrganizationOut,
)
async def get_organization(organization_id: int, db: DBSession) -> OrganizationOut:
    return await OrganizationService.get_by_id(db, organization_id)


@router.get(
    "/organizations/{organization_id}/detail",
    response_model=OrganizationDetailOut,
)
async def get_organization_detail(organization_id: int, db: DBSession) -> OrganizationDetailOut:
    return await OrganizationService.get_detail(db, organization_id)


@router.get(
    "/organizations/{organization_id}/locations",
    response_model=list[LocationOut],
)
async def get_organization_locations(
    organization_id: int,
    db: DBSession,
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[LocationOut]:
    return await OrganizationService.get_locations(
        db,
        organization_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/organizations/{organization_id}/departments",
    response_model=list[DepartmentOut],
)
async def get_organization_departments(
    organization_id: int,
    db: DBSession,
    location_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DepartmentOut]:
    return await OrganizationService.get_departments(
        db,
        organization_id,
        location_id=location_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/organizations/{organization_id}/employees",
    response_model=list[EmployeeOut],
)
async def get_organization_employees(
    organization_id: int,
    db: DBSession,
    department_id: int | None = Query(default=None),
    primary_location_id: int | None = Query(default=None),
    employment_status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EmployeeOut]:
    return await OrganizationService.get_employees(
        db,
        organization_id,
        department_id=department_id,
        primary_location_id=primary_location_id,
        employment_status=employment_status,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/organizations/{organization_id}",
    response_model=OrganizationOut,
)
async def update_organization(
    organization_id: int,
    payload: OrganizationUpdate,
    db: DBSession,
) -> OrganizationOut:
    return await OrganizationService.update(
        db,
        organization_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/organizations/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_organization(organization_id: int, db: DBSession) -> Response:
    await OrganizationService.delete(db, organization_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Restaurant Locations ──────────────────────────────────────────────────────

@router.post(
    "/locations",
    response_model=LocationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(payload: LocationCreate, db: DBSession) -> LocationOut:
    return await RestaurantLocationService.create(db, payload.model_dump())


@router.get(
    "/locations",
    response_model=list[LocationOut],
)
async def list_locations(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[LocationOut]:
    return await RestaurantLocationService.list(
        db,
        organization_id=organization_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/locations/{location_id}",
    response_model=LocationOut,
)
async def get_location(location_id: int, db: DBSession) -> LocationOut:
    return await RestaurantLocationService.get_by_id(db, location_id)


@router.get(
    "/locations/{location_id}/detail",
    response_model=LocationDetailOut,
)
async def get_location_detail(location_id: int, db: DBSession) -> LocationDetailOut:
    return await RestaurantLocationService.get_detail(db, location_id)


@router.get(
    "/locations/{location_id}/settings",
    response_model=LocationSettingOut | None,
)
async def get_location_settings(location_id: int, db: DBSession) -> LocationSettingOut | None:
    return await RestaurantLocationService.get_settings(db, location_id)


@router.get(
    "/locations/{location_id}/departments",
    response_model=list[DepartmentOut],
)
async def get_location_departments(
    location_id: int,
    db: DBSession,
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DepartmentOut]:
    return await RestaurantLocationService.get_departments(
        db,
        location_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/locations/{location_id}/employees",
    response_model=list[EmployeeOut],
)
async def get_location_employees(
    location_id: int,
    db: DBSession,
    employment_status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EmployeeOut]:
    return await RestaurantLocationService.get_employees(
        db,
        location_id,
        employment_status=employment_status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/locations/{location_id}/assignments",
    response_model=list[EmployeeLocationAssignmentOut],
)
async def get_location_assignments(
    location_id: int,
    db: DBSession,
    employee_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    is_primary: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EmployeeLocationAssignmentOut]:
    return await RestaurantLocationService.get_assignments(
        db,
        location_id,
        employee_id=employee_id,
        status=status_filter,
        is_primary=is_primary,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/locations/{location_id}",
    response_model=LocationOut,
)
async def update_location(
    location_id: int,
    payload: LocationUpdate,
    db: DBSession,
) -> LocationOut:
    return await RestaurantLocationService.update(
        db,
        location_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location(location_id: int, db: DBSession) -> Response:
    await RestaurantLocationService.delete(db, location_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Location Settings ─────────────────────────────────────────────────────────

@router.post(
    "/location-settings",
    response_model=LocationSettingOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_location_setting(
    payload: LocationSettingCreate,
    db: DBSession,
) -> LocationSettingOut:
    return await LocationSettingService.create(db, payload.model_dump())


@router.get(
    "/location-settings",
    response_model=list[LocationSettingOut],
)
async def list_location_settings(
    db: DBSession,
    location_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[LocationSettingOut]:
    return await LocationSettingService.list(
        db,
        location_id=location_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/location-settings/{setting_id}",
    response_model=LocationSettingOut,
)
async def get_location_setting(setting_id: int, db: DBSession) -> LocationSettingOut:
    return await LocationSettingService.get_by_id(db, setting_id)


@router.get(
    "/location-settings/by-location/{location_id}",
    response_model=LocationSettingOut | None,
)
async def get_location_setting_by_location(
    location_id: int,
    db: DBSession,
) -> LocationSettingOut | None:
    return await LocationSettingService.get_by_location_id(db, location_id)


@router.patch(
    "/location-settings/{setting_id}",
    response_model=LocationSettingOut,
)
async def update_location_setting(
    setting_id: int,
    payload: LocationSettingUpdate,
    db: DBSession,
) -> LocationSettingOut:
    return await LocationSettingService.update(
        db,
        setting_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/location-settings/{setting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location_setting(setting_id: int, db: DBSession) -> Response:
    await LocationSettingService.delete(db, setting_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Departments ───────────────────────────────────────────────────────────────

@router.post(
    "/departments",
    response_model=DepartmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(payload: DepartmentCreate, db: DBSession) -> DepartmentOut:
    return await DepartmentService.create(db, payload.model_dump())


@router.get(
    "/departments",
    response_model=list[DepartmentOut],
)
async def list_departments(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DepartmentOut]:
    return await DepartmentService.list(
        db,
        organization_id=organization_id,
        location_id=location_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/departments/{department_id}",
    response_model=DepartmentOut,
)
async def get_department(department_id: int, db: DBSession) -> DepartmentOut:
    return await DepartmentService.get_by_id(db, department_id)


@router.get(
    "/departments/{department_id}/employees",
    response_model=list[EmployeeOut],
)
async def get_department_employees(
    department_id: int,
    db: DBSession,
    employment_status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EmployeeOut]:
    return await DepartmentService.get_employees(
        db,
        department_id,
        employment_status=employment_status,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/departments/{department_id}",
    response_model=DepartmentOut,
)
async def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    db: DBSession,
) -> DepartmentOut:
    return await DepartmentService.update(
        db,
        department_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/departments/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_department(department_id: int, db: DBSession) -> Response:
    await DepartmentService.delete(db, department_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Employees ─────────────────────────────────────────────────────────────────

@router.post(
    "/employees",
    response_model=EmployeeOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(payload: EmployeeCreate, db: DBSession) -> EmployeeOut:
    return await EmployeeService.create(db, payload.model_dump())


@router.get(
    "/employees",
    response_model=list[EmployeeOut],
)
async def list_employees(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    department_id: int | None = Query(default=None),
    primary_location_id: int | None = Query(default=None),
    employment_status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EmployeeOut]:
    return await EmployeeService.list(
        db,
        organization_id=organization_id,
        department_id=department_id,
        primary_location_id=primary_location_id,
        employment_status=employment_status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
)
async def get_employee(employee_id: int, db: DBSession) -> EmployeeOut:
    return await EmployeeService.get_by_id(db, employee_id)


@router.get(
    "/employees/{employee_id}/detail",
    response_model=EmployeeDetailOut,
)
async def get_employee_detail(employee_id: int, db: DBSession) -> EmployeeDetailOut:
    return await EmployeeService.get_detail(db, employee_id)


@router.get(
    "/employees/{employee_id}/assignments",
    response_model=list[EmployeeLocationAssignmentOut],
)
async def get_employee_assignments(
    employee_id: int,
    db: DBSession,
    status_filter: str | None = Query(default=None, alias="status"),
    is_primary: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EmployeeLocationAssignmentOut]:
    return await EmployeeService.get_assignments(
        db,
        employee_id,
        status=status_filter,
        is_primary=is_primary,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/employees/{employee_id}",
    response_model=EmployeeOut,
)
async def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: DBSession,
) -> EmployeeOut:
    return await EmployeeService.update(
        db,
        employee_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/employees/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee(employee_id: int, db: DBSession) -> Response:
    await EmployeeService.delete(db, employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Employee Location Assignments ─────────────────────────────────────────────

@router.post(
    "/employee-location-assignments",
    response_model=EmployeeLocationAssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_location_assignment(
    payload: EmployeeLocationAssignmentCreate,
    db: DBSession,
) -> EmployeeLocationAssignmentOut:
    return await EmployeeLocationAssignmentService.create(db, payload.model_dump())


@router.get(
    "/employee-location-assignments",
    response_model=list[EmployeeLocationAssignmentOut],
)
async def list_employee_location_assignments(
    db: DBSession,
    employee_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    is_primary: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EmployeeLocationAssignmentOut]:
    return await EmployeeLocationAssignmentService.list(
        db,
        employee_id=employee_id,
        location_id=location_id,
        status=status_filter,
        is_primary=is_primary,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/employee-location-assignments/{assignment_id}",
    response_model=EmployeeLocationAssignmentOut,
)
async def get_employee_location_assignment(
    assignment_id: int,
    db: DBSession,
) -> EmployeeLocationAssignmentOut:
    return await EmployeeLocationAssignmentService.get_by_id(db, assignment_id)


@router.patch(
    "/employee-location-assignments/{assignment_id}",
    response_model=EmployeeLocationAssignmentOut,
)
async def update_employee_location_assignment(
    assignment_id: int,
    payload: EmployeeLocationAssignmentUpdate,
    db: DBSession,
) -> EmployeeLocationAssignmentOut:
    return await EmployeeLocationAssignmentService.update(
        db,
        assignment_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/employee-location-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_employee_location_assignment(
    assignment_id: int,
    db: DBSession,
) -> Response:
    await EmployeeLocationAssignmentService.delete(db, assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)