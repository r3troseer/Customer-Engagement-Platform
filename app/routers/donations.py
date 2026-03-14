"""
FR9 — Donations and ESG Offset
API router for donation causes, donations, conversions,
impacts, and attributions.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.dependencies.db import DBSession
from app.schemas.donations import (
    DonationAttributionCreate,
    DonationAttributionOut,
    DonationAttributionUpdate,
    DonationCauseCreate,
    DonationCauseOut,
    DonationCauseUpdate,
    DonationConversionCreate,
    DonationConversionOut,
    DonationConversionUpdate,
    DonationCreate,
    DonationDetailOut,
    DonationImpactCreate,
    DonationImpactOut,
    DonationImpactUpdate,
    DonationOut,
    DonationUpdate,
)
from app.services.donations_service import (
    DonationAttributionService,
    DonationCauseService,
    DonationConversionService,
    DonationImpactService,
    DonationService,
)

router = APIRouter(prefix="/donations", tags=["FR9 — Donations & ESG Offset"])


# ── Donation Causes ───────────────────────────────────────────────────────────

@router.post(
    "/causes",
    response_model=DonationCauseOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation_cause(
    payload: DonationCauseCreate,
    db: DBSession,
) -> DonationCauseOut:
    return await DonationCauseService.create(db, payload.model_dump())


@router.get(
    "/causes",
    response_model=list[DonationCauseOut],
)
async def list_donation_causes(
    db: DBSession,
    organization_id: int | None = Query(default=None),
    cause_type: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationCauseOut]:
    return await DonationCauseService.list(
        db,
        organization_id=organization_id,
        cause_type=cause_type,
        is_active=is_active,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/causes/{cause_id}",
    response_model=DonationCauseOut,
)
async def get_donation_cause(
    cause_id: int,
    db: DBSession,
) -> DonationCauseOut:
    return await DonationCauseService.get_by_id(db, cause_id)


@router.get(
    "/causes/{cause_id}/donations",
    response_model=list[DonationOut],
)
async def get_cause_donations(
    cause_id: int,
    db: DBSession,
    user_id: int | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationOut]:
    return await DonationCauseService.get_donations(
        db,
        cause_id,
        user_id=user_id,
        organization_id=organization_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/organizations/{organization_id}/causes",
    response_model=list[DonationCauseOut],
)
async def get_organization_donation_causes(
    organization_id: int,
    db: DBSession,
    cause_type: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationCauseOut]:
    return await DonationCauseService.list(
        db,
        organization_id=organization_id,
        cause_type=cause_type,
        is_active=is_active,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/causes/{cause_id}",
    response_model=DonationCauseOut,
)
async def update_donation_cause(
    cause_id: int,
    payload: DonationCauseUpdate,
    db: DBSession,
) -> DonationCauseOut:
    return await DonationCauseService.update(
        db,
        cause_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/causes/{cause_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_donation_cause(
    cause_id: int,
    db: DBSession,
) -> Response:
    await DonationCauseService.delete(db, cause_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Donations ─────────────────────────────────────────────────────────────────

@router.post(
    "/records",
    response_model=DonationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation(
    payload: DonationCreate,
    db: DBSession,
) -> DonationOut:
    return await DonationService.create(db, payload.model_dump())


@router.get(
    "/records",
    response_model=list[DonationOut],
)
async def list_donations(
    db: DBSession,
    user_id: int | None = Query(default=None),
    cause_id: int | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    wallet_transaction_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationOut]:
    return await DonationService.list(
        db,
        user_id=user_id,
        cause_id=cause_id,
        organization_id=organization_id,
        wallet_transaction_id=wallet_transaction_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/records/{donation_id}",
    response_model=DonationOut,
)
async def get_donation(
    donation_id: int,
    db: DBSession,
) -> DonationOut:
    return await DonationService.get_by_id(db, donation_id)


@router.get(
    "/records/{donation_id}/detail",
    response_model=DonationDetailOut,
)
async def get_donation_detail(
    donation_id: int,
    db: DBSession,
) -> DonationDetailOut:
    return await DonationService.get_detail(db, donation_id)


@router.get(
    "/organizations/{organization_id}/donations",
    response_model=list[DonationOut],
)
async def get_organization_donations(
    organization_id: int,
    db: DBSession,
    user_id: int | None = Query(default=None),
    cause_id: int | None = Query(default=None),
    wallet_transaction_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationOut]:
    return await DonationService.list(
        db,
        user_id=user_id,
        cause_id=cause_id,
        organization_id=organization_id,
        wallet_transaction_id=wallet_transaction_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/users/{user_id}/donations",
    response_model=list[DonationOut],
)
async def get_user_donations(
    user_id: int,
    db: DBSession,
    cause_id: int | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    wallet_transaction_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationOut]:
    return await DonationService.list(
        db,
        user_id=user_id,
        cause_id=cause_id,
        organization_id=organization_id,
        wallet_transaction_id=wallet_transaction_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/records/{donation_id}/conversion",
    response_model=DonationConversionOut | None,
)
async def get_donation_conversion(
    donation_id: int,
    db: DBSession,
) -> DonationConversionOut | None:
    return await DonationService.get_conversion(db, donation_id)


@router.get(
    "/records/{donation_id}/impacts",
    response_model=list[DonationImpactOut],
)
async def get_donation_impacts(
    donation_id: int,
    db: DBSession,
    impact_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationImpactOut]:
    return await DonationService.get_impacts(
        db,
        donation_id,
        impact_type=impact_type,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/records/{donation_id}/attributions",
    response_model=list[DonationAttributionOut],
)
async def get_donation_attributions(
    donation_id: int,
    db: DBSession,
    user_id: int | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationAttributionOut]:
    return await DonationService.get_attributions(
        db,
        donation_id,
        user_id=user_id,
        organization_id=organization_id,
        offset=offset,
        limit=limit,
    )


@router.patch(
    "/records/{donation_id}",
    response_model=DonationOut,
)
async def update_donation(
    donation_id: int,
    payload: DonationUpdate,
    db: DBSession,
) -> DonationOut:
    return await DonationService.update(
        db,
        donation_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/records/{donation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_donation(
    donation_id: int,
    db: DBSession,
) -> Response:
    await DonationService.delete(db, donation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Donation Conversions ──────────────────────────────────────────────────────

@router.post(
    "/conversions",
    response_model=DonationConversionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation_conversion(
    payload: DonationConversionCreate,
    db: DBSession,
) -> DonationConversionOut:
    return await DonationConversionService.create(db, payload.model_dump())


@router.get(
    "/conversions",
    response_model=list[DonationConversionOut],
)
async def list_donation_conversions(
    db: DBSession,
    donation_id: int | None = Query(default=None),
    conversion_currency: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationConversionOut]:
    return await DonationConversionService.list(
        db,
        donation_id=donation_id,
        conversion_currency=conversion_currency,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/conversions/{conversion_id}",
    response_model=DonationConversionOut,
)
async def get_donation_conversion_by_id(
    conversion_id: int,
    db: DBSession,
) -> DonationConversionOut:
    return await DonationConversionService.get_by_id(db, conversion_id)


@router.patch(
    "/conversions/{conversion_id}",
    response_model=DonationConversionOut,
)
async def update_donation_conversion(
    conversion_id: int,
    payload: DonationConversionUpdate,
    db: DBSession,
) -> DonationConversionOut:
    return await DonationConversionService.update(
        db,
        conversion_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/conversions/{conversion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_donation_conversion(
    conversion_id: int,
    db: DBSession,
) -> Response:
    await DonationConversionService.delete(db, conversion_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Donation Impacts ──────────────────────────────────────────────────────────

@router.post(
    "/impacts",
    response_model=DonationImpactOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation_impact(
    payload: DonationImpactCreate,
    db: DBSession,
) -> DonationImpactOut:
    return await DonationImpactService.create(db, payload.model_dump())


@router.get(
    "/impacts",
    response_model=list[DonationImpactOut],
)
async def list_donation_impacts(
    db: DBSession,
    donation_id: int | None = Query(default=None),
    impact_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationImpactOut]:
    return await DonationImpactService.list(
        db,
        donation_id=donation_id,
        impact_type=impact_type,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/impacts/{impact_id}",
    response_model=DonationImpactOut,
)
async def get_donation_impact(
    impact_id: int,
    db: DBSession,
) -> DonationImpactOut:
    return await DonationImpactService.get_by_id(db, impact_id)


@router.patch(
    "/impacts/{impact_id}",
    response_model=DonationImpactOut,
)
async def update_donation_impact(
    impact_id: int,
    payload: DonationImpactUpdate,
    db: DBSession,
) -> DonationImpactOut:
    return await DonationImpactService.update(
        db,
        impact_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/impacts/{impact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_donation_impact(
    impact_id: int,
    db: DBSession,
) -> Response:
    await DonationImpactService.delete(db, impact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Donation Attributions ─────────────────────────────────────────────────────

@router.post(
    "/attributions",
    response_model=DonationAttributionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_donation_attribution(
    payload: DonationAttributionCreate,
    db: DBSession,
) -> DonationAttributionOut:
    return await DonationAttributionService.create(db, payload.model_dump())


@router.get(
    "/attributions",
    response_model=list[DonationAttributionOut],
)
async def list_donation_attributions(
    db: DBSession,
    donation_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[DonationAttributionOut]:
    return await DonationAttributionService.list(
        db,
        donation_id=donation_id,
        user_id=user_id,
        organization_id=organization_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/attributions/{attribution_id}",
    response_model=DonationAttributionOut,
)
async def get_donation_attribution(
    attribution_id: int,
    db: DBSession,
) -> DonationAttributionOut:
    return await DonationAttributionService.get_by_id(db, attribution_id)


@router.patch(
    "/attributions/{attribution_id}",
    response_model=DonationAttributionOut,
)
async def update_donation_attribution(
    attribution_id: int,
    payload: DonationAttributionUpdate,
    db: DBSession,
) -> DonationAttributionOut:
    return await DonationAttributionService.update(
        db,
        attribution_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/attributions/{attribution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_donation_attribution(
    attribution_id: int,
    db: DBSession,
) -> Response:
    await DonationAttributionService.delete(db, attribution_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
