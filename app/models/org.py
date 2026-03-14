"""
Organisation models — owned by Sunny (FR2).
Tables:
- organizations
- restaurant_locations
- location_settings
- departments
- employees
- employee_location_assignments
"""
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    AssignmentStatusEnum,
    DepartmentStatusEnum,
    EmploymentStatusEnum,
    LocationStatusEnum,
    OrgStatusEnum,
)


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    tax_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(OrgStatusEnum, nullable=False, default="active")

    locations: Mapped[list["RestaurantLocation"]] = relationship(
        "RestaurantLocation",
        back_populates="organization",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="organization",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="organization",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    # Seed: GreenBite Restaurants


class RestaurantLocation(Base, TimestampMixin):
    __tablename__ = "restaurant_locations"
    __table_args__ = (UniqueConstraint("organization_id", "location_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_code: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_line_1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True, default="Europe/London")
    status: Mapped[str] = mapped_column(LocationStatusEnum, nullable=False, default="active")

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="locations",
        lazy="selectin",
    )
    settings: Mapped["LocationSetting | None"] = relationship(
        "LocationSetting",
        back_populates="location",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="location",
        lazy="selectin",
    )
    employee_assignments: Mapped[list["EmployeeLocationAssignment"]] = relationship(
        "EmployeeLocationAssignment",
        back_populates="location",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    primary_employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="primary_location",
        lazy="selectin",
        foreign_keys="Employee.primary_location_id",
    )
    # Seed: GreenBite Central (London), GreenBite Riverside (Manchester)


class LocationSetting(Base, TimestampMixin):
    __tablename__ = "location_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    esg_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    compliance_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supplier_transparency_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    employee_rewards_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    customer_rewards_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    blockchain_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    token_multiplier: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=1.00)
    weekly_leaderboard_reset_day: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped["RestaurantLocation"] = relationship(
        "RestaurantLocation",
        back_populates="settings",
        lazy="selectin",
    )


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(DepartmentStatusEnum, nullable=False, default="active")

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="departments",
        lazy="selectin",
    )
    location: Mapped["RestaurantLocation | None"] = relationship(
        "RestaurantLocation",
        back_populates="departments",
        lazy="selectin",
    )
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        lazy="selectin",
    )


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("organization_id", "employee_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    department_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    employee_code: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(EmploymentStatusEnum, nullable=False, default="active")
    primary_location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="employees",
        lazy="selectin",
    )
    department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="employees",
        lazy="selectin",
    )
    primary_location: Mapped["RestaurantLocation | None"] = relationship(
        "RestaurantLocation",
        back_populates="primary_employees",
        lazy="selectin",
        foreign_keys=[primary_location_id],
    )
    location_assignments: Mapped[list["EmployeeLocationAssignment"]] = relationship(
        "EmployeeLocationAssignment",
        back_populates="employee",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    # Seed: EMP001 Restaurant Manager, EMP002 Chef


class EmployeeLocationAssignment(Base, TimestampMixin):
    __tablename__ = "employee_location_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(AssignmentStatusEnum, nullable=False, default="active")

    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="location_assignments",
        lazy="selectin",
    )
    location: Mapped["RestaurantLocation"] = relationship(
        "RestaurantLocation",
        back_populates="employee_assignments",
        lazy="selectin",
    )