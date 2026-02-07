from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UpdateRoomRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None


class RoomItem(BaseModel):
    store_room_id: int
    store_id: int
    name: str
    is_active: bool


class RoomListResponse(BaseModel):
    items: list[RoomItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int

