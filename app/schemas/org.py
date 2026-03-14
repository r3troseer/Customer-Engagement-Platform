"""
FR2 — Organization & Restaurant Structure

Request/response schemas for organizations, restaurant locations,
location settings, departments, employees, and employee location assignments.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


# ── Organizations ─────────────────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    name: str
    legal_name: str | None = None
    registration_number: str | None = None
    tax_number: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    website: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postcode: str | None = None
    country: str | None = None
    status: str = "active"


class OrganizationUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    registration_number: str | None = None
    tax_number: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    website: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postcode: str | None = None
    country: str | None = None
    status: str | None = None


class OrganizationOut(BaseModel):
    id: int
    name: str
    legal_name: str | None
    registration_number: str | None
    tax_number: str | None
    contact_email: str | None
    contact_phone: str | None
    website: str | None
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    state_region: str | None
    postcode: str | None
    country: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Restaurant Locations ──────────────────────────────────────────────────────

class LocationCreate(BaseModel):
    organization_id: int
    name: str
    location_code: str
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postcode: str | None = None
    country: str | None = None
    timezone: str = "Europe/London"
    status: str = "active"


class LocationUpdate(BaseModel):
    name: str | None = None
    location_code: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postcode: str | None = None
    country: str | None = None
    timezone: str | None = None
    status: str | None = None


class LocationOut(BaseModel):
    id: int
    organization_id: int
    name: str
    location_code: str
    contact_email: str | None
    contact_phone: str | None
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    state_region: str | None
    postcode: str | None
    country: str | None
    timezone: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Location Settings ─────────────────────────────────────────────────────────

class LocationSettingCreate(BaseModel):
    location_id: int
    esg_enabled: bool = True
    compliance_enabled: bool = True
    supplier_transparency_enabled: bool = False
    employee_rewards_enabled: bool = False
    customer_rewards_enabled: bool = False
    blockchain_enabled: bool = False
    token_multiplier: Decimal = Field(default=Decimal("1.00"))
    weekly_leaderboard_reset_day: str | None = None
    notes: str | None = None


class LocationSettingUpdate(BaseModel):
    esg_enabled: bool | None = None
    compliance_enabled: bool | None = None
    supplier_transparency_enabled: bool | None = None
    employee_rewards_enabled: bool | None = None
    customer_rewards_enabled: bool | None = None
    blockchain_enabled: bool | None = None
    token_multiplier: Decimal | None = None
    weekly_leaderboard_reset_day: str | None = None
    notes: str | None = None


class LocationSettingOut(BaseModel):
    id: int
    location_id: int
    esg_enabled: bool
    compliance_enabled: bool
    supplier_transparency_enabled: bool
    employee_rewards_enabled: bool
    customer_rewards_enabled: bool
    blockchain_enabled: bool
    token_multiplier: Decimal
    weekly_leaderboard_reset_day: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Departments ───────────────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    organization_id: int
    location_id: int | None = None
    name: str
    description: str | None = None
    status: str = "active"


class DepartmentUpdate(BaseModel):
    location_id: int | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None


class DepartmentOut(BaseModel):
    id: int
    organization_id: int
    location_id: int | None
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Employees ─────────────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    user_id: int
    organization_id: int
    department_id: int | None = None
    employee_code: str
    job_title: str | None = None
    hire_date: date | None = None
    employment_status: str = "active"
    primary_location_id: int | None = None


class EmployeeUpdate(BaseModel):
    department_id: int | None = None
    employee_code: str | None = None
    job_title: str | None = None
    hire_date: date | None = None
    employment_status: str | None = None
    primary_location_id: int | None = None


class EmployeeOut(BaseModel):
    id: int
    user_id: int
    organization_id: int
    department_id: int | None
    employee_code: str
    job_title: str | None
    hire_date: date | None
    employment_status: str
    primary_location_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Employee Location Assignments ─────────────────────────────────────────────

class EmployeeLocationAssignmentCreate(BaseModel):
    employee_id: int
    location_id: int
    assigned_role: str | None = None
    assigned_from: date | None = None
    assigned_to: date | None = None
    is_primary: bool = False
    status: str = "active"


class EmployeeLocationAssignmentUpdate(BaseModel):
    assigned_role: str | None = None
    assigned_from: date | None = None
    assigned_to: date | None = None
    is_primary: bool | None = None
    status: str | None = None


class EmployeeLocationAssignmentOut(BaseModel):
    id: int
    employee_id: int
    location_id: int
    assigned_role: str | None
    assigned_from: date | None
    assigned_to: date | None
    is_primary: bool
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Nested / Detail Response Schemas ──────────────────────────────────────────

class OrganizationDetailOut(OrganizationOut):
    locations: list[LocationOut] = []
    departments: list[DepartmentOut] = []
    employees: list[EmployeeOut] = []

    model_config = {"from_attributes": True}


class LocationDetailOut(LocationOut):
    settings: LocationSettingOut | None = None
    departments: list[DepartmentOut] = []
    employee_assignments: list[EmployeeLocationAssignmentOut] = []

    model_config = {"from_attributes": True}


class EmployeeDetailOut(EmployeeOut):
    location_assignments: list[EmployeeLocationAssignmentOut] = []

    model_config = {"from_attributes": True}