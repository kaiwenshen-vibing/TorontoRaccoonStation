from pydantic import BaseModel, Field, model_validator


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    pic_storage_key: str | None = None


class UpdateRoomRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    pic_storage_key: str | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateRoomRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        return self


class RoomItem(BaseModel):
    store_room_id: int
    store_id: int
    name: str
    is_active: bool
    pic_storage_key: str | None = None


class RoomListResponse(BaseModel):
    items: list[RoomItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int
