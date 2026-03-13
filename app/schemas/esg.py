"""
FR4 — ESG & SDG Management

Schemas for the simplified ESG model design:
- esg_objectives
- esg_metric_values
- esg_activities
- esg_reports
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# ── ESG Objectives ────────────────────────────────────────────────────────────

class EsgObjectiveCreate(BaseModel):
    organization_id: int
    category: str
    sdg_goal_numbers: list[int] | None = None
    title: str
    description: str | None = None
    target_value: Decimal | None = None
    target_unit: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "draft"
    created_by: int | None = None


class EsgObjectiveUpdate(BaseModel):
    category: str | None = None
    sdg_goal_numbers: list[int] | None = None
    title: str | None = None
    description: str | None = None
    target_value: Decimal | None = None
    target_unit: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None


class EsgObjectiveOut(BaseModel):
    id: int
    organization_id: int
    category: str
    sdg_goal_numbers: list[int] | None
    title: str
    description: str | None
    target_value: Decimal | None
    target_unit: str | None
    start_date: date | None
    end_date: date | None
    status: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── ESG Metric Values ─────────────────────────────────────────────────────────

class EsgMetricValueCreate(BaseModel):
    organization_id: int
    location_id: int | None = None
    esg_objective_id: int | None = None
    metric_name: str
    metric_code: str
    category: str
    unit: str
    metric_value: Decimal
    value_date: date
    source_type: str = "manual"
    source_reference: str | None = None
    notes: str | None = None
    recorded_by: int | None = None


class EsgMetricValueUpdate(BaseModel):
    location_id: int | None = None
    esg_objective_id: int | None = None
    metric_name: str | None = None
    metric_code: str | None = None
    category: str | None = None
    unit: str | None = None
    metric_value: Decimal | None = None
    value_date: date | None = None
    source_type: str | None = None
    source_reference: str | None = None
    notes: str | None = None
    recorded_by: int | None = None


class EsgMetricValueOut(BaseModel):
    id: int
    organization_id: int
    location_id: int | None
    esg_objective_id: int | None
    metric_name: str
    metric_code: str
    category: str
    unit: str
    metric_value: Decimal
    value_date: date
    source_type: str
    source_reference: str | None
    notes: str | None
    recorded_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── ESG Activities ────────────────────────────────────────────────────────────

class EsgActivityCreate(BaseModel):
    organization_id: int
    location_id: int | None = None
    esg_objective_id: int | None = None
    title: str
    description: str | None = None
    activity_type: str
    start_date: date | None = None
    end_date: date | None = None
    impact_notes: str | None = None
    created_by: int | None = None
    status: str = "planned"


class EsgActivityUpdate(BaseModel):
    location_id: int | None = None
    esg_objective_id: int | None = None
    title: str | None = None
    description: str | None = None
    activity_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    impact_notes: str | None = None
    status: str | None = None


class EsgActivityOut(BaseModel):
    id: int
    organization_id: int
    location_id: int | None
    esg_objective_id: int | None
    title: str
    description: str | None
    activity_type: str
    start_date: date | None
    end_date: date | None
    impact_notes: str | None
    created_by: int | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── ESG Reports ───────────────────────────────────────────────────────────────

class EsgReportCreate(BaseModel):
    organization_id: int
    location_id: int | None = None
    report_name: str
    report_type: str = "esg"
    period_start: date | None = None
    period_end: date | None = None
    report_file_path: str | None = None
    generated_by: int | None = None
    generated_at: datetime | None = None
    status: str = "draft"


class EsgReportUpdate(BaseModel):
    location_id: int | None = None
    report_name: str | None = None
    report_type: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    report_file_path: str | None = None
    generated_by: int | None = None
    generated_at: datetime | None = None
    status: str | None = None


class EsgReportOut(BaseModel):
    id: int
    organization_id: int
    location_id: int | None
    report_name: str
    report_type: str
    period_start: date | None
    period_end: date | None
    report_file_path: str | None
    generated_by: int | None
    generated_at: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Detail Schemas ────────────────────────────────────────────────────────────

class EsgObjectiveDetailOut(EsgObjectiveOut):
    metric_values: list[EsgMetricValueOut] = []
    activities: list[EsgActivityOut] = []

    model_config = {"from_attributes": True}