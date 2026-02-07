from datetime import date

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator


class BookingConflictSummary(BaseModel):
    has_conflict: bool = False
    conflict_count: int = 0
    conflict_booking_ids: list[int] = Field(default_factory=list)


class BookingItem(BaseModel):
    booking_id: int
    store_id: int
    script_id: int | None
    booking_status_id: int
    target_month: date | None
    start_at: AwareDatetime | None
    end_at: AwareDatetime | None
    duration_override_minutes: int | None
    client_ids: list[int] = Field(default_factory=list)
    has_conflict: bool = False
    conflict_count: int = 0
    conflict_booking_ids: list[int] = Field(default_factory=list)


class BookingListResponse(BaseModel):
    items: list[BookingItem] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class CreateIncompleteBookingRequest(BaseModel):
    target_month: date
    client_ids: list[int] = Field(min_length=1)
    script_id: int | None = Field(default=None, ge=1)

    @field_validator("target_month")
    @classmethod
    def target_month_must_be_first_day(cls, value: date) -> date:
        if value.day != 1:
            raise ValueError("target_month must be first day of month (YYYY-MM-01).")
        return value


class UpdateIncompleteBookingRequest(BaseModel):
    target_month: date | None = None
    script_id: int | None = Field(default=None, ge=1)
    clear_script: bool = False

    @field_validator("target_month")
    @classmethod
    def target_month_must_be_first_day(cls, value: date | None) -> date | None:
        if value is not None and value.day != 1:
            raise ValueError("target_month must be first day of month (YYYY-MM-01).")
        return value


class ConfirmBookingRequest(BaseModel):
    start_at: AwareDatetime
    preferred_room_id: int | None = Field(default=None, ge=1)


class AddBookingClientRequest(BaseModel):
    client_id: int = Field(ge=1)


class CreateCharacterClientMatchRequest(BaseModel):
    character_id: int = Field(ge=1)
    client_id: int = Field(ge=1)


class UpdateCharacterClientMatchRequest(BaseModel):
    character_id: int | None = Field(default=None, ge=1)
    client_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def require_any_field(self):
        if self.character_id is None and self.client_id is None:
            raise ValueError("At least one of character_id or client_id must be set.")
        return self


class CharacterClientMatchItem(BaseModel):
    character_client_match_id: int
    booking_id: int
    character_id: int
    client_id: int


class CreateCharacterDmMatchRequest(BaseModel):
    dm_id: int = Field(ge=1)
    character_id: int | None = Field(default=None, ge=1)


class UpdateCharacterDmMatchRequest(BaseModel):
    dm_id: int | None = Field(default=None, ge=1)
    character_id: int | None = Field(default=None, ge=1)
    clear_character: bool = False

    @model_validator(mode="after")
    def require_any_field(self):
        if self.dm_id is None and self.character_id is None and not self.clear_character:
            raise ValueError("Provide dm_id, character_id, or clear_character.")
        return self


class CharacterDmMatchItem(BaseModel):
    character_dm_match_id: int
    booking_id: int
    dm_id: int
    character_id: int | None

