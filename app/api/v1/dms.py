from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_dm_service
from app.schemas.dm import (
    CreateDmRequest,
    CreateDmStoreMembershipRequest,
    DmItem,
    DmListResponse,
    DmStoreMembershipItem,
    DmStoreMembershipListResponse,
    UpdateDmRequest,
)
from app.services.dm_service import DmService

router = APIRouter(prefix="/dms")


@router.get("", response_model=DmListResponse)
async def list_dms(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: DmService = Depends(get_dm_service),
) -> DmListResponse:
    return await service.list_dms(limit=limit, offset=offset)


@router.post("", response_model=DmItem, status_code=status.HTTP_201_CREATED)
async def create_dm(
    payload: CreateDmRequest,
    service: DmService = Depends(get_dm_service),
) -> DmItem:
    return await service.create_dm(payload=payload)


@router.get("/{dm_id}", response_model=DmItem)
async def get_dm(
    dm_id: int,
    service: DmService = Depends(get_dm_service),
) -> DmItem:
    return await service.get_dm(dm_id=dm_id)


@router.patch("/{dm_id}", response_model=DmItem)
async def update_dm(
    dm_id: int,
    payload: UpdateDmRequest,
    service: DmService = Depends(get_dm_service),
) -> DmItem:
    return await service.update_dm(dm_id=dm_id, payload=payload)


@router.delete("/{dm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dm(
    dm_id: int,
    service: DmService = Depends(get_dm_service),
) -> Response:
    await service.delete_dm(dm_id=dm_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{dm_id}/stores", response_model=DmStoreMembershipListResponse)
async def list_dm_store_memberships(
    dm_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: DmService = Depends(get_dm_service),
) -> DmStoreMembershipListResponse:
    return await service.list_dm_store_memberships(dm_id=dm_id, limit=limit, offset=offset)


@router.post("/{dm_id}/stores", response_model=DmStoreMembershipItem, status_code=status.HTTP_201_CREATED)
async def create_dm_store_membership(
    dm_id: int,
    payload: CreateDmStoreMembershipRequest,
    service: DmService = Depends(get_dm_service),
) -> DmStoreMembershipItem:
    return await service.create_dm_store_membership(dm_id=dm_id, payload=payload)


@router.delete("/{dm_id}/stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dm_store_membership(
    dm_id: int,
    store_id: int,
    service: DmService = Depends(get_dm_service),
) -> Response:
    await service.delete_dm_store_membership(dm_id=dm_id, store_id=store_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
