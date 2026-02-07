from app.core.errors import FeatureNotImplementedError
from app.schemas.room import CreateRoomRequest, RoomItem, RoomListResponse, UpdateRoomRequest
from app.services.base import BaseService


class RoomService(BaseService):
    async def list_rooms(self, store_id: int, limit: int, offset: int) -> RoomListResponse:
        raise FeatureNotImplementedError("list_rooms is not implemented yet.")

    async def create_room(self, store_id: int, payload: CreateRoomRequest) -> RoomItem:
        raise FeatureNotImplementedError("create_room is not implemented yet.")

    async def update_room(
        self,
        store_id: int,
        store_room_id: int,
        payload: UpdateRoomRequest,
    ) -> RoomItem:
        raise FeatureNotImplementedError("update_room is not implemented yet.")

