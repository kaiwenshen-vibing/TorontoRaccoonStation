from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_room_service
from app.schemas.room import CreateRoomRequest, RoomItem, RoomListResponse, UpdateRoomRequest
from app.services.room_service import RoomService

router = APIRouter(prefix="/stores/{store_id}/rooms")


@router.get("", response_model=RoomListResponse)
async def list_rooms(
    store_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: RoomService = Depends(get_room_service),
) -> RoomListResponse:
    return await service.list_rooms(store_id=store_id, limit=limit, offset=offset)


@router.post("", response_model=RoomItem, status_code=status.HTTP_201_CREATED)
async def create_room(
    store_id: int,
    payload: CreateRoomRequest,
    service: RoomService = Depends(get_room_service),
) -> RoomItem:
    return await service.create_room(store_id=store_id, payload=payload)


@router.patch("/{store_room_id}", response_model=RoomItem)
async def update_room(
    store_id: int,
    store_room_id: int,
    payload: UpdateRoomRequest,
    service: RoomService = Depends(get_room_service),
) -> RoomItem:
    return await service.update_room(
        store_id=store_id,
        store_room_id=store_room_id,
        payload=payload,
    )

