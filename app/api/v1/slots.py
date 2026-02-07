from fastapi import APIRouter, Depends, Query, Response, status

from app.core.dependencies import get_slot_service
from app.schemas.slot import CreateSlotRequest, SlotItem, SlotListResponse, UpdateSlotRequest
from app.services.slot_service import SlotService

router = APIRouter(prefix="/stores/{store_id}/slots")


@router.get("", response_model=SlotListResponse)
async def list_slots(
    store_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: SlotService = Depends(get_slot_service),
) -> SlotListResponse:
    return await service.list_slots(store_id=store_id, limit=limit, offset=offset)


@router.post("", response_model=SlotItem, status_code=status.HTTP_201_CREATED)
async def create_slot(
    store_id: int,
    payload: CreateSlotRequest,
    service: SlotService = Depends(get_slot_service),
) -> SlotItem:
    return await service.create_slot(store_id=store_id, payload=payload)


@router.patch("/{slot_id}", response_model=SlotItem)
async def update_slot(
    store_id: int,
    slot_id: int,
    payload: UpdateSlotRequest,
    service: SlotService = Depends(get_slot_service),
) -> SlotItem:
    return await service.update_slot(store_id=store_id, slot_id=slot_id, payload=payload)


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    store_id: int,
    slot_id: int,
    service: SlotService = Depends(get_slot_service),
) -> Response:
    await service.delete_slot(store_id=store_id, slot_id=slot_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

