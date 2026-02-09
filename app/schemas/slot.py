from pydantic import AwareDatetime, BaseModel, Field, model_validator


class CreateSlotRequest(BaseModel):
    start_at: AwareDatetime


class UpdateSlotRequest(BaseModel):
    start_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateSlotRequest":
        if self.start_at is None:
            raise ValueError("At least one field must be provided.")
        return self


class SlotItem(BaseModel):
    slot_id: int
    store_id: int
    start_at: AwareDatetime


class SlotListResponse(BaseModel):
    items: list[SlotItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int
