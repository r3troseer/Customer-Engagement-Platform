"""
FR4 — ESG & SDG Management
API router for the simplified ESG model design.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.dependencies.db import DBSession
from app.schemas.esg import (
    EsgActivityCreate,
    EsgActivityOut,
    EsgActivityUpdate,
    EsgMetricValueCreate,
    EsgMetricValueOut,
    EsgMetricValueUpdate,
    EsgObjectiveCreate,
    EsgObjectiveDetailOut,
    EsgObjectiveOut,
    EsgObjectiveUpdate,
    EsgReportCreate,
    EsgReportOut,
    EsgReportUpdate,
)
from app.services.esg_service import (
    EsgActivityService,
    EsgMetricValueService,
    EsgObjectiveService,
    EsgReportService,
)

router = APIRouter(prefix="/esg", tags=["FR4 — ESG & SDG Management"])


# ── ESG Objectives ────────────────────────────────────────────────────────────

@router.post("/objectives", response_model=EsgObjectiveOut, status_code=status.HTTP_201_CREATED)
async def create_esg_objective(payload: EsgObjectiveCreate, db: DBSession) -> EsgObjectiveOut:
    return await EsgObjectiveService.create(db, payload.model_dump())


@router.get("/objectives", response_model=list[EsgObjectiveOut])
async def list_esg_objectives(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    created_by: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EsgObjectiveOut]:
    return await EsgObjectiveService.list(
        db,
        organization_id=organization_id,
        category=category,
        status=status_filter,
        created_by=created_by,
        offset=offset,
        limit=limit,
    )


@router.get("/objectives/{objective_id}", response_model=EsgObjectiveOut)
async def get_esg_objective(objective_id: int, db: DBSession) -> EsgObjectiveOut:
    return await EsgObjectiveService.get_by_id(db, objective_id)


@router.get("/objectives/{objective_id}/detail", response_model=EsgObjectiveDetailOut)
async def get_esg_objective_detail(objective_id: int, db: DBSession) -> EsgObjectiveDetailOut:
    return await EsgObjectiveService.get_detail(db, objective_id)


@router.patch("/objectives/{objective_id}", response_model=EsgObjectiveOut)
async def update_esg_objective(objective_id: int, payload: EsgObjectiveUpdate, db: DBSession) -> EsgObjectiveOut:
    return await EsgObjectiveService.update(db, objective_id, payload.model_dump(exclude_unset=True))


@router.delete("/objectives/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_esg_objective(objective_id: int, db: DBSession) -> Response:
    await EsgObjectiveService.delete(db, objective_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── ESG Metric Values ─────────────────────────────────────────────────────────

@router.post("/metric-values", response_model=EsgMetricValueOut, status_code=status.HTTP_201_CREATED)
async def create_esg_metric_value(payload: EsgMetricValueCreate, db: DBSession) -> EsgMetricValueOut:
    return await EsgMetricValueService.create(db, payload.model_dump())


@router.get("/metric-values", response_model=list[EsgMetricValueOut])
async def list_esg_metric_values(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    esg_objective_id: int | None = Query(default=None),
    metric_code: str | None = Query(default=None),
    category: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EsgMetricValueOut]:
    return await EsgMetricValueService.list(
        db,
        organization_id=organization_id,
        location_id=location_id,
        esg_objective_id=esg_objective_id,
        metric_code=metric_code,
        category=category,
        source_type=source_type,
        offset=offset,
        limit=limit,
    )


@router.get("/metric-values/{value_id}", response_model=EsgMetricValueOut)
async def get_esg_metric_value(value_id: int, db: DBSession) -> EsgMetricValueOut:
    return await EsgMetricValueService.get_by_id(db, value_id)


@router.patch("/metric-values/{value_id}", response_model=EsgMetricValueOut)
async def update_esg_metric_value(
    value_id: int,
    payload: EsgMetricValueUpdate,
    db: DBSession,
) -> EsgMetricValueOut:
    return await EsgMetricValueService.update(db, value_id, payload.model_dump(exclude_unset=True))


@router.delete("/metric-values/{value_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_esg_metric_value(value_id: int, db: DBSession) -> Response:
    await EsgMetricValueService.delete(db, value_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── ESG Activities ────────────────────────────────────────────────────────────

@router.post("/activities", response_model=EsgActivityOut, status_code=status.HTTP_201_CREATED)
async def create_esg_activity(payload: EsgActivityCreate, db: DBSession) -> EsgActivityOut:
    return await EsgActivityService.create(db, payload.model_dump())


@router.get("/activities", response_model=list[EsgActivityOut])
async def list_esg_activities(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    esg_objective_id: int | None = Query(default=None),
    activity_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    created_by: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EsgActivityOut]:
    return await EsgActivityService.list(
        db,
        organization_id=organization_id,
        location_id=location_id,
        esg_objective_id=esg_objective_id,
        activity_type=activity_type,
        status=status_filter,
        created_by=created_by,
        offset=offset,
        limit=limit,
    )


@router.get("/activities/{activity_id}", response_model=EsgActivityOut)
async def get_esg_activity(activity_id: int, db: DBSession) -> EsgActivityOut:
    return await EsgActivityService.get_by_id(db, activity_id)


@router.patch("/activities/{activity_id}", response_model=EsgActivityOut)
async def update_esg_activity(activity_id: int, payload: EsgActivityUpdate, db: DBSession) -> EsgActivityOut:
    return await EsgActivityService.update(db, activity_id, payload.model_dump(exclude_unset=True))


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_esg_activity(activity_id: int, db: DBSession) -> Response:
    await EsgActivityService.delete(db, activity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── ESG Reports ───────────────────────────────────────────────────────────────

@router.post("/reports", response_model=EsgReportOut, status_code=status.HTTP_201_CREATED)
async def create_esg_report(payload: EsgReportCreate, db: DBSession) -> EsgReportOut:
    return await EsgReportService.create(db, payload.model_dump())


@router.get("/reports", response_model=list[EsgReportOut])
async def list_esg_reports(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    report_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    generated_by: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[EsgReportOut]:
    return await EsgReportService.list(
        db,
        organization_id=organization_id,
        location_id=location_id,
        report_type=report_type,
        status=status_filter,
        generated_by=generated_by,
        offset=offset,
        limit=limit,
    )


@router.get("/reports/{report_id}", response_model=EsgReportOut)
async def get_esg_report(report_id: int, db: DBSession) -> EsgReportOut:
    return await EsgReportService.get_by_id(db, report_id)


@router.patch("/reports/{report_id}", response_model=EsgReportOut)
async def update_esg_report(report_id: int, payload: EsgReportUpdate, db: DBSession) -> EsgReportOut:
    return await EsgReportService.update(db, report_id, payload.model_dump(exclude_unset=True))


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_esg_report(report_id: int, db: DBSession) -> Response:
    await EsgReportService.delete(db, report_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)