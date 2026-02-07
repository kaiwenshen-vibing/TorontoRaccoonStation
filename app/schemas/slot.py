from pydantic import AwareDatetime, BaseModel, Field


class CreateSlotRequest(BaseModel):
    start_at: AwareDatetime


class UpdateSlotRequest(BaseModel):
    start_at: AwareDatetime | None = None


class SlotItem(BaseModel):
    slot_id: int
    store_id: int
    start_at: AwareDatetime


class SlotListResponse(BaseModel):
    items: list[SlotItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int

