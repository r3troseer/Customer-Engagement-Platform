"""
FR3 — Compliance Core
API router for compliance frameworks, requirements, tracking, evidence,
reviews, documents, status history, alerts, and scores.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.dependencies.db import DBSession
from app.schemas.compliance import (
    ComplianceAlertCreate,
    ComplianceAlertOut,
    ComplianceAlertResolveRequest,
    ComplianceAlertUpdate,
    ComplianceDocumentCreate,
    ComplianceDocumentOut,
    ComplianceDocumentVersionCreate,
    ComplianceDocumentVersionOut,
    ComplianceEvidenceCreate,
    ComplianceEvidenceOut,
    ComplianceEvidenceUpdate,
    ComplianceFrameworkCreate,
    ComplianceFrameworkOut,
    ComplianceFrameworkUpdate,
    ComplianceRequirementCreate,
    ComplianceRequirementOut,
    ComplianceRequirementUpdate,
    ComplianceReviewCreate,
    ComplianceReviewOut,
    ComplianceReviewUpdate,
    ComplianceScoreCreate,
    ComplianceScoreOut,
    ComplianceScoreUpdate,
    ComplianceStatusHistoryOut,
    LocationComplianceCreate,
    LocationComplianceOut,
    LocationComplianceUpdate,
    OrganizationComplianceCreate,
    OrganizationComplianceOut,
    OrganizationComplianceUpdate,
)
from app.services.compliance_service import (
    ComplianceAlertService,
    ComplianceDocumentService,
    ComplianceDocumentVersionService,
    ComplianceEvidenceService,
    ComplianceFrameworkService,
    ComplianceRequirementService,
    ComplianceReviewService,
    ComplianceScoreService,
    ComplianceStatusHistoryService,
    LocationComplianceService,
    OrganizationComplianceService,
)

router = APIRouter(prefix="/compliance", tags=["FR3 — Compliance Core"])


# ── Compliance Frameworks ─────────────────────────────────────────────────────

@router.post(
    "/frameworks",
    response_model=ComplianceFrameworkOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_framework(
    payload: ComplianceFrameworkCreate,
    db: DBSession,
) -> ComplianceFrameworkOut:
    return await ComplianceFrameworkService.create(db, payload.model_dump())


@router.get(
    "/frameworks",
    response_model=list[ComplianceFrameworkOut],
)
async def list_frameworks(
    db: DBSession,
    framework_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    created_by: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceFrameworkOut]:
    return await ComplianceFrameworkService.list(
        db,
        framework_type=framework_type,
        status=status_filter,
        created_by=created_by,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/frameworks/{framework_id}",
    response_model=ComplianceFrameworkOut,
)
async def get_framework(
    framework_id: int,
    db: DBSession,
) -> ComplianceFrameworkOut:
    return await ComplianceFrameworkService.get_by_id(db, framework_id)


@router.get(
    "/frameworks/{framework_id}/requirements",
    response_model=list[ComplianceRequirementOut],
)
async def get_framework_requirements(
    framework_id: int,
    db: DBSession,
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceRequirementOut]:
    return await ComplianceFrameworkService.get_requirements(
        db,
        framework_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/frameworks/{framework_id}",
    response_model=ComplianceFrameworkOut,
)
async def update_framework(
    framework_id: int,
    payload: ComplianceFrameworkUpdate,
    db: DBSession,
) -> ComplianceFrameworkOut:
    return await ComplianceFrameworkService.update(
        db,
        framework_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/frameworks/{framework_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_framework(
    framework_id: int,
    db: DBSession,
) -> Response:
    await ComplianceFrameworkService.delete(db, framework_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Compliance Requirements ───────────────────────────────────────────────────

@router.post(
    "/requirements",
    response_model=ComplianceRequirementOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement(
    payload: ComplianceRequirementCreate,
    db: DBSession,
) -> ComplianceRequirementOut:
    return await ComplianceRequirementService.create(db, payload.model_dump())


@router.get(
    "/requirements",
    response_model=list[ComplianceRequirementOut],
)
async def list_requirements(
    db: DBSession,
    framework_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceRequirementOut]:
    return await ComplianceRequirementService.list(
        db,
        framework_id=framework_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/requirements/{requirement_id}",
    response_model=ComplianceRequirementOut,
)
async def get_requirement(
    requirement_id: int,
    db: DBSession,
) -> ComplianceRequirementOut:
    return await ComplianceRequirementService.get_by_id(db, requirement_id)


@router.patch(
    "/requirements/{requirement_id}",
    response_model=ComplianceRequirementOut,
)
async def update_requirement(
    requirement_id: int,
    payload: ComplianceRequirementUpdate,
    db: DBSession,
) -> ComplianceRequirementOut:
    return await ComplianceRequirementService.update(
        db,
        requirement_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_requirement(
    requirement_id: int,
    db: DBSession,
) -> Response:
    await ComplianceRequirementService.delete(db, requirement_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Organization Compliance ───────────────────────────────────────────────────

@router.post(
    "/organization-compliance",
    response_model=OrganizationComplianceOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization_compliance(
    payload: OrganizationComplianceCreate,
    db: DBSession,
) -> OrganizationComplianceOut:
    return await OrganizationComplianceService.create(db, payload.model_dump())


@router.get(
    "/organization-compliance",
    response_model=list[OrganizationComplianceOut],
)
async def list_organization_compliance(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    requirement_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    assigned_to: int | None = Query(default=None),
    due_before: str | None = Query(default=None),
    expiry_before: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[OrganizationComplianceOut]:
    from datetime import datetime

    due_before_dt = datetime.fromisoformat(due_before) if due_before else None
    expiry_before_dt = datetime.fromisoformat(expiry_before) if expiry_before else None

    return await OrganizationComplianceService.list(
        db,
        organization_id=organization_id,
        requirement_id=requirement_id,
        status=status_filter,
        assigned_to=assigned_to,
        due_before=due_before_dt,
        expiry_before=expiry_before_dt,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/organization-compliance/{compliance_id}",
    response_model=OrganizationComplianceOut,
)
async def get_organization_compliance(
    compliance_id: int,
    db: DBSession,
) -> OrganizationComplianceOut:
    return await OrganizationComplianceService.get_by_id(db, compliance_id)


@router.get(
    "/organization-compliance/{compliance_id}/evidence",
    response_model=list[ComplianceEvidenceOut],
)
async def get_organization_compliance_evidence(
    compliance_id: int,
    db: DBSession,
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceEvidenceOut]:
    return await OrganizationComplianceService.get_evidence(
        db,
        compliance_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/organization-compliance/{compliance_id}/status-history",
    response_model=list[ComplianceStatusHistoryOut],
)
async def get_organization_compliance_status_history(
    compliance_id: int,
    db: DBSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceStatusHistoryOut]:
    return await OrganizationComplianceService.get_status_history(
        db,
        compliance_id,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/organization-compliance/{compliance_id}",
    response_model=OrganizationComplianceOut,
)
async def update_organization_compliance(
    compliance_id: int,
    payload: OrganizationComplianceUpdate,
    db: DBSession,
    changed_by: int | None = Query(default=None),
    change_reason: str | None = Query(default=None),
) -> OrganizationComplianceOut:
    return await OrganizationComplianceService.update(
        db,
        compliance_id,
        payload.model_dump(exclude_unset=True),
        changed_by=changed_by,
        change_reason=change_reason,
    )


@router.delete(
    "/organization-compliance/{compliance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_organization_compliance(
    compliance_id: int,
    db: DBSession,
) -> Response:
    await OrganizationComplianceService.delete(db, compliance_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Location Compliance ───────────────────────────────────────────────────────

@router.post(
    "/location-compliance",
    response_model=LocationComplianceOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_location_compliance(
    payload: LocationComplianceCreate,
    db: DBSession,
) -> LocationComplianceOut:
    return await LocationComplianceService.create(db, payload.model_dump())


@router.get(
    "/location-compliance",
    response_model=list[LocationComplianceOut],
)
async def list_location_compliance(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    requirement_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    assigned_to: int | None = Query(default=None),
    due_before: str | None = Query(default=None),
    expiry_before: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[LocationComplianceOut]:
    from datetime import datetime

    due_before_dt = datetime.fromisoformat(due_before) if due_before else None
    expiry_before_dt = datetime.fromisoformat(expiry_before) if expiry_before else None

    return await LocationComplianceService.list(
        db,
        organization_id=organization_id,
        location_id=location_id,
        requirement_id=requirement_id,
        status=status_filter,
        assigned_to=assigned_to,
        due_before=due_before_dt,
        expiry_before=expiry_before_dt,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/location-compliance/{compliance_id}",
    response_model=LocationComplianceOut,
)
async def get_location_compliance(
    compliance_id: int,
    db: DBSession,
) -> LocationComplianceOut:
    return await LocationComplianceService.get_by_id(db, compliance_id)


@router.get(
    "/location-compliance/{compliance_id}/evidence",
    response_model=list[ComplianceEvidenceOut],
)
async def get_location_compliance_evidence(
    compliance_id: int,
    db: DBSession,
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceEvidenceOut]:
    return await LocationComplianceService.get_evidence(
        db,
        compliance_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/location-compliance/{compliance_id}/status-history",
    response_model=list[ComplianceStatusHistoryOut],
)
async def get_location_compliance_status_history(
    compliance_id: int,
    db: DBSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceStatusHistoryOut]:
    return await LocationComplianceService.get_status_history(
        db,
        compliance_id,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/location-compliance/{compliance_id}",
    response_model=LocationComplianceOut,
)
async def update_location_compliance(
    compliance_id: int,
    payload: LocationComplianceUpdate,
    db: DBSession,
    changed_by: int | None = Query(default=None),
    change_reason: str | None = Query(default=None),
) -> LocationComplianceOut:
    return await LocationComplianceService.update(
        db,
        compliance_id,
        payload.model_dump(exclude_unset=True),
        changed_by=changed_by,
        change_reason=change_reason,
    )


@router.delete(
    "/location-compliance/{compliance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location_compliance(
    compliance_id: int,
    db: DBSession,
) -> Response:
    await LocationComplianceService.delete(db, compliance_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Compliance Evidence ───────────────────────────────────────────────────────

@router.post(
    "/evidence",
    response_model=ComplianceEvidenceOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_evidence(
    payload: ComplianceEvidenceCreate,
    db: DBSession,
) -> ComplianceEvidenceOut:
    return await ComplianceEvidenceService.create(db, payload.model_dump())


@router.get(
    "/evidence",
    response_model=list[ComplianceEvidenceOut],
)
async def list_evidence(
    db: DBSession,
    organization_compliance_id: int | None = Query(default=None),
    location_compliance_id: int | None = Query(default=None),
    submitted_by: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    evidence_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceEvidenceOut]:
    return await ComplianceEvidenceService.list(
        db,
        organization_compliance_id=organization_compliance_id,
        location_compliance_id=location_compliance_id,
        submitted_by=submitted_by,
        status=status_filter,
        evidence_type=evidence_type,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/evidence/{evidence_id}",
    response_model=ComplianceEvidenceOut,
)
async def get_evidence(
    evidence_id: int,
    db: DBSession,
) -> ComplianceEvidenceOut:
    return await ComplianceEvidenceService.get_by_id(db, evidence_id)


@router.get(
    "/evidence/{evidence_id}/reviews",
    response_model=list[ComplianceReviewOut],
)
async def get_evidence_reviews(
    evidence_id: int,
    db: DBSession,
    review_status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceReviewOut]:
    return await ComplianceEvidenceService.get_reviews(
        db,
        evidence_id,
        review_status=review_status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/evidence/{evidence_id}/documents",
    response_model=list[ComplianceDocumentOut],
)
async def get_evidence_documents(
    evidence_id: int,
    db: DBSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceDocumentOut]:
    return await ComplianceEvidenceService.get_documents(
        db,
        evidence_id,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/evidence/{evidence_id}",
    response_model=ComplianceEvidenceOut,
)
async def update_evidence(
    evidence_id: int,
    payload: ComplianceEvidenceUpdate,
    db: DBSession,
) -> ComplianceEvidenceOut:
    return await ComplianceEvidenceService.update(
        db,
        evidence_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/evidence/{evidence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_evidence(
    evidence_id: int,
    db: DBSession,
) -> Response:
    await ComplianceEvidenceService.delete(db, evidence_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Compliance Reviews ────────────────────────────────────────────────────────

@router.post(
    "/reviews",
    response_model=ComplianceReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    payload: ComplianceReviewCreate,
    db: DBSession,
) -> ComplianceReviewOut:
    return await ComplianceReviewService.create(db, payload.model_dump())


@router.get(
    "/reviews",
    response_model=list[ComplianceReviewOut],
)
async def list_reviews(
    db: DBSession,
    evidence_id: int | None = Query(default=None),
    reviewer_id: int | None = Query(default=None),
    review_status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceReviewOut]:
    return await ComplianceReviewService.list(
        db,
        evidence_id=evidence_id,
        reviewer_id=reviewer_id,
        review_status=review_status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/reviews/{review_id}",
    response_model=ComplianceReviewOut,
)
async def get_review(
    review_id: int,
    db: DBSession,
) -> ComplianceReviewOut:
    return await ComplianceReviewService.get_by_id(db, review_id)


@router.patch(
    "/reviews/{review_id}",
    response_model=ComplianceReviewOut,
)
async def update_review(
    review_id: int,
    payload: ComplianceReviewUpdate,
    db: DBSession,
) -> ComplianceReviewOut:
    return await ComplianceReviewService.update(
        db,
        review_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    review_id: int,
    db: DBSession,
) -> Response:
    await ComplianceReviewService.delete(db, review_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Compliance Documents ──────────────────────────────────────────────────────

@router.post(
    "/documents",
    response_model=ComplianceDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    payload: ComplianceDocumentCreate,
    db: DBSession,
) -> ComplianceDocumentOut:
    return await ComplianceDocumentService.create(db, payload.model_dump())


@router.get(
    "/documents",
    response_model=list[ComplianceDocumentOut],
)
async def list_documents(
    db: DBSession,
    evidence_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceDocumentOut]:
    return await ComplianceDocumentService.list(
        db,
        evidence_id=evidence_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/documents/{document_id}",
    response_model=ComplianceDocumentOut,
)
async def get_document(
    document_id: int,
    db: DBSession,
) -> ComplianceDocumentOut:
    return await ComplianceDocumentService.get_by_id(db, document_id)


@router.get(
    "/documents/{document_id}/versions",
    response_model=list[ComplianceDocumentVersionOut],
)
async def get_document_versions(
    document_id: int,
    db: DBSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceDocumentVersionOut]:
    return await ComplianceDocumentService.get_versions(
        db,
        document_id,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/documents/{document_id}",
    response_model=ComplianceDocumentOut,
)
async def update_document(
    document_id: int,
    payload: ComplianceDocumentCreate,
    db: DBSession,
) -> ComplianceDocumentOut:
    return await ComplianceDocumentService.update(
        db,
        document_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: int,
    db: DBSession,
) -> Response:
    await ComplianceDocumentService.delete(db, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Compliance Document Versions ──────────────────────────────────────────────

@router.post(
    "/document-versions",
    response_model=ComplianceDocumentVersionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_document_version(
    payload: ComplianceDocumentVersionCreate,
    db: DBSession,
) -> ComplianceDocumentVersionOut:
    return await ComplianceDocumentVersionService.create(db, payload.model_dump())


@router.get(
    "/document-versions",
    response_model=list[ComplianceDocumentVersionOut],
)
async def list_document_versions(
    db: DBSession,
    document_id: int | None = Query(default=None),
    changed_by: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceDocumentVersionOut]:
    return await ComplianceDocumentVersionService.list(
        db,
        document_id=document_id,
        changed_by=changed_by,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/document-versions/{version_id}",
    response_model=ComplianceDocumentVersionOut,
)
async def get_document_version(
    version_id: int,
    db: DBSession,
) -> ComplianceDocumentVersionOut:
    return await ComplianceDocumentVersionService.get_by_id(db, version_id)


@router.delete(
    "/document-versions/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document_version(
    version_id: int,
    db: DBSession,
) -> Response:
    await ComplianceDocumentVersionService.delete(db, version_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Compliance Status History ─────────────────────────────────────────────────

@router.get(
    "/status-history",
    response_model=list[ComplianceStatusHistoryOut],
)
async def list_status_history(
    db: DBSession,
    organization_compliance_id: int | None = Query(default=None),
    location_compliance_id: int | None = Query(default=None),
    changed_by: int | None = Query(default=None),
    new_status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceStatusHistoryOut]:
    return await ComplianceStatusHistoryService.list(
        db,
        organization_compliance_id=organization_compliance_id,
        location_compliance_id=location_compliance_id,
        changed_by=changed_by,
        new_status=new_status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/status-history/{history_id}",
    response_model=ComplianceStatusHistoryOut,
)
async def get_status_history_item(
    history_id: int,
    db: DBSession,
) -> ComplianceStatusHistoryOut:
    return await ComplianceStatusHistoryService.get_by_id(db, history_id)


# ── Compliance Alerts ─────────────────────────────────────────────────────────

@router.post(
    "/alerts",
    response_model=ComplianceAlertOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_alert(
    payload: ComplianceAlertCreate,
    db: DBSession,
) -> ComplianceAlertOut:
    return await ComplianceAlertService.create(db, payload.model_dump())


@router.get(
    "/alerts",
    response_model=list[ComplianceAlertOut],
)
async def list_alerts(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    requirement_id: int | None = Query(default=None),
    document_id: int | None = Query(default=None),
    alert_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    is_resolved: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceAlertOut]:
    return await ComplianceAlertService.list(
        db,
        organization_id=organization_id,
        location_id=location_id,
        requirement_id=requirement_id,
        document_id=document_id,
        alert_type=alert_type,
        severity=severity,
        is_resolved=is_resolved,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/alerts/{alert_id}",
    response_model=ComplianceAlertOut,
)
async def get_alert(
    alert_id: int,
    db: DBSession,
) -> ComplianceAlertOut:
    return await ComplianceAlertService.get_by_id(db, alert_id)


@router.patch(
    "/alerts/{alert_id}",
    response_model=ComplianceAlertOut,
)
async def update_alert(
    alert_id: int,
    payload: ComplianceAlertUpdate,
    db: DBSession,
) -> ComplianceAlertOut:
    return await ComplianceAlertService.update(
        db,
        alert_id,
        payload.model_dump(exclude_unset=True),
    )


@router.post(
    "/alerts/{alert_id}/resolve",
    response_model=ComplianceAlertOut,
)
async def resolve_alert(
    alert_id: int,
    payload: ComplianceAlertResolveRequest,
    db: DBSession,
) -> ComplianceAlertOut:
    return await ComplianceAlertService.resolve(
        db,
        alert_id,
        resolved_by=payload.resolved_by,
    )


@router.delete(
    "/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_alert(
    alert_id: int,
    db: DBSession,
) -> Response:
    await ComplianceAlertService.delete(db, alert_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Compliance Scores ─────────────────────────────────────────────────────────

@router.post(
    "/scores",
    response_model=ComplianceScoreOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_score(
    payload: ComplianceScoreCreate,
    db: DBSession,
) -> ComplianceScoreOut:
    return await ComplianceScoreService.create(db, payload.model_dump())


@router.get(
    "/scores",
    response_model=list[ComplianceScoreOut],
)
async def list_scores(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    framework_id: int | None = Query(default=None),
    period_start: str | None = Query(default=None),
    period_end: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ComplianceScoreOut]:
    from datetime import datetime

    period_start_dt = datetime.fromisoformat(period_start) if period_start else None
    period_end_dt = datetime.fromisoformat(period_end) if period_end else None

    return await ComplianceScoreService.list(
        db,
        organization_id=organization_id,
        location_id=location_id,
        framework_id=framework_id,
        period_start=period_start_dt,
        period_end=period_end_dt,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/scores/{score_id}",
    response_model=ComplianceScoreOut,
)
async def get_score(
    score_id: int,
    db: DBSession,
) -> ComplianceScoreOut:
    return await ComplianceScoreService.get_by_id(db, score_id)


@router.patch(
    "/scores/{score_id}",
    response_model=ComplianceScoreOut,
)
async def update_score(
    score_id: int,
    payload: ComplianceScoreUpdate,
    db: DBSession,
) -> ComplianceScoreOut:
    return await ComplianceScoreService.update(
        db,
        score_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/scores/{score_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_score(
    score_id: int,
    db: DBSession,
) -> Response:
    await ComplianceScoreService.delete(db, score_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)